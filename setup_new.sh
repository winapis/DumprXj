#!/bin/bash
# DumprX Setup Script - System dependency installation
# Refactored to use modular approach with improved error handling and user experience

# Get script directory for module loading
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"

# Load modules
source "${SCRIPT_DIR}/lib/ui.sh"
source "${SCRIPT_DIR}/lib/utils.sh"
source "${SCRIPT_DIR}/lib/setup.sh"

# Main setup execution
main() {
    # Initialize UI
    init_ui
    
    show_title "DumprX Dependency Setup"
    echo
    msg_info "This script will install required dependencies for DumprX"
    echo
    
    # Run the main setup function
    setup_system
}

# Handle script interruption
trap 'echo; msg_error "Setup interrupted by user"; exit 1' INT TERM

# Execute main function
main "$@"