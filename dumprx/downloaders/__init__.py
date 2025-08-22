"""
Download manager for various file hosting services.
"""

import os
import re
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple
from abc import ABC, abstractmethod

from ..core.logger import Logger

class DownloadError(Exception):
    """Exception raised for download errors."""
    pass

class BaseDownloader(ABC):
    """Base class for downloaders."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this downloader can handle the URL."""
        pass
    
    @abstractmethod
    def download(self, url: str, output_dir: str) -> str:
        """Download file and return path to downloaded file."""
        pass

class MegaMediaDriveDownloader(BaseDownloader):
    """Downloader for Mega.nz, MediaFire, and Google Drive."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from supported services."""
        supported_domains = ['mega.nz', 'mediafire.com', 'drive.google.com']
        return any(domain in url for domain in supported_domains)
    
    def download(self, url: str, output_dir: str) -> str:
        """Download using mega-media-drive script."""
        script_path = Path(__file__).parent.parent.parent / "utils" / "downloaders" / "mega-media-drive_dl.sh"
        
        if not script_path.exists():
            raise DownloadError(f"Download script not found: {script_path}")
        
        self.logger.info("Downloading from cloud storage", f"Service: {self._get_service_name(url)}")
        
        try:
            result = subprocess.run(
                ["bash", str(script_path), url],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                raise DownloadError(f"Download failed: {result.stderr}")
            
            # Find downloaded file
            files = list(Path(output_dir).glob("*"))
            if not files:
                raise DownloadError("No files downloaded")
            
            # Return the largest file (likely the firmware)
            downloaded_file = max(files, key=lambda f: f.stat().st_size)
            self.logger.success("Download completed", f"File: {downloaded_file.name}")
            
            return str(downloaded_file)
            
        except subprocess.TimeoutExpired:
            raise DownloadError("Download timeout (1 hour)")
        except Exception as e:
            raise DownloadError(f"Download error: {str(e)}")
    
    def _get_service_name(self, url: str) -> str:
        """Get service name from URL."""
        if 'mega.nz' in url:
            return "Mega.nz"
        elif 'mediafire.com' in url:
            return "MediaFire"
        elif 'drive.google.com' in url:
            return "Google Drive"
        return "Unknown"

class AndroidFileHostDownloader(BaseDownloader):
    """Downloader for AndroidFileHost."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from AndroidFileHost."""
        return 'androidfilehost.com' in url
    
    def download(self, url: str, output_dir: str) -> str:
        """Download using AFH downloader script."""
        script_path = Path(__file__).parent.parent.parent / "utils" / "downloaders" / "afh_dl.py"
        
        if not script_path.exists():
            raise DownloadError(f"AFH downloader not found: {script_path}")
        
        self.logger.info("Downloading from AndroidFileHost")
        
        try:
            result = subprocess.run(
                ["python3", str(script_path), "-l", url],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode != 0:
                raise DownloadError(f"AFH download failed: {result.stderr}")
            
            # Find downloaded file
            files = list(Path(output_dir).glob("*"))
            if not files:
                raise DownloadError("No files downloaded from AFH")
            
            downloaded_file = max(files, key=lambda f: f.stat().st_size)
            self.logger.success("Download completed", f"File: {downloaded_file.name}")
            
            return str(downloaded_file)
            
        except subprocess.TimeoutExpired:
            raise DownloadError("AFH download timeout")
        except Exception as e:
            raise DownloadError(f"AFH download error: {str(e)}")

class TransferDownloader(BaseDownloader):
    """Downloader for WeTransfer."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from WeTransfer."""
        return '/we.tl/' in url
    
    def download(self, url: str, output_dir: str) -> str:
        """Download using transfer tool."""
        transfer_path = Path(__file__).parent.parent.parent / "utils" / "bin" / "transfer"
        
        if not transfer_path.exists():
            raise DownloadError(f"Transfer tool not found: {transfer_path}")
        
        self.logger.info("Downloading from WeTransfer")
        
        try:
            result = subprocess.run(
                [str(transfer_path), url],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode != 0:
                raise DownloadError(f"WeTransfer download failed: {result.stderr}")
            
            # Find downloaded file
            files = list(Path(output_dir).glob("*"))
            if not files:
                raise DownloadError("No files downloaded from WeTransfer")
            
            downloaded_file = max(files, key=lambda f: f.stat().st_size)
            self.logger.success("Download completed", f"File: {downloaded_file.name}")
            
            return str(downloaded_file)
            
        except subprocess.TimeoutExpired:
            raise DownloadError("WeTransfer download timeout")
        except Exception as e:
            raise DownloadError(f"WeTransfer download error: {str(e)}")

class DirectDownloader(BaseDownloader):
    """Downloader for direct HTTP/HTTPS links."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is a direct download link."""
        return url.startswith(('http://', 'https://'))
    
    def download(self, url: str, output_dir: str) -> str:
        """Download using aria2c or wget."""
        # Handle OneDrive links
        if '1drv.ms' in url:
            url = url.replace('ms', 'ws')
        
        filename = self._extract_filename(url)
        output_path = Path(output_dir) / filename
        
        self.logger.info("Downloading direct link", f"URL: {url}")
        
        # Try aria2c first
        try:
            result = subprocess.run([
                "aria2c", "-x16", "-s8", 
                "--console-log-level=warn",
                "--summary-interval=0",
                "--check-certificate=false",
                "--out", filename,
                "--dir", output_dir,
                url
            ], capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0 and output_path.exists():
                self.logger.success("Download completed", f"File: {filename}")
                return str(output_path)
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback to wget
        try:
            self.logger.info("Retrying with wget")
            result = subprocess.run([
                "wget", "-q", "--show-progress", 
                "--progress=bar:force",
                "--no-check-certificate",
                "-O", str(output_path),
                url
            ], timeout=3600)
            
            if result.returncode == 0 and output_path.exists():
                self.logger.success("Download completed", f"File: {filename}")
                return str(output_path)
            else:
                raise DownloadError("wget download failed")
                
        except subprocess.TimeoutExpired:
            raise DownloadError("Direct download timeout")
        except FileNotFoundError:
            raise DownloadError("wget not found")
        except Exception as e:
            raise DownloadError(f"Direct download error: {str(e)}")
    
    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL."""
        parsed = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed.path)
        
        if not filename or '.' not in filename:
            filename = "firmware_download"
        
        return filename

class DownloadManager:
    """Manages downloads from various sources."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.downloaders = [
            MegaMediaDriveDownloader(logger),
            AndroidFileHostDownloader(logger),
            TransferDownloader(logger),
            DirectDownloader(logger)  # This should be last as it handles all HTTP(S)
        ]
    
    def download(self, url: str, output_dir: str) -> str:
        """
        Download file from URL to output directory.
        
        Args:
            url: URL to download from
            output_dir: Directory to save downloaded file
            
        Returns:
            Path to downloaded file
            
        Raises:
            DownloadError: If download fails
        """
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Clean existing files in output directory
        for file in Path(output_dir).glob("*"):
            if file.is_file():
                file.unlink()
        
        # Find appropriate downloader
        for downloader in self.downloaders:
            if downloader.can_handle(url):
                try:
                    return downloader.download(url, output_dir)
                except DownloadError:
                    raise
                except Exception as e:
                    raise DownloadError(f"Downloader {downloader.__class__.__name__} failed: {str(e)}")
        
        raise DownloadError(f"No downloader available for URL: {url}")
    
    def is_url(self, path: str) -> bool:
        """Check if path is a URL."""
        return bool(re.match(r'^https?://.*$', path))
    
    def get_supported_services(self) -> list:
        """Get list of supported download services."""
        return [
            "Direct HTTP/HTTPS links",
            "Mega.nz",
            "MediaFire",
            "Google Drive", 
            "OneDrive (1drv.ms)",
            "AndroidFileHost",
            "WeTransfer"
        ]