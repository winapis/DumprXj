#!/usr/bin/env python3

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def install_system_dependencies():
    system = platform.system().lower()
    
    if system == "linux":
        if shutil.which("apt"):
            print("🐧 Ubuntu/Debian detected")
            deps = [
                "unace", "unrar", "zip", "unzip", "sharutils", "uudeview", 
                "arj", "cabextract", "file-roller", "dtc", "python3-pip", 
                "brotli", "axel", "aria2", "detox", "cpio", "lz4", 
                "python3-dev", "xz-utils", "p7zip-full", "p7zip-rar", 
                "git-lfs", "jq", "curl"
            ]
            cmd = f"sudo apt-get update && sudo apt-get install -y {' '.join(deps)}"
            return run_command(cmd)
            
        elif shutil.which("dnf"):
            print("🎩 Fedora/RHEL detected")
            deps = [
                "unace", "unrar", "zip", "unzip", "sharutils", "uudeview",
                "arj", "cabextract", "file-roller", "dtc", "python3-pip",
                "brotli", "axel", "aria2", "detox", "cpio", "lz4",
                "python3-devel", "xz-devel", "p7zip", "p7zip-plugins",
                "git-lfs"
            ]
            cmd = f"sudo dnf install -y {' '.join(deps)}"
            return run_command(cmd)
            
        elif shutil.which("pacman"):
            print("🏹 Arch Linux detected")
            deps = [
                "unace", "unrar", "p7zip", "sharutils", "uudeview", "arj",
                "cabextract", "file-roller", "dtc", "brotli", "axel", "gawk",
                "aria2", "detox", "cpio", "lz4", "jq", "git-lfs"
            ]
            cmd = f"sudo pacman -Syyu --needed --noconfirm && sudo pacman -Sy --noconfirm {' '.join(deps)}"
            return run_command(cmd)
            
    elif system == "darwin":
        print("🍎 macOS detected")
        deps = [
            "protobuf", "xz", "brotli", "lz4", "aria2", "detox",
            "coreutils", "p7zip", "gawk", "git-lfs"
        ]
        cmd = f"brew install {' '.join(deps)}"
        return run_command(cmd)
    
    return False

def install_python_deps():
    print("🐍 Installing Python dependencies...")
    return run_command("python3 -m pip install -r requirements.txt")

def install_uv():
    print("⚡ Installing uv for Python package management...")
    cmd = 'curl -sL https://astral.sh/uv/install.sh | bash'
    return run_command(cmd, check=False)

def setup_git_lfs():
    print("📦 Setting up Git LFS...")
    return run_command("git lfs install")

def main():
    print("🚀 Setting up DumprX...")
    
    success = True
    
    if not install_system_dependencies():
        print("❌ Failed to install system dependencies")
        success = False
    else:
        print("✅ System dependencies installed")
    
    if not install_python_deps():
        print("❌ Failed to install Python dependencies")
        success = False
    else:
        print("✅ Python dependencies installed")
    
    if not setup_git_lfs():
        print("⚠️ Git LFS setup failed (optional)")
    else:
        print("✅ Git LFS configured")
    
    install_uv()
    
    if success:
        print("🎉 Setup completed successfully!")
        print("📖 Usage: python3 dumprx.py <firmware_file_or_url>")
    else:
        print("💥 Setup failed! Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()