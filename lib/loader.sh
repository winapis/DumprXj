#!/bin/bash
# DumprX Module Loader - Centralized module loading system
# Provides a single entry point to load all required modules

# Get the directory where this script is located
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"

# Module loading function with error handling
load_module() {
    local module="$1"
    local module_path="${LIB_DIR}/${module}.sh"
    
    if [[ -f "${module_path}" ]]; then
        # shellcheck disable=SC1090
        source "${module_path}"
        return 0
    else
        echo "Error: Module ${module} not found at ${module_path}" >&2
        return 1
    fi
}

# Load core modules in dependency order
load_core_modules() {
    local modules=(
        "ui"          # UI and messaging (no dependencies)
        "utils"       # Utilities (depends on ui)
        "git"         # Git operations (depends on ui)
        "downloader"  # Download functionality (depends on ui, utils)
        "extractors"  # Firmware extraction (depends on ui, utils)
        "metadata"    # Device metadata (depends on ui)
        "setup"       # System setup (depends on ui, utils)
    )
    
    for module in "${modules[@]}"; do
        if ! load_module "${module}"; then
            echo "Failed to load module: ${module}" >&2
            return 1
        fi
    done
    
    return 0
}

# Initialize all modules
init_dumprx() {
    # Load all core modules
    if ! load_core_modules; then
        echo "Failed to initialize DumprX modules" >&2
        return 1
    fi
    
    # Initialize directory structure
    if command -v init_directories >/dev/null 2>&1; then
        init_directories
    fi
    
    # Initialize extractors
    if command -v init_extractors >/dev/null 2>&1; then
        init_extractors
    fi
    
    # Initialize downloader
    if command -v init_downloader >/dev/null 2>&1; then
        init_downloader
    fi
    
    return 0
}

# Check if modules are loaded
check_modules() {
    local required_functions=(
        "msg_info"              # From ui module
        "init_directories"      # From utils module
        "download_file"         # From downloader module
        "extract_firmware"      # From extractors module
        "extract_device_metadata" # From metadata module
    )
    
    local missing_functions=()
    
    for func in "${required_functions[@]}"; do
        if ! command -v "${func}" >/dev/null 2>&1; then
            missing_functions+=("${func}")
        fi
    done
    
    if [[ ${#missing_functions[@]} -eq 0 ]]; then
        return 0
    else
        echo "Missing functions: ${missing_functions[*]}" >&2
        return 1
    fi
}

# Get module information
get_module_info() {
    echo "DumprX Module System"
    echo "==================="
    echo "Library Directory: ${LIB_DIR}"
    echo
    echo "Available Modules:"
    echo "- ui.sh          : User interface and messaging"
    echo "- utils.sh       : Common utilities and file operations"
    echo "- git.sh         : Git operations and repository management"
    echo "- downloader.sh  : Download functionality for various sources"
    echo "- extractors.sh  : Firmware extraction for different formats"
    echo "- metadata.sh    : Device metadata extraction"
    echo "- setup.sh       : System setup and dependency management"
    echo
    
    if check_modules; then
        echo "Status: All modules loaded successfully ✅"
    else
        echo "Status: Some modules missing or not loaded ❌"
    fi
}