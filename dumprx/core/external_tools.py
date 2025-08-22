import subprocess
import shutil
from pathlib import Path
from typing import List
import logging

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

from dumprx.core.config import Config
from dumprx.utils.ui import print_info, print_success, print_warning

logger = logging.getLogger(__name__)
console = Console()


class ExternalToolsManager:
    def __init__(self, config: Config):
        self.config = config
        
    def setup_tools(self):
        """Setup external tools by cloning/updating repositories"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Setting up external tools...", total=len(self.config.external_tools))
            
            for tool_slug in self.config.external_tools:
                tool_name = tool_slug.split('/')[-1]
                tool_dir = self.config.utils_dir / tool_name
                
                progress.update(task, description=f"Setting up {tool_name}...")
                
                if not tool_dir.exists():
                    # Clone repository
                    clone_cmd = [
                        "git", "clone", "-q",
                        f"https://github.com/{tool_slug}.git",
                        str(tool_dir)
                    ]
                    
                    try:
                        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
                        if result.returncode == 0:
                            print_info(f"Cloned {tool_name}")
                        else:
                            print_warning(f"Failed to clone {tool_name}: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        print_warning(f"Timeout cloning {tool_name}")
                    except Exception as e:
                        print_warning(f"Error cloning {tool_name}: {str(e)}")
                else:
                    # Update existing repository
                    pull_cmd = ["git", "pull"]
                    
                    try:
                        result = subprocess.run(pull_cmd, cwd=tool_dir, capture_output=True, text=True, timeout=60)
                        if result.returncode == 0:
                            logger.debug(f"Updated {tool_name}")
                        else:
                            logger.warning(f"Failed to update {tool_name}: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Timeout updating {tool_name}")
                    except Exception as e:
                        logger.warning(f"Error updating {tool_name}: {str(e)}")
                
                progress.advance(task)
            
            progress.update(task, description="External tools setup completed")
        
        # Setup UV path if needed
        self._setup_uv_path()
    
    def _setup_uv_path(self):
        """Setup UV path if not in system PATH"""
        if not shutil.which("uvx"):
            uv_path = Path.home() / ".local" / "bin"
            if uv_path.exists():
                import os
                current_path = os.environ.get("PATH", "")
                if str(uv_path) not in current_path:
                    os.environ["PATH"] = f"{uv_path}:{current_path}"
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available in the system"""
        
        # Check if it's a system command
        if shutil.which(tool_name):
            return True
        
        # Check if it's in our tools directory
        tool_path = Path(self.config.tools_dir) / tool_name
        if tool_path.exists():
            return True
        
        # Check common tool locations
        common_locations = [
            Path(self.config.tools_dir) / 'bin' / tool_name,
            Path(self.config.tools_dir) / tool_name / tool_name,
            Path(self.config.utils_dir) / tool_name / tool_name,
        ]
        
        for location in common_locations:
            if location.exists():
                return True
        
        return False