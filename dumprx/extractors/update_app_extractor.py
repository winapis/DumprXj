"""
UPDATE.APP (Huawei) extractor.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any

from ..core.detector import FirmwareType
from . import BaseExtractor, ExtractionError

class UpdateAppExtractor(BaseExtractor):
    """Extractor for Huawei UPDATE.APP files."""
    
    def can_extract(self, firmware_type: FirmwareType) -> bool:
        """Check if this extractor can handle UPDATE.APP files."""
        return firmware_type == FirmwareType.UPDATE_APP
    
    def extract(self, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract UPDATE.APP file."""
        self.logger.step(1, 3, "Preparing UPDATE.APP extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy file to temp directory
        input_file = self.copy_input_file(filepath, temp_dir)
        
        self.logger.step(2, 3, "Extracting UPDATE.APP")
        
        # Path to splituapp tool
        splituapp_tool = Path(self.config.get_utils_dir()) / "splituapp.py"
        
        if not splituapp_tool.exists():
            raise ExtractionError(f"splituapp tool not found: {splituapp_tool}")
        
        try:
            # Extract UPDATE.APP
            cmd = [
                "python3", str(splituapp_tool),
                "-f", str(input_file)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            if result.returncode != 0:
                raise ExtractionError(f"UPDATE.APP extraction failed: {result.stderr}")
            
            self.logger.step(3, 3, "Collecting extracted images")
            
            # Find extracted files in output directory
            output_dir = temp_dir / "output"
            extracted_files = []
            
            if output_dir.exists():
                for file in output_dir.rglob("*"):
                    if file.is_file():
                        extracted_files.append(str(file))
            
            # Also check temp directory for extracted files
            for file in temp_dir.glob("*.img"):
                if file != input_file:
                    extracted_files.append(str(file))
            
            if not extracted_files:
                raise ExtractionError("No files extracted from UPDATE.APP")
            
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
            raise ExtractionError("UPDATE.APP extraction timeout")
        except Exception as e:
            raise ExtractionError(f"UPDATE.APP extraction error: {str(e)}")