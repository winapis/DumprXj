"""
Enhanced partition detection and management module.
"""

import struct
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..core.config import Config
from ..core.logger import get_logger


class PartitionManager:
    """Enhanced partition detection and management."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
    
    def analyze_partitions(self, firmware_dir: Path) -> Dict[str, Any]:
        """
        Analyze extracted firmware for partitions.
        
        Args:
            firmware_dir: Directory containing extracted firmware
            
        Returns:
            Dictionary with partition analysis results
        """
        self.logger.info("🔍 Analyzing partitions")
        
        result = {
            'partitions_found': [],
            'boot_images': [],
            'system_info': {},
            'vendor_info': {},
            'recovery_info': {},
            'analysis_complete': True
        }
        
        # Find partition files
        self._find_partition_files(firmware_dir, result)
        
        # Analyze boot images
        self._analyze_boot_images(firmware_dir, result)
        
        # Extract system information
        self._extract_system_info(firmware_dir, result)
        
        return result
    
    def _find_partition_files(self, firmware_dir: Path, result: Dict[str, Any]) -> None:
        """Find and categorize partition files."""
        partition_files = []
        
        # Look for partition files
        for partition in self.config.partitions:
            # Try different naming patterns
            patterns = [
                f"{partition}.img",
                f"{partition}.bin",
                f"{partition}_a.img",
                f"{partition}-verified.img",
                f"{partition}-sign.img"
            ]
            
            for pattern in patterns:
                files = list(firmware_dir.rglob(pattern))
                for file_path in files:
                    partition_info = {
                        'name': partition,
                        'file': str(file_path),
                        'size': file_path.stat().st_size,
                        'type': self._detect_partition_type(file_path)
                    }
                    partition_files.append(partition_info)
        
        result['partitions_found'] = partition_files
        self.logger.info(f"📦 Found {len(partition_files)} partition files")
    
    def _detect_partition_type(self, file_path: Path) -> str:
        """Detect the type of partition file."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                
                # Check for different filesystem signatures
                if header.startswith(b'\x00AID'):
                    return 'boot_image'
                elif header.startswith(b'ANDROID!'):
                    return 'boot_image'
                elif b'\x53\xef' in header[:1024]:  # ext4 magic
                    return 'ext4'
                elif header.startswith(b'EROFS'):
                    return 'erofs'
                elif header.startswith(b'hsqs'):  # squashfs
                    return 'squashfs'
                elif header.startswith(b'UBI#'):
                    return 'ubifs'
                elif header.startswith(b'\x3a\xff\x26\xed'):  # sparse image
                    return 'sparse'
                else:
                    return 'unknown'
        
        except Exception:
            return 'unknown'
    
    def _analyze_boot_images(self, firmware_dir: Path, result: Dict[str, Any]) -> None:
        """Analyze boot images for ramdisk versions and other info."""
        boot_patterns = ['boot.img', 'recovery.img', 'vendor_boot.img', 'init_boot.img']
        boot_images = []
        
        for pattern in boot_patterns:
            files = list(firmware_dir.rglob(pattern))
            for boot_file in files:
                boot_info = self._analyze_single_boot_image(boot_file)
                if boot_info:
                    boot_images.append(boot_info)
        
        result['boot_images'] = boot_images
        self.logger.info(f"🥾 Analyzed {len(boot_images)} boot images")
    
    def _analyze_single_boot_image(self, boot_file: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single boot image."""
        try:
            with open(boot_file, 'rb') as f:
                header = f.read(1648)  # Read full boot header
                
                if not header.startswith(b'ANDROID!'):
                    return None
                
                # Parse boot image header
                info = {
                    'file': str(boot_file),
                    'type': boot_file.stem,
                    'kernel_size': struct.unpack('<L', header[8:12])[0],
                    'kernel_addr': struct.unpack('<L', header[12:16])[0],
                    'ramdisk_size': struct.unpack('<L', header[16:20])[0],
                    'ramdisk_addr': struct.unpack('<L', header[20:24])[0],
                    'second_size': struct.unpack('<L', header[24:28])[0],
                    'second_addr': struct.unpack('<L', header[28:32])[0],
                    'tags_addr': struct.unpack('<L', header[32:36])[0],
                    'page_size': struct.unpack('<L', header[36:40])[0],
                    'header_version': struct.unpack('<L', header[40:44])[0],
                    'os_version': struct.unpack('<L', header[44:48])[0],
                    'name': header[48:64].rstrip(b'\x00').decode('ascii', errors='ignore'),
                    'cmdline': header[64:576].rstrip(b'\x00').decode('ascii', errors='ignore'),
                }
                
                # Determine ramdisk version based on header version
                info['ramdisk_version'] = self._get_ramdisk_version(info['header_version'])
                
                return info
        
        except Exception as e:
            self.logger.debug(f"Boot image analysis failed for {boot_file}: {e}")
            return None
    
    def _get_ramdisk_version(self, header_version: int) -> int:
        """Determine ramdisk version from header version."""
        if header_version >= 4:
            return 4
        elif header_version >= 3:
            return 3
        elif header_version >= 2:
            return 2
        else:
            return 1
    
    def _extract_system_info(self, firmware_dir: Path, result: Dict[str, Any]) -> None:
        """Extract system information from build.prop files."""
        build_prop_files = list(firmware_dir.rglob('build.prop'))
        
        system_info = {}
        vendor_info = {}
        
        for prop_file in build_prop_files:
            props = self._parse_build_prop(prop_file)
            
            if 'system' in str(prop_file):
                system_info.update(props)
            elif 'vendor' in str(prop_file):
                vendor_info.update(props)
            else:
                system_info.update(props)  # Default to system
        
        # Extract key information
        result['system_info'] = {
            'android_version': system_info.get('ro.build.version.release', 'Unknown'),
            'api_level': system_info.get('ro.build.version.sdk', 'Unknown'),
            'security_patch': system_info.get('ro.build.version.security_patch', 'Unknown'),
            'build_id': system_info.get('ro.build.id', 'Unknown'),
            'fingerprint': system_info.get('ro.build.fingerprint', 'Unknown'),
            'product': system_info.get('ro.product.name', 'Unknown'),
            'device': system_info.get('ro.product.device', 'Unknown'),
            'brand': system_info.get('ro.product.brand', 'Unknown'),
            'manufacturer': system_info.get('ro.product.manufacturer', 'Unknown'),
            'model': system_info.get('ro.product.model', 'Unknown'),
        }
        
        result['vendor_info'] = {
            'fingerprint': vendor_info.get('ro.vendor.build.fingerprint', 'Unknown'),
            'security_patch': vendor_info.get('ro.vendor.build.security_patch', 'Unknown'),
        }
        
        self.logger.info(f"📱 Device: {result['system_info']['brand']} {result['system_info']['model']}")
        self.logger.info(f"🤖 Android: {result['system_info']['android_version']} (API {result['system_info']['api_level']})")
    
    def _parse_build_prop(self, prop_file: Path) -> Dict[str, str]:
        """Parse a build.prop file."""
        props = {}
        
        try:
            with open(prop_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        props[key.strip()] = value.strip()
        
        except Exception as e:
            self.logger.debug(f"Failed to parse {prop_file}: {e}")
        
        return props