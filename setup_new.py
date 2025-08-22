#!/usr/bin/env python3
"""
Modern setup script for DumprX.
Replaces the old bash setup.sh with Python implementation.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

from dumprx.core.logger import Logger
from dumprx.core.config import Config

class DumprXSetup:
    """Setup manager for DumprX."""
    
    def __init__(self):
        self.logger = Logger("Setup")
        self.config = Config()
        self.system = platform.system().lower()
        self.distro = self._detect_linux_distro()
    
    def _detect_linux_distro(self):
        """Detect Linux distribution."""
        if self.system != "linux":
            return None
        
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read().lower()
                if "ubuntu" in content or "debian" in content:
                    return "debian"
                elif "fedora" in content or "rhel" in content or "centos" in content:
                    return "fedora"  
                elif "arch" in content:
                    return "arch"
                elif "alpine" in content:
                    return "alpine"
        except FileNotFoundError:
            pass
        
        return "unknown"
    
    def show_banner(self):
        """Show setup banner."""
        banner = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝

Setup & Dependency Installation
        """
        self.logger.banner(banner)
    
    def check_python_version(self):
        """Check Python version compatibility."""
        self.logger.step(1, 8, "Checking Python version")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.logger.error("Python 3.8+ required", f"Current: {version.major}.{version.minor}")
            return False
        
        self.logger.success(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    
    def install_python_packages(self):
        """Install Python package dependencies."""
        self.logger.step(2, 8, "Installing Python packages")
        
        requirements_file = Path(__file__).parent / "requirements.txt"
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.success("Python packages installed")
                return True
            else:
                self.logger.error("Failed to install Python packages", result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Python package installation timeout")
            return False
        except Exception as e:
            self.logger.error("Python package installation failed", str(e))
            return False
    
    def install_system_packages(self):
        """Install system packages based on distribution."""
        self.logger.step(3, 8, f"Installing system packages for {self.distro or self.system}")
        
        if self.system == "linux":
            return self._install_linux_packages()
        elif self.system == "darwin":
            return self._install_macos_packages()
        else:
            self.logger.warning(f"Unsupported system: {self.system}")
            return True  # Continue anyway
    
    def _install_linux_packages(self):
        """Install Linux packages based on distribution."""
        packages = {
            "debian": {
                "update_cmd": ["sudo", "apt", "-y", "update"],
                "install_cmd": ["sudo", "apt", "install", "-y"],
                "packages": [
                    "unace", "unrar", "zip", "unzip", "p7zip-full", "p7zip-rar",
                    "sharutils", "rar", "uudeview", "mpack", "arj", "cabextract",
                    "device-tree-compiler", "liblzma-dev", "python3-pip", "brotli",
                    "liblz4-tool", "axel", "gawk", "aria2", "detox", "cpio", "rename",
                    "liblz4-dev", "jq", "git-lfs", "xz-utils"
                ]
            },
            "fedora": {
                "install_cmd": ["sudo", "dnf", "install", "-y"],
                "packages": [
                    "unace", "unrar", "zip", "unzip", "sharutils", "uudeview", "arj",
                    "cabextract", "file-roller", "dtc", "python3-pip", "brotli", "axel",
                    "aria2", "detox", "cpio", "lz4", "python3-devel", "xz-devel",
                    "p7zip", "p7zip-plugins", "git-lfs", "xz"
                ]
            },
            "arch": {
                "update_cmd": ["sudo", "pacman", "-Syyu", "--needed", "--noconfirm"],
                "install_cmd": ["sudo", "pacman", "-Sy", "--noconfirm"],
                "packages": [
                    "unace", "unrar", "p7zip", "sharutils", "uudeview", "arj", "cabextract",
                    "file-roller", "dtc", "brotli", "axel", "gawk", "aria2", "detox",
                    "cpio", "lz4", "jq", "git-lfs", "xz"
                ]
            },
            "alpine": {
                "update_cmd": ["sudo", "apk", "update"],
                "install_cmd": ["sudo", "apk", "add"],
                "packages": [
                    "unrar", "zip", "unzip", "p7zip", "sharutils", "arj", "brotli",
                    "axel", "gawk", "aria2", "cpio", "lz4", "jq", "git-lfs", "xz"
                ]
            }
        }
        
        if self.distro not in packages:
            self.logger.warning(f"Unknown distribution: {self.distro}")
            self.logger.info("Please install packages manually:")
            self.logger.info("unrar, zip, unzip, p7zip, brotli, aria2, git-lfs, xz")
            return True
        
        distro_info = packages[self.distro]
        
        try:
            # Update package list if needed
            if "update_cmd" in distro_info:
                self.logger.info("Updating package lists")
                result = subprocess.run(
                    distro_info["update_cmd"], 
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode != 0:
                    self.logger.warning("Package list update failed, continuing anyway")
            
            # Install packages
            self.logger.info("Installing system packages")
            cmd = distro_info["install_cmd"] + distro_info["packages"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.logger.success("System packages installed")
                return True
            else:
                self.logger.warning("Some packages failed to install", result.stderr[:200])
                return True  # Continue anyway
                
        except subprocess.TimeoutExpired:
            self.logger.error("Package installation timeout")
            return False
        except Exception as e:
            self.logger.error("Package installation failed", str(e))
            return False
    
    def _install_macos_packages(self):
        """Install macOS packages using Homebrew."""
        try:
            # Check if Homebrew is installed
            result = subprocess.run(["which", "brew"], capture_output=True)
            if result.returncode != 0:
                self.logger.error("Homebrew not found. Please install Homebrew first:")
                self.logger.info("https://brew.sh/")
                return False
            
            packages = ["p7zip", "brotli", "aria2", "git-lfs", "xz"]
            
            self.logger.info("Installing packages via Homebrew")
            cmd = ["brew", "install"] + packages
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.logger.success("macOS packages installed")
                return True
            else:
                self.logger.warning("Some packages failed to install", result.stderr[:200])
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error("macOS package installation failed", str(e))
            return False
    
    def setup_git_lfs(self):
        """Setup Git LFS."""
        self.logger.step(4, 8, "Setting up Git LFS")
        
        try:
            result = subprocess.run(["git", "lfs", "install"], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.success("Git LFS configured")
                return True
            else:
                self.logger.warning("Git LFS setup failed", result.stderr)
                return True  # Not critical
                
        except Exception as e:
            self.logger.warning("Git LFS setup failed", str(e))
            return True  # Not critical
    
    def clone_external_tools(self):
        """Clone external tools repositories."""
        self.logger.step(5, 8, "Cloning external tools")
        
        utils_dir = Path(self.config.get_utils_dir())
        utils_dir.mkdir(exist_ok=True)
        
        success_count = 0
        for tool_repo in self.config.external_tools:
            try:
                tool_name = tool_repo.split("/")[1]
                tool_dir = utils_dir / tool_name
                
                if tool_dir.exists():
                    # Update existing repository
                    self.logger.debug(f"Updating {tool_name}")
                    result = subprocess.run(
                        ["git", "-C", str(tool_dir), "pull"],
                        capture_output=True, text=True, timeout=60
                    )
                else:
                    # Clone new repository
                    self.logger.debug(f"Cloning {tool_name}")
                    result = subprocess.run([
                        "git", "clone", "-q", 
                        f"https://github.com/{tool_repo}.git", 
                        str(tool_dir)
                    ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    success_count += 1
                else:
                    self.logger.warning(f"Failed to clone/update {tool_name}")
                    
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Timeout cloning {tool_repo}")
            except Exception as e:
                self.logger.warning(f"Error with {tool_repo}: {str(e)}")
        
        total_tools = len(self.config.external_tools)
        self.logger.success(f"External tools: {success_count}/{total_tools} ready")
        return success_count > 0
    
    def setup_directories(self):
        """Create necessary directories."""
        self.logger.step(6, 8, "Creating directories")
        
        try:
            self.config.create_directories()
            self.logger.success("Directories created")
            return True
        except Exception as e:
            self.logger.error("Failed to create directories", str(e))
            return False
    
    def make_tools_executable(self):
        """Make binary tools executable."""
        self.logger.step(7, 8, "Setting tool permissions")
        
        utils_dir = Path(self.config.get_utils_dir())
        bin_dir = utils_dir / "bin"
        
        if not bin_dir.exists():
            self.logger.warning("Binary tools directory not found")
            return True
        
        try:
            for tool in bin_dir.iterdir():
                if tool.is_file():
                    tool.chmod(0o755)
            
            # Also make other tools executable
            other_tools = [
                utils_dir / "lpunpack",
                utils_dir / "unsin", 
                utils_dir / "nb0-extract",
                utils_dir / "dtc",
                utils_dir / "extract-ikconfig"
            ]
            
            for tool in other_tools:
                if tool.exists():
                    tool.chmod(0o755)
            
            self.logger.success("Tool permissions set")
            return True
            
        except Exception as e:
            self.logger.warning("Failed to set tool permissions", str(e))
            return True  # Not critical
    
    def validate_setup(self):
        """Validate setup completion."""
        self.logger.step(8, 8, "Validating setup")
        
        # Check critical tools
        critical_tools = [
            "python3", "git", "aria2c", "7zz"
        ]
        
        missing_tools = []
        for tool in critical_tools:
            result = subprocess.run(["which", tool], capture_output=True)
            if result.returncode != 0:
                missing_tools.append(tool)
        
        if missing_tools:
            self.logger.warning(f"Missing tools: {', '.join(missing_tools)}")
        else:
            self.logger.success("All critical tools available")
        
        # Check if main script is executable
        main_script = Path(__file__).parent / "dumprx_main.py"
        if main_script.exists():
            main_script.chmod(0o755)
            self.logger.success("Setup validation completed")
        
        return True
    
    def run_setup(self):
        """Run complete setup process."""
        self.show_banner()
        
        steps = [
            self.check_python_version,
            self.install_python_packages,
            self.install_system_packages,
            self.setup_git_lfs,
            self.clone_external_tools,
            self.setup_directories,
            self.make_tools_executable,
            self.validate_setup
        ]
        
        failed_steps = []
        for step in steps:
            if not step():
                failed_steps.append(step.__name__)
        
        if failed_steps:
            self.logger.warning(f"Setup completed with {len(failed_steps)} issues")
            self.logger.info("You may need to install some packages manually")
        else:
            self.logger.success("Setup completed successfully!")
        
        self.logger.info("You can now run: python3 dumprx_main.py <firmware_path>")
        return len(failed_steps) == 0

def main():
    """Main setup entry point."""
    setup = DumprXSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()