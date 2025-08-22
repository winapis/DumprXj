#!/bin/bash
# DumprX Utilities Module - Common utility functions
# Provides file operations, directory management, and validation functions

# Load UI module for messaging
source "$(dirname "${BASH_SOURCE[0]}")/ui.sh"

# Global variables for directory paths
declare -g PROJECT_DIR
declare -g INPUTDIR
declare -g UTILSDIR  
declare -g OUTDIR
declare -g TMPDIR

# Initialize project directories
init_directories() {
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[1]}")" >/dev/null && pwd)"
    
    # Validate project directory path
    if echo "${PROJECT_DIR}" | grep -q " "; then
        abort "Project directory path contains spaces. Please move to a proper UNIX-formatted folder."
    fi
    
    # Set directory paths
    INPUTDIR="${PROJECT_DIR}/input"
    UTILSDIR="${PROJECT_DIR}/utils"
    OUTDIR="${PROJECT_DIR}/out"
    TMPDIR="${OUTDIR}/tmp"
    
    # Create necessary directories
    rm -rf "${TMPDIR}" 2>/dev/null
    mkdir -p "${OUTDIR}" "${TMPDIR}" 2>/dev/null
    
    msg_info "Project directory: ${PROJECT_DIR}"
}

# Validate input parameters
validate_input() {
    local input="$1"
    
    if [[ $# -eq 0 ]]; then
        msg_error "No input provided"
        return 1
    elif [[ -z "${input}" ]]; then
        msg_error "Enter firmware path"
        return 1
    elif [[ "${input}" == " " ]] || [[ -n "$2" ]]; then
        msg_error "Enter only firmware file path"
        return 1
    fi
    
    return 0
}

# Check if path exists
path_exists() {
    local path="$1"
    [[ -e "${path}" ]]
}

# Get file extension
get_extension() {
    local filepath="$1"
    echo "${filepath##*.}"
}

# Get filename without path
get_filename() {
    local filepath="$1"
    echo "${filepath##*/}"
}

# Get filename without extension
get_basename() {
    local filepath="$1"
    local filename="${filepath##*/}"
    echo "${filename%.*}"
}

# Check if URL is valid
is_url() {
    local input="$1"
    echo "${input}" | grep -q -E '^\(https?\|ftp\)://.*$'
}

# Detect file format
detect_format() {
    local filepath="$1"
    local extension
    extension=$(get_extension "${filepath}")
    
    case "${extension}" in
        zip|rar|7z|tar|gz|tgz|md5) echo "archive" ;;
        ozip|ofp|ops|kdz|exe) echo "firmware" ;;
        img|bin|dat|pac|nb0|sin) echo "image" ;;
        *) echo "unknown" ;;
    esac
}

# Clean filename (remove special characters)
clean_filename() {
    local filepath="$1"
    if echo "${filepath}" | grep -q " "; then
        if [[ -w "${filepath}" ]]; then
            detox -r "${filepath}" 2>/dev/null
            echo "${filepath}" | tr ' ' '_' | tr -d '()[]{}!'
        else
            echo "${filepath}"
        fi
    else
        echo "${filepath}"
    fi
}

# Check if file is large enough (for firmware files)
is_large_file() {
    local filepath="$1"
    local min_size="${2:-300M}"
    
    if [[ -f "${filepath}" ]]; then
        find "$(dirname "${filepath}")" -name "$(basename "${filepath}")" -size "+${min_size}" -print | grep -q .
    else
        return 1
    fi
}

# Count files in directory matching pattern
count_files() {
    local directory="$1"
    local pattern="${2:-*}"
    local min_size="${3:-10M}"
    
    find "${directory}" -maxdepth 1 -name "${pattern}" -size "+${min_size}" -type f 2>/dev/null | wc -l
}

# Copy with progress indication
copy_with_progress() {
    local source="$1"
    local destination="$2"
    local description="${3:-Copying files}"
    
    msg_process "${description}"
    if [[ -d "${source}" ]]; then
        cp -a "${source}"/* "${destination}"/
    else
        cp -a "${source}" "${destination}"/
    fi
    msg_success "Copy completed"
}

# Move with progress indication  
move_with_progress() {
    local source="$1"
    local destination="$2"
    local description="${3:-Moving files}"
    
    msg_process "${description}"
    if [[ -d "${source}" ]]; then
        mv "${source}"/* "${destination}"/
    else
        mv "${source}" "${destination}"/
    fi
    msg_success "Move completed"
}

# Check if command exists
command_exists() {
    local cmd="$1"
    command -v "${cmd}" >/dev/null 2>&1
}

# Wait with progress dots
wait_with_progress() {
    local seconds="$1"
    local message="${2:-Processing}"
    
    echo -n "${message}"
    for ((i=0; i<seconds; i++)); do
        echo -n "."
        sleep 1
    done
    echo
}

# Get absolute path
get_absolute_path() {
    local path="$1"
    realpath "${path}" 2>/dev/null || echo "${path}"
}

# Create backup of file
backup_file() {
    local filepath="$1"
    local backup_path="${filepath}.backup.$(date +%s)"
    
    if [[ -f "${filepath}" ]]; then
        cp "${filepath}" "${backup_path}"
        msg_info "Backup created: ${backup_path}"
        echo "${backup_path}"
    fi
}

# Cleanup temporary files
cleanup_temp() {
    local temp_pattern="${1:-${TMPDIR}}"
    
    if [[ -n "${temp_pattern}" && "${temp_pattern}" != "/" ]]; then
        rm -rf "${temp_pattern:?}"/* 2>/dev/null
        msg_info "Temporary files cleaned"
    fi
}

# Check disk space
check_disk_space() {
    local required_gb="$1"
    local path="${2:-.}"
    
    local available_kb
    available_kb=$(df "${path}" | awk 'NR==2 {print $4}')
    local available_gb=$((available_kb / 1024 / 1024))
    
    if [[ ${available_gb} -lt ${required_gb} ]]; then
        msg_warning "Low disk space: ${available_gb}GB available, ${required_gb}GB required"
        return 1
    fi
    
    return 0
}

# Validate archive integrity
validate_archive() {
    local filepath="$1"
    local extension
    extension=$(get_extension "${filepath}")
    
    case "${extension}" in
        zip)
            if command_exists unzip; then
                unzip -t "${filepath}" >/dev/null 2>&1
            else
                return 1
            fi
            ;;
        rar)
            if command_exists unrar; then
                unrar t "${filepath}" >/dev/null 2>&1
            else
                return 1
            fi
            ;;
        7z)
            if command_exists 7z; then
                7z t "${filepath}" >/dev/null 2>&1
            else
                return 1
            fi
            ;;
        *)
            return 0
            ;;
    esac
}