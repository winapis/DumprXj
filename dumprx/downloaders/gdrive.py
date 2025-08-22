"""
Google Drive downloader
"""

import re
import requests
from pathlib import Path
from typing import Optional

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole
from dumprx.downloaders.direct import DirectDownloader


class GDriveDownloader:
    """Google Drive downloader"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        self.direct_dl = DirectDownloader(config, console)
        
    def download(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download from Google Drive"""
        try:
            self.console.step("Processing Google Drive URL...")
            
            # Extract file ID from URL
            file_id = self._extract_file_id(url)
            if not file_id:
                self.console.error("Could not extract file ID from Google Drive URL")
                return None
                
            self.console.step(f"File ID: {file_id}")
            
            # Get download URL
            download_url = self._get_download_url(file_id)
            if not download_url:
                self.console.error("Could not generate download URL")
                return None
                
            # Use direct downloader for the actual download
            return self.direct_dl.download(download_url, output_dir)
            
        except Exception as e:
            self.console.error(f"Google Drive download failed: {e}")
            return None
            
    def _extract_file_id(self, url: str) -> Optional[str]:
        """Extract file ID from Google Drive URL"""
        try:
            # Pattern for extracting Google Drive file ID
            patterns = [
                r'/file/d/([a-zA-Z0-9_-]{33,})',
                r'id=([a-zA-Z0-9_-]{33,})',
                r'/d/([a-zA-Z0-9_-]{33,})',
                r'([a-zA-Z0-9_-]{33,})'  # Fallback: any 33+ char string
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    file_id = match.group(1)
                    # Validate file ID length (Google Drive IDs are typically 33+ chars)
                    if len(file_id) >= 33:
                        return file_id
                        
            return None
            
        except Exception:
            return None
            
    def _get_download_url(self, file_id: str) -> Optional[str]:
        """Get direct download URL for Google Drive file"""
        try:
            # First, try to check if we need a confirmation token
            check_url = f"https://docs.google.com/uc?export=download&id={file_id}"
            
            headers = {
                'User-Agent': self.config.download.user_agents['default']
            }
            
            response = requests.get(check_url, headers=headers, stream=True)
            
            # Look for confirmation token in the response
            confirm_token = None
            if 'download_warning' in response.text or 'virus' in response.text.lower():
                # Extract confirmation token
                patterns = [
                    r'confirm=([a-zA-Z0-9_-]+)',
                    r'name="confirm"[^>]*value="([^"]+)"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        confirm_token = match.group(1)
                        break
                        
            if confirm_token:
                # Use confirmation token
                download_url = f"https://docs.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
            else:
                # Direct download URL
                download_url = f"https://docs.google.com/uc?export=download&id={file_id}"
                
            return download_url
            
        except Exception as e:
            self.console.error(f"Error generating Google Drive download URL: {e}")
            return None