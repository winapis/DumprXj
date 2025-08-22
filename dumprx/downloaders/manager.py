"""
Download manager for various firmware sources
"""

import re
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import requests
import json
import base64
import hashlib

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole
from dumprx.downloaders.mega import MegaDownloader
from dumprx.downloaders.mediafire import MediaFireDownloader
from dumprx.downloaders.gdrive import GDriveDownloader
from dumprx.downloaders.afh import AFHDownloader
from dumprx.downloaders.direct import DirectDownloader


class DownloadManager:
    """Manages downloads from various sources"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        
        # Initialize downloaders
        self.mega_dl = MegaDownloader(config, console)
        self.mediafire_dl = MediaFireDownloader(config, console)
        self.gdrive_dl = GDriveDownloader(config, console)
        self.afh_dl = AFHDownloader(config, console)
        self.direct_dl = DirectDownloader(config, console)
        
        # URL patterns for detection
        self.url_patterns = {
            'mega': [
                r'mega\.nz',
                r'mega\.co\.nz'
            ],
            'mediafire': [
                r'mediafire\.com',
                r'www\.mediafire\.com'
            ],
            'gdrive': [
                r'drive\.google\.com',
                r'docs\.google\.com'
            ],
            'afh': [
                r'androidfilehost\.com',
                r'www\.androidfilehost\.com'
            ],
            'onedrive': [
                r'1drv\.ms',
                r'onedrive\.live\.com'
            ]
        }
        
    def download(self, url: str) -> Optional[Path]:
        """
        Download firmware from URL
        
        Args:
            url: URL to download from
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Detect URL type
            url_type = self._detect_url_type(url)
            self.console.detected(f"Detected {url_type} URL")
            
            # Ensure input directory exists
            input_dir = self.config.get_input_dir()
            input_dir.mkdir(parents=True, exist_ok=True)
            
            # Download based on type
            if url_type == 'mega':
                return self.mega_dl.download(url, input_dir)
            elif url_type == 'mediafire':
                return self.mediafire_dl.download(url, input_dir)
            elif url_type == 'gdrive':
                return self.gdrive_dl.download(url, input_dir)
            elif url_type == 'afh':
                return self.afh_dl.download(url, input_dir)
            elif url_type == 'onedrive':
                return self._download_onedrive(url, input_dir)
            else:
                return self.direct_dl.download(url, input_dir)
                
        except Exception as e:
            self.console.error(f"Download failed: {e}")
            return None
            
    def _detect_url_type(self, url: str) -> str:
        """Detect the type of URL"""
        url_lower = url.lower()
        
        for url_type, patterns in self.url_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return url_type
                    
        return 'direct'
        
    def _download_onedrive(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download from OneDrive (basic implementation)"""
        try:
            self.console.step("Downloading from OneDrive...")
            
            # Try to convert OneDrive share URL to direct download
            if '1drv.ms' in url:
                # Expand shortened URL
                response = requests.head(url, allow_redirects=True)
                url = response.url
                
            # Extract direct download URL
            if 'onedrive.live.com' in url and 'redir' in url:
                # Convert to direct download
                download_url = url.replace('redir?', 'download?')
                return self.direct_dl.download(download_url, output_dir)
            else:
                self.console.warning("OneDrive URL format not supported for direct download")
                return None
                
        except Exception as e:
            self.console.error(f"OneDrive download failed: {e}")
            return None