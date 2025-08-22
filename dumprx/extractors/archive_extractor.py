"""
Archive extractor for ZIP, RAR, 7Z, TAR files.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any

from ..core.detector import FirmwareType
from . import BaseExtractor, ExtractionError

class ArchiveExtractor(BaseExtractor):
    """Extractor for archive files (ZIP, RAR, 7Z, TAR)."""
    
    def can_extract(self, firmware_type: FirmwareType) -> bool:
        """Check if this extractor can handle archive files."""
        return firmware_type in [
            FirmwareType.ZIP_ARCHIVE,
            FirmwareType.TAR_MD5,
            FirmwareType.TGZ
        ]
    
    def extract(self, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract archive file."""
        file_path = Path(filepath)
        
        # Determine firmware type from metadata or file extension
        firmware_type = metadata.get('firmware_type')
        if firmware_type is None:
            # Infer from file extension
            if file_path.suffix.lower() == '.tgz' or file_path.name.endswith('.tar.gz'):
                firmware_type = FirmwareType.TGZ
            elif file_path.name.endswith('.tar.md5'):
                firmware_type = FirmwareType.TAR_MD5
            else:
                firmware_type = FirmwareType.ZIP_ARCHIVE
        
        if firmware_type == FirmwareType.TGZ:
            return self._extract_tgz(file_path, metadata)
        elif firmware_type == FirmwareType.TAR_MD5:
            return self._extract_tar_md5(file_path, metadata)
        else:
            return self._extract_general_archive(file_path, metadata)
    
    def _extract_general_archive(self, file_path: Path, metadata: Dict[str, Any]) -> List[str]:
        """Extract general archive files."""
        self.logger.step(1, 3, "Preparing archive extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy file to temp directory
        input_file = self.copy_input_file(str(file_path), temp_dir)
        
        self.logger.step(2, 3, f"Extracting {file_path.suffix} archive")
        
        try:
            # Use 7zip for extraction
            sevenzip_cmd = self.config.tools.sevenzip
            
            cmd = [sevenzip_cmd, "x", "-y", str(input_file)]
            
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            if result.returncode != 0:
                raise ExtractionError(f"Archive extraction failed: {result.stderr}")
            
            self.logger.step(3, 3, "Collecting extracted files")
            
            # Collect all extracted files
            extracted_files = []
            for file in temp_dir.rglob("*"):
                if file.is_file() and file != input_file:
                    extracted_files.append(str(file))
            
            if not extracted_files:
                raise ExtractionError("No files extracted from archive")
            
            # Move files to output directory
            final_files = []
            for file_path in extracted_files:
                file = Path(file_path)
                if file.exists():
                    # Preserve directory structure
                    rel_path = file.relative_to(temp_dir)
                    dest_path = self.output_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    file.rename(dest_path)
                    final_files.append(str(dest_path))
            
            return final_files
            
        except subprocess.TimeoutExpired:
            raise ExtractionError("Archive extraction timeout")
        except Exception as e:
            raise ExtractionError(f"Archive extraction error: {str(e)}")
    
    def _extract_tgz(self, file_path: Path, metadata: Dict[str, Any]) -> List[str]:
        """Extract TGZ (Xiaomi gzipped tar) files."""
        self.logger.step(1, 3, "Preparing TGZ extraction")
        temp_dir = self.prepare_extraction()
        
        self.logger.step(2, 3, "Extracting TGZ archive")
        
        try:
            # Use tar for TGZ extraction
            cmd = [
                "tar", "xzvf", str(file_path),
                "-C", str(temp_dir),
                "--transform=s/.*\\///"  # Flatten directory structure
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode != 0:
                raise ExtractionError(f"TGZ extraction failed: {result.stderr}")
            
            self.logger.step(3, 3, "Collecting extracted files")
            
            # Collect extracted files
            extracted_files = []
            for file in temp_dir.rglob("*"):
                if file.is_file():
                    extracted_files.append(str(file))
            
            # Remove empty directories
            for dir_path in temp_dir.rglob("*"):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
            
            # Move files to output directory
            final_files = []
            for file_path in extracted_files:
                file = Path(file_path)
                if file.exists():
                    dest_path = self.output_dir / file.name
                    file.rename(dest_path)
                    final_files.append(str(dest_path))
            
            return final_files
            
        except subprocess.TimeoutExpired:
            raise ExtractionError("TGZ extraction timeout")
        except Exception as e:
            raise ExtractionError(f"TGZ extraction error: {str(e)}")
    
    def _extract_tar_md5(self, file_path: Path, metadata: Dict[str, Any]) -> List[str]:
        """Extract TAR.MD5 (Samsung) files.""" 
        self.logger.step(1, 3, "Preparing TAR.MD5 extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy file to temp directory
        input_file = self.copy_input_file(str(file_path), temp_dir)
        
        self.logger.step(2, 3, "Extracting TAR.MD5 archive")
        
        try:
            # Samsung tar.md5 files are just tar files
            cmd = ["tar", "xvf", str(input_file), "-C", str(temp_dir)]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode != 0:
                raise ExtractionError(f"TAR.MD5 extraction failed: {result.stderr}")
            
            self.logger.step(3, 3, "Collecting extracted files")
            
            # Collect extracted files
            extracted_files = []
            for file in temp_dir.rglob("*"):
                if file.is_file() and file != input_file:
                    extracted_files.append(str(file))
            
            # Move files to output directory  
            final_files = []
            for file_path in extracted_files:
                file = Path(file_path)
                if file.exists():
                    dest_path = self.output_dir / file.name
                    file.rename(dest_path)
                    final_files.append(str(dest_path))
            
            return final_files
            
        except subprocess.TimeoutExpired:
            raise ExtractionError("TAR.MD5 extraction timeout")
        except Exception as e:
            raise ExtractionError(f"TAR.MD5 extraction error: {str(e)}")