"""
Extraction manager for various firmware types
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import zipfile
import rarfile
import py7zr
import tarfile

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole
from dumprx.extractors.archive import ArchiveExtractor
from dumprx.extractors.firmware import FirmwareExtractor
from dumprx.extractors.image import ImageExtractor


class ExtractionManager:
    """Manages firmware extraction for various types"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        
        # Initialize extractors
        self.archive_extractor = ArchiveExtractor(config, console)
        self.firmware_extractor = FirmwareExtractor(config, console)
        self.image_extractor = ImageExtractor(config, console)
        
    def detect_firmware_type(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Detect firmware type based on file
        
        Args:
            file_path: Path to firmware file
            
        Returns:
            Dictionary with firmware info or None if unsupported
        """
        try:
            if not file_path.exists():
                return None
                
            # Check if it's a directory
            if file_path.is_dir():
                return self._detect_directory_type(file_path)
                
            # Check file extension
            extension = file_path.suffix.lower()
            filename = file_path.name.lower()
            
            # Check for specific firmware patterns
            if filename.startswith('ruu_') and filename.endswith('.exe'):
                return {'type': 'ruu', 'format': '.exe', 'extractor': 'firmware', 'manufacturer': 'htc'}
                
            if extension in self.config.extraction.supported_formats['archives']:
                return {'type': 'archive', 'format': extension, 'extractor': 'archive'}
            elif extension in self.config.extraction.supported_formats['firmware']:
                return self._detect_firmware_specific(file_path, extension)
            elif extension in self.config.extraction.supported_formats['images']:
                return self._detect_image_type(file_path, extension)
            
            # Check file content for specific signatures
            with open(file_path, 'rb') as f:
                header = f.read(16)
                
            # Check for various signatures
            if header.startswith(b'OPPOENCRYPT!'):
                return {'type': 'ozip', 'format': '.ozip', 'extractor': 'firmware', 'manufacturer': 'oppo'}
            elif header.startswith(b'PK'):
                return {'type': 'archive', 'format': '.zip', 'extractor': 'archive'}
            elif header.startswith(b'\x1f\x8b'):
                return {'type': 'gzip', 'format': '.gz', 'extractor': 'archive'}
            elif header.startswith(b'7z\xbc\xaf\x27\x1c'):
                return {'type': 'archive', 'format': '.7z', 'extractor': 'archive'}
            elif header.startswith(b'Rar!'):
                return {'type': 'archive', 'format': '.rar', 'extractor': 'archive'}
                
            # Check for Android-specific formats
            if self._check_android_image(file_path):
                return {'type': 'android_image', 'format': extension, 'extractor': 'image'}
                
            return None
            
        except Exception as e:
            self.console.error(f"Error detecting firmware type: {e}")
            return None
            
    def extract_firmware(self, file_path: Path, firmware_info: Dict[str, Any], 
                        force: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract firmware based on detected type
        
        Args:
            file_path: Path to firmware file
            firmware_info: Firmware information from detection
            force: Force extraction even if output exists
            
        Returns:
            Dictionary with extraction results or None if failed
        """
        try:
            extractor_type = firmware_info.get('extractor')
            
            # Prepare output directory
            output_dir = self.config.get_output_dir()
            temp_dir = self.config.get_temp_dir()
            
            # Clear temp directory if it exists
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            self.console.step(f"Extracting {firmware_info['type']} firmware...")
            
            if extractor_type == 'archive':
                result = self.archive_extractor.extract(file_path, temp_dir, firmware_info)
            elif extractor_type == 'firmware':
                result = self.firmware_extractor.extract(file_path, temp_dir, firmware_info)
            elif extractor_type == 'image':
                result = self.image_extractor.extract(file_path, temp_dir, firmware_info)
            else:
                self.console.error(f"Unknown extractor type: {extractor_type}")
                return None
                
            if not result:
                return None
                
            # Post-process extracted files
            extracted_info = self._analyze_extracted_files(temp_dir)
            
            # Copy to final output directory
            final_output = output_dir / extracted_info.get('device_name', 'unknown_device')
            if final_output.exists() and not force:
                self.console.warning(f"Output directory already exists: {final_output}")
                self.console.step("Use --force to overwrite")
                return None
                
            if final_output.exists():
                shutil.rmtree(final_output)
                
            shutil.copytree(temp_dir, final_output)
            
            return {
                'success': True,
                'output_dir': final_output,
                'temp_dir': temp_dir,
                'info': extracted_info
            }
                
        except Exception as e:
            self.console.error(f"Error during extraction: {e}")
            return None
            
    def _detect_directory_type(self, dir_path: Path) -> Optional[Dict[str, Any]]:
        """Detect firmware type from directory contents"""
        # Check for common firmware files in directory
        files = list(dir_path.glob('*'))
        
        for file in files:
            if file.is_file():
                file_info = self.detect_firmware_type(file)
                if file_info:
                    file_info['source_type'] = 'directory'
                    return file_info
                    
        # Check for extracted firmware patterns
        if any(f.name in ['system.new.dat', 'system.img', 'boot.img'] for f in files):
            return {'type': 'extracted_firmware', 'format': 'directory', 'extractor': 'image'}
            
        return None
        
    def _detect_firmware_specific(self, file_path: Path, extension: str) -> Dict[str, Any]:
        """Detect specific firmware types"""
        if extension == '.ozip':
            return {'type': 'ozip', 'format': extension, 'extractor': 'firmware', 'manufacturer': 'oppo'}
        elif extension == '.ofp':
            return {'type': 'ofp', 'format': extension, 'extractor': 'firmware', 'manufacturer': 'oppo'}
        elif extension == '.ops':
            return {'type': 'ops', 'format': extension, 'extractor': 'firmware', 'manufacturer': 'oppo'}
        elif extension == '.kdz':
            return {'type': 'kdz', 'format': extension, 'extractor': 'firmware', 'manufacturer': 'lg'}
        elif extension == '.nb0':
            return {'type': 'nb0', 'format': extension, 'extractor': 'firmware', 'manufacturer': 'nokia'}
        elif extension == '.pac':
            return {'type': 'pac', 'format': extension, 'extractor': 'firmware', 'manufacturer': 'spreadtrum'}
        else:
            return {'type': 'firmware', 'format': extension, 'extractor': 'firmware'}
            
    def _detect_image_type(self, file_path: Path, extension: str) -> Dict[str, Any]:
        """Detect image types"""
        filename = file_path.name.lower()
        
        if 'system' in filename:
            return {'type': 'system_image', 'format': extension, 'extractor': 'image'}
        elif 'boot' in filename:
            return {'type': 'boot_image', 'format': extension, 'extractor': 'image'}
        elif 'recovery' in filename:
            return {'type': 'recovery_image', 'format': extension, 'extractor': 'image'}
        elif 'super' in filename:
            return {'type': 'super_image', 'format': extension, 'extractor': 'image'}
        else:
            return {'type': 'image', 'format': extension, 'extractor': 'image'}
            
    def _check_android_image(self, file_path: Path) -> bool:
        """Check if file is an Android image"""
        try:
            with open(file_path, 'rb') as f:
                # Check for Android boot image magic
                magic = f.read(8)
                if magic == b'ANDROID!':
                    return True
                    
                # Check for sparse image magic
                f.seek(0)
                sparse_magic = f.read(4)
                if sparse_magic == b'\x3a\xff\x26\xed':
                    return True
                    
            return False
        except Exception:
            return False
            
    def _analyze_extracted_files(self, extraction_dir: Path) -> Dict[str, Any]:
        """Analyze extracted files to get device information"""
        info = {
            'device_name': 'unknown_device',
            'brand': 'unknown',
            'model': 'unknown',
            'android_version': 'unknown',
            'build_fingerprint': 'unknown',
            'partitions': []
        }
        
        try:
            # Look for build.prop files
            build_props = []
            for prop_file in extraction_dir.rglob('build.prop'):
                build_props.append(prop_file)
                
            if build_props:
                # Parse first build.prop found
                info.update(self._parse_build_prop(build_props[0]))
                
            # Count partitions
            partition_files = []
            for partition in self.config.extraction.partitions:
                partition_files.extend(list(extraction_dir.rglob(f'{partition}.*')))
                
            info['partitions'] = [f.name for f in partition_files]
            
        except Exception as e:
            self.console.debug(f"Error analyzing extracted files: {e}")
            
        return info
        
    def _parse_build_prop(self, build_prop_path: Path) -> Dict[str, str]:
        """Parse build.prop file for device information"""
        info = {}
        
        try:
            with open(build_prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        
                        if key == 'ro.product.brand':
                            info['brand'] = value
                        elif key == 'ro.product.model':
                            info['model'] = value
                        elif key == 'ro.product.device':
                            info['device_name'] = value
                        elif key == 'ro.build.version.release':
                            info['android_version'] = value
                        elif key == 'ro.build.fingerprint':
                            info['build_fingerprint'] = value
                            
        except Exception:
            pass
            
        return info