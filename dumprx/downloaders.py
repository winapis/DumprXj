#!/usr/bin/env python3

import os
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs

from dumprx.console import info, warning, error, step, success, create_progress
from dumprx.config import config


class BaseDownloader:
    
    def __init__(self, url: str, output_dir: str):
        self.url = url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_agent = config.get('download', 'user_agents', 'default')
        self.chunk_size = config.get('download', 'chunk_size', default=8192)
        self.timeout = config.get('download', 'timeout', default=300)
        self.retry_attempts = config.get('download', 'retry_attempts', default=3)
        self.retry_delay = config.get('download', 'retry_delay', default=5)
    
    def download(self) -> Optional[str]:
        raise NotImplementedError


class DirectDownloader(BaseDownloader):
    
    def download(self) -> Optional[str]:
        step(f"Downloading from direct URL: {self.url}")
        
        headers = {'User-Agent': self.user_agent}
        
        try:
            response = requests.head(self.url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            filename = self._get_filename_from_response(response)
            if not filename:
                filename = Path(urlparse(self.url).path).name or "firmware"
            
            file_path = self.output_dir / filename
            
            with create_progress() as progress:
                task = progress.add_task("Downloading...", total=None)
                
                with requests.get(self.url, headers=headers, stream=True, timeout=self.timeout) as r:
                    r.raise_for_status()
                    
                    total_size = int(r.headers.get('content-length', 0))
                    if total_size:
                        progress.update(task, total=total_size)
                    
                    with open(file_path, 'wb') as f:
                        downloaded = 0
                        for chunk in r.iter_content(chunk_size=self.chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size:
                                    progress.update(task, completed=downloaded)
            
            success(f"Downloaded: {filename}")
            return str(file_path)
            
        except Exception as e:
            error(f"Direct download failed: {str(e)}")
            return None
    
    def _get_filename_from_response(self, response):
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            parts = content_disposition.split('filename=')
            if len(parts) > 1:
                filename = parts[1].strip().strip('"')
                return filename
        return None


class MegaDownloader(BaseDownloader):
    
    def download(self) -> Optional[str]:
        step(f"Downloading from MEGA: {self.url}")
        
        try:
            cmd = ['python3', '-m', 'mega', 'download', self.url, str(self.output_dir)]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout * 4
            )
            
            if result.returncode == 0:
                downloaded_files = list(self.output_dir.glob('*'))
                if downloaded_files:
                    success(f"Downloaded from MEGA: {downloaded_files[0].name}")
                    return str(downloaded_files[0])
            
            error(f"MEGA download failed: {result.stderr}")
            return None
            
        except subprocess.TimeoutExpired:
            error("MEGA download timed out")
            return None
        except Exception as e:
            error(f"MEGA download error: {str(e)}")
            return None


class MediafireDownloader(BaseDownloader):
    
    def download(self) -> Optional[str]:
        step(f"Downloading from Mediafire: {self.url}")
        
        try:
            import re
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(self.url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            download_pattern = r'href="(https://download\d+\.mediafire\.com/[^"]+)"'
            matches = re.findall(download_pattern, response.text)
            
            if not matches:
                error("Could not find Mediafire download link")
                return None
            
            download_url = matches[0]
            
            direct_downloader = DirectDownloader(download_url, str(self.output_dir))
            return direct_downloader.download()
            
        except Exception as e:
            error(f"Mediafire download error: {str(e)}")
            return None


class GDriveDownloader(BaseDownloader):
    
    def download(self) -> Optional[str]:
        step(f"Downloading from Google Drive: {self.url}")
        
        try:
            file_id = self._extract_file_id()
            if not file_id:
                error("Could not extract Google Drive file ID")
                return None
            
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            session = requests.Session()
            headers = {'User-Agent': self.user_agent}
            
            response = session.get(download_url, headers=headers, stream=True)
            
            if 'download_warning' in response.text:
                for line in response.text.splitlines():
                    if 'confirm=' in line:
                        confirm_token = line.split('confirm=')[1].split('&')[0]
                        download_url = f"{download_url}&confirm={confirm_token}"
                        break
            
            direct_downloader = DirectDownloader(download_url, str(self.output_dir))
            return direct_downloader.download()
            
        except Exception as e:
            error(f"Google Drive download error: {str(e)}")
            return None
    
    def _extract_file_id(self):
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            import re
            match = re.search(pattern, self.url)
            if match:
                return match.group(1)
        
        return None


class OneDriveDownloader(BaseDownloader):
    
    def download(self) -> Optional[str]:
        step(f"Downloading from OneDrive: {self.url}")
        
        try:
            if '1drv.ms' in self.url:
                response = requests.get(self.url, allow_redirects=True, timeout=self.timeout)
                self.url = response.url
            
            download_url = self.url.replace('/view?', '/download?')
            
            direct_downloader = DirectDownloader(download_url, str(self.output_dir))
            return direct_downloader.download()
            
        except Exception as e:
            error(f"OneDrive download error: {str(e)}")
            return None


class AFHDownloader(BaseDownloader):
    
    def download(self) -> Optional[str]:
        step(f"Downloading from AndroidFileHost: {self.url}")
        
        try:
            from dumprx import UTILS_DIR
            afh_script = UTILS_DIR / "downloaders" / "afh_dl.py"
            
            if not afh_script.exists():
                error("AFH downloader script not found")
                return None
            
            cmd = ['python3', str(afh_script), '-l', self.url]
            
            result = subprocess.run(
                cmd,
                cwd=str(self.output_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout * 2
            )
            
            if result.returncode == 0:
                downloaded_files = list(self.output_dir.glob('*'))
                if downloaded_files:
                    success(f"Downloaded from AFH: {downloaded_files[0].name}")
                    return str(downloaded_files[0])
            
            error(f"AFH download failed: {result.stderr}")
            return None
            
        except Exception as e:
            error(f"AFH download error: {str(e)}")
            return None


def get_downloader(url: str, output_dir: str) -> BaseDownloader:
    url_lower = url.lower()
    
    if 'mega.nz' in url_lower or 'mega.co.nz' in url_lower:
        return MegaDownloader(url, output_dir)
    elif 'mediafire.com' in url_lower:
        return MediafireDownloader(url, output_dir)
    elif 'drive.google.com' in url_lower or 'docs.google.com' in url_lower:
        return GDriveDownloader(url, output_dir)
    elif 'onedrive.live.com' in url_lower or '1drv.ms' in url_lower:
        return OneDriveDownloader(url, output_dir)
    elif 'androidfilehost.com' in url_lower:
        return AFHDownloader(url, output_dir)
    else:
        return DirectDownloader(url, output_dir)


def download_firmware(url: str, output_dir: str) -> Optional[str]:
    downloader = get_downloader(url, output_dir)
    return downloader.download()