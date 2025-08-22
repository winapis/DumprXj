#!/usr/bin/env python3

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from dumprx.console import info, warning, error, step, success
from dumprx import UTILS_DIR


class FirmwareAnalyzer:
    
    def __init__(self, extracted_dir: str, output_dir: str):
        self.extracted_dir = Path(extracted_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.firmware_info = {}
    
    def analyze(self) -> Dict:
        step("Analyzing extracted firmware")
        
        self._detect_bootimage()
        self._extract_system_info()
        self._extract_boot_info()
        self._extract_recovery_info()
        self._extract_vendor_info()
        self._generate_board_info()
        self._cleanup_unnecessary_files()
        
        info(f"Firmware analysis completed")
        return self.firmware_info
    
    def _detect_bootimage(self):
        boot_files = [
            'boot.img', 'recovery.img', 'kernel', 'ramdisk'
        ]
        
        for boot_file in boot_files:
            boot_path = self.extracted_dir / boot_file
            if boot_path.exists():
                self._unpack_boot_image(boot_path)
    
    def _unpack_boot_image(self, boot_path: Path):
        step(f"Unpacking boot image: {boot_path.name}")
        
        try:
            unpackboot_script = UTILS_DIR / "unpackboot.sh"
            if not unpackboot_script.exists():
                warning("unpackboot.sh not found")
                return
            
            boot_output_dir = self.output_dir / f"{boot_path.stem}RE"
            boot_output_dir.mkdir(exist_ok=True)
            
            result = subprocess.run(
                ['bash', str(unpackboot_script), str(boot_path)],
                cwd=str(boot_output_dir),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                success(f"Boot image unpacked: {boot_path.name}")
                self._extract_kernel_info(boot_output_dir)
            else:
                warning(f"Failed to unpack {boot_path.name}")
                
        except Exception as e:
            warning(f"Boot image unpacking error: {str(e)}")
    
    def _extract_kernel_info(self, boot_dir: Path):
        ikconfig_path = boot_dir / "ikconfig"
        if ikconfig_path.exists():
            try:
                with open(ikconfig_path, 'r') as f:
                    content = f.read()
                    
                kernel_match = re.search(r'Kernel Configuration\s+(\S+)', content)
                if kernel_match:
                    self.firmware_info['kernel_version'] = kernel_match.group(1)
                    
            except Exception as e:
                warning(f"Failed to extract kernel info: {str(e)}")
    
    def _extract_system_info(self):
        system_dirs = [
            self.extracted_dir / "system",
            self.extracted_dir / "system" / "system"
        ]
        
        for system_dir in system_dirs:
            if system_dir.exists():
                self._analyze_system_partition(system_dir)
                break
    
    def _analyze_system_partition(self, system_dir: Path):
        build_prop_path = system_dir / "build.prop"
        if build_prop_path.exists():
            self._parse_build_prop(build_prop_path)
        
        self._extract_euclid_images(system_dir)
    
    def _parse_build_prop(self, build_prop_path: Path):
        try:
            with open(build_prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            props = {}
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    props[key.strip()] = value.strip()
            
            self.firmware_info.update({
                'brand': props.get('ro.product.brand', 'Unknown'),
                'device': props.get('ro.product.device', 'Unknown'),
                'model': props.get('ro.product.model', 'Unknown'),
                'android_version': props.get('ro.build.version.release', 'Unknown'),
                'sdk_version': props.get('ro.build.version.sdk', 'Unknown'),
                'platform': props.get('ro.board.platform', 'Unknown'),
                'fingerprint': props.get('ro.build.fingerprint', 'Unknown'),
                'build_id': props.get('ro.build.id', 'Unknown'),
                'security_patch': props.get('ro.build.version.security_patch', 'Unknown')
            })
            
            success("System build.prop analyzed")
            
        except Exception as e:
            warning(f"Failed to parse build.prop: {str(e)}")
    
    def _extract_vendor_info(self):
        vendor_dirs = [
            self.extracted_dir / "vendor",
            self.extracted_dir / "system" / "vendor"
        ]
        
        for vendor_dir in vendor_dirs:
            if vendor_dir.exists():
                self._analyze_vendor_partition(vendor_dir)
                break
    
    def _analyze_vendor_partition(self, vendor_dir: Path):
        vendor_build_prop = vendor_dir / "build.prop"
        if vendor_build_prop.exists():
            try:
                with open(vendor_build_prop, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if 'ro.vendor.build.fingerprint' in key:
                            self.firmware_info['vendor_fingerprint'] = value.strip()
                        elif 'ro.vendor.build.security_patch' in key:
                            self.firmware_info['vendor_security_patch'] = value.strip()
                
                success("Vendor build.prop analyzed")
                
            except Exception as e:
                warning(f"Failed to parse vendor build.prop: {str(e)}")
        
        self._extract_euclid_images(vendor_dir)
    
    def _extract_recovery_info(self):
        recovery_dirs = [
            self.output_dir / "recoveryRE",
            self.extracted_dir / "recovery"
        ]
        
        for recovery_dir in recovery_dirs:
            if recovery_dir.exists():
                info(f"Recovery partition found: {recovery_dir}")
                break
    
    def _extract_boot_info(self):
        boot_dirs = [
            self.output_dir / "bootRE",
            self.extracted_dir / "boot"
        ]
        
        for boot_dir in boot_dirs:
            if boot_dir.exists():
                info(f"Boot partition found: {boot_dir}")
                break
    
    def _extract_euclid_images(self, partition_dir: Path):
        euclid_dir = partition_dir / "euclid"
        if euclid_dir.exists():
            step(f"Extracting Euclid images from {partition_dir.name}")
            
            try:
                seven_zip = UTILS_DIR / "bin" / "7zz"
                if not seven_zip.exists():
                    return
                
                for img_file in euclid_dir.glob("*.img"):
                    extract_dir = euclid_dir / img_file.stem
                    extract_dir.mkdir(exist_ok=True)
                    
                    result = subprocess.run([
                        str(seven_zip), "x", str(img_file), f"-o{extract_dir}"
                    ], capture_output=True)
                    
                    if result.returncode == 0:
                        img_file.unlink()
                        success(f"Extracted Euclid image: {img_file.name}")
                    
            except Exception as e:
                warning(f"Failed to extract Euclid images: {str(e)}")
    
    def _generate_board_info(self):
        board_info_path = self.output_dir / "board-info.txt"
        
        try:
            with open(board_info_path, 'w') as f:
                f.write("Board Information\n")
                f.write("==================\n\n")
                
                for key, value in self.firmware_info.items():
                    f.write(f"{key}: {value}\n")
                
                f.write(f"\nExtracted files location: {self.output_dir}\n")
            
            success("Board info file created")
            
        except Exception as e:
            warning(f"Failed to create board info: {str(e)}")
    
    def _cleanup_unnecessary_files(self):
        step("Cleaning up unnecessary files")
        
        patterns_to_remove = [
            "*.zip", "*.rar", "*.7z", "*.tar*"
        ]
        
        unnecessary_files = [
            "zip.log", "extraction.log"
        ]
        
        for pattern in patterns_to_remove:
            for file_path in self.extracted_dir.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
        
        for filename in unnecessary_files:
            file_path = self.extracted_dir / filename
            if file_path.exists():
                file_path.unlink()
        
        # Remove empty partitions that don't contain important data
        important_partitions = {
            'boot', 'recovery', 'dtbo', 'tz', 'system', 'vendor', 'product', 'odm'
        }
        
        for file_path in self.extracted_dir.rglob("*"):
            if file_path.is_file():
                filename = file_path.name.lower()
                stem = file_path.stem.lower()
                
                # Keep important partition images
                if any(partition in stem for partition in important_partitions):
                    continue
                
                # Remove other image files that are not essential
                if filename.endswith(('.img', '.bin')) and file_path.stat().st_size < 1024:
                    file_path.unlink()
        
        success("Cleanup completed")