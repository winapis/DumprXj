#!/bin/bash
# DumprX UI Module - Banner, colors, and messaging system
# Provides consistent UI elements across all scripts

# Color definitions
declare -r RED='\033[0;31m'
declare -r GREEN='\033[0;32m'
declare -r YELLOW='\033[0;33m'
declare -r BLUE='\033[0;34m'
declare -r PURPLE='\033[0;35m'
declare -r CYAN='\033[0;36m'
declare -r WHITE='\033[0;37m'
declare -r BOLD='\033[1m'
declare -r NC='\033[0m' # No Color

# Message types
declare -r MSG_INFO="ℹ"
declare -r MSG_SUCCESS="✅"
declare -r MSG_WARNING="⚠"
declare -r MSG_ERROR="❌"
declare -r MSG_PROCESS="🔄"

# Clear screen function
clear_screen() {
    tput reset 2>/dev/null || clear
}

# DumprX ASCII Banner
show_banner() {
    echo -e "${GREEN}
	██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
	██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
	██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
	██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
	██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
	╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝${NC}"
}

# Modern message functions
msg_info() {
    echo -e "${BLUE}${MSG_INFO} ${*}${NC}"
}

msg_success() {
    echo -e "${GREEN}${MSG_SUCCESS} ${*}${NC}"
}

msg_warning() {
    echo -e "${YELLOW}${MSG_WARNING} ${*}${NC}"
}

msg_error() {
    echo -e "${RED}${MSG_ERROR} ${*}${NC}"
}

msg_process() {
    echo -e "${CYAN}${MSG_PROCESS} ${*}${NC}"
}

# Progress indicator
show_progress() {
    local message="$1"
    local current="$2"
    local total="$3"
    
    if [[ -n "$current" && -n "$total" ]]; then
        local percentage=$((current * 100 / total))
        echo -e "${CYAN}${MSG_PROCESS} ${message} [${current}/${total}] (${percentage}%)${NC}"
    else
        echo -e "${CYAN}${MSG_PROCESS} ${message}${NC}"
    fi
}

# Title with separator
show_title() {
    local title="$1"
    echo
    echo -e "${BOLD}${BLUE}${title}${NC}"
    echo -e "${BLUE}$(printf '=%.0s' $(seq 1 ${#title}))${NC}"
}

# Section header
show_section() {
    local section="$1"
    echo
    echo -e "${BOLD}${GREEN}➤ ${section}${NC}"
}

# Usage display
show_usage() {
    local script_name="$1"
    local description="$2"
    
    show_title "Usage"
    echo -e "${CYAN}${script_name} ${YELLOW}<Firmware File/Folder or URL>${NC}"
    echo
    echo -e "${WHITE}${description}${NC}"
    echo
    
    show_section "Supported Websites"
    echo -e "${WHITE}  • Direct download links from any website${NC}"
    echo -e "${WHITE}  • File hosters: mega.nz, mediafire, gdrive, onedrive, androidfilehost${NC}"
    echo -e "${YELLOW}  ⚠ Wrap URLs in single quotes ('')${NC}"
    echo
    
    show_section "Supported File Formats"
    echo -e "${WHITE}  • Archives: *.zip, *.rar, *.7z, *.tar, *.tar.gz, *.tgz, *.tar.md5${NC}"
    echo -e "${WHITE}  • Firmware: *.ozip, *.ofp, *.ops, *.kdz, ruu_*.exe${NC}"
    echo -e "${WHITE}  • Images: system.new.dat*, system.img, payload.bin, *.nb0, *.pac${NC}"
    echo -e "${WHITE}  • Others: UPDATE.APP, *super*.img, *system*.sin${NC}"
    echo
}

# Error with exit
abort() {
    msg_error "$@"
    exit 1
}

# Initialize UI (clear screen and show banner)
init_ui() {
    clear_screen
    # Resize terminal for better view
    printf "\033[8;30;90t" 2>/dev/null || true
    show_banner
    sleep 0.3
}