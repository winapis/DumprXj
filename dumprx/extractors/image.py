"""
Image extraction functionality (Android images, boot, system, etc.)
"""

import subprocess
import struct
import gzip
import lzma
from pathlib import Path
from typing import Optional, Dict, Any, List

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole


class ImageExtractor:
    """Handles extraction of Android image files"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        
    def extract(self, file_path: Path, output_dir: Path, 
               firmware_info: Dict[str, Any]) -> bool:
        """Extract image file"""
        try:
            image_type = firmware_info.get('type', '')
            
            self.console.step(f"Extracting {image_type} image...")
            
            if image_type == 'boot_image':
                return self._extract_boot_image(file_path, output_dir)
            elif image_type == 'system_image':
                return self._extract_system_image(file_path, output_dir)
            elif image_type == 'super_image':
                return self._extract_super_image(file_path, output_dir)
            elif image_type == 'android_image':
                return self._extract_android_image(file_path, output_dir)
            elif image_type == 'extracted_firmware':
                return self._process_extracted_firmware(file_path, output_dir)
            else:
                # Generic image processing
                return self._extract_generic_image(file_path, output_dir)
                
        except Exception as e:
            self.console.error(f"Image extraction failed: {e}")
            return False
            
    def _extract_boot_image(self, file_path: Path, output_dir: Path) -> bool:
        """Extract boot.img using unpackboot.sh"""
        try:
            utils_dir = self.config.get_utils_dir()
            unpack_tool = utils_dir / "unpackboot.sh"
            
            if not unpack_tool.exists():
                self.console.error("Boot image extraction tool not found")
                return False
                
            # Create boot directory
            boot_dir = output_dir / "boot"
            boot_dir.mkdir(exist_ok=True)
            
            # Copy boot image to extraction directory
            boot_img = boot_dir / "boot.img"
            import shutil
            shutil.copy2(file_path, boot_img)
            
            # Run boot image extraction
            cmd = ["bash", str(unpack_tool), str(boot_img)]
            
            result = subprocess.run(
                cmd,
                cwd=boot_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.console.success("Boot image extraction completed")
                # Extract ramdisk if present
                self._extract_ramdisk(boot_dir)
                return True
            else:
                self.console.error(f"Boot image extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"Boot image extraction error: {e}")
            return False
            
    def _extract_system_image(self, file_path: Path, output_dir: Path) -> bool:
        """Extract system image (system.img, system.new.dat, etc.)"""
        try:
            filename = file_path.name.lower()
            
            if 'new.dat' in filename:
                return self._extract_dat_image(file_path, output_dir)
            elif filename.endswith('.img'):
                return self._extract_img_file(file_path, output_dir)
            elif filename.endswith('.sin'):
                return self._extract_sin_file(file_path, output_dir)
            else:
                return self._extract_generic_image(file_path, output_dir)
                
        except Exception as e:
            self.console.error(f"System image extraction error: {e}")
            return False
            
    def _extract_dat_image(self, file_path: Path, output_dir: Path) -> bool:
        """Extract .new.dat files using sdat2img"""
        try:
            utils_dir = self.config.get_utils_dir()
            sdat2img = utils_dir / "sdat2img.py"
            
            if not sdat2img.exists():
                self.console.error("sdat2img tool not found")
                return False
                
            # Find corresponding transfer list
            base_name = file_path.stem.replace('.new', '')
            transfer_list = file_path.parent / f"{base_name}.transfer.list"
            
            if not transfer_list.exists():
                # Look for other possible names
                for pattern in [f"{base_name}.list", "transfer.list"]:
                    candidate = file_path.parent / pattern
                    if candidate.exists():
                        transfer_list = candidate
                        break
                        
            if not transfer_list.exists():
                self.console.error("Transfer list file not found")
                return False
                
            # Output image file
            output_img = output_dir / f"{base_name}.img"
            
            # Run sdat2img
            cmd = [
                "python3", str(sdat2img),
                str(transfer_list), str(file_path), str(output_img)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_img.exists():
                self.console.success(f"DAT image extraction completed: {output_img}")
                # Try to mount and extract the img file
                self._extract_img_file(output_img, output_dir)
                return True
            else:
                self.console.error(f"DAT image extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"DAT image extraction error: {e}")
            return False
            
    def _extract_img_file(self, file_path: Path, output_dir: Path) -> bool:
        """Extract .img files"""
        try:
            # Check if it's a sparse image first
            if self._is_sparse_image(file_path):
                return self._extract_sparse_image(file_path, output_dir)
                
            # Try to extract as ext4 filesystem
            return self._extract_ext4_image(file_path, output_dir)
            
        except Exception as e:
            self.console.error(f"IMG file extraction error: {e}")
            return False
            
    def _extract_sparse_image(self, file_path: Path, output_dir: Path) -> bool:
        """Extract sparse image using simg2img"""
        try:
            utils_dir = self.config.get_utils_dir()
            simg2img = utils_dir / "bin" / "simg2img"
            
            if not simg2img.exists():
                self.console.error("simg2img tool not found")
                return False
                
            # Convert sparse to raw image
            raw_img = output_dir / f"{file_path.stem}_raw.img"
            
            cmd = [str(simg2img), str(file_path), str(raw_img)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and raw_img.exists():
                self.console.success("Sparse image conversion completed")
                # Extract the raw image
                return self._extract_ext4_image(raw_img, output_dir)
            else:
                self.console.error(f"Sparse image conversion failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"Sparse image extraction error: {e}")
            return False
            
    def _extract_ext4_image(self, file_path: Path, output_dir: Path) -> bool:
        """Extract ext4 filesystem image"""
        try:
            # Try using 7zip first (works for many ext4 images)
            cmd = ["7zz", "x", str(file_path), f"-o{output_dir}"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console.success("EXT4 image extraction completed")
                return True
            else:
                self.console.warning("7zip extraction failed, trying alternative methods")
                return self._try_alternative_ext4_extraction(file_path, output_dir)
                
        except Exception as e:
            self.console.error(f"EXT4 image extraction error: {e}")
            return False
            
    def _try_alternative_ext4_extraction(self, file_path: Path, output_dir: Path) -> bool:
        """Try alternative methods for ext4 extraction"""
        try:
            # Try loop mount (requires root, might not work in containers)
            self.console.step("Attempting loop mount extraction...")
            
            mount_point = output_dir / "mnt"
            mount_point.mkdir(exist_ok=True)
            
            # This might fail due to permissions, but we'll try
            cmd = ["sudo", "mount", "-o", "loop,ro", str(file_path), str(mount_point)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Copy files
                import shutil
                extract_dir = output_dir / file_path.stem
                shutil.copytree(mount_point, extract_dir)
                
                # Unmount
                subprocess.run(["sudo", "umount", str(mount_point)], capture_output=True)
                mount_point.rmdir()
                
                self.console.success("Loop mount extraction completed")
                return True
            else:
                self.console.warning("Loop mount failed (normal in containers)")
                return False
                
        except Exception as e:
            self.console.debug(f"Alternative ext4 extraction failed: {e}")
            return False
            
    def _extract_super_image(self, file_path: Path, output_dir: Path) -> bool:
        """Extract super.img (dynamic partitions)"""
        try:
            utils_dir = self.config.get_utils_dir()
            lpunpack = utils_dir / "lpunpack"
            
            if not lpunpack.exists():
                self.console.error("lpunpack tool not found")
                return False
                
            # First convert sparse to raw if needed
            if self._is_sparse_image(file_path):
                raw_img = output_dir / "super_raw.img"
                simg2img = utils_dir / "bin" / "simg2img"
                if simg2img.exists():
                    cmd = [str(simg2img), str(file_path), str(raw_img)]
                    subprocess.run(cmd, capture_output=True)
                    if raw_img.exists():
                        file_path = raw_img
                        
            # Extract partitions from super image
            for partition in self.config.extraction.partitions:
                cmd = [str(lpunpack), f"--partition={partition}", str(file_path)]
                result = subprocess.run(
                    cmd,
                    cwd=output_dir,
                    capture_output=True,
                    text=True
                )
                
                # Also try with _a suffix (A/B partitions)
                if result.returncode != 0:
                    cmd = [str(lpunpack), f"--partition={partition}_a", str(file_path)]
                    subprocess.run(cmd, cwd=output_dir, capture_output=True)
                    
            self.console.success("Super image extraction completed")
            return True
            
        except Exception as e:
            self.console.error(f"Super image extraction error: {e}")
            return False
            
    def _extract_sin_file(self, file_path: Path, output_dir: Path) -> bool:
        """Extract Sony .sin files"""
        try:
            utils_dir = self.config.get_utils_dir()
            unsin = utils_dir / "unsin"
            
            if not unsin.exists():
                self.console.error("unsin tool not found")
                return False
                
            # Run unsin
            cmd = [str(unsin), "-i", str(file_path), "-o", str(output_dir)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console.success("SIN file extraction completed")
                return True
            else:
                self.console.error(f"SIN file extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"SIN file extraction error: {e}")
            return False
            
    def _extract_ramdisk(self, boot_dir: Path) -> bool:
        """Extract ramdisk from boot image"""
        try:
            ramdisk_file = boot_dir / "ramdisk.packed"
            if not ramdisk_file.exists():
                return False
                
            ramdisk_dir = boot_dir / "ramdisk"
            ramdisk_dir.mkdir(exist_ok=True)
            
            # Try different compression formats
            for fmt in self.config.extraction.ramdisk_formats:
                if self._try_ramdisk_format(ramdisk_file, ramdisk_dir, fmt):
                    self.console.success(f"Ramdisk extracted using {fmt} format")
                    return True
                    
            self.console.warning("Could not extract ramdisk")
            return False
            
        except Exception as e:
            self.console.error(f"Ramdisk extraction error: {e}")
            return False
            
    def _try_ramdisk_format(self, ramdisk_file: Path, output_dir: Path, fmt: str) -> bool:
        """Try to extract ramdisk with specific format"""
        try:
            if fmt == "gzip":
                with gzip.open(ramdisk_file, 'rb') as f:
                    # Extract cpio archive
                    cmd = ["cpio", "-i", "-d", "-m", "--no-absolute-filenames"]
                    proc = subprocess.Popen(
                        cmd, 
                        cwd=output_dir,
                        stdin=subprocess.PIPE,
                        capture_output=True
                    )
                    proc.communicate(input=f.read())
                    return proc.returncode == 0
                    
            elif fmt == "lzma":
                with lzma.open(ramdisk_file, 'rb') as f:
                    cmd = ["cpio", "-i", "-d", "-m", "--no-absolute-filenames"]
                    proc = subprocess.Popen(
                        cmd,
                        cwd=output_dir,
                        stdin=subprocess.PIPE,
                        capture_output=True
                    )
                    proc.communicate(input=f.read())
                    return proc.returncode == 0
                    
            # Add more format support as needed
            return False
            
        except Exception:
            return False
            
    def _is_sparse_image(self, file_path: Path) -> bool:
        """Check if image is sparse format"""
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                return magic == b'\x3a\xff\x26\xed'
        except Exception:
            return False
            
    def _extract_android_image(self, file_path: Path, output_dir: Path) -> bool:
        """Extract Android boot image format"""
        return self._extract_boot_image(file_path, output_dir)
        
    def _process_extracted_firmware(self, dir_path: Path, output_dir: Path) -> bool:
        """Process already extracted firmware directory"""
        try:
            import shutil
            shutil.copytree(dir_path, output_dir, dirs_exist_ok=True)
            
            # Process any images found in the directory
            for img_file in dir_path.rglob("*.img"):
                self._extract_img_file(img_file, output_dir)
                
            return True
            
        except Exception as e:
            self.console.error(f"Extracted firmware processing error: {e}")
            return False
            
    def _extract_generic_image(self, file_path: Path, output_dir: Path) -> bool:
        """Generic image extraction fallback"""
        try:
            # Copy file to output directory for manual analysis
            import shutil
            output_file = output_dir / file_path.name
            shutil.copy2(file_path, output_file)
            
            self.console.warning(f"Copied {file_path.name} for manual analysis")
            return True
            
        except Exception as e:
            self.console.error(f"Generic image extraction error: {e}")
            return False