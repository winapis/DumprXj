import re
from pathlib import Path
from typing import Optional, Dict, List
from lib.core.logger import logger
from lib.utils.filesystem import get_extension

class FirmwareDetector:
    def __init__(self):
        self.patterns = {
            'zip_archive': ['.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz', '.tar.md5'],
            'oppo_ozip': ['.ozip'],
            'oppo_ofp': ['.ofp'],
            'oppo_ops': ['.ops'],
            'lg_kdz': ['.kdz'],
            'htc_ruu': ['ruu_', '.exe'],
            'sony_ftf': ['.ftf'],
            'samsung_odin': ['.tar.md5', '.tar'],
            'huawei_update': ['update.app'],
            'xiaomi_fastboot': ['.tgz', '.tar.gz'],
            'android_sparse': ['.img'],
            'system_new_dat': ['system.new.dat', 'system.new.dat.br', 'system.new.dat.xz'],
            'system_img': ['system.img', 'system-sign.img'],
            'payload_bin': ['payload.bin'],
            'super_img': ['super.img'],
            'chunk_files': ['.chunk'],
            'pac_files': ['.pac'],
            'nb0_files': ['.nb0'],
            'sin_files': ['.sin'],
            'emmc_img': ['.emmc.img', '.img.ext4'],
            'system_bin': ['system.bin', 'system-p']
        }
    
    def detect_type(self, file_path: Path) -> Optional[str]:
        filename = file_path.name.lower()
        extension = get_extension(filename)
        
        for firmware_type, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.startswith('.') and filename.endswith(pattern):
                    return firmware_type
                elif not pattern.startswith('.') and pattern in filename:
                    return firmware_type
        
        if self._is_archive(file_path):
            return 'zip_archive'
        
        return None
    
    def _is_archive(self, file_path: Path) -> bool:
        try:
            import subprocess
            result = subprocess.run(['file', str(file_path)], capture_output=True, text=True)
            file_type = result.stdout.lower()
            
            archive_types = ['zip', 'rar', '7-zip', 'tar', 'gzip', 'bzip2']
            return any(arch_type in file_type for arch_type in archive_types)
        except:
            return False
    
    def get_extraction_strategy(self, firmware_type: str) -> Dict:
        strategies = {
            'zip_archive': {'extractor': 'archive', 'priority': 1},
            'oppo_ozip': {'extractor': 'ozip', 'priority': 2},
            'oppo_ofp': {'extractor': 'ofp', 'priority': 2},
            'oppo_ops': {'extractor': 'ops', 'priority': 2},
            'lg_kdz': {'extractor': 'kdz', 'priority': 2},
            'htc_ruu': {'extractor': 'ruu', 'priority': 2},
            'huawei_update': {'extractor': 'huawei', 'priority': 2},
            'payload_bin': {'extractor': 'payload', 'priority': 2},
            'system_new_dat': {'extractor': 'sdat2img', 'priority': 3},
            'super_img': {'extractor': 'super', 'priority': 3},
            'chunk_files': {'extractor': 'chunk', 'priority': 3},
            'pac_files': {'extractor': 'pac', 'priority': 2},
            'nb0_files': {'extractor': 'nb0', 'priority': 2},
            'sin_files': {'extractor': 'sin', 'priority': 2}
        }
        
        return strategies.get(firmware_type, {'extractor': 'generic', 'priority': 5})
    
    def analyze_directory(self, directory: Path) -> List[Dict]:
        found_firmware = []
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                firmware_type = self.detect_type(file_path)
                if firmware_type:
                    strategy = self.get_extraction_strategy(firmware_type)
                    found_firmware.append({
                        'path': file_path,
                        'type': firmware_type,
                        'extractor': strategy['extractor'],
                        'priority': strategy['priority']
                    })
        
        return sorted(found_firmware, key=lambda x: x['priority'])