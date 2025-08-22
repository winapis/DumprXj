#!/bin/bash
# DumprX Enhanced Download Service Handlers
# Improved link detection and downloading from various services

# Source messaging module
source "$(dirname "${BASH_SOURCE[0]}")/../messaging/ui.sh"

# Supported download services
declare -g SUPPORTED_SERVICES=(
    "mega.nz"
    "mediafire.com"
    "drive.google.com"
    "onedrive.live.com"
    "1drv.ms"
    "androidfilehost.com"
    "dropbox.com"
    "github.com"
    "gitlab.com"
)

# Check if URL is a supported download service
is_supported_url() {
    local url="$1"
    
    for service in "${SUPPORTED_SERVICES[@]}"; do
        if [[ "$url" =~ $service ]]; then
            return 0
        fi
    done
    
    # Check for direct download links
    if [[ "$url" =~ \.(zip|rar|7z|tar|gz|bz2|xz|bin|img|ozip|kdz|ofp|ops)(\?.*)?$ ]]; then
        return 0
    fi
    
    return 1
}

# Enhanced URL validation and normalization
validate_and_normalize_url() {
    local url="$1"
    
    # Remove surrounding quotes
    url="${url#\'}"
    url="${url%\'}"
    url="${url#\"}"
    url="${url%\"}"
    
    # Validate URL format
    if ! [[ "$url" =~ ^https?:// ]]; then
        msg_error "Invalid URL format: $url"
        return 1
    fi
    
    # Normalize common URL patterns
    case "$url" in
        *"mega.nz"*)
            # Handle mega.nz URLs
            if [[ "$url" =~ mega\.nz/(file|folder)/ ]]; then
                echo "$url"
                return 0
            fi
            ;;
        *"mediafire.com"*)
            # Handle MediaFire URLs
            if [[ "$url" =~ mediafire\.com/(file|download)/ ]]; then
                echo "$url"
                return 0
            fi
            ;;
        *"drive.google.com"*)
            # Handle Google Drive URLs
            if [[ "$url" =~ drive\.google\.com.*/(file/d/|open\?id=) ]]; then
                echo "$url"
                return 0
            fi
            ;;
        *"onedrive.live.com"* | *"1drv.ms"*)
            # Handle OneDrive URLs
            echo "$url"
            return 0
            ;;
        *"androidfilehost.com"*)
            # Handle AndroidFileHost URLs
            if [[ "$url" =~ androidfilehost\.com.*fid= ]]; then
                echo "$url"
                return 0
            fi
            ;;
        *"dropbox.com"*)
            # Handle Dropbox URLs
            if [[ "$url" =~ dropbox\.com.*/(s/|sh/) ]]; then
                echo "$url"
                return 0
            fi
            ;;
        *"github.com"* | *"gitlab.com"*)
            # Handle Git repository releases
            if [[ "$url" =~ (github|gitlab)\.com.*/(releases|uploads)/ ]]; then
                echo "$url"
                return 0
            fi
            ;;
        *)
            # Handle direct download links
            if [[ "$url" =~ \.(zip|rar|7z|tar|gz|bz2|xz|bin|img|ozip|kdz|ofp|ops)(\?.*)?$ ]]; then
                echo "$url"
                return 0
            fi
            ;;
    esac
    
    msg_error "Unsupported or invalid URL: $url"
    return 1
}

# Detect file type from URL
detect_file_type_from_url() {
    local url="$1"
    local filename
    
    # Extract filename from URL
    filename=$(basename "$url" | cut -d'?' -f1)
    
    case "$filename" in
        *.zip) echo "zip" ;;
        *.rar) echo "rar" ;;
        *.7z) echo "7z" ;;
        *.tar*) echo "tar" ;;
        *.ozip) echo "ozip" ;;
        *.kdz) echo "kdz" ;;
        *.ofp) echo "ofp" ;;
        *.ops) echo "ops" ;;
        *.bin) echo "bin" ;;
        *.img) echo "img" ;;
        *) echo "unknown" ;;
    esac
}

# Enhanced download function with service-specific handling
download_firmware() {
    local url="$1"
    local output_dir="$2"
    local service_type
    
    msg_download "Analyzing download URL..."
    
    # Validate and normalize URL
    if ! url=$(validate_and_normalize_url "$url"); then
        return 1
    fi
    
    # Detect service type
    case "$url" in
        *"mega.nz"*)
            service_type="mega"
            ;;
        *"mediafire.com"*)
            service_type="mediafire"
            ;;
        *"drive.google.com"*)
            service_type="gdrive"
            ;;
        *"onedrive.live.com"* | *"1drv.ms"*)
            service_type="onedrive"
            ;;
        *"androidfilehost.com"*)
            service_type="afh"
            ;;
        *"dropbox.com"*)
            service_type="dropbox"
            ;;
        *"github.com"* | *"gitlab.com"*)
            service_type="git"
            ;;
        *)
            service_type="direct"
            ;;
    esac
    
    msg_info "Detected service: $service_type"
    
    # Create output directory
    mkdir -p "$output_dir"
    
    # Download based on service type
    case "$service_type" in
        "mega")
            download_mega "$url" "$output_dir"
            ;;
        "mediafire")
            download_mediafire "$url" "$output_dir"
            ;;
        "gdrive")
            download_gdrive "$url" "$output_dir"
            ;;
        "onedrive")
            download_onedrive "$url" "$output_dir"
            ;;
        "afh")
            download_afh "$url" "$output_dir"
            ;;
        "dropbox")
            download_dropbox "$url" "$output_dir"
            ;;
        "git")
            download_git "$url" "$output_dir"
            ;;
        "direct")
            download_direct "$url" "$output_dir"
            ;;
        *)
            msg_error "Unsupported download service"
            return 1
            ;;
    esac
}

# Service-specific download functions
download_mega() {
    local url="$1"
    local output_dir="$2"
    
    msg_progress "Downloading from Mega.nz..."
    bash "${UTILSDIR}/downloaders/mega-media-drive_dl.sh" "$url" "$output_dir"
}

download_mediafire() {
    local url="$1"
    local output_dir="$2"
    
    msg_progress "Downloading from MediaFire..."
    bash "${UTILSDIR}/downloaders/mega-media-drive_dl.sh" "$url" "$output_dir"
}

download_gdrive() {
    local url="$1"
    local output_dir="$2"
    
    msg_progress "Downloading from Google Drive..."
    bash "${UTILSDIR}/downloaders/mega-media-drive_dl.sh" "$url" "$output_dir"
}

download_onedrive() {
    local url="$1"
    local output_dir="$2"
    
    msg_progress "Downloading from OneDrive..."
    # Convert OneDrive sharing URL to direct download
    if [[ "$url" =~ 1drv\.ms ]]; then
        # Expand shortened URL first
        url=$(curl -s -I "$url" | grep -i location | cut -d' ' -f2 | tr -d '\r')
    fi
    download_direct "$url" "$output_dir"
}

download_afh() {
    local url="$1"
    local output_dir="$2"
    
    msg_progress "Downloading from AndroidFileHost..."
    python3 "${UTILSDIR}/downloaders/afh_dl.py" "$url" "$output_dir"
}

download_dropbox() {
    local url="$1"
    local output_dir="$2"
    
    msg_progress "Downloading from Dropbox..."
    # Convert Dropbox sharing URL to direct download
    url="${url/dropbox.com/dl.dropboxusercontent.com}"
    url="${url/?dl=0/?dl=1}"
    download_direct "$url" "$output_dir"
}

download_git() {
    local url="$1"
    local output_dir="$2"
    
    msg_progress "Downloading from Git repository..."
    download_direct "$url" "$output_dir"
}

download_direct() {
    local url="$1"
    local output_dir="$2"
    local filename
    
    filename=$(basename "$url" | cut -d'?' -f1)
    if [[ -z "$filename" || "$filename" == "/" ]]; then
        filename="firmware_$(date +%s)"
    fi
    
    msg_progress "Downloading directly from server..."
    
    # Try aria2c first (faster, supports resume)
    if command -v aria2c >/dev/null 2>&1; then
        aria2c -x 16 -s 16 -k 1M -c -d "$output_dir" -o "$filename" "$url"
    # Fallback to wget
    elif command -v wget >/dev/null 2>&1; then
        wget -c -O "$output_dir/$filename" "$url"
    # Fallback to curl
    elif command -v curl >/dev/null 2>&1; then
        curl -L -C - -o "$output_dir/$filename" "$url"
    else
        msg_error "No download tool available (aria2c, wget, or curl required)"
        return 1
    fi
}

# Get download progress (if supported)
get_download_progress() {
    local pid="$1"
    
    # This would need to be implemented based on the specific download tool
    # For now, just check if process is still running
    if kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Export functions
export -f is_supported_url validate_and_normalize_url detect_file_type_from_url
export -f download_firmware download_mega download_mediafire download_gdrive
export -f download_onedrive download_afh download_dropbox download_git download_direct