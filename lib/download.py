import asyncio
import aiohttp
import os
import re
import subprocess
import tempfile
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs
import json
from pathlib import Path

from .ui import UI, ProgressBar
from .logging import get_logger

logger = get_logger()


class DownloadError(Exception):
    pass


class BaseDownloader:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.user_agent = config.get('user_agents', {}).get('default', 
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        self.timeout = config.get('timeout', 300)
        self.chunk_size = config.get('chunk_size', 8192)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.retry_delay = config.get('retry_delay', 5)

    async def download(self, url: str, output_path: str) -> str:
        raise NotImplementedError

    def _get_filename_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        return filename if filename else 'firmware_file'


class DirectDownloader(BaseDownloader):
    async def download(self, url: str, output_path: str) -> str:
        filename = self._get_filename_from_url(url)
        filepath = os.path.join(output_path, filename)
        
        UI.print_download_start(url)
        
        try:
            return await self._download_with_aria2c(url, filepath)
        except Exception:
            logger.warning("aria2c failed, falling back to aiohttp")
            return await self._download_with_aiohttp(url, filepath)

    async def _download_with_aria2c(self, url: str, filepath: str) -> str:
        cmd = [
            'aria2c',
            '--user-agent', self.user_agent,
            '--max-connection-per-server', '16',
            '--split', '16',
            '--file-allocation', 'none',
            '--continue', 'true',
            '--timeout', str(self.timeout),
            '--out', os.path.basename(filepath),
            '--dir', os.path.dirname(filepath),
            url
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise DownloadError(f"aria2c failed: {stderr.decode()}")
        
        UI.print_success(f"Downloaded: {os.path.basename(filepath)}")
        return filepath

    async def _download_with_aiohttp(self, url: str, filepath: str) -> str:
        headers = {'User-Agent': self.user_agent}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise DownloadError(f"HTTP {response.status}: {response.reason}")
                
                total_size = int(response.headers.get('content-length', 0))
                progress = ProgressBar(total_size, f"Downloading {os.path.basename(filepath)}")
                
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    async for chunk in response.content.iter_chunked(self.chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress.set_progress(downloaded)
                
                progress.finish()
                UI.print_success(f"Downloaded: {os.path.basename(filepath)}")
                return filepath


class MegaDownloader(BaseDownloader):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mega_user_agent = config.get('user_agents', {}).get('mega', 'MEGAsync/4.8.8.0')

    async def download(self, url: str, output_path: str) -> str:
        UI.print_download_start(url)
        
        if not self._is_mega_url(url):
            raise DownloadError("Invalid Mega.nz URL")
        
        try:
            return await self._download_with_megatools(url, output_path)
        except Exception:
            logger.warning("megatools failed, trying fallback method")
            return await self._download_with_script(url, output_path)

    def _is_mega_url(self, url: str) -> bool:
        return 'mega.nz' in url or 'mega.co.nz' in url

    async def _download_with_megatools(self, url: str, output_path: str) -> str:
        cmd = ['megadl', '--path', output_path, url]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise DownloadError(f"megadl failed: {stderr.decode()}")
        
        downloaded_files = [f for f in os.listdir(output_path) 
                          if os.path.isfile(os.path.join(output_path, f))]
        
        if not downloaded_files:
            raise DownloadError("No file downloaded")
        
        filepath = os.path.join(output_path, downloaded_files[0])
        UI.print_success(f"Downloaded: {os.path.basename(filepath)}")
        return filepath

    async def _download_with_script(self, url: str, output_path: str) -> str:
        script_path = os.path.join('utils', 'downloaders', 'mega-media-drive_dl.sh')
        
        if not os.path.exists(script_path):
            raise DownloadError("Mega downloader script not found")
        
        cmd = ['bash', script_path, url, output_path]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise DownloadError(f"Mega script failed: {stderr.decode()}")
        
        downloaded_files = [f for f in os.listdir(output_path) 
                          if os.path.isfile(os.path.join(output_path, f))]
        
        if not downloaded_files:
            raise DownloadError("No file downloaded")
        
        filepath = os.path.join(output_path, downloaded_files[0])
        UI.print_success(f"Downloaded: {os.path.basename(filepath)}")
        return filepath


class MediaFireDownloader(BaseDownloader):
    async def download(self, url: str, output_path: str) -> str:
        UI.print_download_start(url)
        
        if not self._is_mediafire_url(url):
            raise DownloadError("Invalid MediaFire URL")
        
        direct_url = await self._get_direct_url(url)
        downloader = DirectDownloader(self.config)
        return await downloader.download(direct_url, output_path)

    def _is_mediafire_url(self, url: str) -> bool:
        return 'mediafire.com' in url

    async def _get_direct_url(self, url: str) -> str:
        headers = {'User-Agent': self.user_agent}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise DownloadError(f"Failed to access MediaFire page: {response.status}")
                
                html = await response.text()
                
                direct_link_pattern = r'href="(https://download\d+\.mediafire\.com/[^"]+)"'
                match = re.search(direct_link_pattern, html)
                
                if not match:
                    raise DownloadError("Could not find direct download link")
                
                return match.group(1)


class AndroidFileHostDownloader(BaseDownloader):
    async def download(self, url: str, output_path: str) -> str:
        UI.print_download_start(url)
        
        if not self._is_afh_url(url):
            raise DownloadError("Invalid AndroidFileHost URL")
        
        script_path = os.path.join('utils', 'downloaders', 'afh_dl.py')
        
        if not os.path.exists(script_path):
            raise DownloadError("AFH downloader script not found")
        
        old_cwd = os.getcwd()
        os.chdir(output_path)
        
        try:
            cmd = ['python3', os.path.join(old_cwd, script_path), url]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise DownloadError(f"AFH download failed: {stderr.decode()}")
            
            downloaded_files = [f for f in os.listdir('.') 
                              if os.path.isfile(f)]
            
            if not downloaded_files:
                raise DownloadError("No file downloaded")
            
            filepath = os.path.join(output_path, downloaded_files[0])
            UI.print_success(f"Downloaded: {os.path.basename(filepath)}")
            return filepath
        
        finally:
            os.chdir(old_cwd)

    def _is_afh_url(self, url: str) -> bool:
        return 'androidfilehost.com' in url


class GoogleDriveDownloader(BaseDownloader):
    async def download(self, url: str, output_path: str) -> str:
        UI.print_download_start(url)
        
        if not self._is_gdrive_url(url):
            raise DownloadError("Invalid Google Drive URL")
        
        file_id = self._extract_file_id(url)
        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        try:
            downloader = DirectDownloader(self.config)
            return await downloader.download(direct_url, output_path)
        except Exception:
            return await self._download_large_file(file_id, output_path)

    def _is_gdrive_url(self, url: str) -> bool:
        return 'drive.google.com' in url or 'docs.google.com' in url

    def _extract_file_id(self, url: str) -> str:
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'/open\?id=([a-zA-Z0-9-_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise DownloadError("Could not extract file ID from Google Drive URL")

    async def _download_large_file(self, file_id: str, output_path: str) -> str:
        session_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(session_url) as response:
                html = await response.text()
                
                confirm_pattern = r'name="confirm" value="([^"]+)"'
                match = re.search(confirm_pattern, html)
                
                if not match:
                    raise DownloadError("Could not get confirmation token")
                
                confirm_token = match.group(1)
                download_url = f"{session_url}&confirm={confirm_token}"
                
                downloader = DirectDownloader(self.config)
                return await downloader.download(download_url, output_path)


class DownloadManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('download', {})
        self.downloaders = {
            'direct': DirectDownloader(self.config),
            'mega': MegaDownloader(self.config),
            'mediafire': MediaFireDownloader(self.config),
            'afh': AndroidFileHostDownloader(self.config),
            'gdrive': GoogleDriveDownloader(self.config),
        }

    async def download(self, url: str, output_path: str) -> str:
        os.makedirs(output_path, exist_ok=True)
        
        downloader_type = self._detect_url_type(url)
        downloader = self.downloaders.get(downloader_type, self.downloaders['direct'])
        
        for attempt in range(self.config.get('retry_attempts', 3)):
            try:
                return await downloader.download(url, output_path)
            except Exception as e:
                if attempt < self.config.get('retry_attempts', 3) - 1:
                    UI.print_warning(f"Download attempt {attempt + 1} failed: {e}")
                    UI.print_info(f"Retrying in {self.config.get('retry_delay', 5)} seconds...")
                    await asyncio.sleep(self.config.get('retry_delay', 5))
                else:
                    raise DownloadError(f"All download attempts failed: {e}")

    def _detect_url_type(self, url: str) -> str:
        url_lower = url.lower()
        
        if 'mega.nz' in url_lower or 'mega.co.nz' in url_lower:
            return 'mega'
        elif 'mediafire.com' in url_lower:
            return 'mediafire'
        elif 'androidfilehost.com' in url_lower:
            return 'afh'
        elif 'drive.google.com' in url_lower or 'docs.google.com' in url_lower:
            return 'gdrive'
        else:
            return 'direct'

    def is_url(self, path: str) -> bool:
        return path.startswith(('http://', 'https://', 'ftp://'))