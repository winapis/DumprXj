import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HTCExtractor:
    def __init__(self, utils_dir: Path):
        self.utils_dir = utils_dir
        self.ruu_decrypt = utils_dir / "RUU_Decrypt_Tool"
    
    def extract_ruu(self, ruu_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting HTC RUU: {ruu_path}")
        
        cmd = [str(self.ruu_decrypt), str(ruu_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
        if result.returncode != 0:
            raise RuntimeError(f"RUU extraction failed: {result.stderr}")
        
        extracted_info = {
            'extracted_files': [],
            'partitions': []
        }
        
        for img_file in output_dir.glob("*.img"):
            extracted_info['extracted_files'].append(str(img_file))
            extracted_info['partitions'].append(img_file.name)
        
        for zip_file in output_dir.glob("rom.zip"):
            extracted_info['extracted_files'].append(str(zip_file))
        
        return extracted_info