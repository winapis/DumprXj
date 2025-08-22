#!/usr/bin/env python3
"""
DumprX Setup Script - Python version
Replaces the old bash setup.sh script
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, 
                              capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def print_banner():
    """Print the DumprX banner"""
    banner = """
\033[32m██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝\033[0m

\033[36mDumprX v2.0.0 - Advanced Firmware Dumper & Extractor\033[0m
\033[36mPython-based setup script\033[0m
"""
    print(banner)

def detect_os():
    """Detect the operating system"""
    system = platform.system().lower()
    if system == "linux":
        # Try to detect distribution
        if Path("/etc/debian_version").exists():
            return "debian"
        elif Path("/etc/alpine-release").exists():
            return "alpine"
        else:
            return "linux"
    elif system == "darwin":
        return "macos"
    else:
        return "unknown"

def install_debian_packages():
    """Install packages on Debian/Ubuntu systems"""
    print("\033[35mDebian/Ubuntu system detected\033[0m")
    
    packages = [
        "python3", "python3-pip", "python3-venv",
        "unzip", "zip", "p7zip-full", "rar", "unrar",
        "git", "git-lfs", "curl", "wget", "aria2",
        "build-essential", "cmake",
        "protobuf-compiler", "libprotobuf-dev",
        "liblz4-tool", "liblzma-dev", "libbz2-dev",
        "android-tools-adb", "android-tools-fastboot"
    ]
    
    print("\033[34m>> Updating package lists...\033[0m")
    if not run_command("sudo apt-get update"):
        print("\033[31mFailed to update package lists\033[0m")
        return False
        
    print("\033[34m>> Installing required packages...\033[0m")
    cmd = f"sudo apt-get install -y {' '.join(packages)}"
    if not run_command(cmd):
        print("\033[31mFailed to install some packages\033[0m")
        return False
        
    return True

def install_alpine_packages():
    """Install packages on Alpine Linux"""
    print("\033[35mAlpine Linux detected\033[0m")
    
    packages = [
        "python3", "py3-pip",
        "unzip", "zip", "p7zip", "rar", "unrar",
        "git", "git-lfs", "curl", "wget", "aria2",
        "build-base", "cmake",
        "protobuf", "protobuf-dev",
        "lz4", "xz", "bzip2",
        "android-tools"
    ]
    
    print("\033[34m>> Updating package lists...\033[0m")
    if not run_command("sudo apk update"):
        print("\033[31mFailed to update package lists\033[0m")
        return False
        
    print("\033[34m>> Installing required packages...\033[0m")
    cmd = f"sudo apk add {' '.join(packages)}"
    if not run_command(cmd):
        print("\033[31mFailed to install some packages\033[0m")
        return False
        
    return True

def install_macos_packages():
    """Install packages on macOS using Homebrew"""
    print("\033[35mmacOS detected\033[0m")
    
    # Check if Homebrew is installed
    if not run_command("which brew", check=False):
        print("\033[31mHomebrew not found. Please install Homebrew first:\033[0m")
        print("https://brew.sh")
        return False
        
    packages = [
        "python3", "unzip", "p7zip", "rar",
        "git", "git-lfs", "curl", "wget", "aria2",
        "protobuf", "xz", "brotli", "lz4",
        "coreutils", "gawk"
    ]
    
    print("\033[34m>> Installing required packages...\033[0m")
    cmd = f"brew install {' '.join(packages)}"
    if not run_command(cmd):
        print("\033[31mFailed to install some packages\033[0m")
        return False
        
    return True

def setup_python_environment():
    """Set up Python environment and install dependencies"""
    print("\033[34m>> Setting up Python environment...\033[0m")
    
    # Install/upgrade pip
    if not run_command("python3 -m pip install --upgrade pip"):
        print("\033[31mFailed to upgrade pip\033[0m")
        return False
        
    # Install the package in development mode
    if not run_command("python3 -m pip install -e ."):
        print("\033[31mFailed to install DumprX package\033[0m")
        return False
        
    return True

def setup_git_lfs():
    """Setup Git LFS"""
    print("\033[34m>> Setting up Git LFS...\033[0m")
    
    if not run_command("git lfs install --global"):
        print("\033[33mWarning: Git LFS setup failed\033[0m")
        return False
        
    return True

def create_directories():
    """Create necessary directories"""
    print("\033[34m>> Creating directories...\033[0m")
    
    directories = ["input", "out", "out/tmp"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
    return True

def verify_installation():
    """Verify that DumprX is properly installed"""
    print("\033[34m>> Verifying installation...\033[0m")
    
    # Test dumprx command
    if not run_command("dumprx version"):
        print("\033[31mDumprX command not working\033[0m")
        return False
        
    # Test dumprx setup command
    if not run_command("dumprx setup"):
        print("\033[33mWarning: dumprx setup had issues\033[0m")
        
    return True

def main():
    """Main setup function"""
    print_banner()
    
    # Detect OS
    os_type = detect_os()
    
    try:
        # Install system packages
        if os_type == "debian":
            if not install_debian_packages():
                sys.exit(1)
        elif os_type == "alpine":
            if not install_alpine_packages():
                sys.exit(1)
        elif os_type == "macos":
            if not install_macos_packages():
                sys.exit(1)
        else:
            print(f"\033[33mUnsupported OS: {os_type}\033[0m")
            print("Please install dependencies manually and run:")
            print("python3 -m pip install -e .")
            sys.exit(1)
            
        # Setup Python environment
        if not setup_python_environment():
            sys.exit(1)
            
        # Setup Git LFS
        setup_git_lfs()
        
        # Create directories
        create_directories()
        
        # Verify installation
        if not verify_installation():
            sys.exit(1)
            
        print("\033[32m>> Setup completed successfully!\033[0m")
        print()
        print("\033[36mNext steps:\033[0m")
        print("1. Configure your settings: dumprx config show")
        print("2. Test the installation: dumprx test")
        print("3. Extract firmware: dumprx dump <firmware_file_or_url>")
        print()
        print("\033[36mFor help: dumprx --help\033[0m")
        
    except KeyboardInterrupt:
        print("\n\033[31mSetup interrupted by user\033[0m")
        sys.exit(1)
    except Exception as e:
        print(f"\033[31mSetup failed: {e}\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()