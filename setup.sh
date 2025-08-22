#!/bin/bash

# DumprX Setup Script - Modern Python Version
# This script installs system dependencies and sets up the Python package

# Clear Screen
tput reset 2>/dev/null || clear

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NORMAL='\033[0m'

# Banner
function __bannerTop() {
	echo -e \
	${GREEN}"
	██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
	██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
	██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
	██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
	██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
	╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
	"${NORMAL}
}

# Abort function
function abort(){
    [ ! -z "$@" ] && echo -e ${RED}"${@}"${NORMAL}
    exit 1
}

# Welcome Banner
printf "\e[32m" && __bannerTop && printf "\e[0m"
echo -e ${BLUE}"DumprX Setup - Installing Dependencies and Python Package"${NORMAL}
echo

# Minor Sleep
sleep 1

# Check if Python 3 is available
if ! command -v python3 > /dev/null 2>&1; then
    abort "Python 3 is required but not installed. Please install Python 3.8 or later."
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e ${BLUE}"Python ${PYTHON_VERSION} detected"${NORMAL}

# Check minimum Python version (3.8+)
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    abort "Python 3.8 or later is required. Current version: ${PYTHON_VERSION}"
fi

# Check for package managers and install system dependencies
if [[ "$OSTYPE" == "linux-gnu" ]]; then

    if command -v apt > /dev/null 2>&1; then

        echo -e ${PURPLE}"Ubuntu/Debian Based Distro Detected"${NORMAL}
        sleep 1
        echo -e ${BLUE}">> Updating apt repos..."${NORMAL}
        sleep 1
	    sudo apt -y update || abort "Setup Failed!"
	    sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1
        sudo apt install -y unace unrar zip unzip p7zip-full p7zip-rar sharutils rar uudeview mpack arj cabextract device-tree-compiler liblzma-dev python3-pip brotli liblz4-tool axel gawk aria2 detox cpio rename liblz4-dev jq git-lfs python3-venv || abort "Setup Failed!"

    elif command -v dnf > /dev/null 2>&1; then

        echo -e ${PURPLE}"Fedora Based Distro Detected"${NORMAL}
        sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1

	    # "dnf" automatically updates repos before installing packages
        sudo dnf install -y unace unrar zip unzip sharutils uudeview arj cabextract file-roller dtc python3-pip brotli axel aria2 detox cpio lz4 python3-devel xz-devel p7zip p7zip-plugins git-lfs || abort "Setup Failed!"

    elif command -v pacman > /dev/null 2>&1; then

        echo -e ${PURPLE}"Arch or Arch Based Distro Detected"${NORMAL}
        sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1

        sudo pacman -Syyu --needed --noconfirm >/dev/null || abort "Setup Failed!"
        sudo pacman -Sy --noconfirm unace unrar p7zip sharutils uudeview arj cabextract file-roller dtc brotli axel gawk aria2 detox cpio lz4 jq git-lfs python || abort "Setup Failed!"

    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then

    echo -e ${PURPLE}"macOS Detected"${NORMAL}
    sleep 1
	echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	sleep 1
    brew install protobuf xz brotli lz4 aria2 detox coreutils p7zip gawk git-lfs python@3.11 || abort "Setup Failed!"

fi

sleep 1

# Install Python package in development mode
echo -e ${BLUE}">> Installing DumprX Python package..."${NORMAL}
sleep 1

# Install package in development mode so it's editable
python3 -m pip install -e . || abort "Python package installation failed!"

sleep 1

# Create executable script in ~/.local/bin
LOCAL_BIN_DIR="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN_DIR"

cat > "$LOCAL_BIN_DIR/dumprx" << 'EOF'
#!/usr/bin/env python3

import sys
import os

# Add current directory to Python path if running from source
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if os.path.exists(os.path.join(parent_dir, 'dumprx', '__init__.py')):
    sys.path.insert(0, parent_dir)

try:
    from dumprx.cli import cli
    cli()
except ImportError:
    # Fallback to module execution
    import subprocess
    subprocess.run([sys.executable, '-m', 'dumprx.cli'] + sys.argv[1:])
EOF

chmod +x "$LOCAL_BIN_DIR/dumprx"

echo -e ${GREEN}"✅ DumprX executable created at $LOCAL_BIN_DIR/dumprx"${NORMAL}

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$LOCAL_BIN_DIR:"* ]]; then
    echo -e ${YELLOW}"💡 Add $LOCAL_BIN_DIR to your PATH to use 'dumprx' command globally"${NORMAL}
    echo -e ${YELLOW}"   Add this line to your ~/.bashrc or ~/.zshrc:"${NORMAL}
    echo -e ${YELLOW}"   export PATH=\"\$HOME/.local/bin:\$PATH\""${NORMAL}
fi

# Test installation
echo -e ${BLUE}">> Testing DumprX installation..."${NORMAL}

if python3 -m dumprx.cli --version >/dev/null 2>&1; then
    echo -e ${GREEN}"✅ DumprX installation test passed"${NORMAL}
else
    echo -e ${YELLOW}"⚠️ DumprX installation test failed, but package is installed"${NORMAL}
fi

sleep 1

# Done!
echo -e ${GREEN}"🎉 Setup Complete!"${NORMAL}
echo
echo -e ${BLUE}"You can now use DumprX by running:"${NORMAL}
echo -e ${GREEN}"  dumprx <firmware_file_or_url>"${NORMAL}
echo -e ${GREEN}"  python3 -m dumprx.cli <firmware_file_or_url>"${NORMAL}
echo
echo -e ${BLUE}"For help:"${NORMAL}
echo -e ${GREEN}"  dumprx --help"${NORMAL}

# Exit
exit 0
