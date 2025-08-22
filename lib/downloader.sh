#!/bin/bash
# DumprX Download Module - File download from various sources
# Handles downloads from file hosters and direct URLs

# Load required modules
source "$(dirname "${BASH_SOURCE[0]}")/ui.sh"
source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"

# Download utilities paths (will be set by init_downloader)
declare -g MEGAMEDIADRIVE_DL
declare -g AFHDL
declare -g TRANSFER

# Initialize downloader paths
init_downloader() {
    MEGAMEDIADRIVE_DL="${UTILSDIR}/downloaders/mega-media-drive_dl.sh"
    AFHDL="${UTILSDIR}/downloaders/afh_dl.py"
    TRANSFER="${UTILSDIR}/bin/transfer"
}

# Detect URL type
detect_url_type() {
    local url="$1"
    
    if echo "${url}" | grep -q "mega.nz"; then
        echo "mega"
    elif echo "${url}" | grep -q "mediafire.com"; then
        echo "mediafire"
    elif echo "${url}" | grep -q "drive.google.com"; then
        echo "gdrive"
    elif echo "${url}" | grep -q "androidfilehost.com"; then
        echo "afh"
    elif echo "${url}" | grep -q "/we.tl/"; then
        echo "wetransfer"
    elif echo "${url}" | grep -q "1drv.ms"; then
        echo "onedrive"
    else
        echo "direct"
    fi
}

# Download from mega.nz, mediafire, or google drive
download_mega_media_drive() {
    local url="$1"
    
    msg_process "Downloading from file hoster (Mega/MediaFire/GDrive)"
    
    if [[ ! -x "${MEGAMEDIADRIVE_DL}" ]]; then
        msg_error "Mega/MediaFire/GDrive downloader not found"
        return 1
    fi
    
    if "${MEGAMEDIADRIVE_DL}" "${url}"; then
        msg_success "Download completed from file hoster"
        return 0
    else
        msg_error "Download failed from file hoster"
        return 1
    fi
}

# Download from AndroidFileHost
download_afh() {
    local url="$1"
    
    msg_process "Downloading from AndroidFileHost"
    
    if [[ ! -f "${AFHDL}" ]]; then
        msg_error "AndroidFileHost downloader not found"
        return 1
    fi
    
    if python3 "${AFHDL}" -l "${url}"; then
        msg_success "Download completed from AndroidFileHost"
        return 0
    else
        msg_error "Download failed from AndroidFileHost"
        return 1
    fi
}

# Download from WeTransfer
download_wetransfer() {
    local url="$1"
    
    msg_process "Downloading from WeTransfer"
    
    if [[ ! -x "${TRANSFER}" ]]; then
        msg_error "WeTransfer downloader not found"
        return 1
    fi
    
    if "${TRANSFER}" "${url}"; then
        msg_success "Download completed from WeTransfer"
        return 0
    else
        msg_error "Download failed from WeTransfer"
        return 1
    fi
}

# Download using aria2c
download_aria2c() {
    local url="$1"
    
    msg_process "Downloading with aria2c"
    
    if ! command_exists aria2c; then
        msg_warning "aria2c not found, falling back to wget"
        return 1
    fi
    
    if aria2c -x16 -s8 --console-log-level=warn --summary-interval=0 --check-certificate=false "${url}"; then
        msg_success "Download completed with aria2c"
        return 0
    else
        msg_warning "aria2c download failed"
        return 1
    fi
}

# Download using wget
download_wget() {
    local url="$1"
    
    msg_process "Downloading with wget"
    
    if ! command_exists wget; then
        msg_error "wget not found"
        return 1
    fi
    
    if wget -q --show-progress --progress=bar:force --no-check-certificate "${url}"; then
        msg_success "Download completed with wget"
        return 0
    else
        msg_error "wget download failed"
        return 1
    fi
}

# Main download function
download_file() {
    local url="$1"
    local download_dir="${2:-${INPUTDIR}}"
    
    if [[ -z "${url}" ]]; then
        msg_error "URL is required"
        return 1
    fi
    
    # Ensure download directory exists and is clean
    mkdir -p "${download_dir}" 2>/dev/null
    cd "${download_dir}" || {
        msg_error "Cannot access download directory: ${download_dir}"
        return 1
    }
    
    # Clean download directory
    rm -rf "${download_dir:?}"/* 2>/dev/null
    
    msg_info "Download URL: ${url}"
    msg_info "Download directory: ${download_dir}"
    
    # Fix OneDrive URLs
    if echo "${url}" | grep -q "1drv.ms"; then
        url="${url/ms/ws}"
        msg_info "Fixed OneDrive URL: ${url}"
    fi
    
    # Detect URL type and download accordingly
    local url_type
    url_type=$(detect_url_type "${url}")
    
    case "${url_type}" in
        mega|mediafire|gdrive)
            download_mega_media_drive "${url}"
            ;;
        afh)
            download_afh "${url}"
            ;;
        wetransfer)
            download_wetransfer "${url}"
            ;;
        onedrive|direct)
            # Try aria2c first, fallback to wget
            if ! download_aria2c "${url}"; then
                download_wget "${url}"
            fi
            ;;
        *)
            msg_error "Unsupported URL type: ${url_type}"
            return 1
            ;;
    esac
    
    local download_status=$?
    
    if [[ ${download_status} -eq 0 ]]; then
        # Clean up downloaded filenames
        for file in *; do
            if [[ -f "${file}" ]]; then
                detox -r "${file}" 2>/dev/null || true
            fi
        done
        
        msg_success "Download and cleanup completed"
        
        # Show downloaded files
        msg_info "Downloaded files:"
        ls -la
        
        return 0
    else
        msg_error "Download failed"
        return 1
    fi
}

# Validate download
validate_download() {
    local download_dir="${1:-${INPUTDIR}}"
    
    msg_process "Validating download"
    
    cd "${download_dir}" || return 1
    
    # Check if any files were downloaded
    local file_count
    file_count=$(find . -maxdepth 1 -type f | wc -l)
    
    if [[ ${file_count} -eq 0 ]]; then
        msg_error "No files downloaded"
        return 1
    fi
    
    msg_info "Found ${file_count} downloaded file(s)"
    
    # Check for common firmware file patterns
    local firmware_files
    firmware_files=$(find . -maxdepth 1 -type f \( \
        -name "*.zip" -o -name "*.rar" -o -name "*.7z" -o -name "*.tar*" -o \
        -name "*.ozip" -o -name "*.ofp" -o -name "*.ops" -o -name "*.kdz" -o \
        -name "*.img" -o -name "*.bin" -o -name "*.dat" -o -name "*.pac" \
        \) | wc -l)
    
    if [[ ${firmware_files} -gt 0 ]]; then
        msg_success "Found ${firmware_files} firmware file(s)"
        return 0
    else
        msg_warning "No recognized firmware files found"
        return 1
    fi
}

# Get download info
get_download_info() {
    local download_dir="${1:-${INPUTDIR}}"
    
    cd "${download_dir}" || return 1
    
    # Find the main file (largest or most relevant)
    local main_file
    main_file=$(find . -maxdepth 1 -type f -printf '%s %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
    
    if [[ -n "${main_file}" ]]; then
        echo "FILEPATH=${main_file}"
        echo "FILE=$(basename "${main_file}")"
        echo "EXTENSION=$(get_extension "${main_file}")"
        
        # Check if it's an archive
        local format
        format=$(detect_format "${main_file}")
        if [[ "${format}" == "archive" ]]; then
            echo "UNZIP_DIR=$(get_basename "${main_file}")"
        fi
    fi
}

# Resume interrupted download
resume_download() {
    local url="$1"
    local download_dir="${2:-${INPUTDIR}}"
    
    msg_info "Attempting to resume download"
    
    cd "${download_dir}" || return 1
    
    # Check for partial files
    local partial_files
    partial_files=$(find . -name "*.aria2" -o -name "*.part" -o -name "*.tmp" | wc -l)
    
    if [[ ${partial_files} -gt 0 ]]; then
        msg_info "Found ${partial_files} partial file(s), attempting resume"
        
        # Try aria2c resume
        if command_exists aria2c; then
            aria2c -c -x16 -s8 --console-log-level=warn --summary-interval=0 --check-certificate=false "${url}"
        else
            msg_warning "aria2c not available for resume, starting fresh download"
            download_file "${url}" "${download_dir}"
        fi
    else
        msg_info "No partial files found, starting fresh download"
        download_file "${url}" "${download_dir}"
    fi
}