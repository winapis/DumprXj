"""
OZIP (Oppo/Realme encrypted zip) extractor.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any

from ..core.detector import FirmwareType
from . import BaseExtractor, ExtractionError

class OzipExtractor(BaseExtractor):
    """Extractor for OZIP files."""
    
    def can_extract(self, firmware_type: FirmwareType) -> bool:
        """Check if this extractor can handle OZIP files."""
        return firmware_type == FirmwareType.OZIP
    
    def extract(self, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract OZIP file."""
        self.logger.step(1, 3, "Preparing OZIP extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy file to temp directory
        input_file = self.copy_input_file(filepath, temp_dir)
        
        self.logger.step(2, 3, "Decrypting OZIP file")
        
        # Path to ozipdecrypt tool
        ozip_tool = Path(self.config.get_utils_dir()) / "oppo_ozip_decrypt" / "ozipdecrypt.py"
        
        if not ozip_tool.exists():
            raise ExtractionError(f"OZIP decryption tool not found: {ozip_tool}")
        
        try:
            # Run OZIP decryption
            cmd = [
                "uv", "run", 
                "--with-requirements", str(ozip_tool.parent / "requirements.txt"),
                str(ozip_tool),
                str(input_file)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )
            
            if result.returncode != 0:
                raise ExtractionError(f"OZIP decryption failed: {result.stderr}")
            
            self.logger.step(3, 3, "Collecting extracted files")
            
            # Find extracted files
            extracted_files = []
            
            # Look for decrypted zip file
            zip_files = list(temp_dir.glob("*.zip"))
            if zip_files:
                extracted_files.extend([str(f) for f in zip_files])
            
            # Look for 'out' directory with extracted content
            out_dir = temp_dir / "out"
            if out_dir.exists():
                for file in out_dir.rglob("*"):
                    if file.is_file():
                        extracted_files.append(str(file))
            
            if not extracted_files:
                raise ExtractionError("No files extracted from OZIP")
            
            # Move extracted files to output directory
            final_files = []
            for file_path in extracted_files:
                file = Path(file_path)
                if file.exists():
                    dest_path = self.output_dir / file.name
                    file.rename(dest_path)
                    final_files.append(str(dest_path))
            
            return final_files
            
        except subprocess.TimeoutExpired:
            raise ExtractionError("OZIP decryption timeout")
        except Exception as e:
            raise ExtractionError(f"OZIP extraction error: {str(e)}")