"""
Archive extraction functionality
"""

import zipfile
import rarfile
import py7zr
import tarfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole


class ArchiveExtractor:
    """Handles extraction of various archive formats"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        
    def extract(self, file_path: Path, output_dir: Path, 
               firmware_info: Dict[str, Any]) -> bool:
        """Extract archive file"""
        try:
            format_type = firmware_info.get('format', '').lower()
            
            self.console.step(f"Extracting {format_type} archive...")
            
            if format_type in ['.zip']:
                return self._extract_zip(file_path, output_dir)
            elif format_type in ['.rar']:
                return self._extract_rar(file_path, output_dir)
            elif format_type in ['.7z']:
                return self._extract_7z(file_path, output_dir)
            elif format_type in ['.tar', '.tar.gz', '.tgz', '.tar.md5']:
                return self._extract_tar(file_path, output_dir)
            else:
                self.console.error(f"Unsupported archive format: {format_type}")
                return False
                
        except Exception as e:
            self.console.error(f"Archive extraction failed: {e}")
            return False
            
    def _extract_zip(self, file_path: Path, output_dir: Path) -> bool:
        """Extract ZIP archive"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Get total size for progress
                total_size = sum(file.file_size for file in zip_ref.infolist())
                
                with self.console.progress_bar(f"Extracting ZIP") as progress:
                    task = progress.add_task("Extract", total=total_size)
                    extracted_size = 0
                    
                    for file in zip_ref.infolist():
                        zip_ref.extract(file, output_dir)
                        extracted_size += file.file_size
                        progress.update(task, completed=extracted_size)
                        
            self.console.success("ZIP extraction completed")
            return True
            
        except Exception as e:
            self.console.error(f"ZIP extraction failed: {e}")
            return False
            
    def _extract_rar(self, file_path: Path, output_dir: Path) -> bool:
        """Extract RAR archive"""
        try:
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(output_dir)
                
            self.console.success("RAR extraction completed")
            return True
            
        except Exception as e:
            self.console.error(f"RAR extraction failed: {e}")
            return False
            
    def _extract_7z(self, file_path: Path, output_dir: Path) -> bool:
        """Extract 7Z archive"""
        try:
            with py7zr.SevenZipFile(file_path, mode='r') as archive:
                archive.extractall(output_dir)
                
            self.console.success("7Z extraction completed")
            return True
            
        except Exception as e:
            self.console.error(f"7Z extraction failed: {e}")
            return False
            
    def _extract_tar(self, file_path: Path, output_dir: Path) -> bool:
        """Extract TAR archive (including compressed variants)"""
        try:
            # Determine compression mode
            mode = 'r'
            if file_path.suffix.lower() in ['.gz', '.tgz']:
                mode = 'r:gz'
            elif file_path.suffix.lower() in ['.bz2']:
                mode = 'r:bz2'
            elif file_path.suffix.lower() in ['.xz']:
                mode = 'r:xz'
                
            with tarfile.open(file_path, mode) as tar_ref:
                tar_ref.extractall(output_dir)
                
            self.console.success("TAR extraction completed")
            return True
            
        except Exception as e:
            self.console.error(f"TAR extraction failed: {e}")
            return False