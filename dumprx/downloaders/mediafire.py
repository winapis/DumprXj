"""
MediaFire downloader
"""

import re
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole
from dumprx.downloaders.direct import DirectDownloader


class MediaFireDownloader:
    """MediaFire downloader"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        self.direct_dl = DirectDownloader(config, console)
        
    def download(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download from MediaFire"""
        try:
            self.console.step("Processing MediaFire URL...")
            
            # Get the actual download URL
            download_url = self._get_download_url(url)
            if not download_url:
                self.console.error("Could not extract download URL from MediaFire")
                return None
                
            # Extract filename from download URL
            filename = self._extract_filename(download_url)
            self.console.step(f"Found file: {filename}")
            
            # Use direct downloader for the actual download
            return self.direct_dl.download(download_url, output_dir)
            
        except Exception as e:
            self.console.error(f"MediaFire download failed: {e}")
            return None
            
    def _get_download_url(self, url: str) -> Optional[str]:
        """Extract direct download URL from MediaFire page"""
        try:
            headers = {
                'User-Agent': self.config.download.user_agents['default']
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Look for download URL in the page content
            # MediaFire typically has the download URL in specific patterns
            patterns = [
                r'href="(https?://download\d+\.mediafire\.com/[^"]+)"',
                r'"(https?://download[^"]*\.mediafire\.com[^"]*)"',
                r'href="([^"]*://download[^"]*)"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    # Return the first valid-looking download URL
                    for match in matches:
                        if 'mediafire.com' in match and ('download' in match or 'file' in match):
                            return match
                            
            # Alternative method: look for aria-label download button
            aria_pattern = r'aria-label="Download file"[^>]*href="([^"]+)"'
            aria_matches = re.findall(aria_pattern, response.text)
            if aria_matches:
                return aria_matches[0]
                
            return None
            
        except Exception as e:
            self.console.error(f"Error extracting MediaFire download URL: {e}")
            return None
            
    def _extract_filename(self, download_url: str) -> str:
        """Extract filename from download URL"""
        try:
            # Decode URL and extract filename
            decoded_url = unquote(download_url)
            
            # Try to extract from URL path
            if '/' in decoded_url:
                filename = decoded_url.split('/')[-1]
                # Remove query parameters
                if '?' in filename:
                    filename = filename.split('?')[0]
                if filename and not filename.startswith('.'):
                    return filename
                    
            # Fallback: generate filename based on URL hash
            return f"mediafire_file_{hash(download_url) % 10000}.bin"
            
        except Exception:
            return f"mediafire_file_{hash(download_url) % 10000}.bin"