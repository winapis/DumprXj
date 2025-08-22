"""
Enhanced file and firmware detection module.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import struct

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from ..core.config import Config
from ..core.logger import get_logger


class FileDetector:
    """
    Enhanced file detection with support for various firmware formats
    and vendor-specific detection.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
        
        # Initialize magic for file type detection
        if MAGIC_AVAILABLE:
            try:
                self.magic = magic.Magic(mime=True)
                self.magic_desc = magic.Magic()
            except Exception:
                self.logger.warning("python-magic setup failed, using basic detection")
                self.magic = None
                self.magic_desc = None
        else:
            self.logger.warning("python-magic not available, using basic detection")
            self.magic = None
            self.magic_desc = None
        
        # Vendor signatures for detection
        self.vendor_signatures = {
            'oppo': [
                b'OPPOENCRYPT!',  # OZIP files
                b'OPOTAPACK',     # OTA packages
                b'ops',           # OPS files
            ],
            'oneplus': [
                b'OnePlus',
                b'ops',
                b'payload.bin'
            ],
            'lg': [
                b'\x28\x05\x00\x00\x24\x38\x22\x25',  # KDZ header
                b'KDZ_MAGIC',
            ],
            'htc': [
                b'RUU',
                b'htc',
                b'android-info.txt'
            ],
            'samsung': [
                b'SAMSUNG',
                b'.tar.md5',
                b'Odin',
                b'AP_',
                b'BL_',
                b'CP_',
                b'CSC_'
            ],
            'xiaomi': [
                b'MIUI',
                b'xiaomi',
                b'fastboot',
                b'images'
            ],
            'huawei': [
                b'UPDATE.APP',
                b'HUAWEI',
                b'HONOR'
            ],
            'sony': [
                b'sin',
                b'SONY',
                b'Xperia'
            ],
            'motorola': [
                b'MOTOROLA',
                b'fastboot',
                b'sparsechunk'
            ],
            'nokia': [
                b'nb0',
                b'NOKIA',
                b'HMD'
            ],
            'spreadtrum': [
                b'pac',
                b'SPREADTRUM'
            ],
            'mediatek': [
                b'MTK',
                b'MediaTek',
                b'scatter'
            ],
            'qualcomm': [
                b'rawprogram',
                b'patch',
                b'QUALCOMM'
            ]
        }
        
        # URL patterns for different services
        self.url_patterns = {
            'mega': [
                r'mega\.nz',
                r'mega\.co\.nz'
            ],
            'mediafire': [
                r'mediafire\.com',
                r'download\d+\.mediafire\.com'
            ],
            'google_drive': [
                r'drive\.google\.com',
                r'docs\.google\.com'
            ],
            'onedrive': [
                r'1drv\.ms',
                r'onedrive\.live\.com'
            ],
            'androidfilehost': [
                r'androidfilehost\.com',
                r'afh\.link'
            ],
            'wetransfer': [
                r'we\.tl',
                r'wetransfer\.com'
            ],
            'direct': [
                r'\.zip$',
                r'\.rar$',
                r'\.7z$',
                r'\.tar$',
                r'\.gz$'
            ]
        }
    
    def detect_input(self, input_path: str) -> Dict[str, Any]:
        """
        Detect and analyze the input (file, folder, or URL).
        
        Args:
            input_path: Path to file/folder or URL
            
        Returns:
            Dictionary with detection results
        """
        self.logger.debug(f"Detecting input: {input_path}")
        
        # Check if it's a URL
        if self._is_url(input_path):
            return self._analyze_url(input_path)
        
        # Check if it's a local path
        path = Path(input_path)
        if path.exists():
            if path.is_file():
                return self._analyze_file(path)
            elif path.is_dir():
                return self._analyze_directory(path)
        
        raise ValueError(f"Input path does not exist: {input_path}")
    
    def _is_url(self, input_path: str) -> bool:
        """Check if the input is a URL."""
        try:
            result = urlparse(input_path)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyze URL and determine the service type."""
        self.logger.debug(f"Analyzing URL: {url}")
        
        result = {
            'type': 'url',
            'url': url,
            'service': 'unknown',
            'supported': False
        }
        
        # Detect service type
        for service, patterns in self.url_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    result['service'] = service
                    result['supported'] = True
                    break
            if result['supported']:
                break
        
        # Special handling for different services
        if result['service'] == 'google_drive':
            result['file_id'] = self._extract_gdrive_id(url)
        elif result['service'] == 'mega':
            result['file_key'] = self._extract_mega_key(url)
        
        return result
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file."""
        self.logger.debug(f"Analyzing file: {file_path}")
        
        result = {
            'type': 'file',
            'path': str(file_path),
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'format': file_path.suffix.lower().lstrip('.'),
            'vendor': None,
            'encrypted': False,
            'supported': False
        }
        
        # Detect MIME type
        if self.magic:
            try:
                result['mime_type'] = self.magic.from_file(str(file_path))
                result['description'] = self.magic_desc.from_file(str(file_path))
            except Exception as e:
                self.logger.debug(f"Magic detection failed: {e}")
        
        # Check if format is supported
        result['supported'] = result['format'] in self.config.supported_formats
        
        # Detect vendor from file signatures
        result['vendor'] = self._detect_vendor_from_file(file_path)
        
        # Check if file is encrypted
        result['encrypted'] = self._is_encrypted_file(file_path)
        
        # Additional format-specific analysis
        if result['format'] == 'ozip':
            result.update(self._analyze_ozip(file_path))
        elif result['format'] == 'kdz':
            result.update(self._analyze_kdz(file_path))
        elif result['format'] == 'nb0':
            result.update(self._analyze_nb0(file_path))
        elif result['format'] == 'pac':
            result.update(self._analyze_pac(file_path))
        
        return result
    
    def _analyze_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Analyze a directory."""
        self.logger.debug(f"Analyzing directory: {dir_path}")
        
        result = {
            'type': 'directory',
            'path': str(dir_path),
            'name': dir_path.name,
            'files': [],
            'firmware_files': [],
            'vendor': None,
            'supported': False
        }
        
        # Scan for files
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                file_info = self._analyze_file(file_path)
                result['files'].append(file_info)
                
                # Check if it's a firmware file
                if file_info['supported']:
                    result['firmware_files'].append(file_info)
                    result['supported'] = True
                
                # Update vendor info
                if file_info['vendor'] and not result['vendor']:
                    result['vendor'] = file_info['vendor']
        
        return result
    
    def _detect_vendor_from_file(self, file_path: Path) -> Optional[str]:
        """Detect vendor from file contents and name."""
        # Check filename patterns
        filename = file_path.name.lower()
        
        vendor_patterns = {
            'oppo': ['oppo', 'realme', 'ozip', 'ops'],
            'oneplus': ['oneplus', 'ops'],
            'lg': ['kdz', 'dz'],
            'htc': ['ruu', 'htc'],
            'samsung': ['odin', 'ap_', 'bl_', 'cp_', 'csc_', '.tar.md5'],
            'xiaomi': ['miui', 'xiaomi', 'fastboot'],
            'huawei': ['update.app', 'huawei', 'honor'],
            'sony': ['.sin', 'sony', 'xperia'],
            'motorola': ['motorola', 'sparsechunk'],
            'nokia': ['.nb0', 'nokia', 'hmd'],
            'spreadtrum': ['.pac', 'spreadtrum'],
        }
        
        for vendor, patterns in vendor_patterns.items():
            if any(pattern in filename for pattern in patterns):
                return vendor
        
        # Check file signatures
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)  # Read first 1KB
                
                for vendor, signatures in self.vendor_signatures.items():
                    for signature in signatures:
                        if signature in header:
                            return vendor
        except Exception as e:
            self.logger.debug(f"Could not read file for signature detection: {e}")
        
        return None
    
    def _is_encrypted_file(self, file_path: Path) -> bool:
        """Check if the file appears to be encrypted."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
                
                # Check for encryption signatures
                encryption_signatures = [
                    b'OPPOENCRYPT!',  # Oppo encrypted files
                    b'ENCRYPTED',
                    b'AES',
                ]
                
                for sig in encryption_signatures:
                    if sig in header:
                        return True
                
                # Check for high entropy (might indicate encryption)
                if len(set(header)) > 12:  # High byte diversity
                    return True
                    
        except Exception:
            pass
        
        return False
    
    def _analyze_ozip(self, file_path: Path) -> Dict[str, Any]:
        """Analyze OZIP files (Oppo/Realme)."""
        result = {'ozip_info': {}}
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)
                if header.startswith(b'OPPOENCRYPT!'):
                    result['encrypted'] = True
                    result['ozip_info']['version'] = 'encrypted'
                else:
                    result['ozip_info']['version'] = 'standard'
        except Exception as e:
            self.logger.debug(f"OZIP analysis failed: {e}")
        
        return result
    
    def _analyze_kdz(self, file_path: Path) -> Dict[str, Any]:
        """Analyze KDZ files (LG)."""
        result = {'kdz_info': {}}
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)
                if header[:4] == b'\x28\x05\x00\x00':
                    result['kdz_info']['valid'] = True
                    result['kdz_info']['magic'] = header[4:8].hex()
        except Exception as e:
            self.logger.debug(f"KDZ analysis failed: {e}")
        
        return result
    
    def _analyze_nb0(self, file_path: Path) -> Dict[str, Any]:
        """Analyze NB0 files (Nokia/Sharp/Essential)."""
        result = {'nb0_info': {}}
        
        try:
            with open(file_path, 'rb') as f:
                # NB0 files have specific structure
                header = f.read(16)
                result['nb0_info']['header'] = header.hex()
        except Exception as e:
            self.logger.debug(f"NB0 analysis failed: {e}")
        
        return result
    
    def _analyze_pac(self, file_path: Path) -> Dict[str, Any]:
        """Analyze PAC files (Spreadtrum)."""
        result = {'pac_info': {}}
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
                result['pac_info']['header'] = header.hex()
        except Exception as e:
            self.logger.debug(f"PAC analysis failed: {e}")
        
        return result
    
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
    
    def _extract_mega_key(self, url: str) -> Optional[str]:
        """Extract file key from Mega URL."""
        match = re.search(r'#!([^!]+)!(.+)', url)
        if match:
            return {
                'file_id': match.group(1),
                'key': match.group(2)
            }
        return None
    
    def is_supported_format(self, input_info: Dict[str, Any]) -> bool:
        """Check if the detected input format is supported."""
        if input_info['type'] == 'url':
            return input_info.get('supported', False)
        elif input_info['type'] == 'file':
            return input_info.get('supported', False)
        elif input_info['type'] == 'directory':
            return input_info.get('supported', False)
        
        return False
    
    def get_ramdisk_version(self, boot_image_path: Path) -> Optional[int]:
        """
        Detect ramdisk version from boot image.
        Supports ramdisk versions 2, 3, and 4.
        """
        try:
            with open(boot_image_path, 'rb') as f:
                # Read boot image header
                header = f.read(1648)  # Standard boot header size
                
                # Check for boot magic
                if not header.startswith(b'ANDROID!'):
                    return None
                
                # Parse header structure
                # Offset 40: header version
                header_version = struct.unpack('<I', header[40:44])[0]
                
                # Ramdisk version detection based on header version
                if header_version >= 4:
                    return 4
                elif header_version >= 3:
                    return 3
                elif header_version >= 2:
                    return 2
                else:
                    return 1  # Legacy
                    
        except Exception as e:
            self.logger.debug(f"Ramdisk version detection failed: {e}")
            return None