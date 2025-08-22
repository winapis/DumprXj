"""
Enhanced downloader module with support for multiple file hosting services.
"""

import asyncio
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse, unquote

try:
    import aiohttp
    import aiofiles
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

from ..core.config import Config
from ..core.logger import get_logger


class Downloader:
    """
    Enhanced downloader with support for multiple file hosting services.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
        
        # Service handlers
        self.handlers = {
            'mega': self._download_mega,
            'mediafire': self._download_mediafire,
            'google_drive': self._download_gdrive,
            'onedrive': self._download_onedrive,
            'androidfilehost': self._download_afh,
            'wetransfer': self._download_wetransfer,
            'direct': self._download_direct,
        }
    
    async def download(
        self, 
        url: str, 
        output_dir: Path,
        filename: Optional[str] = None
    ) -> Path:
        """
        Download file from URL to output directory.
        
        Args:
            url: URL to download from
            output_dir: Directory to save the file
            filename: Optional custom filename
            
        Returns:
            Path to downloaded file
        """
        if not ASYNC_AVAILABLE:
            self.logger.warning("Async libraries not available, using fallback methods")
            return self._download_sync(url, output_dir, filename)
            
        self.logger.info(f"🔗 Downloading from: {url}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect service type
        service = self._detect_service(url)
        self.logger.debug(f"Detected service: {service}")
        
        # Get appropriate handler
        handler = self.handlers.get(service, self._download_direct)
        
        # Download the file
        downloaded_path = await handler(url, output_dir, filename)
        
        # Clean filename if needed
        if downloaded_path.exists():
            cleaned_path = self._clean_filename(downloaded_path)
            if cleaned_path != downloaded_path:
                downloaded_path.rename(cleaned_path)
                downloaded_path = cleaned_path
        
        self.logger.success(f"✅ Downloaded: {downloaded_path.name}")
        return downloaded_path
    
    def _download_sync(self, url: str, output_dir: Path, filename: Optional[str] = None) -> Path:
        """Synchronous fallback download method."""
        import urllib.request
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            filename = Path(urlparse(url).path).name or "downloaded_file"
        
        output_path = output_dir / filename
        
        self.logger.info(f"📥 Downloading (sync): {filename}")
        urllib.request.urlretrieve(url, str(output_path))
        
        return output_path
    
    def _detect_service(self, url: str) -> str:
        """Detect the file hosting service from URL."""
        url_lower = url.lower()
        
        if 'mega.nz' in url_lower or 'mega.co.nz' in url_lower:
            return 'mega'
        elif 'mediafire.com' in url_lower:
            return 'mediafire'
        elif 'drive.google.com' in url_lower or 'docs.google.com' in url_lower:
            return 'google_drive'
        elif '1drv.ms' in url_lower or 'onedrive.live.com' in url_lower:
            return 'onedrive'
        elif 'androidfilehost.com' in url_lower or 'afh.link' in url_lower:
            return 'androidfilehost'
        elif 'we.tl' in url_lower or 'wetransfer.com' in url_lower:
            return 'wetransfer'
        else:
            return 'direct'
    
    async def _download_mega(
        self, 
        url: str, 
        output_dir: Path, 
        filename: Optional[str] = None
    ) -> Path:
        """Download from Mega.nz using megatools or direct method."""
        self.logger.info("📁 Downloading from Mega.nz")
        
        # Try using the existing mega-media-drive_dl.sh script
        script_path = self.config.utils_dir / "downloaders" / "mega-media-drive_dl.sh"
        
        if script_path.exists():
            try:
                result = subprocess.run(
                    [str(script_path), url],
                    cwd=str(output_dir),
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
                
                if result.returncode == 0:
                    # Find the downloaded file
                    files = list(output_dir.glob('*'))
                    if files:
                        return max(files, key=lambda p: p.stat().st_mtime)
                
            except subprocess.TimeoutExpired:
                self.logger.error("Download timeout from Mega")
            except Exception as e:
                self.logger.warning(f"Script download failed: {e}")
        
        # Fallback to direct download if script fails
        return await self._download_direct(url, output_dir, filename)
    
    async def _download_mediafire(
        self, 
        url: str, 
        output_dir: Path, 
        filename: Optional[str] = None
    ) -> Path:
        """Download from MediaFire."""
        self.logger.info("📁 Downloading from MediaFire")
        
        if not ASYNC_AVAILABLE:
            return self._download_sync(url, output_dir, filename)
        
        async with aiohttp.ClientSession() as session:
            # Get the page to find direct download link
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to access MediaFire page: {response.status}")
                
                content = await response.text()
                
                # Extract direct download link
                download_link = self._extract_mediafire_link(content)
                if not download_link:
                    raise ValueError("Could not find MediaFire download link")
                
                # Extract filename if not provided
                if not filename:
                    filename = self._extract_mediafire_filename(content)
                
                return await self._download_direct(download_link, output_dir, filename)
    
    def _extract_mediafire_link(self, page_content: str) -> Optional[str]:
        """Extract direct download link from MediaFire page."""
        patterns = [
            r'href="(https://download\d+\.mediafire\.com/[^"]+)"',
            r'"(https://download\d+\.mediafire\.com/[^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_mediafire_filename(self, page_content: str) -> Optional[str]:
        """Extract filename from MediaFire page."""
        patterns = [
            r'<div class="filename">([^<]+)</div>',
            r'aria-label="Download file ([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                return match.group(1).strip()
        
        return None
    
    async def _download_gdrive(
        self, 
        url: str, 
        output_dir: Path, 
        filename: Optional[str] = None
    ) -> Path:
        """Download from Google Drive."""
        self.logger.info("📁 Downloading from Google Drive")
        
        # Extract file ID
        file_id = self._extract_gdrive_id(url)
        if not file_id:
            raise ValueError("Could not extract Google Drive file ID")
        
        # Construct direct download URL
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    # Direct download
                    if not filename:
                        filename = self._get_filename_from_response(response)
                    
                    return await self._save_response_to_file(response, output_dir, filename)
                
                elif response.status == 302 or 'drive.google.com/uc' in str(response.url):
                    # Handle large file confirmation
                    content = await response.text()
                    confirm_url = self._extract_gdrive_confirm_url(content, file_id)
                    
                    if confirm_url:
                        async with session.get(confirm_url) as confirm_response:
                            if not filename:
                                filename = self._get_filename_from_response(confirm_response)
                            
                            return await self._save_response_to_file(
                                confirm_response, output_dir, filename
                            )
                
                raise ValueError(f"Failed to download from Google Drive: {response.status}")
    
    def _extract_gdrive_id(self, url: str) -> Optional[str]:
        """Extract file ID from Google Drive URL."""
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_gdrive_confirm_url(self, page_content: str, file_id: str) -> Optional[str]:
        """Extract confirmation URL for large Google Drive files."""
        patterns = [
            r'href="(/uc\?export=download&amp;confirm=[^&]+&amp;id=' + file_id + ')"',
            r'"(/uc\?export=download&confirm=[^&]+&id=' + file_id + ')"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                return "https://drive.google.com" + match.group(1).replace('&amp;', '&')
        
        return None
    
    async def _download_onedrive(
        self, 
        url: str, 
        output_dir: Path, 
        filename: Optional[str] = None
    ) -> Path:
        """Download from OneDrive."""
        self.logger.info("📁 Downloading from OneDrive")
        
        # Convert 1drv.ms to onedrive.live.com if needed
        if '1drv.ms' in url:
            url = url.replace('1drv.ms', 'onedrive.live.com')
        
        # Add download parameter
        if '?' in url:
            download_url = url + "&download=1"
        else:
            download_url = url + "?download=1"
        
        return await self._download_direct(download_url, output_dir, filename)
    
    async def _download_afh(
        self, 
        url: str, 
        output_dir: Path, 
        filename: Optional[str] = None
    ) -> Path:
        """Download from AndroidFileHost."""
        self.logger.info("📁 Downloading from AndroidFileHost")
        
        # Try using the existing afh_dl.py script
        script_path = self.config.utils_dir / "downloaders" / "afh_dl.py"
        
        if script_path.exists():
            try:
                result = subprocess.run(
                    ["python3", str(script_path), "-l", url],
                    cwd=str(output_dir),
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes timeout
                )
                
                if result.returncode == 0:
                    # Find the downloaded file
                    files = list(output_dir.glob('*'))
                    if files:
                        return max(files, key=lambda p: p.stat().st_mtime)
                
            except subprocess.TimeoutExpired:
                self.logger.error("Download timeout from AndroidFileHost")
            except Exception as e:
                self.logger.warning(f"AFH script download failed: {e}")
        
        # Fallback to parsing AFH page
        return await self._parse_afh_direct_link(url, output_dir, filename)
    
    async def _parse_afh_direct_link(
        self, 
        url: str, 
        output_dir: Path, 
        filename: Optional[str] = None
    ) -> Path:
        """Parse AndroidFileHost page to get direct download link."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to access AFH page: {response.status}")
                
                content = await response.text()
                
                # Extract direct download link
                download_link = self._extract_afh_link(content)
                if not download_link:
                    raise ValueError("Could not find AFH download link")
                
                return await self._download_direct(download_link, output_dir, filename)
    
    def _extract_afh_link(self, page_content: str) -> Optional[str]:
        """Extract direct download link from AFH page."""
        patterns = [
            r'href="(https://download\.androidfilehost\.com/[^"]+)"',
            r'"(https://download\.androidfilehost\.com/[^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                return match.group(1)
        
        return None
    
    async def _download_wetransfer(
        self, 
        url: str, 
        output_dir: Path, 
        filename: Optional[str] = None
    ) -> Path:
        """Download from WeTransfer."""
        self.logger.info("📁 Downloading from WeTransfer")
        
        # Try using the existing transfer utility
        transfer_path = self.config.utils_dir / "bin" / "transfer"
        
        if transfer_path.exists():
            try:
                result = subprocess.run(
                    [str(transfer_path), url],
                    cwd=str(output_dir),
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes timeout
                )
                
                if result.returncode == 0:
                    # Find the downloaded file
                    files = list(output_dir.glob('*'))
                    if files:
                        return max(files, key=lambda p: p.stat().st_mtime)
                
            except subprocess.TimeoutExpired:
                self.logger.error("Download timeout from WeTransfer")
            except Exception as e:
                self.logger.warning(f"WeTransfer download failed: {e}")
        
        raise ValueError("WeTransfer download not supported without transfer utility")
    
    async def _download_direct(
        self, 
        url: str, 
        output_dir: Path, 
        filename: Optional[str] = None
    ) -> Path:
        """Download file directly from URL."""
        self.logger.info("📁 Direct download")
        
        # Try aria2c first (if available)
        if await self._try_aria2c(url, output_dir, filename):
            files = list(output_dir.glob('*'))
            if files:
                return max(files, key=lambda p: p.stat().st_mtime)
        
        # Fallback to aiohttp
        if ASYNC_AVAILABLE:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    
                    if not filename:
                        filename = self._get_filename_from_response(response)
                    
                    return await self._save_response_to_file(response, output_dir, filename)
        else:
            # Use sync method as fallback
            return self._download_sync(url, output_dir, filename)
    
    async def _try_aria2c(
        self, 
        url: str, 
        output_dir: Path, 
        filename: Optional[str] = None
    ) -> bool:
        """Try downloading with aria2c."""
        try:
            cmd = [
                "aria2c",
                "-x16", "-s8",
                "--console-log-level=warn",
                "--summary-interval=0",
                "--check-certificate=false",
                "--dir", str(output_dir)
            ]
            
            if filename:
                cmd.extend(["--out", filename])
            
            cmd.append(url)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=3600)
            
            return process.returncode == 0
            
        except (FileNotFoundError, asyncio.TimeoutError):
            return False
    
    def _get_filename_from_response(self, response) -> str:
        """Extract filename from HTTP response headers."""
        # Try Content-Disposition header
        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition:
            filename_match = re.search(r'filename[*]?=(?:["\']?)([^"\';\r\n]+)', content_disposition)
            if filename_match:
                return unquote(filename_match.group(1))
        
        # Try URL path
        url_path = urlparse(str(response.url)).path
        if url_path:
            filename = Path(url_path).name
            if filename and '.' in filename:
                return unquote(filename)
        
        # Default filename
        return "downloaded_firmware"
    
    async def _save_response_to_file(
        self, 
        response, 
        output_dir: Path, 
        filename: str
    ) -> Path:
        """Save HTTP response content to file."""
        if not ASYNC_AVAILABLE:
            raise ValueError("Async libraries required for this operation")
            
        output_path = output_dir / filename
        
        # Show progress if content length is available
        content_length = response.headers.get('Content-Length')
        if content_length:
            total_size = int(content_length)
            self.logger.info(f"📦 Downloading {filename} ({total_size / 1024 / 1024:.1f} MB)")
        else:
            self.logger.info(f"📦 Downloading {filename}")
        
        async with aiofiles.open(output_path, 'wb') as f:
            async for chunk in response.content.iter_chunked(8192):
                await f.write(chunk)
        
        return output_path
    
    def _clean_filename(self, file_path: Path) -> Path:
        """Clean up downloaded filename."""
        # Remove problematic characters
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', file_path.name)
        
        # Remove extra spaces
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Ensure it's not empty
        if not clean_name or clean_name == '_':
            clean_name = "firmware_file"
        
        clean_path = file_path.parent / clean_name
        return clean_path if clean_path != file_path else file_path