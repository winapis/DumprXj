#!/bin/bash
# DumprX Enhanced Messaging System
# Minimalistic and attractive user interface with improved notifications

# Colors and formatting
declare -g C_RED='\033[31;1m'
declare -g C_GREEN='\033[32;1m'
declare -g C_YELLOW='\033[33;1m'
declare -g C_BLUE='\033[34;1m'
declare -g C_PURPLE='\033[35;1m'
declare -g C_CYAN='\033[36;1m'
declare -g C_WHITE='\033[37;1m'
declare -g C_CLEAR='\033[0m'
declare -g C_BOLD='\033[1m'
declare -g C_DIM='\033[2m'

# Icons
declare -g ICON_SUCCESS="✅"
declare -g ICON_ERROR="❌"
declare -g ICON_WARNING="⚠️"
declare -g ICON_INFO="ℹ️"
declare -g ICON_PROGRESS="🔄"
declare -g ICON_DOWNLOAD="⬇️"
declare -g ICON_EXTRACT="📦"
declare -g ICON_UPLOAD="⬆️"
declare -g ICON_SEARCH="🔍"
declare -g ICON_TOOL="🔧"
declare -g ICON_PHONE="📱"
declare -g ICON_FIRE="🔥"

# Banner function
show_banner() {
    local version="${1:-v2.0}"
    echo -e "${C_GREEN}"
    cat << 'EOF'
	██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
	██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
	██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
	██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
	██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
	╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
EOF
    echo -e "${C_CLEAR}"
    echo -e "${C_CYAN}${C_BOLD}    📱 Advanced Firmware Extraction Toolkit ${version} 📱${C_CLEAR}"
    echo -e "${C_DIM}    ═══════════════════════════════════════════════════${C_CLEAR}"
    echo
}

# Message functions
msg_success() {
    echo -e "${C_GREEN}${ICON_SUCCESS} ${*}${C_CLEAR}"
}

msg_error() {
    echo -e "${C_RED}${ICON_ERROR} ${*}${C_CLEAR}" >&2
}

msg_warning() {
    echo -e "${C_YELLOW}${ICON_WARNING} ${*}${C_CLEAR}"
}

msg_info() {
    echo -e "${C_BLUE}${ICON_INFO} ${*}${C_CLEAR}"
}

msg_progress() {
    echo -e "${C_CYAN}${ICON_PROGRESS} ${*}${C_CLEAR}"
}

msg_download() {
    echo -e "${C_PURPLE}${ICON_DOWNLOAD} ${*}${C_CLEAR}"
}

msg_extract() {
    echo -e "${C_YELLOW}${ICON_EXTRACT} ${*}${C_CLEAR}"
}

msg_upload() {
    echo -e "${C_GREEN}${ICON_UPLOAD} ${*}${C_CLEAR}"
}

msg_search() {
    echo -e "${C_CYAN}${ICON_SEARCH} ${*}${C_CLEAR}"
}

msg_tool() {
    echo -e "${C_BLUE}${ICON_TOOL} ${*}${C_CLEAR}"
}

msg_device() {
    echo -e "${C_PURPLE}${ICON_PHONE} ${*}${C_CLEAR}"
}

# Progress bar function
show_progress() {
    local current=$1
    local total=$2
    local message="${3:-Processing}"
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((current * width / total))
    
    printf "\r${C_CYAN}${ICON_PROGRESS} ${message}: ["
    for ((i=0; i<completed; i++)); do printf "█"; done
    for ((i=completed; i<width; i++)); do printf "░"; done
    printf "] %d%%${C_CLEAR}" "$percentage"
    
    if [ "$current" -eq "$total" ]; then
        echo
    fi
}

# Enhanced usage function
show_usage() {
    show_banner
    echo -e "${C_BOLD}${C_WHITE}Usage:${C_CLEAR}"
    echo -e "  ${C_GREEN}\$ ${0} ${C_CYAN}<firmware_file_or_url>${C_CLEAR}"
    echo
    echo -e "${C_BOLD}${C_WHITE}Supported Inputs:${C_CLEAR}"
    echo -e "  ${C_YELLOW}${ICON_EXTRACT} Files:${C_CLEAR} .zip, .rar, .7z, .tar, .ozip, .kdz, .bin, .img"
    echo -e "  ${C_BLUE}${ICON_DOWNLOAD} URLs:${C_CLEAR} Direct links, Mega, MediaFire, Google Drive, OneDrive"
    echo -e "  ${C_PURPLE}${ICON_SEARCH} Folders:${C_CLEAR} Pre-extracted firmware directories"
    echo
    echo -e "${C_BOLD}${C_WHITE}Examples:${C_CLEAR}"
    echo -e "  ${C_DIM}• File extraction:${C_CLEAR}"
    echo -e "    ${C_GREEN}\$ ${0} ${C_CYAN}firmware.zip${C_CLEAR}"
    echo -e "  ${C_DIM}• URL download:${C_CLEAR}"
    echo -e "    ${C_GREEN}\$ ${0} ${C_CYAN}'https://example.com/firmware.zip'${C_CLEAR}"
    echo -e "  ${C_DIM}• Mega.nz link:${C_CLEAR}"
    echo -e "    ${C_GREEN}\$ ${0} ${C_CYAN}'https://mega.nz/file/...'${C_CLEAR}"
    echo
    echo -e "${C_DIM}${ICON_INFO} Wrap URLs in single quotes to handle special characters${C_CLEAR}"
    echo
}

# Error handling with context
die() {
    local exit_code=${1:-1}
    shift
    msg_error "$@"
    exit "$exit_code"
}

# Confirmation prompt
confirm() {
    local message="$1"
    local default="${2:-n}"
    local prompt
    
    if [[ "$default" == "y" ]]; then
        prompt="[Y/n]"
    else
        prompt="[y/N]"
    fi
    
    echo -ne "${C_YELLOW}${ICON_WARNING} ${message} ${prompt}: ${C_CLEAR}"
    read -r response
    
    if [[ -z "$response" ]]; then
        response="$default"
    fi
    
    case "$response" in
        [Yy]|[Yy][Ee][Ss]) return 0 ;;
        *) return 1 ;;
    esac
}

# Section headers
section() {
    echo
    echo -e "${C_CYAN}${C_BOLD}╭─ $* ─${C_CLEAR}"
}

section_end() {
    echo -e "${C_CYAN}${C_BOLD}╰─────────────────────────────────────────${C_CLEAR}"
    echo
}

# Step counter
declare -g STEP_COUNTER=0

step() {
    ((STEP_COUNTER++))
    echo -e "${C_WHITE}${C_BOLD}Step ${STEP_COUNTER}:${C_CLEAR} $*"
}

# Summary function
show_summary() {
    local brand="$1"
    local device="$2"
    local android_version="$3"
    local extracted_partitions="$4"
    
    section "Extraction Summary"
    echo -e "${C_GREEN}${ICON_SUCCESS} Device: ${C_BOLD}$brand $device${C_CLEAR}"
    echo -e "${C_GREEN}${ICON_SUCCESS} Android: ${C_BOLD}$android_version${C_CLEAR}"
    echo -e "${C_GREEN}${ICON_SUCCESS} Partitions: ${C_BOLD}$extracted_partitions${C_CLEAR}"
    section_end
}

# Export functions
export -f show_banner msg_success msg_error msg_warning msg_info msg_progress
export -f msg_download msg_extract msg_upload msg_search msg_tool msg_device
export -f show_progress show_usage die confirm section section_end step show_summary