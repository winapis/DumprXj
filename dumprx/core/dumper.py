import os
import shutil
import subprocess
import re
import time
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
        
        # Import enhanced components for v2.0
        try:
            from dumprx.extractors.manufacturer_detector import ManufacturerDetector
            from dumprx.extractors.enhanced_boot_analyzer import EnhancedBootAnalyzer
            from dumprx.downloaders.enhanced_downloader import EnhancedDownloader
            
            self.manufacturer_detector = ManufacturerDetector(config)
            self.boot_analyzer = EnhancedBootAnalyzer(config)
            self.enhanced_downloader = EnhancedDownloader(config)
            self.v2_available = True
        except ImportError as e:
            logger.warning(f"V2.0 features not available: {e}")
            self.v2_available = False
        
    def setup(self):
        """Setup directories and external tools"""
        self.config.setup_directories()
        self.external_tools.setup_tools()
    
    def process_firmware_v2(self, firmware_path: str, manufacturer_info=None) -> Dict[str, Any]:
        """Enhanced v2.0 firmware processing pipeline with manufacturer-specific extraction"""
        
        if not self.v2_available:
            logger.warning("V2.0 features not available, falling back to legacy mode")
            return self.process_firmware(firmware_path)
        
        try:
            print_info(f"🚀 Processing firmware with DumprX v2.0: {firmware_path}")
            
            results = {
                'success': False,
                'firmware_path': firmware_path,
                'manufacturer_info': manufacturer_info,
                'extracted_files': [],
                'boot_analysis': {},
                'device_info': {},
                'output_dir': None,
                'processing_time': 0,
                'extraction_method': 'v2.0_enhanced'
            }
            
            start_time = time.time()
            
            # Step 1: Handle URL downloads
            firmware_path_obj = Path(firmware_path)
            if self._is_url(firmware_path):
                print_info("🌐 URL detected, using enhanced downloader...")
                
                def progress_callback(progress, downloaded, total):
                    if progress % 10 == 0:  # Report every 10%
                        print_info(f"📥 Download progress: {progress}%")
                
                downloaded_path = self.enhanced_downloader.download(
                    firmware_path, 
                    progress_callback=progress_callback
                )
                
                if not downloaded_path:
                    print_error("❌ Enhanced download failed")
                    return results
                
                firmware_path_obj = downloaded_path
                results['firmware_path'] = str(firmware_path_obj)
            
            # Validate firmware path
            if not firmware_path_obj.exists():
                print_error(f"❌ Firmware file/folder not found: {firmware_path_obj}")
                return results
            
            # Step 2: Manufacturer detection (if not already done)
            if not manufacturer_info:
                print_info("🔍 Detecting manufacturer...")
                manufacturer_info = self.manufacturer_detector.detect_manufacturer(firmware_path_obj)
                results['manufacturer_info'] = manufacturer_info
            
            if manufacturer_info:
                print_info(f"🏭 Detected manufacturer: {manufacturer_info.name.title()}")
                print_info(f"📱 Model: {manufacturer_info.model or 'Unknown'}")
                print_info(f"🔧 Extraction method: {manufacturer_info.extraction_method}")
            
            # Step 3: Create output directory
            output_dir = self._create_output_directory_v2(firmware_path_obj, manufacturer_info)
            results['output_dir'] = str(output_dir)
            
            # Step 4: Extract firmware using manufacturer-specific method
            print_info("📦 Extracting firmware...")
            extracted_files = self._extract_firmware_v2(firmware_path_obj, manufacturer_info, output_dir)
            results['extracted_files'] = extracted_files
            
            if not extracted_files:
                print_warning("⚠️ No files extracted, trying legacy method...")
                legacy_result = self.process_firmware(str(firmware_path_obj))
                results['success'] = legacy_result
                results['extraction_method'] = 'fallback_legacy'
                return results
            
            # Step 5: Enhanced boot image analysis
            print_info("🥾 Analyzing boot images...")
            boot_results = self._analyze_boot_images_v2(output_dir)
            results['boot_analysis'] = boot_results
            
            # Step 6: Device information extraction
            print_info("📱 Extracting device information...")
            device_info = self._extract_device_info_v2(output_dir, manufacturer_info)
            results['device_info'] = device_info
            
            # Step 7: Generate reports and documentation
            print_info("📄 Generating reports...")
            self._generate_extraction_report_v2(results, output_dir)
            
            # Step 8: Git repository setup (if configured)
            if self.config.git_enabled:
                print_info("🐙 Setting up Git repository...")
                self._setup_git_repository_v2(output_dir, results)
            
            results['success'] = True
            results['processing_time'] = time.time() - start_time
            
            print_success(f"✅ V2.0 extraction completed in {results['processing_time']:.1f}s")
            return results
            
        except Exception as e:
            logger.exception("Error in v2.0 firmware processing")
            print_error(f"❌ V2.0 processing failed: {str(e)}")
            results['error'] = str(e)
            return results
        
    def process_firmware(self, firmware_path: str) -> bool:
        """Legacy firmware processing pipeline (maintained for backward compatibility)"""
        try:
            print_info(f"🔧 Processing firmware with legacy dumper: {firmware_path}")
            
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
    
    # V2.0 Enhanced Methods
    def _create_output_directory_v2(self, firmware_path: Path, manufacturer_info) -> Path:
        """Create organized output directory for v2.0"""
        
        # Generate directory name based on manufacturer and device info
        if manufacturer_info and manufacturer_info.model:
            dir_name = f"{manufacturer_info.name}_{manufacturer_info.model}_{int(time.time())}"
        else:
            dir_name = f"{firmware_path.stem}_{int(time.time())}"
        
        # Clean directory name
        dir_name = re.sub(r'[^\w\-_.]', '_', dir_name)
        
        output_dir = Path(self.config.work_dir) / 'extractions' / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir
    
    def _extract_firmware_v2(self, firmware_path: Path, manufacturer_info, output_dir: Path) -> List[str]:
        """Extract firmware using manufacturer-specific v2.0 methods"""
        
        extracted_files = []
        
        try:
            if manufacturer_info and hasattr(self, 'manufacturer_detector'):
                # Get required tools for this manufacturer
                required_tools = self.manufacturer_detector.get_extraction_tools(manufacturer_info)
                
                # Verify tools are available
                missing_tools = []
                for tool in required_tools:
                    if not self.external_tools.is_tool_available(tool):
                        missing_tools.append(tool)
                
                if missing_tools:
                    print_warning(f"⚠️ Missing tools for {manufacturer_info.name}: {', '.join(missing_tools)}")
                    print_info("📦 Falling back to generic extraction...")
                    return self._extract_firmware_generic(firmware_path, output_dir)
                
                # Use manufacturer-specific extraction
                if manufacturer_info.extraction_method == 'tar_extraction':
                    extracted_files = self._extract_tar_firmware(firmware_path, output_dir)
                elif manufacturer_info.extraction_method == 'ozip_decryption':
                    extracted_files = self._extract_ozip_firmware(firmware_path, output_dir)
                elif manufacturer_info.extraction_method == 'update_app_extraction':
                    extracted_files = self._extract_update_app_firmware(firmware_path, output_dir)
                elif manufacturer_info.extraction_method == 'kdz_extraction':
                    extracted_files = self._extract_kdz_firmware(firmware_path, output_dir)
                elif manufacturer_info.extraction_method == 'ruu_decryption':
                    extracted_files = self._extract_ruu_firmware(firmware_path, output_dir)
                elif manufacturer_info.extraction_method == 'sin_extraction':
                    extracted_files = self._extract_sin_firmware(firmware_path, output_dir)
                else:
                    # Generic extraction
                    extracted_files = self._extract_firmware_generic(firmware_path, output_dir)
            else:
                # Generic extraction
                extracted_files = self._extract_firmware_generic(firmware_path, output_dir)
        
        except Exception as e:
            logger.error(f"Error in v2.0 extraction: {e}")
            # Fallback to generic extraction
            extracted_files = self._extract_firmware_generic(firmware_path, output_dir)
        
        return extracted_files
    
    def _extract_firmware_generic(self, firmware_path: Path, output_dir: Path) -> List[str]:
        """Generic firmware extraction using 7zz"""
        
        extracted_files = []
        
        try:
            if firmware_path.is_file():
                # Extract archive
                cmd = ['7zz', 'x', str(firmware_path), f'-o{output_dir}', '-y']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
                
                if result.returncode == 0:
                    # List extracted files
                    for file_path in output_dir.rglob('*'):
                        if file_path.is_file():
                            extracted_files.append(str(file_path.relative_to(output_dir)))
                else:
                    print_warning(f"⚠️ 7zz extraction failed: {result.stderr}")
            
            elif firmware_path.is_dir():
                # Copy directory contents
                for item in firmware_path.rglob('*'):
                    if item.is_file():
                        rel_path = item.relative_to(firmware_path)
                        dest_path = output_dir / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dest_path)
                        extracted_files.append(str(rel_path))
        
        except Exception as e:
            logger.error(f"Generic extraction failed: {e}")
        
        return extracted_files
    
    def _extract_tar_firmware(self, firmware_path: Path, output_dir: Path) -> List[str]:
        """Extract Samsung TAR firmware"""
        
        extracted_files = []
        
        try:
            # Use tar to extract
            cmd = ['tar', '-xf', str(firmware_path), '-C', str(output_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
            if result.returncode == 0:
                for file_path in output_dir.rglob('*'):
                    if file_path.is_file():
                        extracted_files.append(str(file_path.relative_to(output_dir)))
        
        except Exception as e:
            logger.error(f"TAR extraction failed: {e}")
        
        return extracted_files
    
    def _extract_ozip_firmware(self, firmware_path: Path, output_dir: Path) -> List[str]:
        """Extract OPPO/OnePlus OZIP firmware"""
        
        extracted_files = []
        
        try:
            # Use ozipdecrypt.py
            script_path = Path(self.config.tools_dir) / 'ozipdecrypt.py'
            if script_path.exists():
                cmd = ['python3', str(script_path), str(firmware_path), str(output_dir)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
                
                if result.returncode == 0:
                    for file_path in output_dir.rglob('*'):
                        if file_path.is_file():
                            extracted_files.append(str(file_path.relative_to(output_dir)))
        
        except Exception as e:
            logger.error(f"OZIP extraction failed: {e}")
        
        return extracted_files
    
    def _extract_update_app_firmware(self, firmware_path: Path, output_dir: Path) -> List[str]:
        """Extract Huawei UPDATE.APP firmware"""
        
        extracted_files = []
        
        try:
            # Use splituapp.py
            script_path = Path(self.config.tools_dir) / 'splituapp.py'
            if script_path.exists():
                cmd = ['python3', str(script_path), str(firmware_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, cwd=output_dir)
                
                if result.returncode == 0:
                    for file_path in output_dir.rglob('*'):
                        if file_path.is_file():
                            extracted_files.append(str(file_path.relative_to(output_dir)))
        
        except Exception as e:
            logger.error(f"UPDATE.APP extraction failed: {e}")
        
        return extracted_files
    
    def _extract_kdz_firmware(self, firmware_path: Path, output_dir: Path) -> List[str]:
        """Extract LG KDZ firmware"""
        
        extracted_files = []
        
        try:
            # Use unkdz.py
            script_path = Path(self.config.tools_dir) / 'kdztools' / 'unkdz.py'
            if script_path.exists():
                cmd = ['python3', str(script_path), '-f', str(firmware_path), '-x', str(output_dir)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
                
                if result.returncode == 0:
                    for file_path in output_dir.rglob('*'):
                        if file_path.is_file():
                            extracted_files.append(str(file_path.relative_to(output_dir)))
        
        except Exception as e:
            logger.error(f"KDZ extraction failed: {e}")
        
        return extracted_files
    
    def _extract_ruu_firmware(self, firmware_path: Path, output_dir: Path) -> List[str]:
        """Extract HTC RUU firmware"""
        
        extracted_files = []
        
        try:
            # Use RUU_Decrypt_Tool
            tool_path = Path(self.config.tools_dir) / 'RUU_Decrypt_Tool' / 'RUU_Decrypt_Tool'
            if tool_path.exists():
                cmd = [str(tool_path), str(firmware_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, cwd=output_dir)
                
                if result.returncode == 0:
                    for file_path in output_dir.rglob('*'):
                        if file_path.is_file():
                            extracted_files.append(str(file_path.relative_to(output_dir)))
        
        except Exception as e:
            logger.error(f"RUU extraction failed: {e}")
        
        return extracted_files
    
    def _extract_sin_firmware(self, firmware_path: Path, output_dir: Path) -> List[str]:
        """Extract Sony SIN firmware"""
        
        extracted_files = []
        
        try:
            # Use unsin
            tool_path = Path(self.config.tools_dir) / 'unsin' / 'unsin'
            if tool_path.exists():
                cmd = [str(tool_path), str(firmware_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, cwd=output_dir)
                
                if result.returncode == 0:
                    for file_path in output_dir.rglob('*'):
                        if file_path.is_file():
                            extracted_files.append(str(file_path.relative_to(output_dir)))
        
        except Exception as e:
            logger.error(f"SIN extraction failed: {e}")
        
        return extracted_files
    
    def _analyze_boot_images_v2(self, output_dir: Path) -> Dict[str, Any]:
        """Analyze boot images using enhanced v2.0 analyzer"""
        
        boot_results = {}
        
        try:
            if hasattr(self, 'boot_analyzer'):
                boot_results = self.boot_analyzer.analyze_boot_images(output_dir)
        except Exception as e:
            logger.error(f"Boot analysis failed: {e}")
        
        return boot_results
    
    def _extract_device_info_v2(self, output_dir: Path, manufacturer_info) -> Dict[str, Any]:
        """Extract comprehensive device information for v2.0"""
        
        device_info = {}
        
        try:
            # Use existing device detector
            device_info = self.device_detector.detect_device_info(output_dir)
            
            # Enhance with manufacturer-specific info
            if manufacturer_info:
                device_info['manufacturer'] = manufacturer_info.name
                device_info['model'] = manufacturer_info.model
                device_info['android_version'] = manufacturer_info.android_version
                device_info['build_id'] = manufacturer_info.build_id
        
        except Exception as e:
            logger.error(f"Device info extraction failed: {e}")
        
        return device_info
    
    def _generate_extraction_report_v2(self, results: Dict[str, Any], output_dir: Path):
        """Generate comprehensive extraction report for v2.0"""
        
        try:
            report_file = output_dir / 'extraction_report.json'
            
            import json
            with open(report_file, 'w') as f:
                # Convert non-serializable objects
                serializable_results = {}
                for key, value in results.items():
                    if hasattr(value, '__dict__'):
                        serializable_results[key] = value.__dict__
                    elif isinstance(value, Path):
                        serializable_results[key] = str(value)
                    else:
                        serializable_results[key] = value
                
                json.dump(serializable_results, f, indent=2, default=str)
            
            # Generate README
            readme_file = output_dir / 'README.md'
            self._generate_readme_v2(results, readme_file)
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
    
    def _generate_readme_v2(self, results: Dict[str, Any], readme_file: Path):
        """Generate README.md for extracted firmware"""
        
        try:
            manufacturer_info = results.get('manufacturer_info')
            device_info = results.get('device_info', {})
            
            content = f"""# Firmware Extraction Report

## Device Information
- **Manufacturer:** {manufacturer_info.name.title() if manufacturer_info else 'Unknown'}
- **Model:** {manufacturer_info.model if manufacturer_info else device_info.get('model', 'Unknown')}
- **Android Version:** {manufacturer_info.android_version if manufacturer_info else device_info.get('android_version', 'Unknown')}
- **Build ID:** {manufacturer_info.build_id if manufacturer_info else device_info.get('build_id', 'Unknown')}

## Extraction Details
- **Extraction Method:** {results.get('extraction_method', 'Unknown')}
- **Processing Time:** {results.get('processing_time', 0):.1f} seconds
- **Files Extracted:** {len(results.get('extracted_files', []))}

## Boot Analysis
"""
            
            boot_analysis = results.get('boot_analysis', {})
            if boot_analysis:
                for image_name, analysis in boot_analysis.items():
                    if 'boot_info' in analysis:
                        boot_info = analysis['boot_info']
                        content += f"""
### {image_name}
- **Image Type:** {boot_info.image_type.value if hasattr(boot_info, 'image_type') else 'Unknown'}
- **Ramdisk Version:** {boot_info.ramdisk_version.value if hasattr(boot_info, 'ramdisk_version') else 'Unknown'}
- **Compression:** {boot_info.compression.value if hasattr(boot_info, 'compression') else 'Unknown'}
"""
            
            content += f"""
## Extracted Files
"""
            
            for file_path in results.get('extracted_files', [])[:20]:  # Show first 20 files
                content += f"- {file_path}\n"
            
            if len(results.get('extracted_files', [])) > 20:
                content += f"- ... and {len(results.get('extracted_files', [])) - 20} more files\n"
            
            content += f"""
---
*Generated by DumprX v2.0 - Advanced Firmware Extraction Toolkit*
"""
            
            with open(readme_file, 'w') as f:
                f.write(content)
            
        except Exception as e:
            logger.error(f"README generation failed: {e}")
    
    def _setup_git_repository_v2(self, output_dir: Path, results: Dict[str, Any]):
        """Setup Git repository for extracted firmware (v2.0)"""
        
        try:
            # Initialize git repository
            subprocess.run(['git', 'init'], cwd=output_dir, capture_output=True)
            
            # Add all files
            subprocess.run(['git', 'add', '.'], cwd=output_dir, capture_output=True)
            
            # Create commit message
            manufacturer_info = results.get('manufacturer_info')
            if manufacturer_info:
                commit_msg = f"Initial firmware extraction: {manufacturer_info.name} {manufacturer_info.model}"
            else:
                commit_msg = "Initial firmware extraction"
            
            subprocess.run(['git', 'commit', '-m', commit_msg], cwd=output_dir, capture_output=True)
            
            print_info("🐙 Git repository initialized")
            
        except Exception as e:
            logger.error(f"Git setup failed: {e}")