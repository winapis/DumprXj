"""
File utilities for DumprX
"""

from pathlib import Path
from typing import Optional
import subprocess
import struct
import magic

from ..core.config import config
from ..core.logger import logger


class FileUtils:
    """File handling utilities"""
    
    def __init__(self):
        self.magic_detector = magic.Magic(mime=True)
    
    def get_file_type(self, file_path: Path) -> str:
        """Get file MIME type"""
        try:
            return self.magic_detector.from_file(str(file_path))
        except Exception:
            return "unknown"
    
    def is_sparse_image(self, file_path: Path) -> bool:
        """Check if file is Android sparse image"""
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                return magic == b'\x3a\xff\x26\xed'
        except Exception:
            return False
    
    def is_android_sparse(self, file_path: Path) -> bool:
        """Check if file is Android sparse format"""
        return self.is_sparse_image(file_path)
    
    def convert_sparse_image(self, img_file: Path) -> Optional[Path]:
        """Convert sparse image to raw image"""
        try:
            output_file = img_file.with_suffix('.img.raw')
            
            cmd = [
                str(config.get_tool_path("simg2img")),
                str(img_file),
                str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Replace original with converted
                img_file.unlink()
                output_file.rename(img_file)
                return img_file
            else:
                logger.debug(f"Sparse conversion failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.debug(f"Sparse conversion failed: {str(e)}")
            return None
    
    def convert_android_sparse(self, img_file: Path) -> Optional[Path]:
        """Convert Android sparse image to raw image"""
        return self.convert_sparse_image(img_file)
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def calculate_hash(self, file_path: Path, algorithm: str = "md5") -> str:
        """Calculate file hash"""
        import hashlib
        
        hash_algo = getattr(hashlib, algorithm)()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_algo.update(chunk)
            return hash_algo.hexdigest()
        except Exception:
            return ""
    
    def is_ext4_image(self, file_path: Path) -> bool:
        """Check if file is ext4 filesystem image"""
        try:
            with open(file_path, 'rb') as f:
                f.seek(1024)  # ext4 superblock offset
                magic_bytes = f.read(2)
                return magic_bytes == b'\x53\xef'  # ext4 magic
        except Exception:
            return False
    
    def get_partition_name(self, file_path: Path) -> str:
        """Extract partition name from filename"""
        name = file_path.stem.lower()
        
        # Remove common suffixes
        suffixes_to_remove = ['_a', '_b', '-sign', '_new', '_image', '.emmc']
        for suffix in suffixes_to_remove:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        
        return name