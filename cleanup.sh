#!/bin/bash
# DumprX Cleanup Utility - Clean up temporary files and reset workspace
# New functionality added as part of the refactoring

# Get script directory for module loading
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"

# Load modules
source "${SCRIPT_DIR}/lib/ui.sh"
source "${SCRIPT_DIR}/lib/utils.sh"

# Cleanup functions
cleanup_output() {
    msg_process "Cleaning output directory"
    
    if [[ -d "${OUTDIR}" ]]; then
        local file_count
        file_count=$(find "${OUTDIR}" -type f | wc -l)
        
        if [[ ${file_count} -gt 0 ]]; then
            rm -rf "${OUTDIR:?}"/*
            msg_success "Removed ${file_count} files from output directory"
        else
            msg_info "Output directory is already clean"
        fi
    else
        msg_info "Output directory does not exist"
    fi
}

cleanup_input() {
    msg_process "Cleaning input directory"
    
    if [[ -d "${INPUTDIR}" ]]; then
        local file_count
        file_count=$(find "${INPUTDIR}" -type f | wc -l)
        
        if [[ ${file_count} -gt 0 ]]; then
            rm -rf "${INPUTDIR:?}"/*
            msg_success "Removed ${file_count} files from input directory"
        else
            msg_info "Input directory is already clean"
        fi
    else
        msg_info "Input directory does not exist"
    fi
}

cleanup_external_tools() {
    msg_process "Cleaning external tools"
    
    local tools_dir="${UTILSDIR}"
    local external_tools=(
        "oppo_ozip_decrypt"
        "oppo_decrypt"
        "vmlinux-to-elf"
        "android_tools"
        "pacextractor"
    )
    
    local removed_count=0
    for tool in "${external_tools[@]}"; do
        if [[ -d "${tools_dir}/${tool}" ]]; then
            rm -rf "${tools_dir:?}/${tool}"
            ((removed_count++))
        fi
    done
    
    if [[ ${removed_count} -gt 0 ]]; then
        msg_success "Removed ${removed_count} external tools"
    else
        msg_info "No external tools to remove"
    fi
}

cleanup_logs() {
    msg_process "Cleaning log files"
    
    local log_files
    log_files=$(find "${PROJECT_DIR}" -name "*.log" -type f)
    
    if [[ -n "${log_files}" ]]; then
        local log_count
        log_count=$(echo "${log_files}" | wc -l)
        echo "${log_files}" | xargs rm -f
        msg_success "Removed ${log_count} log files"
    else
        msg_info "No log files found"
    fi
}

cleanup_backups() {
    msg_process "Cleaning backup files"
    
    local backup_files
    backup_files=$(find "${PROJECT_DIR}" -name "*.backup" -o -name "*.bak" -o -name "*.orig" -type f)
    
    if [[ -n "${backup_files}" ]]; then
        local backup_count
        backup_count=$(echo "${backup_files}" | wc -l)
        echo "${backup_files}" | xargs rm -f
        msg_success "Removed ${backup_count} backup files"
    else
        msg_info "No backup files found"
    fi
}

# Show cleanup options
show_cleanup_options() {
    show_title "DumprX Cleanup Options"
    echo
    echo "Available cleanup options:"
    echo "  1. Clean output directory"
    echo "  2. Clean input directory"
    echo "  3. Clean external tools"
    echo "  4. Clean log files"
    echo "  5. Clean backup files"
    echo "  6. Full cleanup (all of the above)"
    echo "  7. Cancel"
    echo
}

# Interactive cleanup
interactive_cleanup() {
    while true; do
        show_cleanup_options
        echo -n "Select an option (1-7): "
        read -r choice
        echo
        
        case "${choice}" in
            1)
                cleanup_output
                echo
                ;;
            2)
                cleanup_input
                echo
                ;;
            3)
                cleanup_external_tools
                echo
                ;;
            4)
                cleanup_logs
                echo
                ;;
            5)
                cleanup_backups
                echo
                ;;
            6)
                msg_process "Performing full cleanup"
                cleanup_output
                cleanup_input
                cleanup_external_tools
                cleanup_logs
                cleanup_backups
                msg_success "Full cleanup completed"
                break
                ;;
            7)
                msg_info "Cleanup cancelled"
                break
                ;;
            *)
                msg_error "Invalid option. Please select 1-7."
                echo
                ;;
        esac
    done
}

# Usage information
show_usage() {
    show_usage_info() {
        show_title "DumprX Cleanup Utility"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --output     Clean output directory only"
        echo "  --input      Clean input directory only"
        echo "  --tools      Clean external tools only"
        echo "  --logs       Clean log files only"
        echo "  --backups    Clean backup files only"
        echo "  --all        Full cleanup (all directories and files)"
        echo "  --interactive Interactive mode (default)"
        echo "  --help       Show this help message"
        echo
    }
    show_usage_info
}

# Main function
main() {
    # Initialize directories
    init_directories
    
    # Initialize UI
    init_ui
    
    case "${1:-}" in
        --output)
            cleanup_output
            ;;
        --input)
            cleanup_input
            ;;
        --tools)
            cleanup_external_tools
            ;;
        --logs)
            cleanup_logs
            ;;
        --backups)
            cleanup_backups
            ;;
        --all)
            msg_process "Performing full cleanup"
            cleanup_output
            cleanup_input
            cleanup_external_tools
            cleanup_logs
            cleanup_backups
            msg_success "Full cleanup completed"
            ;;
        --help)
            show_usage
            ;;
        --interactive|"")
            interactive_cleanup
            ;;
        *)
            msg_error "Unknown option: $1"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"