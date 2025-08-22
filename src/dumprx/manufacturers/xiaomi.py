"""
Xiaomi firmware extractor (MIUI packages, Fastboot images)
"""

from pathlib import Path
import tarfile

from .base import BaseExtractor


class XiaomiExtractor(BaseExtractor):
    """Xiaomi firmware extractor for MIUI packages and Fastboot images"""
    
    def extract(self, file_path: Path, output_dir: Path) -> bool:
        """Extract Xiaomi firmware"""
        self.logger.info("🔄 Extracting Xiaomi firmware...")
        
        filename = file_path.name.lower()
        
        if filename.endswith('.tgz'):
            return self._extract_miui_tgz(file_path, output_dir)
        elif self._is_fastboot_package(file_path):
            return self._extract_fastboot_package(file_path, output_dir)
        else:
            return self._extract_with_7zz(file_path, output_dir)
    
    def _extract_miui_tgz(self, file_path: Path, output_dir: Path) -> bool:
        """Extract MIUI TGZ package"""
        try:
            self.logger.info("📦 Extracting MIUI TGZ package...")
            
            with tarfile.open(file_path, 'r:gz') as tar:
                tar.extractall(output_dir)
            
            # Process extracted files
            self._process_miui_files(output_dir)
            
            self.logger.success("✅ MIUI TGZ extraction completed")
            return True
            
        except Exception as e:
            self.logger.error(f"MIUI TGZ extraction failed: {str(e)}")
            return False
    
    def _extract_fastboot_package(self, file_path: Path, output_dir: Path) -> bool:
        """Extract Xiaomi Fastboot package"""
        try:
            self.logger.info("📱 Extracting Xiaomi Fastboot package...")
            
            # First try 7zz extraction
            success = self._extract_with_7zz(file_path, output_dir)
            
            if success:
                # Process fastboot files
                self._process_fastboot_files(output_dir)
                self.logger.success("✅ Fastboot package extraction completed")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Fastboot package extraction failed: {str(e)}")
            return False
    
    def _is_fastboot_package(self, file_path: Path) -> bool:
        """Check if file is Xiaomi Fastboot package"""
        try:
            # Check if it's an archive containing fastboot files
            if self._extract_with_7zz(file_path, Path("/tmp/xiaomi_check")):
                check_dir = Path("/tmp/xiaomi_check")
                has_fastboot = any(
                    f.name.endswith(('.img', '.bat', '.sh')) and 
                    ('flash' in f.name or 'fastboot' in f.name)
                    for f in check_dir.rglob("*")
                )
                import shutil
                shutil.rmtree(check_dir, ignore_errors=True)
                return has_fastboot
        except Exception:
            pass
        return False
    
    def _process_miui_files(self, output_dir: Path):
        """Process extracted MIUI files"""
        # Look for payload.bin
        payload_files = list(output_dir.rglob("payload.bin"))
        for payload in payload_files:
            self.logger.info(f"📦 Found payload.bin: {payload}")
            self._extract_payload(payload, output_dir)
        
        # Look for system images
        system_images = list(output_dir.rglob("system*.img"))
        for img in system_images:
            self._process_system_image(img)
        
        # Look for super images
        super_images = list(output_dir.rglob("*super*.img"))
        for super_img in super_images:
            self.logger.info(f"📱 Found super image: {super_img.name}")
            self._extract_super_image(super_img, output_dir)
    
    def _process_fastboot_files(self, output_dir: Path):
        """Process Fastboot package files"""
        # Look for sparse images that need conversion
        for img_file in output_dir.rglob("*.img"):
            if self._is_sparse_image(img_file):
                self.logger.info(f"🔄 Converting sparse image: {img_file.name}")
                self._convert_sparse_image(img_file)
        
        # Look for compressed images
        for compressed in output_dir.rglob("*.img.br"):
            self.logger.info(f"🗜️ Decompressing Brotli image: {compressed.name}")
            self._decompress_brotli(compressed)
        
        for compressed in output_dir.rglob("*.img.xz"):
            self.logger.info(f"🗜️ Decompressing XZ image: {compressed.name}")
            self._decompress_xz(compressed)
    
    def _extract_payload(self, payload_file: Path, output_dir: Path):
        """Extract payload.bin using payload-dumper-go"""
        try:
            payload_dir = output_dir / "payload_extracted"
            payload_dir.mkdir(exist_ok=True)
            
            cmd = [
                str(self.config.get_tool_path("payload_extractor")),
                "-o", str(payload_dir),
                str(payload_file)
            ]
            
            result = self._run_command(cmd, check=False)
            
            if result.returncode == 0:
                self.logger.success(f"✅ Extracted payload.bin")
                
                # Move extracted images to main output
                for img in payload_dir.glob("*.img"):
                    dest = output_dir / img.name
                    import shutil
                    shutil.move(str(img), str(dest))
                    self.logger.info(f"  📱 {img.name}")
                    
            else:
                self.logger.warning("⚠️ Payload extraction failed")
                
        except Exception as e:
            self.logger.debug(f"Payload extraction failed: {str(e)}")
    
    def _process_system_image(self, img_file: Path):
        """Process system image file"""
        try:
            # Check if it's a sparse image
            if self._is_sparse_image(img_file):
                self._convert_sparse_image(img_file)
            
            # Check if it's a compressed image
            elif img_file.suffix == '.br':
                self._decompress_brotli(img_file)
            elif img_file.suffix == '.xz':
                self._decompress_xz(img_file)
                
        except Exception as e:
            self.logger.debug(f"Failed to process {img_file.name}: {str(e)}")
    
    def _is_sparse_image(self, img_file: Path) -> bool:
        """Check if image is Android sparse format"""
        try:
            with open(img_file, 'rb') as f:
                magic = f.read(4)
                return magic == b'\x3a\xff\x26\xed'
        except Exception:
            return False
    
    def _convert_sparse_image(self, img_file: Path):
        """Convert sparse image to raw image"""
        try:
            output_file = img_file.with_suffix('.img.raw')
            
            cmd = [
                str(self.config.get_tool_path("simg2img")),
                str(img_file),
                str(output_file)
            ]
            
            result = self._run_command(cmd, check=False)
            
            if result.returncode == 0:
                # Replace original with converted
                img_file.unlink()
                output_file.rename(img_file)
                self.logger.success(f"✅ Converted {img_file.name}")
                
        except Exception as e:
            self.logger.debug(f"Sparse conversion failed: {str(e)}")
    
    def _decompress_brotli(self, compressed_file: Path):
        """Decompress Brotli compressed file"""
        try:
            import brotli
            
            output_file = compressed_file.with_suffix('')  # Remove .br extension
            
            with open(compressed_file, 'rb') as f_in:
                compressed_data = f_in.read()
            
            decompressed_data = brotli.decompress(compressed_data)
            
            with open(output_file, 'wb') as f_out:
                f_out.write(decompressed_data)
            
            # Remove compressed file
            compressed_file.unlink()
            self.logger.success(f"✅ Decompressed {output_file.name}")
            
        except Exception as e:
            self.logger.debug(f"Brotli decompression failed: {str(e)}")
    
    def _decompress_xz(self, compressed_file: Path):
        """Decompress XZ compressed file"""
        try:
            import lzma
            
            output_file = compressed_file.with_suffix('')  # Remove .xz extension
            
            with lzma.open(compressed_file, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    import shutil
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove compressed file
            compressed_file.unlink()
            self.logger.success(f"✅ Decompressed {output_file.name}")
            
        except Exception as e:
            self.logger.debug(f"XZ decompression failed: {str(e)}")
    
    def _extract_super_image(self, super_img: Path, output_dir: Path):
        """Extract super.img using lpunpack"""
        try:
            super_dir = output_dir / "super_extracted"
            super_dir.mkdir(exist_ok=True)
            
            cmd = [str(self.config.get_tool_path("lpunpack")), str(super_img), str(super_dir)]
            
            result = self._run_command(cmd, check=False)
            
            if result.returncode == 0:
                self.logger.success(f"✅ Extracted super image")
                
                # Move extracted partitions to main output
                for partition in super_dir.glob("*.img"):
                    dest = output_dir / partition.name
                    import shutil
                    shutil.move(str(partition), str(dest))
                    self.logger.info(f"  📱 {partition.name}")
                    
                # Remove empty super directory
                import shutil
                shutil.rmtree(super_dir, ignore_errors=True)
                
        except Exception as e:
            self.logger.debug(f"Super image extraction failed: {str(e)}")