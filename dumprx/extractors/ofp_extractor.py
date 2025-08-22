"""
OFP (Oppo ofp) extractor.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any

from ..core.detector import FirmwareType
from . import BaseExtractor, ExtractionError

class OfpExtractor(BaseExtractor):
    """Extractor for OFP files."""
    
    def can_extract(self, firmware_type: FirmwareType) -> bool:
        """Check if this extractor can handle OFP files."""
        return firmware_type == FirmwareType.OFP
    
    def extract(self, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract OFP file."""
        self.logger.step(1, 4, "Preparing OFP extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy file to temp directory
        input_file = self.copy_input_file(filepath, temp_dir)
        
        self.logger.step(2, 4, "Trying Qualcomm OFP decryption")
        
        # Path to OFP decryption tools
        ofp_qc_tool = Path(self.config.get_utils_dir()) / "oppo_decrypt" / "ofp_qc_decrypt.py"
        ofp_mtk_tool = Path(self.config.get_utils_dir()) / "oppo_decrypt" / "ofp_mtk_decrypt.py"
        
        if not ofp_qc_tool.exists() or not ofp_mtk_tool.exists():
            raise ExtractionError(f"OFP decryption tools not found")
        
        output_dir = temp_dir / "out"
        output_dir.mkdir(exist_ok=True)
        
        # Try Qualcomm OFP first
        success = self._try_ofp_decrypt(ofp_qc_tool, input_file, output_dir, "Qualcomm")
        
        if not success:
            self.logger.step(3, 4, "Trying MediaTek OFP decryption")
            success = self._try_ofp_decrypt(ofp_mtk_tool, input_file, output_dir, "MediaTek")
        
        if not success:
            raise ExtractionError("OFP decryption failed with both Qualcomm and MediaTek methods")
        
        self.logger.step(4, 4, "Collecting extracted files")
        
        # Find extracted files
        extracted_files = []
        if output_dir.exists():
            for file in output_dir.rglob("*"):
                if file.is_file():
                    extracted_files.append(str(file))
        
        if not extracted_files:
            raise ExtractionError("No files extracted from OFP")
        
        # Move extracted files to final output directory
        final_files = []
        for file_path in extracted_files:
            file = Path(file_path)
            if file.exists():
                dest_path = self.output_dir / file.name
                file.rename(dest_path)
                final_files.append(str(dest_path))
        
        return final_files
    
    def _try_ofp_decrypt(self, tool_path: Path, input_file: Path, output_dir: Path, method: str) -> bool:
        """
        Try OFP decryption with specified tool.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [
                "uv", "run",
                "--with-requirements", str(tool_path.parent / "requirements.txt"),
                str(tool_path),
                str(input_file),
                str(output_dir)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=output_dir.parent,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )
            
            if result.returncode == 0:
                # Check if key files were extracted to verify success
                key_files = ["boot.img", "userdata.img"]
                if any((output_dir / f).exists() for f in key_files):
                    self.logger.success(f"{method} OFP decryption successful")
                    return True
            
            return False
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"{method} OFP decryption timeout")
            return False
        except Exception as e:
            self.logger.warning(f"{method} OFP decryption error: {str(e)}")
            return False