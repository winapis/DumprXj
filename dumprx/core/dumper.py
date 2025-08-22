"""
Core firmware dumper functionality
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import tempfile
import git

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole
from dumprx.downloaders.manager import DownloadManager
from dumprx.extractors.manager import ExtractionManager
from dumprx.utils.git_integration import GitIntegration
from dumprx.utils.telegram_bot import TelegramBot


class FirmwareDumper:
    """Main firmware dumper class"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        self.download_manager = DownloadManager(config, console)
        self.extraction_manager = ExtractionManager(config, console)
        self.git_integration = GitIntegration(config, console)
        self.telegram_bot = TelegramBot(config, console) if config.telegram.enabled else None
        
    def dump_firmware(self, source: str, force: bool = False, 
                     cleanup: bool = True) -> bool:
        """
        Main firmware dumping function
        
        Args:
            source: Path to firmware file or URL
            force: Force extraction even if output exists
            cleanup: Whether to cleanup temporary files
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.console.step("Starting firmware extraction process...")
            
            # Check if source is URL or local file
            if self._is_url(source):
                self.console.step("Downloading firmware...")
                source_path = self.download_manager.download(source)
                if not source_path:
                    self.console.error("Failed to download firmware")
                    return False
            else:
                source_path = Path(source)
                if not source_path.exists():
                    self.console.error(f"Source file does not exist: {source}")
                    return False
                    
            # Detect firmware type
            self.console.step("Detecting firmware type...")
            firmware_info = self.extraction_manager.detect_firmware_type(source_path)
            if not firmware_info:
                self.console.error("Unsupported firmware type")
                return False
                
            self.console.detected(f"Detected: {firmware_info['type']} firmware")
            
            # Extract firmware
            self.console.step("Extracting firmware...")
            extraction_result = self.extraction_manager.extract_firmware(
                source_path, firmware_info, force
            )
            
            if not extraction_result:
                self.console.error("Firmware extraction failed")
                return False
                
            # Get extracted data information
            extracted_info = extraction_result.get('info', {})
            
            # Upload to git if configured
            if self._should_upload_to_git(extracted_info):
                self.console.step("Uploading to git repository...")
                git_result = self.git_integration.upload_firmware(
                    extraction_result['output_dir'], extracted_info
                )
                if git_result:
                    self.console.success("Successfully uploaded to git repository")
                    
                    # Send Telegram notification
                    if self.telegram_bot:
                        self.console.step("Sending Telegram notification...")
                        self.telegram_bot.send_firmware_notification(
                            extracted_info, git_result
                        )
                else:
                    self.console.warning("Git upload failed")
                    
            # Cleanup if requested
            if cleanup:
                self.console.step("Cleaning up temporary files...")
                self._cleanup_temp_files()
                
            self.console.success("Firmware extraction completed successfully!")
            return True
            
        except Exception as e:
            self.console.error(f"Error during firmware extraction: {e}")
            return False
            
    def download_firmware(self, url: str) -> Optional[Path]:
        """
        Download firmware from URL
        
        Args:
            url: URL to download from
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            self.console.step("Downloading firmware...")
            return self.download_manager.download(url)
        except Exception as e:
            self.console.error(f"Error during download: {e}")
            return None
            
    def setup_dependencies(self, force: bool = False) -> bool:
        """
        Setup dependencies and external tools
        
        Args:
            force: Force reinstall of dependencies
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.console.step("Setting up dependencies...")
            
            # Ensure directories exist
            self.config.ensure_directories()
            
            # Clone/update external tools
            utils_dir = self.config.get_utils_dir()
            
            for repo in self.config.external_tools.repositories:
                tool_name = repo.split('/')[-1]
                tool_path = utils_dir / tool_name
                
                if tool_path.exists() and not force:
                    self.console.step(f"Updating {tool_name}...")
                    try:
                        repo_obj = git.Repo(tool_path)
                        repo_obj.remotes.origin.pull()
                        self.console.success(f"Updated {tool_name}")
                    except Exception as e:
                        self.console.warning(f"Could not update {tool_name}: {e}")
                else:
                    if tool_path.exists() and force:
                        shutil.rmtree(tool_path)
                        
                    self.console.step(f"Cloning {tool_name}...")
                    try:
                        git.Repo.clone_from(f"https://github.com/{repo}.git", tool_path)
                        self.console.success(f"Cloned {tool_name}")
                    except Exception as e:
                        self.console.error(f"Failed to clone {tool_name}: {e}")
                        return False
                        
            # Verify tools are available
            self.console.step("Verifying tools...")
            if not self._verify_tools():
                self.console.warning("Some tools may not be available")
                
            self.console.success("Dependencies setup completed!")
            return True
            
        except Exception as e:
            self.console.error(f"Error during setup: {e}")
            return False
            
    def _is_url(self, source: str) -> bool:
        """Check if source is a URL"""
        return source.startswith(('http://', 'https://'))
        
    def _should_upload_to_git(self, extracted_info: Dict[str, Any]) -> bool:
        """Check if we should upload to git based on configuration"""
        return (
            (self.config.git.github.token and self.config.git.github.organization) or
            (self.config.git.gitlab.token and self.config.git.gitlab.group)
        )
        
    def _cleanup_temp_files(self) -> None:
        """Cleanup temporary files"""
        temp_dir = self.config.get_temp_dir()
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
    def _verify_tools(self) -> bool:
        """Verify that required tools are available"""
        required_commands = ['7zz', 'python3', 'git']
        missing_tools = []
        
        for cmd in required_commands:
            if not shutil.which(cmd):
                missing_tools.append(cmd)
                
        if missing_tools:
            self.console.warning(f"Missing tools: {', '.join(missing_tools)}")
            return False
            
        return True