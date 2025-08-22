#!/usr/bin/env python3

import re
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse

from dumprx import UTILS_DIR
from dumprx.console import info, warning, error, step


class FirmwareDetector:
    
    SUPPORTED_EXTENSIONS = {
        '.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.bz2', '.xz',
        '.ozip', '.ofp', '.ops', '.kdz', '.dz', '.exe', '.bin',
        '.img', '.ext4', '.pac', '.nb0', '.sin', '.chunk'
    }
    
    MANUFACTURER_PATTERNS = {
        'oppo': [
            re.compile(r'.*OPPOENCRYPT.*', re.IGNORECASE),
            re.compile(r'.*\.ozip$', re.IGNORECASE),
            re.compile(r'.*\.ofp$', re.IGNORECASE),
            re.compile(r'.*\.ops$', re.IGNORECASE),
        ],
        'lg': [
            re.compile(r'.*\.kdz$', re.IGNORECASE),
            re.compile(r'.*\.dz$', re.IGNORECASE),
        ],
        'htc': [
            re.compile(r'ruu_.*\.exe$', re.IGNORECASE),
        ],
        'huawei': [
            re.compile(r'UPDATE\.APP$', re.IGNORECASE),
        ],
        'sony': [
            re.compile(r'.*\.sin$', re.IGNORECASE),
        ],
        'qcom': [
            re.compile(r'.*rawprogram.*', re.IGNORECASE),
            re.compile(r'.*patch.*', re.IGNORECASE),
        ],
        'android': [
            re.compile(r'payload\.bin$', re.IGNORECASE),
            re.compile(r'system\.new\.dat$', re.IGNORECASE),
            re.compile(r'system\.img$', re.IGNORECASE),
            re.compile(r'super\.img$', re.IGNORECASE),
        ]
    }
    
    URL_PATTERNS = {
        'mega': [
            re.compile(r'mega\.nz', re.IGNORECASE),
            re.compile(r'mega\.co\.nz', re.IGNORECASE),
        ],
        'mediafire': [
            re.compile(r'mediafire\.com', re.IGNORECASE),
        ],
        'gdrive': [
            re.compile(r'drive\.google\.com', re.IGNORECASE),
            re.compile(r'docs\.google\.com', re.IGNORECASE),
        ],
        'onedrive': [
            re.compile(r'onedrive\.live\.com', re.IGNORECASE),
            re.compile(r'1drv\.ms', re.IGNORECASE),
        ],
        'afh': [
            re.compile(r'androidfilehost\.com', re.IGNORECASE),
        ],
        'direct': [
            re.compile(r'.*\.(zip|rar|7z|tar|gz|tgz|bz2|xz|ozip|ofp|ops|kdz|dz|exe|bin|img|ext4|pac|nb0|sin)$', re.IGNORECASE),
        ]
    }
    
    @classmethod
    def detect_input_type(cls, input_path: str) -> Dict[str, str]:
        if cls.is_url(input_path):
            return cls.detect_url_type(input_path)
        elif Path(input_path).is_file():
            return cls.detect_file_type(input_path)
        elif Path(input_path).is_dir():
            return {'type': 'directory', 'format': 'extracted'}
        else:
            return {'type': 'unknown', 'format': 'unknown'}
    
    @classmethod
    def is_url(cls, input_str: str) -> bool:
        try:
            result = urlparse(input_str)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @classmethod
    def detect_url_type(cls, url: str) -> Dict[str, str]:
        for service, patterns in cls.URL_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(url):
                    return {'type': 'url', 'service': service, 'url': url}
        return {'type': 'url', 'service': 'unknown', 'url': url}
    
    @classmethod
    def detect_file_type(cls, file_path: str) -> Dict[str, str]:
        path = Path(file_path)
        
        if not path.exists():
            return {'type': 'file', 'format': 'not_found'}
        
        file_ext = path.suffix.lower()
        file_name = path.name.lower()
        
        if file_ext not in cls.SUPPORTED_EXTENSIONS:
            return {'type': 'file', 'format': 'unsupported'}
        
        manufacturer = cls.detect_manufacturer(file_path)
        firmware_format = cls.detect_firmware_format(file_path)
        
        return {
            'type': 'file',
            'format': firmware_format,
            'manufacturer': manufacturer,
            'extension': file_ext,
            'path': str(path.absolute())
        }
    
    @classmethod
    def detect_manufacturer(cls, file_path: str) -> str:
        path = Path(file_path)
        file_name = path.name.lower()
        
        if path.exists():
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(32)
                    if b'OPPOENCRYPT' in header:
                        return 'oppo'
            except:
                pass
        
        for manufacturer, patterns in cls.MANUFACTURER_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(file_name):
                    return manufacturer
        
        return 'generic'
    
    @classmethod
    def detect_firmware_format(cls, file_path: str) -> str:
        path = Path(file_path)
        file_name = path.name.lower()
        file_ext = path.suffix.lower()
        
        if file_ext == '.kdz':
            return 'lg_kdz'
        elif file_ext == '.dz':
            return 'lg_dz'
        elif file_ext == '.ozip':
            return 'oppo_ozip'
        elif file_ext == '.ofp':
            return 'oppo_ofp'
        elif file_ext == '.ops':
            return 'oppo_ops'
        elif 'ruu_' in file_name and file_ext == '.exe':
            return 'htc_ruu'
        elif file_name == 'update.app':
            return 'huawei_update'
        elif file_ext == '.sin':
            return 'sony_sin'
        elif file_name == 'payload.bin':
            return 'android_ota'
        elif 'system.new.dat' in file_name:
            return 'android_sdat'
        elif 'super' in file_name and file_ext == '.img':
            return 'android_super'
        elif file_ext in ['.zip', '.rar', '.7z', '.tar']:
            return 'archive'
        elif file_ext == '.img':
            return 'android_img'
        elif file_ext == '.bin':
            return 'generic_bin'
        else:
            return 'unknown'
    
    @classmethod
    def get_extraction_strategy(cls, detection_result: Dict[str, str]) -> Dict[str, str]:
        format_type = detection_result.get('format', 'unknown')
        manufacturer = detection_result.get('manufacturer', 'generic')
        
        strategies = {
            'lg_kdz': {'tool': 'kdz_extract', 'module': 'lg_extractor'},
            'lg_dz': {'tool': 'dz_extract', 'module': 'lg_extractor'},
            'oppo_ozip': {'tool': 'ozip_decrypt', 'module': 'oppo_extractor'},
            'oppo_ofp': {'tool': 'ofp_decrypt', 'module': 'oppo_extractor'},
            'oppo_ops': {'tool': 'ops_decrypt', 'module': 'oppo_extractor'},
            'htc_ruu': {'tool': 'ruu_decrypt', 'module': 'htc_extractor'},
            'huawei_update': {'tool': 'splituapp', 'module': 'huawei_extractor'},
            'sony_sin': {'tool': 'unsin', 'module': 'sony_extractor'},
            'android_ota': {'tool': 'payload_dumper', 'module': 'android_extractor'},
            'android_sdat': {'tool': 'sdat2img', 'module': 'android_extractor'},
            'android_super': {'tool': 'lpunpack', 'module': 'android_extractor'},
            'archive': {'tool': '7zip', 'module': 'archive_extractor'},
            'android_img': {'tool': 'simg2img', 'module': 'android_extractor'},
        }
        
        return strategies.get(format_type, {'tool': 'unknown', 'module': 'generic_extractor'})