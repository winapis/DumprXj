"""
OPS (OnePlus/Oppo ops) extractor.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any

from ..core.detector import FirmwareType
from . import BaseExtractor, ExtractionError

class OpsExtractor(BaseExtractor):
    """Extractor for OPS files."""
    
    def can_extract(self, firmware_type: FirmwareType) -> bool:
        """Check if this extractor can handle OPS files."""
        return firmware_type == FirmwareType.OPS
    
    def extract(self, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract OPS file."""
        self.logger.step(1, 3, "Preparing OPS extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy file to temp directory
        input_file = self.copy_input_file(filepath, temp_dir)
        
        self.logger.step(2, 3, "Decrypting OPS file")
        
        # Path to ops decryption tool
        ops_tool = Path(self.config.get_utils_dir()) / "oppo_decrypt" / "opscrypto.py"
        
        if not ops_tool.exists():
            raise ExtractionError(f"OPS decryption tool not found: {ops_tool}")
        
        try:
            # Run OPS decryption
            cmd = [
                "uv", "run",
                "--with-requirements", str(ops_tool.parent / "requirements.txt"),
                str(ops_tool),
                "decrypt",
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
                raise ExtractionError(f"OPS decryption failed: {result.stderr}")
            
            self.logger.step(3, 3, "Collecting extracted files")
            
            # Find extracted files in 'extract' directory
            extract_dir = temp_dir / "extract"
            extracted_files = []
            
            if extract_dir.exists():
                for file in extract_dir.rglob("*"):
                    if file.is_file():
                        extracted_files.append(str(file))
            
            if not extracted_files:
                raise ExtractionError("No files extracted from OPS")
            
            # Move extracted files to output directory
            final_files = []
            for file_path in extracted_files:
                file = Path(file_path)
                if file.exists():
                    # Preserve relative path structure
                    rel_path = file.relative_to(extract_dir)
                    dest_path = self.output_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    file.rename(dest_path)
                    final_files.append(str(dest_path))
            
            return final_files
            
        except subprocess.TimeoutExpired:
            raise ExtractionError("OPS decryption timeout")
        except Exception as e:
            raise ExtractionError(f"OPS extraction error: {str(e)}")