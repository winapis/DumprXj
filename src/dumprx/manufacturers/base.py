"""
Base extractor class for manufacturer-specific firmware extraction
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess
import shutil
import tempfile

from ..core.config import config
from ..core.logger import logger


class BaseExtractor(ABC):
    """Base class for all manufacturer extractors"""
    
    def __init__(self):
        self.config = config
        self.logger = logger
        
    @abstractmethod
    def extract(self, file_path: Path, output_dir: Path) -> bool:
        """
        Extract firmware from file
        
        Args:
            file_path: Path to firmware file
            output_dir: Directory to extract to
            
        Returns:
            bool: True if extraction successful
        """
        pass
    
    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None, 
                    check: bool = True) -> subprocess.CompletedProcess:
        """Run a system command"""
        try:
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check
            )
            
            if result.stdout:
                self.logger.debug(f"Command output: {result.stdout}")
            if result.stderr:
                self.logger.debug(f"Command error: {result.stderr}")
                
            return result
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(cmd)}")
            self.logger.error(f"Error output: {e.stderr}")
            raise
        except FileNotFoundError:
            self.logger.error(f"Command not found: {cmd[0]}")
            raise
    
    def _extract_with_7zz(self, archive_path: Path, output_dir: Path, 
                         password: Optional[str] = None) -> bool:
        """Extract archive using 7zz"""
        try:
            cmd = [str(config.get_tool_path("7zz")), "x", "-y", str(archive_path)]
            
            if password:
                cmd.extend([f"-p{password}"])
                
            # Change to output directory
            original_cwd = Path.cwd()
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                result = self._run_command(cmd, cwd=output_dir, check=False)
                return result.returncode == 0
            finally:
                # Change back to original directory
                import os
                os.chdir(original_cwd)
                
        except Exception as e:
            self.logger.error(f"7zz extraction failed: {str(e)}")
            return False
    
    def _extract_with_python_script(self, script_name: str, file_path: Path, 
                                  output_dir: Path, *args) -> bool:
        """Extract using Python script"""
        try:
            script_path = config.get_tool_path(script_name)
            if not script_path.exists():
                self.logger.error(f"Script not found: {script_path}")
                return False
            
            cmd = ["python3", str(script_path), str(file_path)] + list(args)
            result = self._run_command(cmd, cwd=output_dir, check=False)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Python script extraction failed: {str(e)}")
            return False
    
    def _extract_with_binary(self, binary_name: str, file_path: Path,
                           output_dir: Path, *args) -> bool:
        """Extract using binary tool"""
        try:
            binary_path = config.get_tool_path(binary_name)
            if not binary_path.exists():
                self.logger.error(f"Binary not found: {binary_path}")
                return False
            
            cmd = [str(binary_path)] + list(args) + [str(file_path)]
            result = self._run_command(cmd, cwd=output_dir, check=False)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Binary extraction failed: {str(e)}")
            return False
    
    def _move_extracted_files(self, src_dir: Path, dest_dir: Path, 
                            patterns: List[str] = None) -> List[Path]:
        """Move extracted files matching patterns"""
        moved_files = []
        
        if not patterns:
            patterns = ["*.img", "*.bin", "*.ext4"]
        
        for pattern in patterns:
            for file_path in src_dir.rglob(pattern):
                if file_path.is_file():
                    dest_path = dest_dir / file_path.name
                    shutil.move(str(file_path), str(dest_path))
                    moved_files.append(dest_path)
        
        return moved_files
    
    def _cleanup_temp_files(self, temp_dir: Path, keep_patterns: List[str] = None):
        """Clean up temporary files, keeping specified patterns"""
        if not keep_patterns:
            keep_patterns = ["*.img", "*.bin", "*.txt"]
        
        for file_path in temp_dir.rglob("*"):
            if file_path.is_file():
                should_keep = any(file_path.match(pattern) for pattern in keep_patterns)
                if not should_keep:
                    try:
                        file_path.unlink()
                    except Exception:
                        pass