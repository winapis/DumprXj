#!/bin/bash
# DumprX Git Operations Module - Git functionality for repository management
# Provides git operations, commit handling, and remote repository management

# Load required modules
source "$(dirname "${BASH_SOURCE[0]}")/ui.sh"

# Git configuration
setup_git_config() {
    local email="${1:-guptasushrut@gmail.com}"
    local name="${2:-DumprX Bot}"
    
    msg_process "Configuring Git settings"
    
    # Configure git for large files
    git config --global http.postBuffer 524288000
    
    # Set user info if not already set
    if [[ -z "$(git config --get user.email)" ]]; then
        git config user.email "${email}"
        msg_info "Git email set to: ${email}"
    fi
    
    if [[ -z "$(git config --get user.name)" ]]; then
        git config user.name "${name}"
        msg_info "Git name set to: ${name}"
    fi
}

# Initialize git repository
init_git_repo() {
    local branch="${1:-main}"
    
    msg_process "Initializing Git repository"
    
    git init
    setup_git_config
    
    # Create or switch to branch
    if ! git checkout -b "${branch}" 2>/dev/null; then
        if ! git checkout "${branch}" 2>/dev/null; then
            # If branch creation fails, try incremental naming
            local incremental="${branch}-$(date +%s)"
            git checkout -b "${incremental}"
            export branch="${incremental}"
            msg_info "Using branch: ${incremental}"
        fi
    fi
    
    msg_success "Git repository initialized on branch: ${branch}"
}

# Generate gitignore for sensitive files
create_gitignore() {
    local gitignore_content
    
    # Find sensitive files to ignore
    gitignore_content=$(find . \( -name "*sensetime*" -o -name "*.lic" \) 2>/dev/null | cut -d'/' -f'2-')
    
    if [[ -n "${gitignore_content}" ]]; then
        echo "${gitignore_content}" > .gitignore
        msg_info "Created .gitignore with $(echo "${gitignore_content}" | wc -l) entries"
    else
        # Create basic gitignore
        cat > .gitignore << 'EOF'
# Temporary files
*.tmp
*.temp
.DS_Store

# Sensitive files
*sensetime*
*.lic
github_token
gitlab_token
tg_token
tg_chat

# Build artifacts
*.log
EOF
        msg_info "Created basic .gitignore"
    fi
}

# Write SHA1 checksums
write_sha1sum() {
    local description="$1"
    
    msg_process "Generating SHA1 checksums"
    
    find . -type f \( -name "*.img" -o -name "*.bin" -o -name "*.dat" \) -exec sha1sum {} + > sha1sum.txt 2>/dev/null
    
    if [[ -s sha1sum.txt ]]; then
        msg_success "SHA1 checksums generated"
    else
        rm -f sha1sum.txt
        msg_info "No files found for checksum generation"
    fi
}

# Commit and push with progress tracking
commit_and_push() {
    local description="$1"
    local branch="$2"
    local push_to_gitlab="${3:-false}"
    
    if [[ -z "${description}" ]]; then
        msg_error "Commit description required"
        return 1
    fi
    
    msg_process "Committing and pushing changes"
    
    # Create gitignore if it doesn't exist
    [[ ! -f .gitignore ]] && create_gitignore
    
    # Add and commit files in batches for better performance
    local dirs=(system vendor product odm boot recovery dtbo)
    
    # First commit: apps
    if ls *.apk >/dev/null 2>&1; then
        git add ./*.apk
        git commit -sm "Add apps for ${description}" 2>/dev/null || true
        
        if [[ "${push_to_gitlab}" == "true" ]]; then
            git push -u origin "${branch}" 2>/dev/null || msg_warning "Push failed for apps"
        fi
    fi
    
    # Commit each directory separately
    for dir in "${dirs[@]}"; do
        local added=false
        
        for path in "${dir}" "system/${dir}" "system/system/${dir}" "vendor/${dir}"; do
            if [[ -d "${path}" ]]; then
                git add "${path}"
                added=true
            fi
        done
        
        if [[ "${added}" == "true" ]]; then
            git commit -sm "Add ${dir} for ${description}" 2>/dev/null || true
            
            if [[ "${push_to_gitlab}" == "true" ]]; then
                git push -u origin "${branch}" 2>/dev/null || msg_warning "Push failed for ${dir}"
            fi
        fi
    done
    
    # Final commit: remaining files
    git add .
    git commit -sm "Add extras for ${description}" 2>/dev/null || true
    
    if [[ "${push_to_gitlab}" == "true" ]]; then
        git push -u origin "${branch}" 2>/dev/null || msg_warning "Final push failed"
    fi
    
    msg_success "Commit and push completed"
}

# Split large files for git
split_files() {
    local min_file_size="${1:-62M}"
    local part_size="${2:-47M}"
    
    msg_process "Splitting large files (>${min_file_size})"
    
    local split_count=0
    
    # Create temporary directory for split operations
    mkdir -p "${TMPDIR}/split" 2>/dev/null
    
    # Find and split large files
    while IFS= read -r -d '' file; do
        if [[ -f "${file}" ]]; then
            local filename
            filename=$(basename "${file}")
            local filesize
            filesize=$(du -h "${file}" | cut -f1)
            
            msg_info "Splitting ${filename} (${filesize})"
            
            # Split the file
            split -b "${part_size}" "${file}" "${file}."
            
            # Remove original file
            rm -f "${file}"
            
            ((split_count++))
        fi
    done < <(find . -type f -size "+${min_file_size}" -print0 2>/dev/null)
    
    if [[ ${split_count} -gt 0 ]]; then
        msg_success "Split ${split_count} large files"
    else
        msg_info "No large files to split"
    fi
}

# Check git repository status
check_git_status() {
    if git rev-parse --git-dir >/dev/null 2>&1; then
        local status
        status=$(git status --porcelain)
        
        if [[ -n "${status}" ]]; then
            local untracked
            local modified
            untracked=$(echo "${status}" | grep -c "^??" || echo "0")
            modified=$(echo "${status}" | grep -c "^.M" || echo "0")
            
            msg_info "Repository status: ${untracked} untracked, ${modified} modified files"
        else
            msg_success "Repository is clean"
        fi
        
        return 0
    else
        msg_warning "Not a git repository"
        return 1
    fi
}

# Remote repository operations
add_remote() {
    local remote_name="$1"
    local remote_url="$2"
    
    if [[ -z "${remote_name}" || -z "${remote_url}" ]]; then
        msg_error "Remote name and URL required"
        return 1
    fi
    
    msg_process "Adding remote: ${remote_name}"
    
    if git remote add "${remote_name}" "${remote_url}" 2>/dev/null; then
        msg_success "Remote ${remote_name} added successfully"
    else
        msg_warning "Failed to add remote or remote already exists"
    fi
}

# Get current branch name
get_current_branch() {
    git branch --show-current 2>/dev/null || echo "main"
}

# Create release tag
create_tag() {
    local tag_name="$1"
    local tag_message="${2:-Release ${tag_name}}"
    
    if [[ -z "${tag_name}" ]]; then
        msg_error "Tag name required"
        return 1
    fi
    
    msg_process "Creating tag: ${tag_name}"
    
    if git tag -a "${tag_name}" -m "${tag_message}"; then
        msg_success "Tag ${tag_name} created"
        
        # Push tag if connected to remote
        if git remote | grep -q .; then
            git push --tags 2>/dev/null || msg_warning "Failed to push tags"
        fi
    else
        msg_error "Failed to create tag"
        return 1
    fi
}