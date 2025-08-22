import os
import re
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class DeviceDetector:
    """Auto-detect device configuration and properties from firmware"""
    
    def __init__(self, config):
        self.config = config
        self.device_info = {}
    
    def detect_device_config(self, extracted_dir: Path) -> Dict[str, str]:
        """Auto-detect device configuration from extracted firmware"""
        device_info = {}
        
        # Look for build.prop files
        build_props = self._find_build_props(extracted_dir)
        
        if build_props:
            device_info.update(self._parse_build_props(build_props))
        
        # Look for kernel config
        kernel_config = self._find_kernel_config(extracted_dir)
        if kernel_config:
            device_info.update(self._parse_kernel_config(kernel_config))
        
        # Auto-detect other properties
        device_info.update(self._detect_additional_props(extracted_dir))
        
        self.device_info = device_info
        return device_info
    
    def _find_build_props(self, base_dir: Path) -> List[Path]:
        """Find all build.prop files"""
        build_props = []
        
        search_paths = [
            "system/build.prop",
            "system/system/build.prop", 
            "vendor/build.prop",
            "product/build.prop",
            "odm/build.prop",
            "oem/build.prop"
        ]
        
        for search_path in search_paths:
            prop_file = base_dir / search_path
            if prop_file.exists():
                build_props.append(prop_file)
        
        # Also search recursively for build*.prop
        for prop_file in base_dir.rglob("build*.prop"):
            if prop_file not in build_props:
                build_props.append(prop_file)
        
        return build_props
    
    def _parse_build_props(self, build_props: List[Path]) -> Dict[str, str]:
        """Parse build.prop files to extract device info"""
        device_info = {}
        
        # Properties we're interested in
        interesting_props = {
            'ro.product.model': 'model',
            'ro.product.name': 'name', 
            'ro.product.device': 'device',
            'ro.product.brand': 'brand',
            'ro.product.manufacturer': 'manufacturer',
            'ro.build.version.release': 'android_version',
            'ro.build.version.sdk': 'api_level',
            'ro.build.id': 'build_id',
            'ro.build.display.id': 'display_id',
            'ro.build.version.incremental': 'incremental',
            'ro.build.date': 'build_date',
            'ro.build.fingerprint': 'fingerprint',
            'ro.build.description': 'description',
            'ro.product.locale': 'locale',
            'ro.sf.lcd_density': 'density',
            'ro.product.cpu.abilist': 'abilist',
            'ro.vendor.product.cpu.abilist': 'vendor_abilist',
            'ro.build.tags': 'tags',
            'ro.build.flavor': 'flavor'
        }
        
        for prop_file in build_props:
            try:
                with open(prop_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key in interesting_props:
                                device_info[interesting_props[key]] = value
            except Exception as e:
                logger.debug(f"Error parsing {prop_file}: {e}")
        
        # Generate additional derived properties
        self._generate_derived_properties(device_info)
        
        return device_info
    
    def _generate_derived_properties(self, device_info: Dict[str, str]):
        """Generate derived properties from basic device info"""
        
        # Generate codename from device name
        if 'device' in device_info and 'codename' not in device_info:
            device_info['codename'] = device_info['device']
        
        # Generate description if missing
        if 'description' not in device_info:
            parts = []
            for key in ['flavor', 'android_version', 'build_id', 'incremental', 'tags']:
                if key in device_info and device_info[key]:
                    parts.append(device_info[key])
            
            if parts:
                device_info['description'] = ' '.join(parts)
            elif 'codename' in device_info:
                device_info['description'] = device_info['codename']
        
        # Set locale default
        if 'locale' not in device_info or not device_info['locale']:
            device_info['locale'] = 'undefined'
        
        # Set density default  
        if 'density' not in device_info or not device_info['density']:
            device_info['density'] = 'undefined'
        
        # Use vendor abilist if main one is missing
        if 'abilist' not in device_info and 'vendor_abilist' in device_info:
            device_info['abilist'] = device_info['vendor_abilist']
    
    def _find_kernel_config(self, base_dir: Path) -> Optional[Path]:
        """Find kernel configuration"""
        # Look for ikconfig in boot image extraction
        boot_dirs = list(base_dir.glob("**/bootRE"))
        for boot_dir in boot_dirs:
            ikconfig = boot_dir / "ikconfig"
            if ikconfig.exists():
                return ikconfig
        
        # Look for other kernel config files
        for config_file in base_dir.rglob("*config*"):
            if config_file.is_file() and "kernel" in config_file.name.lower():
                return config_file
        
        return None
    
    def _parse_kernel_config(self, config_file: Path) -> Dict[str, str]:
        """Parse kernel configuration"""
        kernel_info = {}
        
        try:
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Extract kernel version from "Kernel Configuration" line
                version_match = re.search(r'Kernel Configuration.*?(\d+\.\d+\.\d+)', content)
                if version_match:
                    kernel_info['kernel_version'] = version_match.group(1)
                
                # Look for other kernel info
                arch_match = re.search(r'CONFIG_ARCH="([^"]*)"', content)
                if arch_match:
                    kernel_info['arch'] = arch_match.group(1)
                    
        except Exception as e:
            logger.debug(f"Error parsing kernel config: {e}")
        
        return kernel_info
    
    def _detect_additional_props(self, base_dir: Path) -> Dict[str, str]:
        """Detect additional properties from filesystem structure"""
        additional_info = {}
        
        # Detect architecture from lib directories
        if (base_dir / "system" / "lib64").exists():
            additional_info['is_64bit'] = 'true'
        elif (base_dir / "system" / "lib").exists():
            additional_info['is_64bit'] = 'false'
        
        # Detect vendor overlay
        if (base_dir / "vendor").exists():
            additional_info['has_vendor'] = 'true'
        
        # Detect product partition
        if (base_dir / "product").exists():
            additional_info['has_product'] = 'true'
        
        # Detect ODM partition
        if (base_dir / "odm").exists():
            additional_info['has_odm'] = 'true'
        
        # Detect Treble support
        if (base_dir / "vendor" / "etc" / "vintf").exists():
            additional_info['treble_support'] = 'true'
        
        return additional_info
    
    def get_git_branch_name(self) -> str:
        """Generate appropriate git branch name from device info"""
        if not self.device_info:
            return "firmware_dump"
        
        # Use incremental if available, otherwise build_id, otherwise codename
        for key in ['incremental', 'build_id', 'codename', 'name']:
            if key in self.device_info and self.device_info[key]:
                branch = self.device_info[key].lower()
                # Clean branch name (remove invalid characters)
                branch = re.sub(r'[^a-zA-Z0-9_-]', '_', branch)
                return branch
        
        return "firmware_dump"
    
    def get_readme_content(self) -> str:
        """Generate README content for the extracted firmware"""
        if not self.device_info:
            return "# Firmware Dump\n\nExtracted firmware files."
        
        content = ["# Firmware Dump"]
        content.append("")
        
        # Device information
        if any(key in self.device_info for key in ['brand', 'model', 'name']):
            content.append("## Device Information")
            content.append("")
            
            for key, label in [
                ('brand', 'Brand'),
                ('manufacturer', 'Manufacturer'), 
                ('model', 'Model'),
                ('name', 'Product Name'),
                ('device', 'Device'),
                ('codename', 'Codename')
            ]:
                if key in self.device_info and self.device_info[key]:
                    content.append(f"- **{label}**: {self.device_info[key]}")
            
            content.append("")
        
        # Firmware information
        if any(key in self.device_info for key in ['android_version', 'build_id', 'incremental']):
            content.append("## Firmware Information")
            content.append("")
            
            for key, label in [
                ('android_version', 'Android Version'),
                ('api_level', 'API Level'),
                ('build_id', 'Build ID'),
                ('incremental', 'Incremental'),
                ('fingerprint', 'Fingerprint'),
                ('description', 'Description'),
                ('build_date', 'Build Date')
            ]:
                if key in self.device_info and self.device_info[key]:
                    content.append(f"- **{label}**: {self.device_info[key]}")
            
            content.append("")
        
        # Technical information
        technical_keys = ['abilist', 'locale', 'density', 'kernel_version', 'arch']
        if any(key in self.device_info for key in technical_keys):
            content.append("## Technical Information")
            content.append("")
            
            for key, label in [
                ('abilist', 'CPU ABI List'),
                ('locale', 'Locale'),
                ('density', 'Screen Density'),
                ('kernel_version', 'Kernel Version'),
                ('arch', 'Architecture'),
                ('is_64bit', '64-bit Support'),
                ('treble_support', 'Project Treble')
            ]:
                if key in self.device_info and self.device_info[key]:
                    content.append(f"- **{label}**: {self.device_info[key]}")
            
            content.append("")
        
        content.append("## Extracted Files")
        content.append("")
        content.append("This repository contains the extracted firmware files.")
        
        return "\n".join(content)
    
    def print_device_summary(self):
        """Print a summary of detected device information"""
        if not self.device_info:
            print("No device information detected")
            return
        
        from dumprx.utils.ui import print_info, print_success
        
        print_success("🔍 Device Auto-Detection Results:")
        
        # Key information
        key_info = []
        for key, label in [
            ('brand', 'Brand'),
            ('model', 'Model'), 
            ('android_version', 'Android'),
            ('build_id', 'Build ID')
        ]:
            if key in self.device_info and self.device_info[key]:
                key_info.append(f"{label}: {self.device_info[key]}")
        
        if key_info:
            print_info("  " + " | ".join(key_info))
        
        # Additional details
        if 'fingerprint' in self.device_info:
            print_info(f"  Fingerprint: {self.device_info['fingerprint']}")
        
        print_info(f"  Branch: {self.get_git_branch_name()}")