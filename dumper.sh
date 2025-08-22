#!/bin/bash
# DumprX - Firmware Dumping and Extraction Toolkit
# Refactored modular version with improved error handling and user experience

# Script information
readonly SCRIPT_NAME="DumprX"
readonly SCRIPT_VERSION="2.0.0"
readonly SCRIPT_DESCRIPTION="Advanced firmware dumping and extraction toolkit"

# Get script directory for module loading
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"

# Load the module system
source "${SCRIPT_DIR}/lib/loader.sh"

# Initialize DumprX modules
if ! init_dumprx; then
    echo "Error: Failed to initialize DumprX modules" >&2
    exit 1
fi

# Global variables for firmware processing
declare -g FILEPATH FILE EXTENSION UNZIP_DIR
declare -g EXTERNAL_TOOLS=(
    "bkerler/oppo_ozip_decrypt"
    "bkerler/oppo_decrypt"
    "marin-m/vmlinux-to-elf"
    "ShivamKumarJha/android_tools"
    "HemanthJabalpuri/pacextractor"
)

# Display usage information
show_usage_info() {
    show_usage "./dumper.sh" "${SCRIPT_DESCRIPTION}"
}

# Validate input arguments
validate_arguments() {
    if ! validate_input "$@"; then
        show_usage_info
        exit 1
    fi
}

# Setup external tools
setup_external_tools() {
    msg_process "Setting up external tools"
    
    local setup_count=0
    for tool_slug in "${EXTERNAL_TOOLS[@]}"; do
        local tool_name="${tool_slug#*/}"
        local tool_path="${UTILSDIR}/${tool_name}"
        
        if [[ ! -d "${tool_path}" ]]; then
            msg_info "Cloning ${tool_name}"
            if git clone -q "https://github.com/${tool_slug}.git" "${tool_path}"; then
                ((setup_count++))
            else
                msg_warning "Failed to clone ${tool_name}"
            fi
        else
            msg_info "Updating ${tool_name}"
            if git -C "${tool_path}" pull -q; then
                ((setup_count++))
            else
                msg_warning "Failed to update ${tool_name}"
            fi
        fi
    done
    
    msg_success "External tools setup completed (${setup_count}/${#EXTERNAL_TOOLS[@]})"
}

# Setup UV Python package manager
setup_uv() {
    if ! command_exists uvx; then
        msg_info "Adding UV to PATH"
        export PATH="${HOME}/.local/bin:${PATH}"
    fi
}

# Process input and determine file type
process_input() {
    local input="$1"
    
    msg_process "Processing input: ${input}"
    
    # Check if input is from project input directory
    if echo "${input}" | grep -q "${PROJECT_DIR}/input"; then
        process_input_directory "${input}"
        return
    fi
    
    # Check if input is a URL
    if is_url "${input}"; then
        process_url_input "${input}"
        return
    fi
    
    # Process local file/directory
    process_local_input "${input}"
}

# Process input directory
process_input_directory() {
    local input_path="$1"
    
    if [[ $(count_files "${INPUTDIR}" "*" "10M") -gt 1 ]]; then
        # Multiple files in input directory
        FILEPATH=$(get_absolute_path "${input_path}")
        msg_info "Copying multiple files from input directory"
        copy_with_progress "${FILEPATH}" "${TMPDIR}" "Copying files for processing"
        unset FILEPATH
        
    elif [[ $(count_files "${INPUTDIR}" "*" "300M") -eq 1 ]]; then
        # Single large file in input directory
        msg_info "Processing single file from input directory"
        cd "${INPUTDIR}" || abort "Cannot access input directory"
        
        FILEPATH=$(find "$(pwd)" -maxdepth 1 -type f -size +300M 2>/dev/null | head -1)
        FILE=$(get_filename "${FILEPATH}")
        EXTENSION=$(get_extension "${FILEPATH}")
        
        if echo "${EXTENSION}" | grep -q "zip\|rar\|7z\|tar"; then
            UNZIP_DIR=$(get_basename "${FILE}")
        fi
    else
        abort "Input directory is empty or contains no suitable files"
    fi
}

# Process URL input
process_url_input() {
    local url="$1"
    
    msg_info "Processing URL input"
    
    # Download the file
    if download_file "${url}" "${INPUTDIR}"; then
        # Validate download
        if validate_download "${INPUTDIR}"; then
            # Get download information
            eval "$(get_download_info "${INPUTDIR}")"
            msg_success "File downloaded successfully: ${FILE}"
        else
            abort "Download validation failed"
        fi
    else
        abort "Download failed"
    fi
}

# Process local file/directory input
process_local_input() {
    local input="$1"
    
    FILEPATH=$(get_absolute_path "${input}")
    
    # Clean filename if needed
    if echo "${input}" | grep -q " "; then
        if [[ -w "${FILEPATH}" ]]; then
            local cleaned_path
            cleaned_path=$(clean_filename "${FILEPATH}")
            if [[ "${cleaned_path}" != "${FILEPATH}" ]]; then
                mv "${FILEPATH}" "${cleaned_path}"
                FILEPATH="${cleaned_path}"
                msg_info "Cleaned filename: $(basename "${FILEPATH}")"
            fi
        fi
    fi
    
    # Check if file/directory exists
    if ! path_exists "${FILEPATH}"; then
        abort "Input file/directory doesn't exist: ${FILEPATH}"
    fi
    
    # Set file variables
    FILE=$(get_filename "${FILEPATH}")
    EXTENSION=$(get_extension "${FILEPATH}")
    
    if echo "${EXTENSION}" | grep -q "zip\|rar\|7z\|tar"; then
        UNZIP_DIR=$(get_basename "${FILE}")
    fi
    
    # Handle directory input
    if [[ -d "${FILEPATH}" ]]; then
        process_directory_input "${FILEPATH}"
    else
        msg_success "Local file processed: ${FILE}"
    fi
}

# Process directory input
process_directory_input() {
    local dir_path="$1"
    
    msg_info "Processing directory input"
    
    # Check for archives in directory
    local archives
    archives=$(find "${dir_path}" -maxdepth 1 -type f \( -name "*.tar" -o -name "*.zip" -o -name "*.rar" -o -name "*.7z" \) ! -name "compatibility.zip" 2>/dev/null)
    
    if [[ -n "${archives}" ]]; then
        local archive_count
        archive_count=$(echo "${archives}" | wc -l)
        
        if [[ ${archive_count} -eq 1 ]]; then
            msg_info "Found archive in directory, reloading with archive file"
            exec "${0}" "${archives}"
        else
            abort "Multiple archives found in directory. Please specify a single archive file."
        fi
    fi
    
    # Check for firmware files in directory
    local firmware_files
    firmware_files=$(find "${dir_path}" -maxdepth 1 -type f \( \
        -name "*system.ext4.tar*" -o -name "*chunk*" -o -name "system/build.prop" -o \
        -name "system.new.dat" -o -name "system_new.img" -o -name "system.img" -o \
        -name "system-sign.img" -o -name "system.bin" -o -name "payload.bin" -o \
        -name "*rawprogram*" -o -name "system.sin" -o -name "*system_*.sin" -o \
        -name "system-p" -o -name "super*" -o -name "UPDATE.APP" -o -name "*.pac" -o \
        -name "*.nb0" \) ! -name "*chunk*.so" 2>/dev/null)
    
    if [[ -n "${firmware_files}" ]]; then
        msg_info "Found firmware files in directory"
        copy_with_progress "${dir_path}" "${TMPDIR}" "Copying firmware files for processing"
        unset FILEPATH
    else
        abort "No supported firmware files found in directory"
    fi
}

# Main extraction workflow
perform_extraction() {
    msg_process "Starting firmware extraction workflow"
    
    cd "${TMPDIR}" || abort "Cannot access temporary directory"
    
    # Display extraction target
    msg_info "Extraction target: ${OUTDIR}"
    
    # Perform firmware extraction
    if extract_firmware "${FILEPATH}" "${FILE}"; then
        msg_success "Firmware extraction completed"
    else
        msg_warning "Extraction completed with some issues"
    fi
    
    # Extract device metadata
    extract_device_metadata
    
    # Generate README
    generate_readme "${OUTDIR}"
    
    # Setup git repository if configured
    setup_git_repository
}

# Setup git repository
setup_git_repository() {
    if [[ -n "${GITHUB_TOKEN}" ]] || [[ -n "${GITLAB_TOKEN}" ]] || [[ "${PUSH_TO_GITLAB}" == "true" ]]; then
        msg_process "Setting up git repository"
        
        # Initialize git repository
        local branch="${DEVICE_BRANCH:-main}"
        init_git_repo "${branch}"
        
        # Generate SHA1 checksums
        write_sha1sum "${DEVICE_DESCRIPTION}"
        
        # Split large files if needed
        split_files "62M" "47M"
        
        # Commit and push
        commit_and_push "${DEVICE_DESCRIPTION}" "${branch}" "${PUSH_TO_GITLAB:-false}"
        
        msg_success "Git repository setup completed"
    else
        msg_info "No git configuration found, skipping repository setup"
    fi
}

# Load configuration from files
load_configuration() {
    # Load GitHub configuration
    if [[ -f .github_token && -s .github_token ]]; then
        GITHUB_TOKEN=$(cat .github_token)
        export GITHUB_TOKEN
        msg_info "GitHub token loaded"
    fi
    
    if [[ -f .github_orgname && -s .github_orgname ]]; then
        GIT_ORG=$(cat .github_orgname)
        export GIT_ORG
        msg_info "GitHub organization: ${GIT_ORG}"
    fi
    
    # Load GitLab configuration
    if [[ -f .gitlab_token && -s .gitlab_token ]]; then
        GITLAB_TOKEN=$(cat .gitlab_token)
        export GITLAB_TOKEN
        export PUSH_TO_GITLAB=true
        msg_info "GitLab token loaded"
    fi
    
    # Load Telegram configuration
    if [[ -f .tg_token && -s .tg_token ]]; then
        TG_TOKEN=$(cat .tg_token)
        export TG_TOKEN
        msg_info "Telegram token loaded"
    fi
    
    if [[ -f .tg_chat && -s .tg_chat ]]; then
        CHAT_ID=$(cat .tg_chat)
        export CHAT_ID
        msg_info "Telegram chat ID loaded"
    fi
}

# Cleanup function
cleanup() {
    local exit_code=$?
    
    if [[ ${exit_code} -ne 0 ]]; then
        msg_error "Script exited with error code ${exit_code}"
    fi
    
    # Clean up temporary files
    cleanup_temp
    
    # Remove sensitive files
    rm -f .github_token .gitlab_token .tg_token .tg_chat 2>/dev/null
    
    exit ${exit_code}
}

# Main function
main() {
    # Set up cleanup trap
    trap cleanup EXIT INT TERM
    
    # Initialize UI
    init_ui
    
    # Show script header
    show_title "DumprX v${SCRIPT_VERSION}"
    msg_info "${SCRIPT_DESCRIPTION}"
    echo
    
    # Validate arguments
    validate_arguments "$@"
    
    # Load configuration
    load_configuration
    
    # Setup external tools
    setup_external_tools
    
    # Setup UV
    setup_uv
    
    # Process input
    process_input "$1"
    
    # Perform extraction
    perform_extraction
    
    msg_success "DumprX completed successfully!"
    msg_info "Output directory: ${OUTDIR}"
}

# Execute main function with all arguments
main "$@"