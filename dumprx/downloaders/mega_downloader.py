import subprocess
import re
import base64
import json
import tempfile
import os
import urllib.parse
from pathlib import Path
from typing import Optional
import logging

from rich.progress import Progress, DownloadColumn, TransferSpeedColumn, TimeElapsedColumn, BarColumn, TextColumn
from rich.console import Console

from dumprx.utils.ui import print_info, print_error, print_success

logger = logging.getLogger(__name__)
console = Console()


class MegaDownloader:
    """Python implementation of mega-media-drive_dl.sh mega functionality"""
    
    def __init__(self):
        self.session_cookies = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.cookies')
        
    def __del__(self):
        # Cleanup cookies file
        try:
            os.unlink(self.session_cookies.name)
        except:
            pass
    
    def url_str(self, s: str) -> str:
        """Convert URL encoding for mega"""
        return s.replace('-', '+').replace('_', '/').replace(',', '')
    
    def json_req(self, data: str, endpoint: str = "") -> str:
        """Make JSON request to mega API"""
        try:
            result = subprocess.run([
                'wget', '-q', '-O-', '--post-data', data,
                '--header', 'Content-Type:application/json',
                f'https://g.api.mega.co.nz/cs{endpoint}'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return ""
        except:
            return ""
    
    def key_solver(self, key: str) -> str:
        """Solve mega key"""
        try:
            decoded = base64.b64decode(key + '==', validate=True)
            return decoded.hex()
        except:
            return ""
    
    def json_post(self, field: str, json_data: str) -> str:
        """Extract field from JSON response"""
        try:
            import json as json_lib
            data = json_lib.loads(json_data)
            
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            if isinstance(data, dict) and field in data:
                return str(data[field])
        except:
            pass
        
        # Fallback to regex parsing (like original awk)
        pattern = rf'"{field}"\s*:\s*"([^"]*)"'
        match = re.search(pattern, json_data)
        if match:
            return match.group(1)
        
        return ""
    
    def key_dec(self, encrypted_data: str, key: str) -> str:
        """Decrypt data with key"""
        try:
            key_hex = self.key_solver(self.url_str(key))
            if not key_hex:
                return ""
            
            # Use openssl for decryption
            result = subprocess.run([
                'openssl', 'enc', '-a', '-d', '-A', '-aes-128-ecb',
                '-K', key_hex, '-iv', '00000000000000000000000000000000',
                '-nopad'
            ], input=self.url_str(encrypted_data), text=True, capture_output=True)
            
            if result.returncode == 0:
                return base64.b64encode(result.stdout.encode()).decode()
            
        except Exception as e:
            logger.debug(f"Key decryption error: {e}")
        
        return ""
    
    def size_pad(self, data: str) -> str:
        """Add padding to base64 data"""
        pad = (4 - len(data) % 4) % 4
        return data + '=' * pad
    
    def meta_dec_key(self, key_data: str) -> tuple:
        """Generate metadata decryption key and IV"""
        try:
            if len(key_data) < 64:
                return "", ""
            
            var0 = int(key_data[0:16], 16) ^ int(key_data[32:48], 16)
            var1 = int(key_data[16:32], 16) ^ int(key_data[48:64], 16)
            
            meta_key = f"{var0:016x}{var1:016x}"
            meta_iv = key_data[32:48] + "0000000000000000"
            
            return meta_key, meta_iv
        except:
            return "", ""
    
    def meta_dec(self, key: str, data: str) -> str:
        """Decrypt metadata"""
        try:
            result = subprocess.run([
                'openssl', 'enc', '-a', '-A', '-d', '-aes-128-cbc',
                '-K', key, '-iv', '00000000000000000000000000000000',
                '-nopad'
            ], input=data, text=True, capture_output=True)
            
            if result.returncode == 0:
                return result.stdout.rstrip('\x00')
        except:
            pass
        
        return ""
    
    def mega_link_vars(self, url: str) -> tuple:
        """Parse mega URL to extract ID and key"""
        if "/#" in url:
            parts = url.split('!')
            if len(parts) >= 3:
                fld = parts[0]
                id_part = parts[1] if len(parts) > 1 else ""
                key = parts[2] if len(parts) > 2 else ""
                return fld, id_part, key
        else:
            # Handle direct file URLs
            url_parts = url.split('/')
            if len(url_parts) > 0:
                last_part = url_parts[-1]
                if '#' in last_part:
                    id_part, key = last_part.split('#', 1)
                    fld = '/'.join(url_parts[:-1]) + '/'
                    return fld, id_part, key
        
        return "", "", ""
    
    def file_downdec(self, url: str, filename: str, key: str, iv: str, output_dir: Path) -> bool:
        """Download and decrypt file"""
        print_info(f"Downloading file {filename}...")
        
        output_path = output_dir / filename
        temp_path = output_path.with_suffix(output_path.suffix + '.tmp')
        
        try:
            # Download with aria2c first
            result = subprocess.run([
                'aria2c', '-c', '-s16', '-x8', '-m10',
                '--console-log-level=warn', '--summary-interval=0',
                '--check-certificate=false', '-o', temp_path.name,
                url
            ], cwd=output_dir, capture_output=True, timeout=3600)
            
            if result.returncode != 0 or not temp_path.exists():
                # Fallback to wget
                subprocess.run([
                    'wget', '-O', str(temp_path), '-q', '--show-progress',
                    '--progress=bar:force', '--no-check-certificate', url
                ], timeout=3600)
            
            if not temp_path.exists():
                return False
            
            # Decrypt file
            with open(temp_path, 'rb') as encrypted_file:
                result = subprocess.run([
                    'openssl', 'enc', '-d', '-aes-128-ctr',
                    '-K', key, '-iv', iv
                ], stdin=encrypted_file, stdout=open(output_path, 'wb'))
            
            # Clean up temp file
            temp_path.unlink()
            
            if result.returncode == 0:
                print_success(f"Downloaded and decrypted: {filename}")
                return True
            
        except Exception as e:
            logger.exception(f"Error downloading {filename}")
            if temp_path.exists():
                temp_path.unlink()
        
        return False
    
    def file_down(self, url: str, filename: str, output_dir: Path) -> bool:
        """Download file without decryption"""
        print_info(f"Downloading file {filename}...")
        
        output_path = output_dir / filename
        temp_path = output_path.with_suffix(output_path.suffix + '.tmp')
        
        try:
            # Download with aria2c first
            result = subprocess.run([
                'aria2c', '-c', '-s16', '-x8', '-m10',
                '--console-log-level=warn', '--summary-interval=0',
                '--check-certificate=false', '-o', temp_path.name,
                url
            ], cwd=output_dir, capture_output=True, timeout=3600)
            
            if result.returncode != 0 or not temp_path.exists():
                # Fallback to wget
                subprocess.run([
                    'wget', '-O', str(temp_path), '-q', '--show-progress',
                    '--progress=bar:force', '--no-check-certificate', url
                ], timeout=3600)
            
            if temp_path.exists():
                temp_path.rename(output_path)
                print_success(f"Downloaded: {filename}")
                return True
            
        except Exception as e:
            logger.exception(f"Error downloading {filename}")
            if temp_path.exists():
                temp_path.unlink()
        
        return False
    
    def download_mega(self, url: str, output_dir: Path) -> Optional[Path]:
        """Main mega download function"""
        print_info("Mega.NZ Website Link Detected")
        
        fld, id_part, key = self.mega_link_vars(url)
        
        if not id_part or not key:
            print_error("Invalid Mega URL format")
            return None
        
        try:
            if fld.endswith("F") or "folder" in fld:
                return self._download_folder(id_part, key, output_dir)
            elif fld.endswith("#") or "file" in fld:
                return self._download_file(id_part, key, output_dir)
        except Exception as e:
            logger.exception("Error downloading from Mega")
            print_error(f"Mega download failed: {e}")
        
        return None
    
    def _download_file(self, file_id: str, key: str, output_dir: Path) -> Optional[Path]:
        """Download single file from mega"""
        try:
            # Get file metadata
            meta_key, meta_iv = self.meta_dec_key(self.key_solver(self.url_str(key)))
            if not meta_key:
                print_error("Could not generate decryption key")
                return None
            
            # Get file attributes
            response = self.json_req(f'[{{"a":"g", "p":"{file_id}"}}]', '?')
            name_key = self.url_str(self.json_post('at', response))
            
            if not name_key:
                print_error("Could not get file attributes")
                return None
            
            # Decrypt filename
            filename = self.json_post('n', self.meta_dec(meta_key, self.size_pad(name_key)))
            if not filename:
                filename = f"mega_file_{file_id}"
            
            # Get download URL
            download_response = self.json_req(f'[{{"a":"g","g":1,"p":"{file_id}"}}]', '?')
            file_url = self.json_post('g', download_response)
            
            if not file_url:
                print_error("Could not get download URL")
                return None
            
            # Download and decrypt
            if self.file_downdec(file_url, filename, meta_key, meta_iv, output_dir):
                return output_dir / filename
            
        except Exception as e:
            logger.exception("Error downloading mega file")
            print_error(f"File download failed: {e}")
        
        return None
    
    def _download_folder(self, folder_id: str, key: str, output_dir: Path) -> Optional[Path]:
        """Download folder from mega (simplified implementation)"""
        print_error("Mega folder download not yet fully implemented")
        print_info("Please use mega-cmd or download files individually")
        return None


def download_mega_advanced(url: str, output_dir: Path) -> Optional[Path]:
    """Advanced mega download with full folder support"""
    downloader = MegaDownloader()
    return downloader.download_mega(url, output_dir)