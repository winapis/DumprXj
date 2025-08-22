"""
AndroidFileHost downloader
"""

import re
import requests
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole
from dumprx.downloaders.direct import DirectDownloader


class AFHDownloader:
    """AndroidFileHost downloader based on existing afh_dl.py"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        self.direct_dl = DirectDownloader(config, console)
        
        self.mirror_url = "https://androidfilehost.com/libs/otf/mirrors.otf.php"
        self.url_matchers = [
            re.compile(r"fid=(?P<id>\d+)")
        ]
        
    def download(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download from AndroidFileHost"""
        try:
            self.console.step("Processing AndroidFileHost URL...")
            
            # Extract file ID from URL
            file_id = self._extract_file_id(url)
            if not file_id:
                self.console.error("Could not extract file ID from URL")
                return None
                
            self.console.step(f"Getting download servers for file ID: {file_id}")
            
            # Get available download servers
            servers = self._get_download_servers(file_id)
            if not servers:
                self.console.error("Could not retrieve download servers")
                return None
                
            # Use the first available server
            server = servers[0]
            self.console.step(f"Downloading from: {server['name']}")
            
            # Get file info and download
            file_info = self._get_file_info(server['url'])
            if not file_info:
                self.console.error("Could not get file information")
                return None
                
            filename = file_info['filename']
            size = file_info['size']
            
            self.console.step(f"File: {filename} | Size: {size}")
            
            # Use direct downloader for the actual download
            return self.direct_dl.download(server['url'], output_dir)
            
        except Exception as e:
            self.console.error(f"AndroidFileHost download failed: {e}")
            return None
            
    def _extract_file_id(self, url: str) -> Optional[str]:
        """Extract file ID from AndroidFileHost URL"""
        for pattern in self.url_matchers:
            match = pattern.search(url)
            if match:
                return match.group('id')
        return None
        
    def _get_download_servers(self, file_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get available download servers for file ID"""
        try:
            # Get cookies first
            cook_response = requests.get(f"https://androidfilehost.com/?fid={file_id}")
            cookies = cook_response.cookies
            
            # Get download mirrors
            post_data = {
                "submit": "submit",
                "action": "getdownloadmirrors",
                "fid": file_id
            }
            
            headers = {
                "User-Agent": self.config.download.user_agents['default'],
                "Referer": f"https://androidfilehost.com/?fid={file_id}",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            response = requests.post(
                self.mirror_url,
                data=post_data,
                headers=headers,
                cookies=cookies
            )
            
            if response.status_code != 200:
                return None
                
            try:
                mirrors_data = response.json()
            except json.JSONDecodeError:
                return None
                
            # Parse mirrors
            servers = []
            for mirror in mirrors_data:
                if isinstance(mirror, dict) and 'url' in mirror and 'name' in mirror:
                    servers.append({
                        'name': mirror['name'],
                        'url': mirror['url']
                    })
                    
            return servers if servers else None
            
        except Exception as e:
            self.console.error(f"Error getting download servers: {e}")
            return None
            
    def _get_file_info(self, url: str) -> Optional[Dict[str, str]]:
        """Get file information from download URL"""
        try:
            headers = {
                'User-Agent': self.config.download.user_agents['default']
            }
            
            response = requests.head(url, headers=headers)
            
            size = "Unknown"
            if 'content-length' in response.headers:
                size_bytes = int(response.headers['content-length'])
                size = self._format_size(size_bytes)
                
            filename = "unknown"
            if 'content-disposition' in response.headers:
                import cgi
                _, params = cgi.parse_header(response.headers['content-disposition'])
                if 'filename' in params:
                    filename = params['filename'].strip('"')
                    
            return {
                'filename': filename,
                'size': size
            }
            
        except Exception:
            return None
            
    def _format_size(self, size: int) -> str:
        """Format file size in human readable form"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"