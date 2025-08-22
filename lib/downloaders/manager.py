import asyncio
import aiohttp
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from lib.core.logger import logger
from lib.core.exceptions import DownloadError
from lib.core.config import config
from lib.utils.progress import create_progress_bar
from lib.utils.command import run_command
from .url_detector import URLDetector

class DownloadManager:
    def __init__(self):
        self.detector = URLDetector()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        headers = {
            'User-Agent': config.get('download.user_agents.default')
        }
        timeout = aiohttp.ClientTimeout(total=config.get('download.timeout', 300))
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def download(self, url: str, output_path: Path) -> Path:
        url_info = self.detector.validate_url(url)
        
        if not url_info['valid']:
            raise DownloadError(f"Unsupported URL: {url}")
        
        logger.processing(f"Starting download from {url_info['type']} source")
        
        if url_info['type'] == 'direct':
            return await self._download_direct(url, output_path)
        elif url_info['type'] == 'mega':
            return await self._download_mega(url, output_path)
        elif url_info['type'] == 'afh':
            return await self._download_afh(url, output_path)
        elif url_info['type'] == 'wetransfer':
            return await self._download_wetransfer(url, output_path)
        else:
            return await self._download_with_aria2c(url, output_path)
    
    async def _download_direct(self, url: str, output_path: Path) -> Path:
        chunk_size = config.get('download.chunk_size', 8192)
        
        async with self.session.get(url) as response:
            if response.status != 200:
                raise DownloadError(f"HTTP {response.status}: {response.reason}")
            
            total_size = int(response.headers.get('content-length', 0))
            progress = create_progress_bar(total_size, "Downloading")
            
            with open(output_path, 'wb') as f:
                downloaded = 0
                async for chunk in response.content.iter_chunked(chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress.set_progress(downloaded)
            
            progress.finish()
            logger.success(f"Downloaded to {output_path}")
            return output_path
    
    async def _download_with_aria2c(self, url: str, output_path: Path) -> Path:
        cmd = [
            'aria2c',
            '-x16', '-s8',
            '--console-log-level=warn',
            '--summary-interval=0',
            '--check-certificate=false',
            f'--out={output_path.name}',
            f'--dir={output_path.parent}',
            url
        ]
        
        try:
            result = await run_command(cmd)
            if result.returncode != 0:
                raise DownloadError(f"aria2c failed: {result.stderr}")
            return output_path
        except FileNotFoundError:
            return await self._download_with_wget(url, output_path)
    
    async def _download_with_wget(self, url: str, output_path: Path) -> Path:
        cmd = [
            'wget',
            '-q', '--show-progress',
            '--progress=bar:force',
            '--no-check-certificate',
            '-O', str(output_path),
            url
        ]
        
        result = await run_command(cmd)
        if result.returncode != 0:
            raise DownloadError(f"wget failed: {result.stderr}")
        return output_path
    
    async def _download_mega(self, url: str, output_path: Path) -> Path:
        script_path = Path(config.get('paths.utils_dir')) / 'downloaders' / 'mega-media-drive_dl.sh'
        result = await run_command(['bash', str(script_path), url], cwd=output_path.parent)
        
        if result.returncode != 0:
            raise DownloadError(f"Mega download failed: {result.stderr}")
        
        downloaded_files = list(output_path.parent.glob('*'))
        if downloaded_files:
            return downloaded_files[0]
        raise DownloadError("No files downloaded from Mega")
    
    async def _download_afh(self, url: str, output_path: Path) -> Path:
        script_path = Path(config.get('paths.utils_dir')) / 'downloaders' / 'afh_dl.py'
        result = await run_command(['python3', str(script_path), '-l', url], cwd=output_path.parent)
        
        if result.returncode != 0:
            raise DownloadError(f"AFH download failed: {result.stderr}")
        
        downloaded_files = list(output_path.parent.glob('*'))
        if downloaded_files:
            return downloaded_files[0]
        raise DownloadError("No files downloaded from AndroidFileHost")
    
    async def _download_wetransfer(self, url: str, output_path: Path) -> Path:
        transfer_bin = Path(config.get('paths.utils_dir')) / 'bin' / 'transfer'
        result = await run_command([str(transfer_bin), url], cwd=output_path.parent)
        
        if result.returncode != 0:
            raise DownloadError(f"WeTransfer download failed: {result.stderr}")
        
        downloaded_files = list(output_path.parent.glob('*'))
        if downloaded_files:
            return downloaded_files[0]
        raise DownloadError("No files downloaded from WeTransfer")