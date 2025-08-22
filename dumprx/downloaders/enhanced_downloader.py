"""
Enhanced Download Services with intelligent URL detection
Supports 8 services with resume capability and cloud storage integration
"""

import os
import re
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse, parse_qs
import logging
from dataclasses import dataclass
from enum import Enum
import time
import json

logger = logging.getLogger(__name__)

class DownloadService(Enum):
    DIRECT = "direct"
    MEGA = "mega"
    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"
    DROPBOX = "dropbox"
    MEDIAFIRE = "mediafire"
    ANDROIDFILEHOST = "androidfilehost"
    GITHUB_RELEASE = "github_release"
    GITLAB_RELEASE = "gitlab_release"

@dataclass
class DownloadInfo:
    """Information about download"""
    service: DownloadService
    url: str
    filename: str = ""
    filesize: int = 0
    resume_supported: bool = False
    auth_required: bool = False
    download_url: str = ""

class EnhancedDownloader:
    """Enhanced downloader with support for multiple services"""
    
    # URL patterns for service detection
    URL_PATTERNS = {
        DownloadService.MEGA: [
            r'mega\.nz',
            r'mega\.co\.nz'
        ],
        DownloadService.GOOGLE_DRIVE: [
            r'drive\.google\.com',
            r'docs\.google\.com'
        ],
        DownloadService.ONEDRIVE: [
            r'onedrive\.live\.com',
            r'1drv\.ms',
            r'sharepoint\.com'
        ],
        DownloadService.DROPBOX: [
            r'dropbox\.com',
            r'db\.tt'
        ],
        DownloadService.MEDIAFIRE: [
            r'mediafire\.com',
            r'mfi\.re'
        ],
        DownloadService.ANDROIDFILEHOST: [
            r'androidfilehost\.com',
            r'afh\.io'
        ],
        DownloadService.GITHUB_RELEASE: [
            r'github\.com/.+/releases',
            r'github\.com/.+/download'
        ],
        DownloadService.GITLAB_RELEASE: [
            r'gitlab\.com/.+/releases',
            r'gitlab\.com/.+/-/releases'
        ]
    }
    
    def __init__(self, config, download_dir: Optional[Path] = None):
        self.config = config
        self.download_dir = download_dir or Path(config.work_dir) / 'downloads'
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure session with retry and resume support
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def detect_service(self, url: str) -> DownloadService:
        """Detect download service from URL"""
        
        url_lower = url.lower()
        
        for service, patterns in self.URL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return service
        
        return DownloadService.DIRECT
    
    def get_download_info(self, url: str) -> DownloadInfo:
        """Get download information for URL"""
        
        service = self.detect_service(url)
        
        info = DownloadInfo(
            service=service,
            url=url,
            resume_supported=True  # Most services support resume
        )
        
        try:
            if service == DownloadService.DIRECT:
                info = self._get_direct_info(url, info)
            elif service == DownloadService.MEGA:
                info = self._get_mega_info(url, info)
            elif service == DownloadService.GOOGLE_DRIVE:
                info = self._get_gdrive_info(url, info)
            elif service == DownloadService.ONEDRIVE:
                info = self._get_onedrive_info(url, info)
            elif service == DownloadService.DROPBOX:
                info = self._get_dropbox_info(url, info)
            elif service == DownloadService.MEDIAFIRE:
                info = self._get_mediafire_info(url, info)
            elif service == DownloadService.ANDROIDFILEHOST:
                info = self._get_afh_info(url, info)
            elif service == DownloadService.GITHUB_RELEASE:
                info = self._get_github_info(url, info)
            elif service == DownloadService.GITLAB_RELEASE:
                info = self._get_gitlab_info(url, info)
        
        except Exception as e:
            logger.error(f"Error getting download info for {url}: {e}")
        
        return info
    
    def download(self, url: str, filename: Optional[str] = None, progress_callback=None) -> Optional[Path]:
        """Download file from URL with progress tracking"""
        
        info = self.get_download_info(url)
        
        if not info.download_url:
            logger.error(f"Could not get download URL for {url}")
            return None
        
        # Determine output filename
        if not filename:
            filename = info.filename or self._extract_filename_from_url(info.download_url)
        
        output_path = self.download_dir / filename
        
        # Check if file already exists and supports resume
        resume_pos = 0
        if output_path.exists() and info.resume_supported:
            resume_pos = output_path.stat().st_size
            
            # Check if file is complete
            if info.filesize > 0 and resume_pos >= info.filesize:
                logger.info(f"File already downloaded: {output_path}")
                return output_path
        
        try:
            logger.info(f"Downloading {filename} from {info.service.value}")
            
            if info.service == DownloadService.MEGA:
                return self._download_mega(info, output_path, progress_callback)
            elif info.service == DownloadService.ANDROIDFILEHOST:
                return self._download_afh(info, output_path, progress_callback)
            else:
                return self._download_http(info, output_path, resume_pos, progress_callback)
        
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def _get_direct_info(self, url: str, info: DownloadInfo) -> DownloadInfo:
        """Get info for direct HTTP/HTTPS downloads"""
        
        try:
            response = self.session.head(url, allow_redirects=True, timeout=30)
            
            info.download_url = response.url
            info.filesize = int(response.headers.get('content-length', 0))
            info.resume_supported = 'bytes' in response.headers.get('accept-ranges', '')
            
            # Extract filename from headers or URL
            content_disp = response.headers.get('content-disposition', '')
            filename_match = re.search(r'filename[*]?=([^;]+)', content_disp)
            
            if filename_match:
                info.filename = filename_match.group(1).strip('"\'')
            else:
                info.filename = self._extract_filename_from_url(url)
        
        except Exception as e:
            logger.debug(f"Error getting direct download info: {e}")
            info.download_url = url
        
        return info
    
    def _get_mega_info(self, url: str, info: DownloadInfo) -> DownloadInfo:
        """Get info for Mega.nz downloads"""
        
        try:
            # Extract file ID from Mega URL
            if '#!' in url:
                file_id = url.split('#!')[1].split('!')[0]
                info.download_url = url  # Mega URLs don't change
                
                # Try to get file info using mega-cmd or megadl
                try:
                    result = subprocess.run(
                        ['megadl', '--print-names', '--no-progress', url],
                        capture_output=True, text=True, timeout=30
                    )
                    
                    if result.returncode == 0:
                        # Parse filename from output
                        for line in result.stdout.split('\n'):
                            if line.strip() and not line.startswith('Downloading'):
                                info.filename = line.strip()
                                break
                
                except subprocess.TimeoutExpired:
                    pass
                except FileNotFoundError:
                    logger.debug("megadl not found, using fallback")
        
        except Exception as e:
            logger.debug(f"Error getting Mega info: {e}")
        
        return info
    
    def _get_gdrive_info(self, url: str, info: DownloadInfo) -> DownloadInfo:
        """Get info for Google Drive downloads"""
        
        try:
            # Extract file ID from Google Drive URL
            file_id = None
            
            # Pattern 1: https://drive.google.com/file/d/FILE_ID/view
            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
            if match:
                file_id = match.group(1)
            
            # Pattern 2: https://drive.google.com/open?id=FILE_ID
            if not file_id:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                file_id = query_params.get('id', [None])[0]
            
            if file_id:
                # Use direct download URL
                info.download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                
                # Try to get file info
                try:
                    response = self.session.get(
                        f"https://drive.google.com/file/d/{file_id}/view",
                        timeout=30
                    )
                    
                    # Extract filename from page
                    filename_match = re.search(r'"title":"([^"]+)"', response.text)
                    if filename_match:
                        info.filename = filename_match.group(1)
                
                except Exception:
                    pass
        
        except Exception as e:
            logger.debug(f"Error getting Google Drive info: {e}")
        
        return info
    
    def _get_onedrive_info(self, url: str, info: DownloadInfo) -> DownloadInfo:
        """Get info for OneDrive downloads"""
        
        try:
            # Convert OneDrive share URL to direct download
            if 'onedrive.live.com' in url or '1drv.ms' in url:
                # Extract share token and convert to direct download
                if '1drv.ms' in url:
                    # Resolve short URL first
                    response = self.session.head(url, allow_redirects=True, timeout=30)
                    url = response.url
                
                # Convert to direct download URL
                if 'redir=1' not in url:
                    info.download_url = url + '&download=1'
                else:
                    info.download_url = url.replace('redir=1', 'download=1')
                
                # Try to get filename from URL or headers
                response = self.session.head(info.download_url, timeout=30)
                content_disp = response.headers.get('content-disposition', '')
                
                filename_match = re.search(r'filename[*]?=([^;]+)', content_disp)
                if filename_match:
                    info.filename = filename_match.group(1).strip('"\'')
        
        except Exception as e:
            logger.debug(f"Error getting OneDrive info: {e}")
        
        return info
    
    def _get_dropbox_info(self, url: str, info: DownloadInfo) -> DownloadInfo:
        """Get info for Dropbox downloads"""
        
        try:
            # Convert Dropbox share URL to direct download
            if 'dropbox.com' in url:
                if '?dl=0' in url:
                    info.download_url = url.replace('?dl=0', '?dl=1')
                elif '?dl=1' not in url:
                    info.download_url = url + ('&dl=1' if '?' in url else '?dl=1')
                else:
                    info.download_url = url
                
                # Extract filename from URL
                path_parts = urlparse(url).path.split('/')
                if path_parts:
                    info.filename = path_parts[-1]
        
        except Exception as e:
            logger.debug(f"Error getting Dropbox info: {e}")
        
        return info
    
    def _get_mediafire_info(self, url: str, info: DownloadInfo) -> DownloadInfo:
        """Get info for MediaFire downloads"""
        
        try:
            # Get MediaFire page to extract direct download link
            response = self.session.get(url, timeout=30)
            
            # Extract direct download URL
            download_match = re.search(r'href="(https?://download\d+\.mediafire\.com[^"]+)"', response.text)
            if download_match:
                info.download_url = download_match.group(1)
            
            # Extract filename
            filename_match = re.search(r'<div class="filename">([^<]+)</div>', response.text)
            if filename_match:
                info.filename = filename_match.group(1).strip()
            
            # Extract file size
            size_match = re.search(r'<div class="filesize">([^<]+)</div>', response.text)
            if size_match:
                size_str = size_match.group(1).strip()
                info.filesize = self._parse_file_size(size_str)
        
        except Exception as e:
            logger.debug(f"Error getting MediaFire info: {e}")
        
        return info
    
    def _get_afh_info(self, url: str, info: DownloadInfo) -> DownloadInfo:
        """Get info for AndroidFileHost downloads"""
        
        try:
            # Extract file ID from AFH URL
            file_id_match = re.search(r'androidfilehost\.com/\?fid=(\d+)', url)
            if file_id_match:
                file_id = file_id_match.group(1)
                
                # Use AFH API to get download info
                api_url = f"https://androidfilehost.com/libs/otf/mirrors.otf.php?fid={file_id}"
                response = self.session.get(api_url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('MIRRORS'):
                        mirror = data['MIRRORS'][0]  # Use first mirror
                        info.download_url = mirror['url']
                        info.filename = mirror.get('name', '')
        
        except Exception as e:
            logger.debug(f"Error getting AFH info: {e}")
        
        return info
    
    def _get_github_info(self, url: str, info: DownloadInfo) -> DownloadInfo:
        """Get info for GitHub release downloads"""
        
        try:
            # GitHub release URLs are usually direct
            info.download_url = url
            
            # Extract filename from URL
            path_parts = urlparse(url).path.split('/')
            if path_parts:
                info.filename = path_parts[-1]
            
            # Try to get file size from headers
            response = self.session.head(url, timeout=30)
            info.filesize = int(response.headers.get('content-length', 0))
        
        except Exception as e:
            logger.debug(f"Error getting GitHub info: {e}")
        
        return info
    
    def _get_gitlab_info(self, url: str, info: DownloadInfo) -> DownloadInfo:
        """Get info for GitLab release downloads"""
        
        try:
            # GitLab release URLs are usually direct
            info.download_url = url
            
            # Extract filename from URL
            path_parts = urlparse(url).path.split('/')
            if path_parts:
                info.filename = path_parts[-1]
            
            # Try to get file size from headers
            response = self.session.head(url, timeout=30)
            info.filesize = int(response.headers.get('content-length', 0))
        
        except Exception as e:
            logger.debug(f"Error getting GitLab info: {e}")
        
        return info
    
    def _download_http(self, info: DownloadInfo, output_path: Path, resume_pos: int = 0, progress_callback=None) -> Path:
        """Download via HTTP with resume support"""
        
        headers = {}
        if resume_pos > 0:
            headers['Range'] = f'bytes={resume_pos}-'
        
        response = self.session.get(
            info.download_url,
            headers=headers,
            stream=True,
            timeout=30
        )
        
        response.raise_for_status()
        
        # Open file in append mode if resuming
        mode = 'ab' if resume_pos > 0 else 'wb'
        
        total_size = info.filesize or int(response.headers.get('content-length', 0))
        downloaded = resume_pos
        
        with open(output_path, mode) as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(progress, downloaded, total_size)
        
        return output_path
    
    def _download_mega(self, info: DownloadInfo, output_path: Path, progress_callback=None) -> Path:
        """Download from Mega.nz using megadl"""
        
        try:
            # Use megadl for Mega downloads
            cmd = ['megadl', '--path', str(output_path.parent), info.url]
            
            if progress_callback:
                # Run with progress monitoring
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    
                    if output:
                        # Parse progress from megadl output
                        progress_match = re.search(r'(\d+)%', output)
                        if progress_match:
                            progress = float(progress_match.group(1))
                            progress_callback(progress, 0, 0)
                
                if process.returncode == 0:
                    return output_path
            
            else:
                # Run without progress monitoring
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                if result.returncode == 0:
                    return output_path
        
        except subprocess.TimeoutExpired:
            logger.error("Mega download timed out")
        except FileNotFoundError:
            logger.error("megadl not found, falling back to HTTP download")
            # Fallback to HTTP download
            return self._download_http(info, output_path, 0, progress_callback)
        
        return None
    
    def _download_afh(self, info: DownloadInfo, output_path: Path, progress_callback=None) -> Path:
        """Download from AndroidFileHost"""
        
        try:
            # Use the existing AFH downloader if available
            afh_script = Path(self.config.tools_dir) / 'downloaders' / 'afh_dl.py'
            
            if afh_script.exists():
                cmd = ['python3', str(afh_script), info.url, str(output_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                
                if result.returncode == 0 and output_path.exists():
                    return output_path
        
        except subprocess.TimeoutExpired:
            logger.error("AFH download timed out")
        except Exception as e:
            logger.error(f"AFH download failed: {e}")
        
        # Fallback to HTTP download
        return self._download_http(info, output_path, 0, progress_callback)
    
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL"""
        
        parsed = urlparse(url)
        path = parsed.path
        
        if path:
            filename = Path(path).name
            if filename and '.' in filename:
                return filename
        
        # Fallback to generic name
        return f"firmware_{int(time.time())}.zip"
    
    def _parse_file_size(self, size_str: str) -> int:
        """Parse file size string to bytes"""
        
        size_str = size_str.strip().upper()
        
        # Extract number and unit
        match = re.match(r'([0-9.]+)\s*([KMGT]?B?)', size_str)
        if not match:
            return 0
        
        number = float(match.group(1))
        unit = match.group(2)
        
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4,
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4
        }
        
        multiplier = multipliers.get(unit, 1)
        return int(number * multiplier)
    
    def batch_download(self, urls: List[str], progress_callback=None) -> List[Path]:
        """Download multiple files with combined progress tracking"""
        
        downloaded_files = []
        total_urls = len(urls)
        
        for i, url in enumerate(urls):
            logger.info(f"Downloading {i+1}/{total_urls}: {url}")
            
            try:
                file_path = self.download(url, progress_callback=progress_callback)
                if file_path:
                    downloaded_files.append(file_path)
                else:
                    logger.error(f"Failed to download: {url}")
            
            except Exception as e:
                logger.error(f"Error downloading {url}: {e}")
        
        return downloaded_files
    
    def verify_download(self, file_path: Path, expected_size: int = 0, checksum: str = "") -> bool:
        """Verify downloaded file integrity"""
        
        if not file_path.exists():
            return False
        
        # Check file size
        if expected_size > 0:
            actual_size = file_path.stat().st_size
            if actual_size != expected_size:
                logger.warning(f"File size mismatch: expected {expected_size}, got {actual_size}")
                return False
        
        # Check checksum if provided
        if checksum:
            try:
                import hashlib
                
                # Determine hash algorithm from checksum length
                if len(checksum) == 32:  # MD5
                    hasher = hashlib.md5()
                elif len(checksum) == 40:  # SHA1
                    hasher = hashlib.sha1()
                elif len(checksum) == 64:  # SHA256
                    hasher = hashlib.sha256()
                else:
                    logger.warning(f"Unknown checksum format: {checksum}")
                    return True  # Skip verification
                
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        hasher.update(chunk)
                
                calculated = hasher.hexdigest().lower()
                expected = checksum.lower()
                
                if calculated != expected:
                    logger.error(f"Checksum mismatch: expected {expected}, got {calculated}")
                    return False
            
            except Exception as e:
                logger.error(f"Error verifying checksum: {e}")
                return False
        
        return True