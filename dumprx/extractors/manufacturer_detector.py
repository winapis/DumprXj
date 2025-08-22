"""
Manufacturer-specific firmware detection and extraction
Supports 12+ manufacturers with intelligent auto-detection
"""

import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ManufacturerInfo:
    """Information about detected manufacturer and device"""
    name: str
    model: str = ""
    android_version: str = ""
    build_id: str = ""
    region: str = ""
    carrier: str = ""
    firmware_type: str = ""
    extraction_method: str = ""

class ManufacturerDetector:
    """Intelligent manufacturer detection with specialized extraction methods"""
    
    MANUFACTURERS = {
        'samsung': {
            'patterns': [r'SM-[A-Z]\d+', r'Galaxy', r'Samsung', r'SAMSUNG'],
            'file_types': ['.tar.md5', '.tar', '.pit'],
            'indicators': ['AP_', 'BL_', 'CP_', 'CSC_', 'HOME_CSC_', 'USERDATA_']
        },
        'xiaomi': {
            'patterns': [r'xiaomi', r'redmi', r'poco', r'mi\d+', r'MIUI'],
            'file_types': ['.tgz', '.zip', '.fastboot'],
            'indicators': ['miui', 'xiaomi', 'redmi', 'poco', 'global_images', 'china_images']
        },
        'oppo': {
            'patterns': [r'OPPO', r'CPH\d+', r'PCLM\d+', r'PDCM\d+'],
            'file_types': ['.ozip', '.ofp', '.ops'],
            'indicators': ['ColorOS', 'OPPO', 'ozip', 'ofp']
        },
        'oneplus': {
            'patterns': [r'OnePlus', r'OP\d+', r'AC\d+', r'HD\d+', r'KB\d+', r'LE\d+'],
            'file_types': ['.ops', '.zip', '.ozip'],
            'indicators': ['OnePlus', 'OxygenOS', 'HydrogenOS', 'ops']
        },
        'huawei': {
            'patterns': [r'HUAWEI', r'HONOR', r'HW\d+', r'H\d+', r'P\d+', r'Mate'],
            'file_types': ['.app', '.zip'],
            'indicators': ['UPDATE.APP', 'EMUI', 'Magic UI', 'HarmonyOS']
        },
        'lg': {
            'patterns': [r'LG-', r'LM-', r'VS\d+', r'H\d+'],
            'file_types': ['.kdz', '.dz', '.tot'],
            'indicators': ['LG', 'WebOS', 'kdz', 'dz']
        },
        'htc': {
            'patterns': [r'HTC', r'Desire', r'One', r'U\d+'],
            'file_types': ['.exe', '.zip'],
            'indicators': ['RUU_', 'HTC', 'Sense']
        },
        'sony': {
            'patterns': [r'Sony', r'Xperia', r'C\d+', r'E\d+', r'F\d+', r'G\d+', r'H\d+', r'I\d+', r'J\d+', r'L\d+', r'M\d+', r'SGP\d+', r'SO-\d+', r'SOV\d+'],
            'file_types': ['.ftf', '.sin', '.ta'],
            'indicators': ['Sony', 'Xperia', '.sin', '.ftf']
        },
        'motorola': {
            'patterns': [r'Motorola', r'Moto', r'XT\d+', r'MB\d+'],
            'file_types': ['.xml.zip', '.zip'],
            'indicators': ['Motorola', 'Moto', 'servicefile.xml']
        },
        'asus': {
            'patterns': [r'ASUS', r'ZenFone', r'ROG', r'ZS\d+', r'ZE\d+'],
            'file_types': ['.zip', '.raw'],
            'indicators': ['ASUS', 'ZenUI', 'ROG']
        },
        'realme': {
            'patterns': [r'realme', r'RMX\d+', r'RealmeUI'],
            'file_types': ['.ozip', '.zip'],
            'indicators': ['realme', 'RealmeUI', 'ColorOS']
        },
        'vivo': {
            'patterns': [r'vivo', r'V\d+', r'Y\d+', r'X\d+', r'iQOO'],
            'file_types': ['.zip', '.qsb'],
            'indicators': ['vivo', 'Funtouch', 'iQOO', 'OriginOS']
        }
    }

    def __init__(self, config):
        self.config = config
        
    def detect_manufacturer(self, firmware_path: Path) -> Optional[ManufacturerInfo]:
        """Detect manufacturer from firmware file/folder"""
        
        # Check filename patterns
        filename = firmware_path.name.lower()
        
        for manufacturer, info in self.MANUFACTURERS.items():
            # Check filename patterns
            for pattern in info['patterns']:
                if re.search(pattern, filename, re.IGNORECASE):
                    return self._build_manufacturer_info(manufacturer, firmware_path, info)
            
            # Check file extensions
            if firmware_path.suffix.lower() in info['file_types']:
                # Verify with content analysis
                if self._verify_manufacturer_content(firmware_path, manufacturer, info):
                    return self._build_manufacturer_info(manufacturer, firmware_path, info)
        
        # If no direct match, analyze content
        return self._analyze_firmware_content(firmware_path)
    
    def _build_manufacturer_info(self, manufacturer: str, firmware_path: Path, info: Dict) -> ManufacturerInfo:
        """Build manufacturer info object"""
        
        # Determine extraction method based on manufacturer
        extraction_method = self._get_extraction_method(manufacturer, firmware_path)
        firmware_type = self._determine_firmware_type(manufacturer, firmware_path)
        
        # Try to extract additional info from filename
        model, version, build_id = self._parse_filename_info(firmware_path.name, manufacturer)
        
        return ManufacturerInfo(
            name=manufacturer,
            model=model,
            android_version=version,
            build_id=build_id,
            firmware_type=firmware_type,
            extraction_method=extraction_method
        )
    
    def _get_extraction_method(self, manufacturer: str, firmware_path: Path) -> str:
        """Determine extraction method for manufacturer"""
        
        methods = {
            'samsung': 'tar_extraction',
            'xiaomi': 'fastboot_extraction' if 'fastboot' in firmware_path.name.lower() else 'miui_extraction',
            'oppo': 'ozip_decryption' if firmware_path.suffix == '.ozip' else 'ofp_extraction',
            'oneplus': 'ops_decryption' if firmware_path.suffix == '.ops' else 'ozip_decryption',
            'huawei': 'update_app_extraction',
            'lg': 'kdz_extraction' if firmware_path.suffix == '.kdz' else 'dz_extraction',
            'htc': 'ruu_decryption',
            'sony': 'ftf_extraction' if firmware_path.suffix == '.ftf' else 'sin_extraction',
            'motorola': 'xml_zip_extraction',
            'asus': 'raw_extraction' if firmware_path.suffix == '.raw' else 'zip_extraction',
            'realme': 'ozip_decryption' if firmware_path.suffix == '.ozip' else 'zip_extraction',
            'vivo': 'qsb_extraction' if firmware_path.suffix == '.qsb' else 'zip_extraction'
        }
        
        return methods.get(manufacturer, 'generic_extraction')
    
    def _determine_firmware_type(self, manufacturer: str, firmware_path: Path) -> str:
        """Determine firmware type based on manufacturer and file"""
        
        filename = firmware_path.name.lower()
        
        if manufacturer == 'samsung':
            if 'ap_' in filename:
                return 'AP (Android Partition)'
            elif 'bl_' in filename:
                return 'BL (Bootloader)'
            elif 'cp_' in filename:
                return 'CP (Modem)'
            elif 'csc_' in filename:
                return 'CSC (Country Specific Code)'
            else:
                return 'Samsung TAR Package'
        
        elif manufacturer == 'xiaomi':
            if 'global' in filename:
                return 'MIUI Global ROM'
            elif 'china' in filename:
                return 'MIUI China ROM'
            elif 'fastboot' in filename:
                return 'Fastboot ROM'
            else:
                return 'MIUI ROM'
        
        elif manufacturer in ['oppo', 'oneplus']:
            if firmware_path.suffix == '.ozip':
                return 'OZIP Encrypted Package'
            elif firmware_path.suffix == '.ofp':
                return 'OFP Package'
            elif firmware_path.suffix == '.ops':
                return 'OPS Package'
            else:
                return 'ColorOS/OxygenOS Package'
        
        elif manufacturer == 'huawei':
            return 'UPDATE.APP Package'
        
        elif manufacturer == 'lg':
            if firmware_path.suffix == '.kdz':
                return 'KDZ Package'
            elif firmware_path.suffix == '.dz':
                return 'DZ Package'
            else:
                return 'LG Package'
        
        elif manufacturer == 'htc':
            return 'RUU Package'
        
        elif manufacturer == 'sony':
            if firmware_path.suffix == '.ftf':
                return 'FTF Package'
            else:
                return 'Sony Package'
        
        else:
            return 'Android Firmware'
    
    def _parse_filename_info(self, filename: str, manufacturer: str) -> Tuple[str, str, str]:
        """Parse model, version, and build info from filename"""
        
        model = ""
        version = ""
        build_id = ""
        
        if manufacturer == 'samsung':
            # Example: SM-G950F_10_QP1A.190711.020_G950FXXU9DTB5_fac.tar.md5
            model_match = re.search(r'(SM-[A-Z]\d+[A-Z]*)', filename, re.IGNORECASE)
            if model_match:
                model = model_match.group(1)
            
            version_match = re.search(r'_(\d+)_', filename)
            if version_match:
                version = f"Android {version_match.group(1)}"
            
            build_match = re.search(r'([A-Z]\d+[A-Z]+\d+[A-Z]+\d+)', filename, re.IGNORECASE)
            if build_match:
                build_id = build_match.group(1)
        
        elif manufacturer == 'xiaomi':
            # Example: miui_MI9_V12.0.1.0.QFAMIXM_eea_10.zip
            model_match = re.search(r'miui_([A-Z0-9]+)_', filename, re.IGNORECASE)
            if model_match:
                model = model_match.group(1)
            
            version_match = re.search(r'V(\d+\.\d+\.\d+\.\d+)', filename, re.IGNORECASE)
            if version_match:
                version = f"MIUI {version_match.group(1)}"
            
            android_match = re.search(r'_(\d+)\.zip', filename)
            if android_match:
                version += f" (Android {android_match.group(1)})"
        
        elif manufacturer in ['oppo', 'oneplus']:
            # Example: CPH1941EX_11_C.14_200320.ofp
            model_match = re.search(r'([A-Z]+\d+[A-Z]*)', filename, re.IGNORECASE)
            if model_match:
                model = model_match.group(1)
            
            version_match = re.search(r'_(\d+)_', filename)
            if version_match:
                version = f"Android {version_match.group(1)}"
        
        # Add more manufacturer-specific parsing as needed
        
        return model, version, build_id
    
    def _verify_manufacturer_content(self, firmware_path: Path, manufacturer: str, info: Dict) -> bool:
        """Verify manufacturer by analyzing firmware content"""
        
        try:
            if firmware_path.is_file():
                # For archive files, check contents
                if firmware_path.suffix.lower() in ['.zip', '.tar', '.7z', '.rar']:
                    result = subprocess.run(
                        ['7zz', 'l', str(firmware_path)],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if result.returncode == 0:
                        content = result.stdout.lower()
                        for indicator in info['indicators']:
                            if indicator.lower() in content:
                                return True
                
                # For specific file types, check file signature or content
                elif manufacturer == 'lg' and firmware_path.suffix == '.kdz':
                    # Check KDZ file signature
                    with open(firmware_path, 'rb') as f:
                        header = f.read(16)
                        return b'kdz' in header.lower()
                
                elif manufacturer == 'sony' and firmware_path.suffix == '.ftf':
                    # Check FTF file signature
                    with open(firmware_path, 'rb') as f:
                        header = f.read(32)
                        return b'sony' in header.lower() or b'xperia' in header.lower()
            
            elif firmware_path.is_dir():
                # For directories, check for specific files or structure
                for indicator in info['indicators']:
                    if any(indicator.lower() in f.name.lower() for f in firmware_path.rglob('*')):
                        return True
        
        except Exception as e:
            logger.debug(f"Error verifying manufacturer content: {e}")
        
        return False
    
    def _analyze_firmware_content(self, firmware_path: Path) -> Optional[ManufacturerInfo]:
        """Deep content analysis when direct detection fails"""
        
        try:
            if firmware_path.is_file() and firmware_path.suffix.lower() in ['.zip', '.tar', '.7z', '.rar']:
                # Extract file list and analyze
                result = subprocess.run(
                    ['7zz', 'l', str(firmware_path)],
                    capture_output=True, text=True, timeout=15
                )
                
                if result.returncode == 0:
                    content = result.stdout.lower()
                    
                    # Check for manufacturer-specific files/patterns
                    if 'update.app' in content:
                        return ManufacturerInfo(name='huawei', firmware_type='UPDATE.APP Package', extraction_method='update_app_extraction')
                    elif 'payload.bin' in content:
                        return ManufacturerInfo(name='google', firmware_type='OTA Package', extraction_method='payload_extraction')
                    elif 'super.img' in content:
                        return ManufacturerInfo(name='generic', firmware_type='Super Partition', extraction_method='super_extraction')
                    elif any(x in content for x in ['boot.img', 'system.img', 'vendor.img']):
                        return ManufacturerInfo(name='generic', firmware_type='Fastboot Images', extraction_method='fastboot_extraction')
                    elif '.sin' in content:
                        return ManufacturerInfo(name='sony', firmware_type='Sony Package', extraction_method='sin_extraction')
            
            elif firmware_path.is_dir():
                # Analyze directory structure
                files = [f.name.lower() for f in firmware_path.rglob('*') if f.is_file()]
                
                if 'update.app' in files:
                    return ManufacturerInfo(name='huawei', firmware_type='UPDATE.APP Package', extraction_method='update_app_extraction')
                elif any('.sin' in f for f in files):
                    return ManufacturerInfo(name='sony', firmware_type='Sony Package', extraction_method='sin_extraction')
                elif 'payload.bin' in files:
                    return ManufacturerInfo(name='google', firmware_type='OTA Package', extraction_method='payload_extraction')
        
        except Exception as e:
            logger.debug(f"Error analyzing firmware content: {e}")
        
        return None
    
    def get_extraction_tools(self, manufacturer_info: ManufacturerInfo) -> List[str]:
        """Get required tools for specific manufacturer extraction"""
        
        tool_map = {
            'tar_extraction': ['tar', '7zz'],
            'fastboot_extraction': ['fastboot', '7zz'],
            'miui_extraction': ['7zz', 'simg2img'],
            'ozip_decryption': ['python3', 'ozipdecrypt.py'],
            'ofp_extraction': ['python3', 'ofp_qc_extract.py', 'ofp_mtk_decrypt.py'],
            'ops_decryption': ['python3', 'opscrypto.py'],
            'update_app_extraction': ['python3', 'splituapp.py'],
            'kdz_extraction': ['python3', 'unkdz.py'],
            'dz_extraction': ['python3', 'undz.py'],
            'ruu_decryption': ['RUU_Decrypt_Tool'],
            'ftf_extraction': ['7zz'],
            'sin_extraction': ['unsin'],
            'xml_zip_extraction': ['7zz'],
            'raw_extraction': ['dd', 'simg2img'],
            'qsb_extraction': ['7zz'],
            'payload_extraction': ['python3', 'extract_android_ota_payload.py'],
            'super_extraction': ['lpunpack', 'simg2img'],
            'generic_extraction': ['7zz', 'simg2img']
        }
        
        return tool_map.get(manufacturer_info.extraction_method, ['7zz'])