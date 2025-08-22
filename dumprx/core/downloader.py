import os
import re
import subprocess
import requests
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlparse, unquote
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

class DownloadManager:
    def __init__(self, config_manager):
        self.config = config_manager.get_download_config()
        self.user_agents = self.config['user_agents']
        self.chunk_size = self.config['chunk_size']
        self.timeout = self.config['timeout']
        self.retry_attempts = self.config['retry_attempts']
        self.retry_delay = self.config['retry_delay']
    
    def download(self, url: str, output_path: Path, url_type: str = 'direct') -> bool:
        if url_type == 'direct':
            return self._download_direct(url, output_path)
        elif url_type == 'mega':
            return self._download_mega(url, output_path)
        elif url_type == 'mediafire':
            return self._download_mediafire(url, output_path)
        elif url_type == 'drive':
            return self._download_gdrive(url, output_path)
        elif url_type == 'androidfilehost':
            return self._download_afh(url, output_path)
        else:
            return self._download_direct(url, output_path)
    
    def _download_direct(self, url: str, output_path: Path) -> bool:
        try:
            headers = {'User-Agent': self.user_agents['default']}
            
            with requests.get(url, headers=headers, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                filename = self._get_filename_from_response(response, url)
                
                if not output_path.name:
                    output_path = output_path / filename
                
                with Progress(
                    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%",
                    "•",
                    TextColumn("[bold green]{task.fields[downloaded]}"),
                    "•",
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task(
                        "Downloading", 
                        total=total_size,
                        filename=filename,
                        downloaded="0 MB"
                    )
                    
                    with open(output_path, 'wb') as f:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=self.chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(
                                    task, 
                                    advance=len(chunk),
                                    downloaded=f"{downloaded / (1024*1024):.1f} MB"
                                )
            
            return True
            
        except Exception as e:
            print(f"Direct download failed: {e}")
            return False
    
    def _download_mega(self, url: str, output_path: Path) -> bool:
        try:
            cmd = ['python3', 'utils/downloaders/mega-media-drive_dl.sh', url]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_path.parent)
            return result.returncode == 0
        except Exception:
            return False
    
    def _download_mediafire(self, url: str, output_path: Path) -> bool:
        try:
            direct_url = self._get_mediafire_direct_url(url)
            if direct_url:
                return self._download_direct(direct_url, output_path)
            return False
        except Exception:
            return False
    
    def _download_gdrive(self, url: str, output_path: Path) -> bool:
        try:
            file_id = self._extract_gdrive_file_id(url)
            if not file_id:
                return False
            
            direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            return self._download_direct(direct_url, output_path)
        except Exception:
            return False
    
    def _download_afh(self, url: str, output_path: Path) -> bool:
        try:
            cmd = ['python3', 'utils/downloaders/afh_dl.py', '-l', url]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_path.parent)
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_filename_from_response(self, response, url: str) -> str:
        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            filename_match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disposition)
            if filename_match:
                return unquote(filename_match.group(1))
        
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if filename:
            return unquote(filename)
        
        return 'firmware_download'
    
    def _get_mediafire_direct_url(self, url: str) -> Optional[str]:
        try:
            headers = {'User-Agent': self.user_agents['default']}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            direct_link_match = re.search(r'href="([^"]*)" class="input popsok"', response.text)
            if direct_link_match:
                return direct_link_match.group(1).replace('&amp;', '&')
            
            return None
        except Exception:
            return None
    
    def _extract_gdrive_file_id(self, url: str) -> Optional[str]:
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'/open\?id=([a-zA-Z0-9-_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None