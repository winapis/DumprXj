"""
Download manager with support for multiple services
"""

from pathlib import Path
from typing import Optional
import requests
from urllib.parse import urlparse
import subprocess
import tempfile

from ..core.logger import logger
from ..core.config import config


class DownloadManager:
    """Manages downloads from various sources"""
    
    def download(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download file from URL to output directory"""
        
        # Detect service type
        service = self._detect_service(url)
        logger.info(f"🌐 Detected service: {service}")
        
        if service == "mega":
            return self._download_mega(url, output_dir)
        elif service == "gdrive":
            return self._download_gdrive(url, output_dir)
        elif service == "mediafire":
            return self._download_mediafire(url, output_dir)
        elif service == "androidfilehost":
            return self._download_afh(url, output_dir)
        elif service == "direct":
            return self._download_direct(url, output_dir)
        else:
            # Try direct download as fallback
            return self._download_direct(url, output_dir)
    
    def _detect_service(self, url: str) -> str:
        """Detect download service from URL"""
        url_lower = url.lower()
        
        if "mega.nz" in url_lower or "mega.co.nz" in url_lower:
            return "mega"
        elif "drive.google.com" in url_lower or "googleusercontent.com" in url_lower:
            return "gdrive"
        elif "mediafire.com" in url_lower:
            return "mediafire"
        elif "androidfilehost.com" in url_lower:
            return "androidfilehost"
        elif "dropbox.com" in url_lower:
            return "dropbox"
        elif "onedrive.live.com" in url_lower or "1drv.ms" in url_lower:
            return "onedrive"
        else:
            return "direct"
    
    def _download_mega(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download from Mega.nz"""
        try:
            # Use mega-media-drive_dl.sh script
            script_path = config.get_tool_path("megamediadrive_dl")
            
            if not script_path.exists():
                logger.error("Mega downloader script not found")
                return None
            
            cmd = ["bash", str(script_path), url]
            
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Find downloaded file
                downloaded_files = list(output_dir.glob("*"))
                if downloaded_files:
                    latest_file = max(downloaded_files, key=lambda f: f.stat().st_mtime)
                    logger.success(f"✅ Downloaded from Mega: {latest_file.name}")
                    return latest_file
            else:
                logger.error(f"Mega download failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Mega download error: {str(e)}")
        
        return None
    
    def _download_gdrive(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download from Google Drive"""
        try:
            import gdown
            
            # Extract file ID from URL
            file_id = self._extract_gdrive_id(url)
            if not file_id:
                logger.error("Could not extract Google Drive file ID")
                return None
            
            # Download using gdown
            download_url = f"https://drive.google.com/uc?id={file_id}"
            output_file = output_dir / "downloaded_file"
            
            logger.info("⬬ Downloading from Google Drive...")
            downloaded_path = gdown.download(download_url, str(output_file), quiet=False)
            
            if downloaded_path:
                result_path = Path(downloaded_path)
                logger.success(f"✅ Downloaded from Google Drive: {result_path.name}")
                return result_path
                
        except ImportError:
            logger.error("gdown library not available for Google Drive downloads")
        except Exception as e:
            logger.error(f"Google Drive download error: {str(e)}")
        
        return None
    
    def _download_afh(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download from AndroidFileHost"""
        try:
            # Use afh_dl.py script
            script_path = config.get_tool_path("afh_dl")
            
            if not script_path.exists():
                logger.error("AFH downloader script not found")
                return None
            
            cmd = ["python3", str(script_path), "-l", url]
            
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Find downloaded file
                downloaded_files = list(output_dir.glob("*"))
                if downloaded_files:
                    latest_file = max(downloaded_files, key=lambda f: f.stat().st_mtime)
                    logger.success(f"✅ Downloaded from AFH: {latest_file.name}")
                    return latest_file
            else:
                logger.error(f"AFH download failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"AFH download error: {str(e)}")
        
        return None
    
    def _download_direct(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download directly from HTTP/HTTPS URL"""
        try:
            logger.info("⬬ Starting direct download...")
            
            # Get filename from URL
            parsed = urlparse(url)
            filename = Path(parsed.path).name
            if not filename:
                filename = "downloaded_file"
            
            output_file = output_dir / filename
            
            # Download with progress
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_file, 'wb') as f:
                if total_size > 0:
                    from tqdm import tqdm
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            logger.success(f"✅ Downloaded: {output_file.name}")
            return output_file
            
        except Exception as e:
            logger.error(f"Direct download error: {str(e)}")
        
        return None
    
    def _download_mediafire(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download from MediaFire"""
        # For now, try direct download (MediaFire often works with direct requests)
        return self._download_direct(url, output_dir)
    
    def _extract_gdrive_id(self, url: str) -> Optional[str]:
        """Extract Google Drive file ID from URL"""
        import re
        
        patterns = [
            r'/d/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'/file/d/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None