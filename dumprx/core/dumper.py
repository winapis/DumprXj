import os
import shutil
import subprocess
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console

from dumprx.core.config import Config
from dumprx.core.external_tools import ExternalToolsManager
from dumprx.core.device_detector import DeviceDetector
from dumprx.extractors.firmware_detector import FirmwareDetector
from dumprx.utils.ui import print_info, print_error, print_success, print_warning

logger = logging.getLogger(__name__)
console = Console()


class FirmwareDumper:
    def __init__(self, config: Config):
        self.config = config
        self.external_tools = ExternalToolsManager(config)
        self.detector = FirmwareDetector(config)
        self.device_detector = DeviceDetector(config)
        
    def setup(self):
        """Setup directories and external tools"""
        self.config.setup_directories()
        self.external_tools.setup_tools()
        
    def process_firmware(self, firmware_path: str) -> bool:
        """Main firmware processing pipeline"""
        try:
            print_info(f"Processing firmware: {firmware_path}")
            
            # Detect if it's a URL or file path
            if self._is_url(firmware_path):
                print_info("URL detected, downloading...")
                firmware_path = self._download_firmware(firmware_path)
                if not firmware_path:
                    return False
            
            # Validate firmware path
            firmware_path_obj = Path(firmware_path)
            if not firmware_path_obj.exists():
                print_error(f"Firmware file/folder not found: {firmware_path}")
                return False
            
            # Set working directory to project dir
            os.chdir(self.config.project_dir)
            
            # Detect firmware type and extract
            firmware_type = self.detector.detect_firmware_type(firmware_path_obj)
            if not firmware_type:
                print_error("Unsupported firmware type")
                return False
            
            print_info(f"Detected firmware type: {firmware_type}")
            
            # Extract firmware based on type
            success = self._extract_firmware(firmware_path_obj, firmware_type)
            if not success:
                return False
            
            # Process extracted files
            self._process_extracted_files()
            
            print_success("Firmware processing completed!")
            return True
            
        except Exception as e:
            logger.exception("Error processing firmware")
            print_error(f"Error processing firmware: {str(e)}")
            return False
    
    def _is_url(self, path: str) -> bool:
        """Check if the path is a URL"""
        url_patterns = [
            r'https?://',
            r'mega\.nz',
            r'mediafire',
            r'drive\.google\.com',
            r'androidfilehost'
        ]
        return any(re.search(pattern, path) for pattern in url_patterns)
    
    def _download_firmware(self, url: str) -> Optional[str]:
        """Download firmware from URL"""
        from dumprx.downloaders.downloader import download_from_url
        
        try:
            download_path = download_from_url(url, self.config.input_dir)
            return str(download_path) if download_path else None
        except Exception as e:
            logger.exception("Error downloading firmware")
            print_error(f"Download failed: {str(e)}")
            return None
    
    def _extract_firmware(self, firmware_path: Path, firmware_type: str) -> bool:
        """Extract firmware based on detected type"""
        try:
            if firmware_type == "zip_archive":
                return self._extract_zip_archive(firmware_path)
            elif firmware_type == "huawei_update_app":
                return self._extract_huawei_update_app(firmware_path)
            elif firmware_type == "lg_kdz":
                return self._extract_lg_kdz(firmware_path)
            elif firmware_type == "oppo_ops":
                return self._extract_oppo_ops(firmware_path)
            elif firmware_type == "htc_ruu":
                return self._extract_htc_ruu(firmware_path)
            elif firmware_type == "payload_bin":
                return self._extract_payload_bin(firmware_path)
            elif firmware_type == "super_img":
                return self._extract_super_image(firmware_path)
            elif firmware_type == "rockchip":
                return self._extract_rockchip(firmware_path)
            elif firmware_type == "amlogic":
                return self._extract_amlogic(firmware_path)
            else:
                print_warning(f"Unknown firmware type: {firmware_type}")
                return False
                
        except Exception as e:
            logger.exception(f"Error extracting {firmware_type}")
            print_error(f"Extraction failed: {str(e)}")
            return False
    
    def _extract_zip_archive(self, firmware_path: Path) -> bool:
        """Extract ZIP/RAR/7Z archives"""
        print_info("Extracting archived firmware...")
        
        cmd = [
            self.config.get_tool_path("7zz"), "x",
            str(firmware_path), "-o" + str(self.config.tmp_dir),
            "-y"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print_error(f"Extraction failed: {result.stderr}")
            return False
        
        return True
    
    def _extract_huawei_update_app(self, firmware_path: Path) -> bool:
        """Extract Huawei UPDATE.APP"""
        print_info("Huawei UPDATE.APP Detected")
        
        # Extract UPDATE.APP from archive if needed
        if firmware_path.suffix.lower() in ['.zip', '.rar', '.7z']:
            cmd = [self.config.get_tool_path("7zz"), "x", str(firmware_path), "UPDATE.APP"]
            subprocess.run(cmd, cwd=self.config.tmp_dir, capture_output=True)
        
        # Find UPDATE.APP file
        update_app_files = list(self.config.tmp_dir.glob("**/UPDATE.APP"))
        if not update_app_files:
            print_error("UPDATE.APP not found")
            return False
        
        update_app = update_app_files[0]
        
        # Extract partitions using splituapp.py
        splituapp_cmd = [
            "python3", self.config.get_tool_path("splituapp"),
            "-f", str(update_app), "-l", "super", "preas", "preavs"
        ]
        
        result = subprocess.run(splituapp_cmd, cwd=self.config.tmp_dir, capture_output=True, text=True)
        if result.returncode != 0:
            # Try individual partitions
            for partition in self.config.partitions:
                part_cmd = [
                    "python3", self.config.get_tool_path("splituapp"),
                    "-f", str(update_app), "-l", partition.replace(".img", "")
                ]
                subprocess.run(part_cmd, cwd=self.config.tmp_dir, capture_output=True)
        
        return True
    
    def _extract_lg_kdz(self, firmware_path: Path) -> bool:
        """Extract LG KDZ firmware"""
        print_info("LG KDZ Detected")
        
        # Copy to temp directory
        shutil.copy2(firmware_path, self.config.tmp_dir)
        kdz_file = self.config.tmp_dir / firmware_path.name
        
        # Extract KDZ
        kdz_cmd = [
            "python3", self.config.get_tool_path("kdz_extract"),
            "-f", firmware_path.name, "-x", "-o", "./"
        ]
        
        result = subprocess.run(kdz_cmd, cwd=self.config.tmp_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print_error("KDZ extraction failed")
            return False
        
        # Find DZ file and extract
        dz_files = list(self.config.tmp_dir.glob("*.dz"))
        if dz_files:
            print_info("Extracting All Partitions As Individual Images")
            dz_cmd = [
                "python3", self.config.get_tool_path("dz_extract"),
                "-f", dz_files[0].name, "-s", "-o", "./"
            ]
            subprocess.run(dz_cmd, cwd=self.config.tmp_dir, capture_output=True)
        
        return True
    
    def _extract_oppo_ops(self, firmware_path: Path) -> bool:
        """Extract Oppo/OnePlus OPS firmware"""
        print_info("Oppo/OnePlus ops Detected")
        
        # Copy to temp directory
        shutil.copy2(firmware_path, self.config.tmp_dir)
        
        print_info("Decrypting ops & extracting...")
        
        # Use uv to run with requirements
        decrypt_cmd = [
            "uv", "run", "--with-requirements",
            str(Path(self.config.get_tool_path("opsdecrypt")).parent / "requirements.txt"),
            self.config.get_tool_path("opsdecrypt"), "decrypt",
            str(self.config.tmp_dir / firmware_path.name)
        ]
        
        result = subprocess.run(decrypt_cmd, cwd=self.config.tmp_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print_error("OPS decryption failed")
            return False
        
        return True
    
    def _extract_htc_ruu(self, firmware_path: Path) -> bool:
        """Extract HTC RUU firmware"""
        print_info("HTC RUU Detected")
        
        # Copy to temp directory
        shutil.copy2(firmware_path, self.config.tmp_dir)
        
        print_info("Extracting System And Firmware Partitions...")
        
        # Extract system partitions
        ruu_cmd = [self.config.get_tool_path("ruudecrypt"), "-s", firmware_path.name]
        subprocess.run(ruu_cmd, cwd=self.config.tmp_dir, capture_output=True)
        
        # Extract firmware partitions
        ruu_cmd = [self.config.get_tool_path("ruudecrypt"), "-f", firmware_path.name]
        subprocess.run(ruu_cmd, cwd=self.config.tmp_dir, capture_output=True)
        
        # Move extracted images
        for out_dir in self.config.tmp_dir.glob("OUT*"):
            for img_file in out_dir.glob("*.img"):
                shutil.move(img_file, self.config.tmp_dir)
        
        return True
    
    def _extract_payload_bin(self, firmware_path: Path) -> bool:
        """Extract AB OTA Payload"""
        print_info("AB OTA Payload Detected")
        
        # Use payload extractor
        payload_cmd = [
            self.config.get_tool_path("payload_extractor"),
            "-c", str(os.cpu_count() or 4),
            "-o", str(self.config.tmp_dir),
            str(firmware_path)
        ]
        
        result = subprocess.run(payload_cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def _extract_super_image(self, firmware_path: Path) -> bool:
        """Extract super.img"""
        print_info("Super Image detected")
        
        # Copy super image
        super_img = self.config.tmp_dir / "super.img"
        if firmware_path.is_file():
            shutil.copy2(firmware_path, super_img)
        
        # Convert sparse to raw if needed
        simg2img_cmd = [
            self.config.get_tool_path("simg2img"),
            str(super_img), str(super_img).replace(".img", ".img.raw")
        ]
        
        result = subprocess.run(simg2img_cmd, capture_output=True)
        if result.returncode != 0:
            # Not sparse, rename
            if super_img.exists():
                shutil.move(super_img, str(super_img).replace(".img", ".img.raw"))
        
        return self._extract_partitions_from_super()
    
    def _extract_partitions_from_super(self) -> bool:
        """Extract individual partitions from super image"""
        super_raw = self.config.tmp_dir / "super.img.raw"
        if not super_raw.exists():
            return False
        
        for partition in self.config.partitions:
            # Try partition_a first, then partition
            lpunpack_cmd = [
                self.config.get_tool_path("lpunpack"),
                f"--partition={partition}_a", str(super_raw)
            ]
            
            result = subprocess.run(lpunpack_cmd, cwd=self.config.tmp_dir, capture_output=True)
            if result.returncode != 0:
                # Try without _a suffix
                lpunpack_cmd = [
                    self.config.get_tool_path("lpunpack"),
                    f"--partition={partition}", str(super_raw)
                ]
                subprocess.run(lpunpack_cmd, cwd=self.config.tmp_dir, capture_output=True)
            
            # Rename partition_a.img to partition.img
            part_a_img = self.config.tmp_dir / f"{partition}_a.img"
            part_img = self.config.tmp_dir / f"{partition}.img"
            if part_a_img.exists():
                shutil.move(part_a_img, part_img)
        
        # Clean up super image
        if super_raw.exists():
            super_raw.unlink()
        
        return True
    
    def _extract_rockchip(self, firmware_path: Path) -> bool:
        """Extract Rockchip firmware"""
        print_info("Rockchip Detected")
        
        # Extract with Rockchip tools
        rk_cmd = [self.config.get_tool_path("rk_extract"), "-unpack", str(firmware_path), str(self.config.tmp_dir)]
        subprocess.run(rk_cmd, capture_output=True)
        
        afp_cmd = [
            self.config.get_tool_path("afptool_extract"), "-unpack",
            str(self.config.tmp_dir / "firmware.img"), str(self.config.tmp_dir)
        ]
        subprocess.run(afp_cmd, capture_output=True)
        
        # Handle super image if present
        super_img = self.config.tmp_dir / "Image" / "super.img"
        if super_img.exists():
            shutil.move(super_img, self.config.tmp_dir / "super.img")
            return self._extract_super_image(self.config.tmp_dir / "super.img")
        
        return True
    
    def _extract_amlogic(self, firmware_path: Path) -> bool:
        """Extract Amlogic AML firmware"""
        print_info("AML Detected")
        
        # Copy to temp
        shutil.copy2(firmware_path, self.config.tmp_dir)
        
        # Extract
        extract_cmd = [self.config.get_tool_path("7zz"), "e", "-y", str(firmware_path)]
        subprocess.run(extract_cmd, cwd=self.config.tmp_dir, capture_output=True)
        
        # Find AML image and extract
        aml_files = list(self.config.tmp_dir.glob("*aml*.img"))
        if aml_files:
            aml_cmd = [self.config.get_tool_path("aml_extract"), str(aml_files[0])]
            subprocess.run(aml_cmd, cwd=self.config.tmp_dir, capture_output=True)
        
        return True
    
    def _process_extracted_files(self):
        """Process extracted firmware files"""
        print_info("Processing extracted files...")
        
        # Move extracted images to output directory
        for img_file in self.config.tmp_dir.glob("*.img"):
            print_info(f"Found partition: {img_file.name}")
        
        # Auto-detect device configuration
        print_info("🔍 Auto-detecting device configuration...")
        device_info = self.device_detector.detect_device_config(self.config.tmp_dir)
        
        if device_info:
            self.device_detector.print_device_summary()
            
            # Create README with device information
            readme_content = self.device_detector.get_readme_content()
            readme_path = self.config.out_dir / "README.md"
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            print_success(f"📄 Device README created: {readme_path}")
        
        # Additional processing can be added here
        # - Convert images to different formats
        # - Extract file systems
        # - Generate device tree info
        # - Create git repository
        
        print_success("File processing completed")