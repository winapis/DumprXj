import subprocess
import re
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from dumprx.core.config import Config

logger = logging.getLogger(__name__)


class FirmwareDetector:
    def __init__(self, config: Config):
        self.config = config
        
    def detect_firmware_type(self, firmware_path: Path) -> Optional[str]:
        """Detect firmware type based on file analysis"""
        
        if firmware_path.is_file():
            return self._detect_file_type(firmware_path)
        elif firmware_path.is_dir():
            return self._detect_directory_type(firmware_path)
        else:
            return None
    
    def _detect_file_type(self, file_path: Path) -> Optional[str]:
        """Detect firmware type for a single file"""
        file_name = file_path.name.lower()
        extension = file_path.suffix.lower()
        
        # Check file extension first
        if extension in ['.zip', '.rar', '.7z', '.tar', '.tgz', '.tar.gz', '.tar.md5']:
            # Check contents using 7zz
            if self._check_archive_contents(file_path, "UPDATE.APP"):
                return "huawei_update_app"
            elif self._check_archive_contents(file_path, "payload.bin"):
                return "payload_bin"
            elif self._check_archive_contents(file_path, "super.img"):
                return "super_img"
            elif self._check_archive_contents(file_path, "rockchip"):
                return "rockchip"
            elif self._check_archive_contents(file_path, r".*\.rar|.*\.zip|.*\.7z|.*\.tar"):
                return "zip_archive"
            else:
                return "zip_archive"
        
        elif extension == '.kdz':
            return "lg_kdz"
        
        elif extension == '.ops':
            return "oppo_ops"
        
        elif extension == '.nb0':
            return "nb0"
        
        elif extension == '.pac':
            return "pac"
        
        elif file_name.startswith('ruu_') and extension == '.exe':
            return "htc_ruu"
        
        elif 'payload.bin' in file_name:
            return "payload_bin"
        
        elif 'super' in file_name and extension == '.img':
            return "super_img"
        
        elif 'update.app' in file_name:
            return "huawei_update_app"
        
        elif any(keyword in file_name for keyword in ['system.new.dat', 'system.img', 'system-sign.img']):
            return "system_image"
        
        elif extension in ['.sin']:
            return "sony_sin"
        
        # Check for AML (Amlogic)
        if self._check_archive_contents(file_path, r".*aml.*"):
            return "amlogic"
        
        # Default fallback
        return self._detect_by_content(file_path)
    
    def _detect_directory_type(self, dir_path: Path) -> Optional[str]:
        """Detect firmware type for a directory"""
        files = list(dir_path.rglob("*"))
        file_names = [f.name.lower() for f in files if f.is_file()]
        
        # Check for specific files
        if any('payload.bin' in name for name in file_names):
            return "payload_bin"
        
        if any('update.app' in name for name in file_names):
            return "huawei_update_app"
        
        if any('super.img' in name for name in file_names):
            return "super_img"
        
        if any(name.endswith('.kdz') for name in file_names):
            return "lg_kdz"
        
        if any(name.endswith('.ops') for name in file_names):
            return "oppo_ops"
        
        # Check for system images
        system_patterns = [
            'system.new.dat', 'system.img', 'system-sign.img',
            'system.bin', 'system-p'
        ]
        
        if any(any(pattern in name for pattern in system_patterns) for name in file_names):
            return "system_image"
        
        # Check for chunks or other patterns
        if any('chunk' in name for name in file_names):
            return "chunked_firmware"
        
        # Default to directory processing
        return "firmware_directory"
    
    def _check_archive_contents(self, archive_path: Path, pattern: str) -> bool:
        """Check if archive contains files matching pattern"""
        try:
            cmd = [
                self.config.get_tool_path("7zz"), "l", "-ba", str(archive_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return bool(re.search(pattern, result.stdout, re.IGNORECASE))
            
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"Error checking archive contents: {e}")
        
        return False
    
    def _detect_by_content(self, file_path: Path) -> Optional[str]:
        """Detect firmware type by analyzing file content"""
        try:
            # Read first few KB to analyze
            with open(file_path, 'rb') as f:
                header = f.read(4096)
            
            # Check for specific magic bytes or signatures
            if b'ANDROID!' in header:
                return "android_boot_img"
            
            if b'VNDRBOOT' in header:
                return "vendor_boot_img"
            
            # Check for sparse image
            if header[:4] == b'\x3a\xff\x26\xed':
                return "sparse_image"
            
            # Check for ext4 filesystem
            if header[1024:1026] == b'\x53\xef':
                return "ext4_image"
            
            # Check for EROFS
            if header[1024:1028] == b'\xe2\xe1\xf5\xe0':
                return "erofs_image"
            
        except Exception as e:
            logger.debug(f"Error analyzing file content: {e}")
        
        return "unknown"
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed information about firmware file"""
        info = {
            'path': str(file_path),
            'size': file_path.stat().st_size if file_path.exists() else 0,
            'type': self.detect_firmware_type(file_path),
            'extension': file_path.suffix.lower(),
            'name': file_path.name
        }
        
        return info