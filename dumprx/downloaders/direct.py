"""
Direct download functionality
"""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional
import requests
from urllib.parse import urlparse, unquote

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole


class DirectDownloader:
    """Handles direct HTTP/HTTPS downloads"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        
    def download(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download file from direct URL"""
        try:
            self.console.step(f"Downloading from: {url}")
            
            # Get filename from URL or Content-Disposition header
            filename = self._get_filename(url)
            if not filename:
                self.console.error("Could not determine filename")
                return None
                
            output_path = output_dir / filename
            
            # Use requests with streaming for large files
            headers = {
                'User-Agent': self.config.download.user_agents['default']
            }
            
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size > 0:
                self.console.step(f"Downloading {filename} ({self._format_size(total_size)})...")
                
                with self.console.progress_bar(f"Downloading {filename}") as progress:
                    task = progress.add_task("Download", total=total_size)
                    
                    with open(output_path, 'wb') as f:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=self.config.download.chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, completed=downloaded)
            else:
                # Unknown size, download without progress bar
                self.console.step(f"Downloading {filename} (unknown size)...")
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=self.config.download.chunk_size):
                        if chunk:
                            f.write(chunk)
            
            self.console.success(f"Downloaded: {output_path}")
            return output_path
            
        except Exception as e:
            self.console.error(f"Direct download failed: {e}")
            return None
            
    def _get_filename(self, url: str) -> Optional[str]:
        """Extract filename from URL or headers"""
        try:
            # First try to get filename from Content-Disposition header
            headers = {
                'User-Agent': self.config.download.user_agents['default']
            }
            response = requests.head(url, headers=headers, allow_redirects=True)
            
            if 'content-disposition' in response.headers:
                import cgi
                _, params = cgi.parse_header(response.headers['content-disposition'])
                if 'filename' in params:
                    return params['filename'].strip('"')
                    
            # Fallback to URL path
            parsed = urlparse(url)
            filename = Path(unquote(parsed.path)).name
            
            if filename and not filename.startswith('.'):
                return filename
                
            # Last resort: generate a filename
            return f"firmware_{hash(url) % 10000}.bin"
            
        except Exception:
            return None
            
    def _format_size(self, size: int) -> str:
        """Format file size in human readable form"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"