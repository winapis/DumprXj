"""
Manufacturer detection and extraction management
"""

from pathlib import Path
from typing import Optional, Tuple, Dict, Type
import magic
import struct

from .samsung import SamsungExtractor
from .xiaomi import XiaomiExtractor  
from .oppo import OppoExtractor
from .huawei import HuaweiExtractor
from .lg import LGExtractor
from .htc import HTCExtractor
from .sony import SonyExtractor
from .generic import GenericExtractor


class ManufacturerDetector:
    """Detects manufacturer and firmware format from files"""
    
    # Register all manufacturer extractors
    EXTRACTORS: Dict[str, Type] = {
        "Samsung": SamsungExtractor,
        "Xiaomi": XiaomiExtractor,
        "OPPO": OppoExtractor, 
        "OnePlus": OppoExtractor,  # OnePlus uses OPPO formats
        "Huawei": HuaweiExtractor,
        "LG": LGExtractor,
        "HTC": HTCExtractor,
        "Sony": SonyExtractor,
        "Generic": GenericExtractor
    }
    
    def __init__(self):
        self.magic_detector = magic.Magic(mime=True)
        
    def detect(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect manufacturer and format from file
        
        Returns:
            Tuple[manufacturer, format_type]
        """
        if file_path.is_dir():
            return self._detect_from_directory(file_path)
        else:
            return self._detect_from_file(file_path)
    
    def _detect_from_file(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """Detect from single file"""
        filename = file_path.name.lower()
        
        # Read first few bytes for magic detection
        try:
            with open(file_path, 'rb') as f:
                header = f.read(512)
        except Exception:
            return None, None
        
        # Samsung detection
        if any(ext in filename for ext in ['.tar.md5', '.tar', '.pit']):
            return "Samsung", "TAR/PIT"
            
        if b'SAMSUNG' in header[:100]:
            return "Samsung", "Samsung Package"
        
        # OPPO/OnePlus detection
        if header.startswith(b'OPPOENCRYPT!'):
            return "OPPO", "OZIP"
            
        if filename.endswith('.ozip'):
            return "OPPO", "OZIP"
            
        if filename.endswith(('.ofp', '.ops')):
            if b'OPPO' in header[:100]:
                return "OPPO", "OFP/OPS"
        
        # Xiaomi detection
        if filename.endswith('.tgz') and b'MIUI' in header:
            return "Xiaomi", "MIUI Package"
            
        if any(pattern in filename for pattern in ['miui', 'xiaomi', 'redmi']):
            return "Xiaomi", "Fastboot Image"
        
        # Huawei detection  
        if filename == 'update.app' or 'UPDATE.APP' in filename:
            return "Huawei", "UPDATE.APP"
        
        # LG detection
        if filename.endswith(('.kdz', '.dz')):
            return "LG", "KDZ/DZ"
            
        # HTC detection
        if filename.startswith('ruu_') and filename.endswith('.exe'):
            return "HTC", "RUU"
            
        if self._is_htc_rom(file_path):
            return "HTC", "RUU"
        
        # Sony detection
        if filename.endswith(('.ftf', '.sin')):
            return "Sony", "FTF/SIN"
            
        # Generic Android detection
        if any(name in filename for name in ['system.img', 'boot.img', 'recovery.img']):
            return "Generic", "Android Images"
            
        if filename.endswith('.img') and self._is_android_image(file_path):
            return "Generic", "Android Image"
            
        if filename == 'payload.bin':
            return "Generic", "OTA Payload"
            
        # Archive detection
        mime_type = self._get_mime_type(file_path)
        if any(archive_type in mime_type for archive_type in ['zip', 'rar', '7z', 'tar']):
            return "Generic", "Archive"
        
        return None, None
    
    def _detect_from_directory(self, dir_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """Detect from directory contents"""
        files = list(dir_path.iterdir())
        
        # Look for manufacturer-specific files
        for file_path in files:
            if file_path.is_file():
                manufacturer, format_type = self._detect_from_file(file_path)
                if manufacturer:
                    return manufacturer, format_type
        
        return "Generic", "Directory"
    
    def _is_htc_rom(self, file_path: Path) -> bool:
        """Check if file is HTC ROM"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(100)
                return b'HTC' in header or b'RUU' in header
        except Exception:
            return False
    
    def _is_android_image(self, file_path: Path) -> bool:
        """Check if file is Android boot/system image"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(100)
                # Check for Android boot image magic
                if header.startswith(b'ANDROID!'):
                    return True
                # Check for ext4 filesystem
                if b'\x53\xEF' in header[56:58]:  # ext4 magic
                    return True
                return False
        except Exception:
            return False
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type of file"""
        try:
            return self.magic_detector.from_file(str(file_path))
        except Exception:
            return ""
    
    def get_extractor(self, manufacturer: str):
        """Get extractor instance for manufacturer"""
        extractor_class = self.EXTRACTORS.get(manufacturer)
        if extractor_class:
            return extractor_class()
        return None