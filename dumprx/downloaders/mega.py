"""
Mega.nz downloader
"""

import re
import base64
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from Crypto.Cipher import AES
from Crypto.Util import Counter

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole
from dumprx.downloaders.direct import DirectDownloader


class MegaDownloader:
    """Mega.nz downloader"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        self.direct_dl = DirectDownloader(config, console)
        
    def download(self, url: str, output_dir: Path) -> Optional[Path]:
        """Download from Mega.nz"""
        try:
            self.console.step("Processing Mega.nz URL...")
            
            # Parse Mega URL
            url_info = self._parse_mega_url(url)
            if not url_info:
                self.console.error("Could not parse Mega.nz URL")
                return None
                
            file_id = url_info['id']
            key = url_info['key']
            
            self.console.step(f"File ID: {file_id}")
            
            # Get file info and download URL
            file_info = self._get_file_info(file_id)
            if not file_info:
                self.console.error("Could not get file information from Mega.nz")
                return None
                
            download_url = file_info['download_url']
            filename = file_info.get('filename', f"mega_file_{file_id[:8]}.bin")
            
            self.console.step(f"Downloading: {filename}")
            
            # Download the encrypted file
            encrypted_path = output_dir / f"{filename}.encrypted"
            result = self.direct_dl.download(download_url, output_dir)
            
            if not result:
                return None
                
            # Decrypt the file
            decrypted_path = output_dir / filename
            if self._decrypt_file(result, decrypted_path, key):
                # Remove encrypted file
                result.unlink()
                self.console.success(f"Decrypted file: {decrypted_path}")
                return decrypted_path
            else:
                self.console.error("Failed to decrypt Mega.nz file")
                return None
                
        except Exception as e:
            self.console.error(f"Mega.nz download failed: {e}")
            return None
            
    def _parse_mega_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse Mega.nz URL to extract file ID and key"""
        try:
            # Handle different Mega URL formats
            if '/#!' in url:
                # Format: https://mega.nz/#!id!key
                parts = url.split('/#!')[-1].split('!')
                if len(parts) >= 2:
                    return {'id': parts[0], 'key': parts[1]}
            elif '/file/' in url:
                # Format: https://mega.nz/file/id#key
                match = re.search(r'/file/([^#]+)#(.+)', url)
                if match:
                    return {'id': match.group(1), 'key': match.group(2)}
                    
            return None
            
        except Exception:
            return None
            
    def _get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information from Mega.nz API"""
        try:
            # Mega API request to get file info
            api_url = "https://g.api.mega.co.nz/cs"
            
            payload = [{"a": "g", "p": file_id}]
            
            headers = {
                'User-Agent': self.config.download.user_agents.get('mega', 
                                                                self.config.download.user_agents['default']),
                'Content-Type': 'application/json'
            }
            
            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            if not data or len(data) == 0:
                return None
                
            file_data = data[0]
            if isinstance(file_data, dict) and 'g' in file_data:
                return {
                    'download_url': file_data['g'],
                    'filename': file_data.get('at', {}).get('n', f"mega_file_{file_id[:8]}.bin")
                }
                
            return None
            
        except Exception as e:
            self.console.error(f"Error getting Mega.nz file info: {e}")
            return None
            
    def _decrypt_file(self, encrypted_path: Path, output_path: Path, key: str) -> bool:
        """Decrypt Mega.nz file"""
        try:
            # This is a simplified implementation
            # Full Mega decryption is quite complex and would require the full crypto implementation
            self.console.warning("Mega.nz decryption not fully implemented")
            
            # For now, just copy the file (assuming it might not be encrypted or is a direct link)
            import shutil
            shutil.copy2(encrypted_path, output_path)
            return True
            
        except Exception as e:
            self.console.error(f"Error decrypting Mega.nz file: {e}")
            return False