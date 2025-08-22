#!/bin/bash

# DumprX v2.0 Setup Script
# This script sets up the Python environment and dependencies

# Clear Screen
tput reset 2>/dev/null || clear

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
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
	██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗  ██╗░░░██╗██████╗░░░███╗░░
	██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝  ██║░░░██║╚════██╗░████║░░
	██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░  ╚██╗░██╔╝░░███╔═╝██╔██║░░
	██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░  ░╚████╔╝░██╔══╝░░╚═╝██║░░
	██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗  ░░╚██╔╝░░███████╗███████╗
	╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝  ░░░╚═╝░░░╚══════╝╚══════╝
	"${NORMAL}
}

# Welcome Banner
printf "\e[32m" && __bannerTop && printf "\e[0m"

echo -e ${BLUE}"🚀 Setting up DumprX v2.0 Python Environment..."${NORMAL}
sleep 1

# Check Python version
echo -e ${BLUE}"🐍 Checking Python version..."${NORMAL}
if command -v python3 > /dev/null 2>&1; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e ${GREEN}"✅ Python ${PYTHON_VERSION} found"${NORMAL}
    
    # Check if Python version is 3.8 or higher
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        echo -e ${GREEN}"✅ Python version is compatible"${NORMAL}
    else
        echo -e ${YELLOW}"⚠️ Python 3.8+ recommended, but continuing..."${NORMAL}
    fi
else
    abort "❌ Python 3 is required but not found!"
fi

# Detect OS and install system packages
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    echo -e ${PURPLE}"🐧 Linux detected"${NORMAL}
    
    if command -v apt > /dev/null 2>&1; then
        echo -e ${BLUE}"📦 Installing system packages with apt..."${NORMAL}
        sudo apt update || abort "Failed to update package lists!"
        sudo apt install -y \
            python3-pip python3-dev python3-venv \
            unace unrar zip unzip p7zip-full p7zip-rar \
            sharutils rar uudeview mpack arj cabextract \
            device-tree-compiler liblzma-dev brotli \
            liblz4-tool axel aria2 detox cpio rename \
            liblz4-dev jq git-lfs libmagic1 \
            build-essential || abort "Failed to install system packages!"
            
    elif command -v dnf > /dev/null 2>&1; then
        echo -e ${BLUE}"📦 Installing system packages with dnf..."${NORMAL}
        sudo dnf install -y \
            python3-pip python3-devel python3-virtualenv \
            unrar p7zip p7zip-plugins lz4 brotli \
            git-lfs file-libs || abort "Failed to install system packages!"
            
    elif command -v pacman > /dev/null 2>&1; then
        echo -e ${BLUE}"📦 Installing system packages with pacman..."${NORMAL}
        sudo pacman -Sy --noconfirm \
            python-pip unrar p7zip lz4 brotli \
            git-lfs file || abort "Failed to install system packages!"
    else
        echo -e ${YELLOW}"⚠️ Unknown package manager, some features may not work"${NORMAL}
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e ${PURPLE}"🍎 macOS detected"${NORMAL}
    
    if command -v brew > /dev/null 2>&1; then
        echo -e ${BLUE}"🍺 Installing packages with Homebrew..."${NORMAL}
        brew install python3 p7zip unrar lz4 brotli git-lfs libmagic || abort "Failed to install packages!"
    else
        echo -e ${YELLOW}"⚠️ Homebrew not found, please install manually"${NORMAL}
    fi
else
    echo -e ${YELLOW}"⚠️ Unknown OS, proceeding with Python setup only"${NORMAL}
fi

# Install Python dependencies
echo -e ${BLUE}"📋 Installing Python dependencies..."${NORMAL}

# Upgrade pip first
python3 -m pip install --upgrade pip || abort "Failed to upgrade pip!"

# Install requirements
if [ -f "requirements.txt" ]; then
    echo -e ${BLUE}"📋 Installing from requirements.txt..."${NORMAL}
    python3 -m pip install -r requirements.txt || abort "Failed to install Python requirements!"
else
    echo -e ${BLUE}"📋 Installing core dependencies..."${NORMAL}
    python3 -m pip install \
        requests click rich colorama humanize psutil \
        rarfile py7zr patoolib python-magic lxml pyyaml \
        tqdm tabulate lz4 zstandard brotli || abort "Failed to install core dependencies!"
fi

# Make dumper_v2.py executable
echo -e ${BLUE}"🔧 Setting up executable permissions..."${NORMAL}
chmod +x dumper_v2.py

# Test the installation
echo -e ${BLUE}"🧪 Testing installation..."${NORMAL}
if python3 dumper_v2.py --version > /dev/null 2>&1; then
    echo -e ${GREEN}"✅ DumprX v2.0 is ready!"${NORMAL}
else
    echo -e ${YELLOW}"⚠️ Warning: Installation test failed, but continuing..."${NORMAL}
fi

# Setup completion message
echo -e ${GREEN}"
🎉 Setup Complete!

📋 Usage:
  ./dumper_v2.py <firmware_file_or_url>
  ./dumper_v2.py --help

🔧 For legacy compatibility:
  ./dumper.sh <firmware_file_or_url>

📖 For more information, see README.md
"${NORMAL}

echo -e ${BLUE}"⚡ DumprX v2.0 is ready to extract firmware!"${NORMAL}