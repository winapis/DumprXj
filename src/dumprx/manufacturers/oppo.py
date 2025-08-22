"""
OPPO/OnePlus firmware extractor (OZIP, OFP, OPS decryption)
"""

from pathlib import Path
import struct

from .base import BaseExtractor


class OppoExtractor(BaseExtractor):
    """OPPO/OnePlus firmware extractor for OZIP, OFP, and OPS files"""
    
    def extract(self, file_path: Path, output_dir: Path) -> bool:
        """Extract OPPO/OnePlus firmware"""
        self.logger.info("🔄 Extracting OPPO/OnePlus firmware...")
        
        filename = file_path.name.lower()
        
        if filename.endswith('.ozip'):
            return self._extract_ozip(file_path, output_dir)
        elif filename.endswith('.ofp'):
            return self._extract_ofp(file_path, output_dir)
        elif filename.endswith('.ops'):
            return self._extract_ops(file_path, output_dir)
        else:
            # Check magic bytes
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(12)
                    if header.startswith(b'OPPOENCRYPT!'):
                        return self._extract_ozip(file_path, output_dir)
            except Exception:
                pass
            
            return self._extract_with_7zz(file_path, output_dir)
    
    def _extract_ozip(self, file_path: Path, output_dir: Path) -> bool:
        """Extract OZIP encrypted file"""
        try:
            self.logger.info("🔐 Decrypting OZIP file...")
            
            # Use ozipdecrypt.py tool
            success = self._extract_with_python_script(
                "ozipdecrypt", file_path, output_dir
            )
            
            if success:
                self.logger.success("✅ OZIP decryption completed")
                
                # Look for decrypted files
                decrypted_files = list(output_dir.glob("*.zip"))
                if decrypted_files:
                    # Extract the decrypted ZIP
                    for zip_file in decrypted_files:
                        self.logger.info(f"📦 Extracting decrypted ZIP: {zip_file.name}")
                        self._extract_with_7zz(zip_file, output_dir)
                
                return True
            else:
                self.logger.error("❌ OZIP decryption failed")
                return False
                
        except Exception as e:
            self.logger.error(f"OZIP extraction failed: {str(e)}")
            return False
    
    def _extract_ofp(self, file_path: Path, output_dir: Path) -> bool:
        """Extract OFP file"""
        try:
            self.logger.info("🔓 Processing OFP file...")
            
            # Detect OFP type (Qualcomm or MediaTek)
            ofp_type = self._detect_ofp_type(file_path)
            
            if ofp_type == "qualcomm":
                script_name = "ofp_qc_decrypt"
                self.logger.info("📱 Detected Qualcomm OFP")
            elif ofp_type == "mediatek":
                script_name = "ofp_mtk_decrypt"
                self.logger.info("📱 Detected MediaTek OFP")
            else:
                # Try both
                self.logger.info("📱 Unknown OFP type, trying Qualcomm first...")
                script_name = "ofp_qc_decrypt"
            
            # Use appropriate extraction script
            success = self._extract_with_python_script(
                script_name, file_path, output_dir
            )
            
            if not success and ofp_type == "unknown":
                self.logger.info("📱 Qualcomm failed, trying MediaTek...")
                success = self._extract_with_python_script(
                    "ofp_mtk_decrypt", file_path, output_dir
                )
            
            if success:
                self.logger.success("✅ OFP extraction completed")
                
                # Process extracted images
                self._process_extracted_images(output_dir)
                return True
            else:
                self.logger.error("❌ OFP extraction failed")
                return False
                
        except Exception as e:
            self.logger.error(f"OFP extraction failed: {str(e)}")
            return False
    
    def _extract_ops(self, file_path: Path, output_dir: Path) -> bool:
        """Extract OPS file"""
        try:
            self.logger.info("🔐 Decrypting OPS file...")
            
            # Use opscrypto.py tool
            success = self._extract_with_python_script(
                "opsdecrypt", file_path, output_dir
            )
            
            if success:
                self.logger.success("✅ OPS decryption completed")
                
                # Process any extracted archives
                for archive in output_dir.glob("*.zip"):
                    self.logger.info(f"📦 Extracting {archive.name}")
                    self._extract_with_7zz(archive, output_dir)
                
                return True
            else:
                self.logger.error("❌ OPS decryption failed")
                return False
                
        except Exception as e:
            self.logger.error(f"OPS extraction failed: {str(e)}")
            return False
    
    def _detect_ofp_type(self, file_path: Path) -> str:
        """Detect OFP type (Qualcomm or MediaTek)"""
        try:
            with open(file_path, 'rb') as f:
                # Read header to detect type
                header = f.read(1024)
                
                # Look for MediaTek signatures
                if b'MTK' in header or b'BROM' in header:
                    return "mediatek"
                
                # Look for Qualcomm signatures  
                if b'QCOM' in header or b'QTI' in header:
                    return "qualcomm"
                
                # Check file structure
                f.seek(0)
                try:
                    # Try to read as Qualcomm format
                    magic = struct.unpack('<I', f.read(4))[0]
                    if magic in [0x7367676F, 0x676F6373]:  # Common Qualcomm magic
                        return "qualcomm"
                except Exception:
                    pass
                
        except Exception:
            pass
        
        return "unknown"
    
    def _process_extracted_images(self, output_dir: Path):
        """Process extracted image files"""
        # Look for system images that need further processing
        for img_file in output_dir.glob("*.img"):
            self._process_single_image(img_file)
        
        # Look for super.img that needs unpacking
        super_imgs = list(output_dir.glob("*super*.img"))
        for super_img in super_imgs:
            self.logger.info(f"📱 Found super image: {super_img.name}")
            self._extract_super_image(super_img, output_dir)
    
    def _process_single_image(self, img_file: Path):
        """Process a single image file"""
        try:
            # Check if it's a sparse image
            with open(img_file, 'rb') as f:
                magic = f.read(4)
                if magic == b'\x3a\xff\x26\xed':  # Android sparse magic
                    self.logger.info(f"🔄 Converting sparse image: {img_file.name}")
                    self._convert_sparse_image(img_file)
                    
        except Exception as e:
            self.logger.debug(f"Failed to process {img_file.name}: {str(e)}")
    
    def _convert_sparse_image(self, img_file: Path):
        """Convert sparse image to raw image"""
        try:
            output_file = img_file.with_suffix('.img.raw')
            
            success = self._extract_with_binary(
                "simg2img", img_file, img_file.parent, 
                str(img_file), str(output_file)
            )
            
            if success:
                # Replace original with converted
                img_file.unlink()
                output_file.rename(img_file)
                self.logger.success(f"✅ Converted {img_file.name}")
                
        except Exception as e:
            self.logger.debug(f"Sparse conversion failed: {str(e)}")
    
    def _extract_super_image(self, super_img: Path, output_dir: Path):
        """Extract super.img using lpunpack"""
        try:
            # Create directory for super image contents
            super_dir = output_dir / "super_extracted"
            super_dir.mkdir(exist_ok=True)
            
            # Use lpunpack to extract super image
            cmd = [str(self.config.get_tool_path("lpunpack")), str(super_img), str(super_dir)]
            
            result = self._run_command(cmd, check=False)
            
            if result.returncode == 0:
                self.logger.success(f"✅ Extracted super image to {super_dir.name}")
                
                # Move extracted partitions to main output
                for partition in super_dir.glob("*.img"):
                    dest = output_dir / partition.name
                    import shutil
                    shutil.move(str(partition), str(dest))
                    self.logger.info(f"  📱 {partition.name}")
                    
                # Remove empty super directory
                import shutil
                shutil.rmtree(super_dir, ignore_errors=True)
                
            else:
                self.logger.warning(f"⚠️ Super image extraction failed")
                
        except Exception as e:
            self.logger.debug(f"Super image extraction failed: {str(e)}")