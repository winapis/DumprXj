"""
KDZ (LG KDZ) extractor.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any

from ..core.detector import FirmwareType
from . import BaseExtractor, ExtractionError

class KdzExtractor(BaseExtractor):
    """Extractor for KDZ files."""
    
    def can_extract(self, firmware_type: FirmwareType) -> bool:
        """Check if this extractor can handle KDZ files."""
        return firmware_type == FirmwareType.KDZ
    
    def extract(self, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract KDZ file."""
        self.logger.step(1, 4, "Preparing KDZ extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy file to temp directory
        input_file = self.copy_input_file(filepath, temp_dir)
        
        self.logger.step(2, 4, "Extracting KDZ file")
        
        # Path to KDZ extraction tools
        kdz_tool = Path(self.config.get_utils_dir()) / "kdztools" / "unkdz.py"
        dz_tool = Path(self.config.get_utils_dir()) / "kdztools" / "undz.py"
        
        if not kdz_tool.exists() or not dz_tool.exists():
            raise ExtractionError(f"KDZ extraction tools not found")
        
        try:
            # Extract KDZ file to get DZ file
            cmd = [
                "python3", str(kdz_tool),
                "-f", str(input_file),
                "-x", "-o", "."
            ]
            
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                raise ExtractionError(f"KDZ extraction failed: {result.stderr}")
            
            self.logger.step(3, 4, "Extracting DZ partitions")
            
            # Find DZ file
            dz_files = list(temp_dir.glob("*.dz"))
            if not dz_files:
                raise ExtractionError("No DZ file found after KDZ extraction")
            
            dz_file = dz_files[0]
            
            # Extract all partitions from DZ file
            cmd = [
                "python3", str(dz_tool),
                "-f", str(dz_file),
                "-s", "-o", "."
            ]
            
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=1200  # 20 minutes for partition extraction
            )
            
            if result.returncode != 0:
                raise ExtractionError(f"DZ extraction failed: {result.stderr}")
            
            self.logger.step(4, 4, "Collecting extracted partitions")
            
            # Find all extracted files (excluding the original KDZ and DZ files)
            extracted_files = []
            for file in temp_dir.glob("*"):
                if file.is_file() and file.suffix not in ['.kdz', '.dz']:
                    extracted_files.append(str(file))
            
            if not extracted_files:
                raise ExtractionError("No partitions extracted from DZ file")
            
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
            raise ExtractionError("KDZ extraction timeout")
        except Exception as e:
            raise ExtractionError(f"KDZ extraction error: {str(e)}")