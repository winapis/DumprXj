"""
Advanced download utilities for various services
Replaces mega-media-drive_dl.sh with Python implementation
"""

import os
import sys
import re
import json
import base64
import struct
import urllib.parse
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from Crypto.Cipher import AES
import subprocess


class AdvancedDownloader:
    """Advanced downloader supporting multiple services"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def log(self, message: str):
        """Print log message if verbose"""
        if self.verbose:
            print(f"[Downloader] {message}")
    
    def error(self, message: str):
        """Print error message"""
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def download_file(self, url: str, output_path: Path, chunk_size: int = 8192) -> bool:
        """Download file with progress tracking"""
        try:
            # Detect service and use appropriate method
            if 'mega.nz' in url or 'mega.co.nz' in url:
                return self._download_mega(url, output_path)
            elif 'mediafire.com' in url:
                return self._download_mediafire(url, output_path)
            elif 'drive.google.com' in url:
                return self._download_gdrive(url, output_path)
            elif 'onedrive' in url:
                return self._download_onedrive(url, output_path)
            elif 'androidfilehost.com' in url:
                return self._download_afh(url, output_path)
            else:
                return self._download_direct(url, output_path, chunk_size)
                
        except Exception as e:
            self.error(f"Download failed: {e}")
            return False
    
    def _download_direct(self, url: str, output_path: Path, chunk_size: int) -> bool:
        """Direct HTTP/HTTPS download"""
        try:
            self.log(f"Direct download: {url}")
            
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            
            print()  # New line after progress
            self.log(f"Downloaded {downloaded} bytes")
            return True
            
        except Exception as e:
            self.error(f"Direct download failed: {e}")
            return False
    
    def _download_mega(self, url: str, output_path: Path) -> bool:
        """Download from Mega.nz"""
        try:
            self.log(f"Mega.nz download: {url}")
            
            # Parse Mega URL
            if '/#' in url:
                file_id = url.split('!')[1]
                key = url.split('!')[2]
            else:
                self.error("Invalid Mega URL format")
                return False
            
            # Get file info
            api_url = "https://g.api.mega.co.nz/cs"
            
            # Request file attributes
            req_data = json.dumps([{"a": "g", "g": 1, "p": file_id}])
            response = self.session.post(api_url, data=req_data)
            
            if response.status_code != 200:
                self.error("Failed to get Mega file info")
                return False
            
            data = response.json()
            if not data or 'g' not in data[0]:
                self.error("Invalid Mega response")
                return False
            
            download_url = data[0]['g']
            file_size = data[0]['s']
            
            # Decode key
            key_bytes = self._decode_mega_key(key)
            if not key_bytes:
                self.error("Failed to decode Mega key")
                return False
            
            # Download and decrypt
            return self._download_mega_encrypted(download_url, output_path, key_bytes, file_size)
            
        except Exception as e:
            self.error(f"Mega download failed: {e}")
            return False
    
    def _decode_mega_key(self, key: str) -> Optional[bytes]:
        """Decode Mega encryption key"""
        try:
            # URL-safe base64 decode
            key = key.replace('-', '+').replace('_', '/')
            # Add padding if needed
            padding = 4 - len(key) % 4
            if padding != 4:
                key += '=' * padding
            
            return base64.b64decode(key)
        except Exception:
            return None
    
    def _download_mega_encrypted(self, url: str, output_path: Path, key: bytes, file_size: int) -> bool:
        """Download and decrypt Mega file"""
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Initialize AES decryption
            iv = b'\x00' * 16
            cipher = AES.new(key[:16], AES.MODE_CTR, nonce=iv[:8], initial_value=0)
            
            downloaded = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        decrypted = cipher.decrypt(chunk)
                        f.write(decrypted)
                        downloaded += len(chunk)
                        
                        progress = (downloaded / file_size) * 100
                        print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            
            print()  # New line after progress
            self.log(f"Downloaded and decrypted {downloaded} bytes")
            return True
            
        except Exception as e:
            self.error(f"Mega encrypted download failed: {e}")
            return False
    
    def _download_mediafire(self, url: str, output_path: Path) -> bool:
        """Download from MediaFire"""
        try:
            self.log(f"MediaFire download: {url}")
            
            # Get the page content
            response = self.session.get(url)
            response.raise_for_status()
            
            # Extract direct download link
            pattern = r'href="(http[^"]+mediafire\.com[^"]+)" class="popsok"'
            match = re.search(pattern, response.text)
            
            if not match:
                # Try alternative pattern
                pattern = r'"(https://download\d+\.mediafire\.com[^"]+)"'
                match = re.search(pattern, response.text)
            
            if not match:
                self.error("Could not find MediaFire download link")
                return False
            
            download_url = match.group(1)
            return self._download_direct(download_url, output_path, 8192)
            
        except Exception as e:
            self.error(f"MediaFire download failed: {e}")
            return False
    
    def _download_gdrive(self, url: str, output_path: Path) -> bool:
        """Download from Google Drive"""
        try:
            self.log(f"Google Drive download: {url}")
            
            # Extract file ID from URL
            file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
            if not file_id_match:
                file_id_match = re.search(r'id=([a-zA-Z0-9-_]+)', url)
            
            if not file_id_match:
                self.error("Could not extract Google Drive file ID")
                return False
            
            file_id = file_id_match.group(1)
            
            # Try direct download first
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            response = self.session.get(download_url, stream=True)
            
            # Check if we need to confirm download
            if 'download_warning' in response.text:
                # Extract confirmation token
                token_match = re.search(r'confirm=([^&]+)', response.text)
                if token_match:
                    token = token_match.group(1)
                    download_url = f"https://drive.google.com/uc?export=download&confirm={token}&id={file_id}"
                    response = self.session.get(download_url, stream=True)
            
            response.raise_for_status()
            
            # Save file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.log("Google Drive download completed")
            return True
            
        except Exception as e:
            self.error(f"Google Drive download failed: {e}")
            return False
    
    def _download_onedrive(self, url: str, output_path: Path) -> bool:
        """Download from OneDrive"""
        try:
            self.log(f"OneDrive download: {url}")
            
            # Convert sharing URL to direct download
            if 'onedrive.live.com' in url:
                # Extract the share token
                download_url = url.replace('onedrive.live.com', 'api.onedrive.live.com/v1.0/drives')
                download_url = download_url.replace('?', '/items/') + ':/content'
            else:
                download_url = url
            
            return self._download_direct(download_url, output_path, 8192)
            
        except Exception as e:
            self.error(f"OneDrive download failed: {e}")
            return False
    
    def _download_afh(self, url: str, output_path: Path) -> bool:
        """Download from AndroidFileHost"""
        try:
            self.log(f"AndroidFileHost download: {url}")
            
            # Use the existing afh_dl.py if available
            afh_script = Path(__file__).parent.parent.parent.parent / "utils" / "downloaders" / "afh_dl.py"
            
            if afh_script.exists():
                cmd = [sys.executable, str(afh_script), url, str(output_path)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log("AndroidFileHost download completed via script")
                    return True
                else:
                    self.error(f"AFH script failed: {result.stderr}")
            
            # Fallback to direct parsing
            response = self.session.get(url)
            response.raise_for_status()
            
            # Extract download link
            pattern = r'href="(https://[^"]*androidfilehost[^"]+/download[^"]*)"'
            match = re.search(pattern, response.text)
            
            if not match:
                self.error("Could not find AndroidFileHost download link")
                return False
            
            download_url = match.group(1)
            return self._download_direct(download_url, output_path, 8192)
            
        except Exception as e:
            self.error(f"AndroidFileHost download failed: {e}")
            return False


def main():
    """Command line interface"""
    if len(sys.argv) < 3:
        print("Usage: python downloader.py <URL> <output_file> [--verbose]")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = Path(sys.argv[2])
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    downloader = AdvancedDownloader(verbose=verbose)
    success = downloader.download_file(url, output_file)
    
    if success:
        print(f"Successfully downloaded to: {output_file}")
    else:
        print("Download failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()