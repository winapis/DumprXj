#!/usr/bin/env python3

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import logging

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

console = Console()
logger = logging.getLogger(__name__)


def show_setup_banner():
    """Show DumprX setup banner"""
    banner = """
	██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
	██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
	██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
	██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
	██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
	╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
	"""
    console.print(banner, style="green")
    console.print("DumprX Setup - Installing Dependencies and Tools", style="bold blue")
    console.print()


def abort(message: str):
    """Print error message and exit"""
    console.print(f"❌ {message}", style="bold red")
    sys.exit(1)


def detect_system():
    """Detect the operating system and package manager"""
    system = platform.system().lower()
    
    if system == "linux":
        # Check for different package managers
        if shutil.which("apt"):
            return "ubuntu"
        elif shutil.which("dnf"):
            return "fedora"
        elif shutil.which("pacman"):
            return "arch"
        elif shutil.which("apk"):
            return "alpine"
        else:
            console.print("⚠️ Linux distribution not fully supported, trying generic approach", style="yellow")
            return "linux"
    elif system == "darwin":
        return "macos"
    else:
        abort(f"Unsupported operating system: {system}")


def install_system_packages(distro: str):
    """Install system packages based on distribution"""
    console.print(f"🔍 {distro.title()} detected", style="purple")
    
    packages = {
        "ubuntu": {
            "cmd": ["sudo", "apt", "install", "-y"],
            "packages": [
                "unace", "unrar", "zip", "unzip", "p7zip-full", "p7zip-rar",
                "sharutils", "rar", "uudeview", "mpack", "arj", "cabextract",
                "device-tree-compiler", "liblzma-dev", "python3-pip", "brotli",
                "liblz4-tool", "axel", "gawk", "aria2", "detox", "cpio", "rename",
                "liblz4-dev", "jq", "git-lfs"
            ],
            "update_cmd": ["sudo", "apt", "-y", "update"]
        },
        "fedora": {
            "cmd": ["sudo", "dnf", "install", "-y"],
            "packages": [
                "unace", "unrar", "zip", "unzip", "sharutils", "uudeview", "arj",
                "cabextract", "file-roller", "dtc", "python3-pip", "brotli", "axel",
                "aria2", "detox", "cpio", "lz4", "python3-devel", "xz-devel",
                "p7zip", "p7zip-plugins", "git-lfs"
            ]
        },
        "arch": {
            "cmd": ["sudo", "pacman", "-Sy", "--noconfirm"],
            "packages": [
                "unace", "unrar", "p7zip", "sharutils", "uudeview", "arj",
                "cabextract", "file-roller", "dtc", "brotli", "axel", "gawk",
                "aria2", "detox", "cpio", "lz4", "jq", "git-lfs"
            ],
            "update_cmd": ["sudo", "pacman", "-Syyu", "--needed", "--noconfirm"]
        },
        "alpine": {
            "cmd": ["sudo", "apk", "add"],
            "packages": [
                "unzip", "p7zip", "aria2", "gawk", "cpio", "lz4", "git-lfs"
            ],
            "update_cmd": ["sudo", "apk", "update"]
        },
        "macos": {
            "cmd": ["brew", "install"],
            "packages": [
                "protobuf", "xz", "brotli", "lz4", "aria2", "detox",
                "coreutils", "p7zip", "gawk", "git-lfs"
            ]
        }
    }
    
    if distro not in packages:
        console.print(f"⚠️ No package list for {distro}, you may need to install dependencies manually", style="yellow")
        return
    
    pkg_info = packages[distro]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Update package manager if needed
        if "update_cmd" in pkg_info:
            task = progress.add_task("Updating package repositories...", total=None)
            try:
                result = subprocess.run(
                    pkg_info["update_cmd"], 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
                if result.returncode != 0:
                    console.print(f"⚠️ Package update warning: {result.stderr}", style="yellow")
            except subprocess.TimeoutExpired:
                console.print("⚠️ Package update timed out", style="yellow")
            except Exception as e:
                console.print(f"⚠️ Package update error: {e}", style="yellow")
        
        # Install packages
        task = progress.add_task("Installing required packages...", total=None)
        try:
            cmd = pkg_info["cmd"] + pkg_info["packages"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
            
            if result.returncode != 0:
                abort(f"Package installation failed: {result.stderr}")
            
            progress.update(task, description="✅ System packages installed")
            
        except subprocess.TimeoutExpired:
            abort("Package installation timed out")
        except Exception as e:
            abort(f"Package installation error: {e}")


def install_uv():
    """Install uv for Python package management"""
    console.print("📦 Installing uv for Python packages...", style="blue")
    
    try:
        # Check if uv is already installed
        if shutil.which("uv"):
            console.print("✅ uv already installed", style="green")
            return
        
        # Install uv
        install_cmd = 'curl -sL https://astral.sh/uv/install.sh | bash'
        result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            abort(f"uv installation failed: {result.stderr}")
        
        console.print("✅ uv installed successfully", style="green")
        
    except subprocess.TimeoutExpired:
        abort("uv installation timed out")
    except Exception as e:
        abort(f"uv installation error: {e}")


def install_python_dependencies():
    """Install Python dependencies using uv"""
    console.print("🐍 Installing Python dependencies...", style="blue")
    
    # Create requirements.txt if it doesn't exist
    requirements = [
        "click>=8.0.0",
        "rich>=13.0.0",
        "requests>=2.25.0"
    ]
    
    project_dir = Path(__file__).parent
    requirements_file = project_dir / "requirements.txt"
    
    if not requirements_file.exists():
        with open(requirements_file, 'w') as f:
            for req in requirements:
                f.write(f"{req}\n")
    
    try:
        # Install with uv
        result = subprocess.run([
            "uv", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            # Fallback to pip
            console.print("⚠️ uv failed, trying pip...", style="yellow")
            result = subprocess.run([
                "python3", "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                abort(f"Python dependencies installation failed: {result.stderr}")
        
        console.print("✅ Python dependencies installed", style="green")
        
    except subprocess.TimeoutExpired:
        abort("Python dependencies installation timed out")
    except Exception as e:
        abort(f"Python dependencies installation error: {e}")


def setup_dumprx_package():
    """Install DumprX as an executable package"""
    console.print("⚙️ Setting up DumprX package...", style="blue")
    
    project_dir = Path(__file__).parent
    
    try:
        # Install in development mode
        result = subprocess.run([
            "python3", "-m", "pip", "install", "-e", str(project_dir)
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            abort(f"DumprX package installation failed: {result.stderr}")
        
        console.print("✅ DumprX package installed", style="green")
        
    except subprocess.TimeoutExpired:
        abort("DumprX package installation timed out")
    except Exception as e:
        abort(f"DumprX package installation error: {e}")


def create_executable_script():
    """Create dumprx executable script"""
    script_content = '''#!/usr/bin/env python3

import sys
from dumprx.cli import cli

if __name__ == "__main__":
    cli()
'''
    
    # Install to /usr/local/bin if possible, otherwise ~/.local/bin
    local_bin = Path.home() / ".local" / "bin"
    system_bin = Path("/usr/local/bin")
    
    target_bin = system_bin if system_bin.exists() and os.access(system_bin, os.W_OK) else local_bin
    target_bin.mkdir(parents=True, exist_ok=True)
    
    dumprx_script = target_bin / "dumprx"
    
    try:
        with open(dumprx_script, 'w') as f:
            f.write(script_content)
        
        dumprx_script.chmod(0o755)
        console.print(f"✅ DumprX executable created at {dumprx_script}", style="green")
        
        # Add to PATH if needed
        if str(target_bin) not in os.environ.get("PATH", ""):
            console.print(f"💡 Add {target_bin} to your PATH to use 'dumprx' command", style="yellow")
            
    except Exception as e:
        console.print(f"⚠️ Could not create executable: {e}", style="yellow")


def main():
    """Main setup function"""
    # Clear screen
    console.clear()
    
    # Show banner
    show_setup_banner()
    
    # Detect system
    distro = detect_system()
    console.print(f"🖥️ System detected: {distro}", style="cyan")
    
    if not Confirm.ask("Continue with installation?"):
        console.print("Setup cancelled", style="yellow")
        return
    
    try:
        # Install system packages
        install_system_packages(distro)
        
        # Install uv
        install_uv()
        
        # Install Python dependencies
        install_python_dependencies()
        
        # Setup DumprX package
        setup_dumprx_package()
        
        # Create executable
        create_executable_script()
        
        console.print("\n🎉 Setup Complete!", style="bold green")
        console.print("You can now use DumprX by running:", style="cyan")
        console.print("  dumprx <firmware_file_or_url>", style="bold cyan")
        console.print("\nFor help, run:", style="cyan")
        console.print("  dumprx --help", style="bold cyan")
        
    except KeyboardInterrupt:
        console.print("\n⚠️ Setup interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        logger.exception("Setup failed")
        abort(f"Setup failed: {e}")


if __name__ == "__main__":
    main()