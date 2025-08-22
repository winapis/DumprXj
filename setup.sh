#!/bin/bash

# Clear Screen
tput reset 2>/dev/null || clear

# Colours (or Colors in en_US)
RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
NORMAL='\033[0m'

# Abort Function
function abort(){
    [ ! -z "$@" ] && echo -e ${RED}"${@}"${NORMAL}
    exit 1
}

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

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Welcome Banner
printf "\e[32m" && __bannerTop && printf "\e[0m"

echo -e ${BLUE}"🚀 DumprX Setup - Installing Dependencies and Configuring Environment"${NORMAL}
echo ""

# Check if Python 3.8+ is available
echo -e ${BLUE}">> Checking Python installation..."${NORMAL}
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e ${GREEN}"✅ Python $PYTHON_VERSION found"${NORMAL}
    
    # Check if version is 3.8+
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        echo -e ${GREEN}"✅ Python version is compatible"${NORMAL}
    else
        echo -e ${RED}"❌ Python 3.8+ required, found $PYTHON_VERSION"${NORMAL}
        abort "Please upgrade Python to 3.8 or higher"
    fi
else
    echo -e ${RED}"❌ Python 3 not found"${NORMAL}
    abort "Please install Python 3.8 or higher"
fi

sleep 1

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
        sudo apt install -y unace unrar zip unzip p7zip-full p7zip-rar sharutils rar uudeview mpack arj cabextract device-tree-compiler liblzma-dev python3-pip python3-venv brotli liblz4-tool axel gawk aria2 detox cpio rename liblz4-dev jq git-lfs curl || abort "Setup Failed!"

    elif command -v dnf > /dev/null 2>&1; then

        echo -e ${PURPLE}"Fedora Based Distro Detected"${NORMAL}
        sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1

	    # "dnf" automatically updates repos before installing packages
        sudo dnf install -y unace unrar zip unzip sharutils uudeview arj cabextract file-roller dtc python3-pip python3-devel brotli axel aria2 detox cpio lz4 python3-devel xz-devel p7zip p7zip-plugins git-lfs curl || abort "Setup Failed!"

    elif command -v pacman > /dev/null 2>&1; then

        echo -e ${PURPLE}"Arch or Arch Based Distro Detected"${NORMAL}
        sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1

        sudo pacman -Syyu --needed --noconfirm >/dev/null || abort "Setup Failed!"
        sudo pacman -Sy --noconfirm unace unrar p7zip sharutils uudeview arj cabextract file-roller dtc brotli axel gawk aria2 detox cpio lz4 jq git-lfs python python-pip curl || abort "Setup Failed!"

    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then

    echo -e ${PURPLE}"macOS Detected"${NORMAL}
    sleep 1
	echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	sleep 1
    brew install protobuf xz brotli lz4 aria2 detox coreutils p7zip gawk git-lfs python curl || abort "Setup Failed!"

fi

sleep 1

# Install `uv` for Python package management
echo -e ${BLUE}">> Installing uv for python packages..."${NORMAL}
sleep 1
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh || abort "UV installation failed!"
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo -e ${GREEN}"✅ uv already installed"${NORMAL}
fi

sleep 1

# Install Python dependencies
echo -e ${BLUE}">> Installing Python dependencies..."${NORMAL}
sleep 1
cd "$SCRIPT_DIR" || abort "Could not change to script directory"

if [[ -f "requirements.txt" ]]; then
    uv pip install --system -r requirements.txt || abort "Python dependencies installation failed!"
    echo -e ${GREEN}"✅ Python dependencies installed"${NORMAL}
else
    echo -e ${RED}"❌ requirements.txt not found"${NORMAL}
    abort "requirements.txt missing"
fi

sleep 1

# Make main script executable
echo -e ${BLUE}">> Setting up DumprX executable..."${NORMAL}
if [[ -f "dumprx.py" ]]; then
    chmod +x dumprx.py
    echo -e ${GREEN}"✅ DumprX CLI configured"${NORMAL}
else
    echo -e ${RED}"❌ dumprx.py not found"${NORMAL}
    abort "Main script missing"
fi

sleep 1

# Create config.yaml if it doesn't exist
echo -e ${BLUE}">> Setting up configuration..."${NORMAL}
if [[ ! -f "config.yaml" ]]; then
    echo -e ${RED}"❌ config.yaml not found"${NORMAL}
    abort "Configuration file missing"
else
    echo -e ${GREEN}"✅ Configuration file found"${NORMAL}
fi

sleep 1

# Test installation
echo -e ${BLUE}">> Testing installation..."${NORMAL}
if python3 dumprx.py --version >/dev/null 2>&1; then
    echo -e ${GREEN}"✅ Installation test passed"${NORMAL}
else
    echo -e ${RED}"❌ Installation test failed"${NORMAL}
    abort "Installation verification failed"
fi

sleep 1

# Done!
echo ""
echo -e ${GREEN}"🎉 DumprX Setup Complete!"${NORMAL}
echo ""
echo -e ${BLUE}"Usage:"${NORMAL}
echo -e "  ${GREEN}python3 dumprx.py dump <firmware_file_or_url>${NORMAL}    # Extract firmware"
echo -e "  ${GREEN}python3 dumprx.py download <url>${NORMAL}                 # Download firmware"
echo -e "  ${GREEN}python3 dumprx.py detect <file>${NORMAL}                  # Detect firmware type"
echo -e "  ${GREEN}python3 dumprx.py status${NORMAL}                         # Show status"
echo -e "  ${GREEN}python3 dumprx.py --help${NORMAL}                         # Show help"
echo ""
echo -e ${BLUE}"Configuration:"${NORMAL}
echo -e "  Edit ${GREEN}config.yaml${NORMAL} to configure tokens and settings"
echo -e "  Or use token files: ${GREEN}.github_token${NORMAL}, ${GREEN}.gitlab_token${NORMAL}, ${GREEN}.tg_token${NORMAL}"
echo ""

# Exit
exit 0
