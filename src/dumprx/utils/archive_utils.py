"""
Archive handling utilities
"""

from pathlib import Path
import subprocess
import tempfile
import shutil

from ..core.config import config
from ..core.logger import logger


class ArchiveUtils:
    """Archive extraction utilities"""
    
    def extract(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract archive using appropriate method"""
        
        # Try 7zz first (handles most formats)
        if self._extract_with_7zz(archive_path, output_dir):
            return True
        
        # Try Python libraries as fallback
        return self._extract_with_python(archive_path, output_dir)
    
    def _extract_with_7zz(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract using 7zz"""
        try:
            cmd = [
                str(config.get_tool_path("7zz")),
                "x", "-y",
                str(archive_path)
            ]
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Run extraction
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            
            success = result.returncode == 0
            if success:
                logger.debug(f"7zz extraction successful: {archive_path.name}")
            else:
                logger.debug(f"7zz extraction failed: {result.stderr}")
                
            return success
            
        except Exception as e:
            logger.debug(f"7zz extraction error: {str(e)}")
            return False
    
    def _extract_with_python(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract using Python libraries"""
        filename = archive_path.name.lower()
        
        try:
            if filename.endswith('.zip'):
                return self._extract_zip(archive_path, output_dir)
            elif filename.endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz')):
                return self._extract_tar(archive_path, output_dir)
            elif filename.endswith('.rar'):
                return self._extract_rar(archive_path, output_dir)
            elif filename.endswith('.7z'):
                return self._extract_7z(archive_path, output_dir)
                
        except Exception as e:
            logger.debug(f"Python extraction failed: {str(e)}")
            
        return False
    
    def _extract_zip(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract ZIP file"""
        import zipfile
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_file:
                zip_file.extractall(output_dir)
            return True
        except Exception:
            return False
    
    def _extract_tar(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract TAR file"""
        import tarfile
        
        try:
            with tarfile.open(archive_path, 'r:*') as tar_file:
                tar_file.extractall(output_dir)
            return True
        except Exception:
            return False
    
    def _extract_rar(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract RAR file"""
        try:
            import rarfile
            with rarfile.RarFile(archive_path) as rar_file:
                rar_file.extractall(output_dir)
            return True
        except ImportError:
            logger.debug("rarfile library not available")
            return False
        except Exception:
            return False
    
    def _extract_7z(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract 7z file"""
        try:
            import py7zr
            with py7zr.SevenZipFile(archive_path, mode='r') as archive:
                archive.extractall(output_dir)
            return True
        except ImportError:
            logger.debug("py7zr library not available")
            return False
        except Exception:
            return False