import re
import os
from pathlib import Path
from typing import Optional, Tuple, List
from urllib.parse import urlparse

class FirmwareDetector:
    def __init__(self):
        self.url_patterns = {
            'mega': [
                r'https?://mega\.nz/(?:#!|file/)',
                r'https?://mega\.co\.nz/(?:#!|file/)'
            ],
            'mediafire': [
                r'https?://(?:www\.)?mediafire\.com/(?:file/|download/|\?)'
            ],
            'drive': [
                r'https?://drive\.google\.com/(?:file/d/|open\?id=)',
                r'https?://docs\.google\.com/(?:uc\?|file/d/)'
            ],
            'onedrive': [
                r'https?://(?:1drv\.ms|onedrive\.live\.com)',
                r'https?://(?:[a-zA-Z0-9-]+\.)?1drv\.ms'
            ],
            'androidfilehost': [
                r'https?://(?:www\.)?androidfilehost\.com/\?fid=',
                r'https?://(?:www\.)?androidfilehost\.com/\?file='
            ],
            'direct': [
                r'https?://.*\.(zip|rar|7z|tar|gz|tgz|md5|bin|ozip|kdz|exe)$'
            ]
        }
        
        self.firmware_extensions = {
            '.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz', '.tar.md5',
            '.ozip', '.ofp', '.ops', '.kdz', '.exe', '.bin', '.img', '.pac',
            '.nb0', '.sin'
        }
        
        self.firmware_patterns = [
            r'.*\.(?:zip|rar|7z|tar|gz|tgz|md5)$',
            r'.*\.(?:ozip|ofp|ops|kdz)$', 
            r'ruu_.*\.exe$',
            r'system\.new\.dat(?:\.br|\.xz)?$',
            r'system\.(?:new\.)?img$',
            r'system-sign\.img$',
            r'UPDATE\.APP$',
            r'.*\.emmc\.img$',
            r'.*\.img\.ext4$',
            r'system\.bin$',
            r'system-p$',
            r'payload\.bin$',
            r'.*\.nb0$',
            r'.*chunk.*$',
            r'.*\.pac$',
            r'.*super.*\.img$',
            r'.*system.*\.sin$'
        ]
    
    def detect_input_type(self, input_path: str) -> Tuple[str, str]:
        if self._is_url(input_path):
            url_type = self._detect_url_type(input_path)
            return 'url', url_type
        
        path = Path(input_path)
        if path.is_file():
            if self._is_firmware_file(path):
                return 'file', self._detect_firmware_type(path)
            else:
                return 'file', 'unknown'
        elif path.is_dir():
            return 'directory', 'extracted'
        else:
            return 'unknown', 'unknown'
    
    def _is_url(self, input_path: str) -> bool:
        parsed = urlparse(input_path)
        return bool(parsed.scheme and parsed.netloc)
    
    def _detect_url_type(self, url: str) -> str:
        for url_type, patterns in self.url_patterns.items():
            for pattern in patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    return url_type
        return 'direct'
    
    def _is_firmware_file(self, path: Path) -> bool:
        if path.suffix.lower() in self.firmware_extensions:
            return True
        
        filename = path.name.lower()
        for pattern in self.firmware_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True
        
        return False
    
    def _detect_firmware_type(self, path: Path) -> str:
        filename = path.name.lower()
        
        if filename.endswith('.kdz'):
            return 'lg_kdz'
        elif filename.startswith('ruu_') and filename.endswith('.exe'):
            return 'htc_ruu'
        elif filename.endswith('.ozip'):
            return 'oppo_ozip'
        elif filename.endswith(('.ofp', '.ops')):
            return 'oppo_ofp'
        elif 'payload.bin' in filename:
            return 'ab_ota'
        elif filename.endswith('.pac'):
            return 'spreadtrum_pac'
        elif filename.endswith('.nb0'):
            return 'qualcomm_nb0'
        elif filename == 'update.app':
            return 'huawei_update'
        elif 'super' in filename and filename.endswith('.img'):
            return 'super_image'
        elif filename.endswith('.sin'):
            return 'sony_sin'
        elif filename.endswith(('.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz')):
            return 'archive'
        else:
            return 'generic'
    
    def find_firmware_files(self, directory: Path) -> List[Path]:
        firmware_files = []
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and self._is_firmware_file(file_path):
                firmware_files.append(file_path)
        
        return firmware_files