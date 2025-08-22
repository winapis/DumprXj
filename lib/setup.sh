#!/bin/bash
# DumprX Setup Module - Dependency installation and system setup
# Handles package installation across different Linux distributions

# Load required modules
source "$(dirname "${BASH_SOURCE[0]}")/ui.sh"

# Package lists for different distributions
declare -ra DEBIAN_PACKAGES=(
    "unace" "unrar" "zip" "unzip" "p7zip-full" "p7zip-rar" 
    "sharutils" "rar" "uudeview" "mpack" "arj" "cabextract"
    "device-tree-compiler" "liblzma-dev" "python3-pip" "brotli"
    "liblz4-tool" "axel" "gawk" "aria2" "detox" "cpio" "rename"
    "liblz4-dev" "jq" "git-lfs"
)

declare -ra FEDORA_PACKAGES=(
    "unrar" "zip" "unzip" "p7zip" "p7zip-plugins" "sharutils"
    "uudeview" "mpack" "arj" "cabextract" "dtc" "xz-devel"
    "python3-pip" "brotli" "lz4" "axel" "gawk" "aria2" "detox"
    "cpio" "util-linux" "lz4-devel" "jq" "git-lfs"
)

declare -ra ARCH_PACKAGES=(
    "unrar" "zip" "unzip" "p7zip" "sharutils" "uudeview" "mpack"
    "arj" "cabextract" "dtc" "xz" "python-pip" "brotli" "lz4"
    "axel" "gawk" "aria2" "detox" "cpio" "util-linux" "jq" "git-lfs"
)

declare -ra MACOS_PACKAGES=(
    "protobuf" "xz" "brotli" "lz4" "aria2" "detox" "coreutils"
    "p7zip" "gawk" "git-lfs"
)

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt; then
            echo "debian"
        elif command_exists dnf; then
            echo "fedora"
        elif command_exists yum; then
            echo "rhel"
        elif command_exists pacman; then
            echo "arch"
        elif command_exists zypper; then
            echo "suse"
        elif command_exists apk; then
            echo "alpine"
        else
            echo "unknown-linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Update package repositories
update_repos() {
    local os_type="$1"
    
    msg_process "Updating package repositories"
    
    case "${os_type}" in
        debian)
            sudo apt -y update || abort "Failed to update apt repositories"
            ;;
        fedora)
            sudo dnf -y update || abort "Failed to update dnf repositories"
            ;;
        rhel)
            sudo yum -y update || abort "Failed to update yum repositories"
            ;;
        arch)
            sudo pacman -Sy || abort "Failed to update pacman repositories"
            ;;
        suse)
            sudo zypper refresh || abort "Failed to update zypper repositories"
            ;;
        alpine)
            sudo apk update || abort "Failed to update apk repositories"
            ;;
        *)
            msg_warning "Unknown package manager, skipping repository update"
            ;;
    esac
    
    msg_success "Package repositories updated"
}

# Install packages for Debian/Ubuntu
install_debian_packages() {
    msg_process "Installing packages for Debian/Ubuntu"
    
    # Install packages with retry mechanism
    local retry_count=0
    local max_retries=3
    
    while [[ ${retry_count} -lt ${max_retries} ]]; do
        if sudo apt install -y "${DEBIAN_PACKAGES[@]}"; then
            msg_success "Debian packages installed successfully"
            return 0
        else
            ((retry_count++))
            msg_warning "Package installation failed, retry ${retry_count}/${max_retries}"
            sleep 2
        fi
    done
    
    abort "Failed to install Debian packages after ${max_retries} attempts"
}

# Install packages for Fedora
install_fedora_packages() {
    msg_process "Installing packages for Fedora"
    
    # Install packages with retry mechanism
    local retry_count=0
    local max_retries=3
    
    while [[ ${retry_count} -lt ${max_retries} ]]; do
        if sudo dnf install -y "${FEDORA_PACKAGES[@]}"; then
            msg_success "Fedora packages installed successfully"
            return 0
        else
            ((retry_count++))
            msg_warning "Package installation failed, retry ${retry_count}/${max_retries}"
            sleep 2
        fi
    done
    
    abort "Failed to install Fedora packages after ${max_retries} attempts"
}

# Install packages for RHEL/CentOS
install_rhel_packages() {
    msg_process "Installing packages for RHEL/CentOS"
    
    # Enable EPEL repository first
    if ! rpm -q epel-release >/dev/null 2>&1; then
        msg_info "Installing EPEL repository"
        sudo yum install -y epel-release || abort "Failed to install EPEL repository"
    fi
    
    # Install packages
    sudo yum install -y "${FEDORA_PACKAGES[@]}" || abort "Failed to install RHEL packages"
    msg_success "RHEL packages installed successfully"
}

# Install packages for Arch Linux
install_arch_packages() {
    msg_process "Installing packages for Arch Linux"
    
    sudo pacman -S --noconfirm "${ARCH_PACKAGES[@]}" || abort "Failed to install Arch packages"
    msg_success "Arch packages installed successfully"
}

# Install packages for openSUSE
install_suse_packages() {
    msg_process "Installing packages for openSUSE"
    
    sudo zypper install -y "${FEDORA_PACKAGES[@]}" || abort "Failed to install openSUSE packages"
    msg_success "openSUSE packages installed successfully"
}

# Install packages for Alpine Linux
install_alpine_packages() {
    msg_process "Installing packages for Alpine Linux"
    
    local alpine_packages=(
        "unrar" "zip" "unzip" "p7zip" "sharutils" "mpack" "arj"
        "xz-dev" "python3" "py3-pip" "brotli" "lz4" "aria2" "gawk"
        "cpio" "util-linux" "jq" "git-lfs"
    )
    
    sudo apk add "${alpine_packages[@]}" || abort "Failed to install Alpine packages"
    msg_success "Alpine packages installed successfully"
}

# Install packages for macOS
install_macos_packages() {
    msg_process "Installing packages for macOS"
    
    if ! command_exists brew; then
        msg_error "Homebrew not found. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    brew install "${MACOS_PACKAGES[@]}" || abort "Failed to install macOS packages"
    msg_success "macOS packages installed successfully"
}

# Install uv (Python package manager)
install_uv() {
    msg_process "Installing uv for Python package management"
    
    if command_exists uv; then
        msg_info "uv is already installed"
        return 0
    fi
    
    # Install uv using the official installer
    if bash -c "$(curl -sL https://astral.sh/uv/install.sh)"; then
        msg_success "uv installed successfully"
        
        # Add to PATH if not already there
        if ! command_exists uv; then
            export PATH="${HOME}/.local/bin:${PATH}"
            echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> ~/.bashrc
            msg_info "Added uv to PATH"
        fi
    else
        msg_warning "Failed to install uv, falling back to pip"
    fi
}

# Verify installation
verify_installation() {
    msg_process "Verifying installation"
    
    local required_commands=("unzip" "7z" "aria2c" "git" "python3")
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "${cmd}"; then
            missing_commands+=("${cmd}")
        fi
    done
    
    if [[ ${#missing_commands[@]} -eq 0 ]]; then
        msg_success "All required commands are available"
        return 0
    else
        msg_error "Missing commands: ${missing_commands[*]}"
        return 1
    fi
}

# Check system requirements
check_requirements() {
    msg_process "Checking system requirements"
    
    # Check available disk space (at least 10GB)
    if ! check_disk_space 10; then
        msg_warning "Low disk space detected, consider freeing up space"
    fi
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        msg_warning "Running as root is not recommended for security reasons"
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        msg_warning "No internet connection detected, some features may not work"
    fi
    
    msg_success "System requirements check completed"
}

# Main setup function
setup_system() {
    local os_type
    os_type=$(detect_os)
    
    show_title "DumprX System Setup"
    msg_info "Detected OS: ${os_type}"
    
    check_requirements
    
    case "${os_type}" in
        debian)
            msg_info "Setting up for Debian/Ubuntu"
            update_repos "${os_type}"
            install_debian_packages
            ;;
        fedora)
            msg_info "Setting up for Fedora"
            update_repos "${os_type}"
            install_fedora_packages
            ;;
        rhel)
            msg_info "Setting up for RHEL/CentOS"
            update_repos "${os_type}"
            install_rhel_packages
            ;;
        arch)
            msg_info "Setting up for Arch Linux"
            update_repos "${os_type}"
            install_arch_packages
            ;;
        suse)
            msg_info "Setting up for openSUSE"
            update_repos "${os_type}"
            install_suse_packages
            ;;
        alpine)
            msg_info "Setting up for Alpine Linux"
            update_repos "${os_type}"
            install_alpine_packages
            ;;
        macos)
            msg_info "Setting up for macOS"
            install_macos_packages
            ;;
        *)
            abort "Unsupported operating system: ${os_type}"
            ;;
    esac
    
    install_uv
    
    if verify_installation; then
        msg_success "Setup completed successfully!"
        echo
        msg_info "You can now run the dumper script:"
        echo "  ./dumper.sh <firmware_file_or_url>"
    else
        abort "Setup verification failed"
    fi
}