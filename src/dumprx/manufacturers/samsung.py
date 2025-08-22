"""
Samsung firmware extractor (TAR.MD5, PIT files)
"""

from pathlib import Path
import tarfile
import hashlib

from .base import BaseExtractor


class SamsungExtractor(BaseExtractor):
    """Samsung firmware extractor for TAR.MD5 and PIT files"""
    
    def extract(self, file_path: Path, output_dir: Path) -> bool:
        """Extract Samsung firmware"""
        self.logger.info("🔄 Extracting Samsung firmware...")
        
        filename = file_path.name.lower()
        
        if filename.endswith('.tar.md5'):
            return self._extract_tar_md5(file_path, output_dir)
        elif filename.endswith('.tar'):
            return self._extract_tar(file_path, output_dir)
        elif filename.endswith('.pit'):
            return self._extract_pit(file_path, output_dir)
        else:
            # Try generic extraction
            return self._extract_with_7zz(file_path, output_dir)
    
    def _extract_tar_md5(self, file_path: Path, output_dir: Path) -> bool:
        """Extract TAR.MD5 file with MD5 verification"""
        try:
            # Read MD5 hash from filename or separate file
            md5_hash = self._get_md5_hash(file_path)
            
            if md5_hash:
                # Verify MD5 hash
                self.logger.info("🔐 Verifying MD5 hash...")
                if not self._verify_md5(file_path, md5_hash):
                    self.logger.warning("⚠️ MD5 verification failed, continuing anyway...")
                else:
                    self.logger.success("✅ MD5 verification passed")
            
            # Extract TAR content
            return self._extract_tar(file_path, output_dir)
            
        except Exception as e:
            self.logger.error(f"TAR.MD5 extraction failed: {str(e)}")
            return False
    
    def _extract_tar(self, file_path: Path, output_dir: Path) -> bool:
        """Extract TAR file"""
        try:
            self.logger.info(f"📦 Extracting TAR archive: {file_path.name}")
            
            with tarfile.open(file_path, 'r') as tar:
                tar.extractall(output_dir)
            
            # Look for IMG files in extracted content
            extracted_imgs = list(output_dir.glob("*.img"))
            if extracted_imgs:
                self.logger.success(f"✅ Extracted {len(extracted_imgs)} IMG files")
                
                # Log extracted partitions
                for img in extracted_imgs:
                    size = self._format_size(img.stat().st_size)
                    self.logger.info(f"  📱 {img.name} ({size})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"TAR extraction failed: {str(e)}")
            return False
    
    def _extract_pit(self, file_path: Path, output_dir: Path) -> bool:
        """Extract PIT file (Partition Information Table)"""
        try:
            self.logger.info(f"📋 Processing PIT file: {file_path.name}")
            
            # Copy PIT file to output directory
            dest_path = output_dir / file_path.name
            import shutil
            shutil.copy2(file_path, dest_path)
            
            # Parse PIT file for partition information
            pit_info = self._parse_pit_file(file_path)
            if pit_info:
                # Save partition information
                info_file = output_dir / "pit_info.txt"
                with open(info_file, 'w') as f:
                    f.write("Samsung PIT (Partition Information Table)\n")
                    f.write("=" * 50 + "\n\n")
                    for partition in pit_info:
                        f.write(f"Name: {partition.get('name', 'Unknown')}\n")
                        f.write(f"Size: {partition.get('size', 'Unknown')}\n")
                        f.write(f"Offset: {partition.get('offset', 'Unknown')}\n")
                        f.write("-" * 30 + "\n")
                
                self.logger.success(f"✅ PIT info saved to pit_info.txt")
            
            return True
            
        except Exception as e:
            self.logger.error(f"PIT extraction failed: {str(e)}")
            return False
    
    def _get_md5_hash(self, file_path: Path) -> str:
        """Get MD5 hash from filename or separate file"""
        # Try to find MD5 in filename
        filename = file_path.name
        if '.md5' in filename:
            # Extract MD5 from filename pattern
            parts = filename.split('_')
            for part in parts:
                if len(part) == 32 and all(c in '0123456789abcdef' for c in part.lower()):
                    return part.lower()
        
        # Try to find separate MD5 file
        md5_file = file_path.with_suffix('.md5')
        if md5_file.exists():
            try:
                with open(md5_file, 'r') as f:
                    return f.read().strip().split()[0]
            except Exception:
                pass
        
        return ""
    
    def _verify_md5(self, file_path: Path, expected_md5: str) -> bool:
        """Verify MD5 hash of file"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            
            calculated_md5 = hasher.hexdigest().lower()
            return calculated_md5 == expected_md5.lower()
            
        except Exception:
            return False
    
    def _parse_pit_file(self, file_path: Path) -> list:
        """Parse Samsung PIT file for partition information"""
        try:
            partitions = []
            
            with open(file_path, 'rb') as f:
                # Skip PIT header (first 28 bytes)
                f.seek(28)
                
                # Read partition count
                partition_count_data = f.read(4)
                if len(partition_count_data) < 4:
                    return partitions
                
                partition_count = int.from_bytes(partition_count_data, byteorder='little')
                
                # Read each partition entry (132 bytes each)
                for i in range(min(partition_count, 100)):  # Limit to prevent infinite loop
                    entry_data = f.read(132)
                    if len(entry_data) < 132:
                        break
                    
                    # Parse partition entry
                    partition = self._parse_pit_entry(entry_data)
                    if partition:
                        partitions.append(partition)
            
            return partitions
            
        except Exception as e:
            self.logger.debug(f"PIT parsing failed: {str(e)}")
            return []
    
    def _parse_pit_entry(self, entry_data: bytes) -> dict:
        """Parse individual PIT partition entry"""
        try:
            # Extract partition name (32 bytes, null-terminated)
            name_data = entry_data[0:32]
            name = name_data.rstrip(b'\x00').decode('ascii', errors='ignore')
            
            # Extract size and offset (simplified parsing)
            if len(name) > 0:
                return {
                    'name': name,
                    'size': 'Unknown',
                    'offset': 'Unknown'
                }
            
        except Exception:
            pass
        
        return None
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"