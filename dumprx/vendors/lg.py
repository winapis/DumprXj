import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LGExtractor:
    def __init__(self, utils_dir: Path):
        self.utils_dir = utils_dir
        self.kdz_extract = utils_dir / "kdztools" / "unkdz.py"
        self.dz_extract = utils_dir / "kdztools" / "undz.py"
    
    def extract_kdz(self, kdz_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting LG KDZ: {kdz_path}")
        
        cmd = [
            "python3", str(self.kdz_extract),
            "-f", str(kdz_path),
            "-x", "-o", str(output_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"KDZ extraction failed: {result.stderr}")
        
        dz_files = list(output_dir.glob("*.dz"))
        
        extracted_info = {
            'extracted_files': [],
            'partitions': []
        }
        
        for dz_file in dz_files:
            logger.info(f"Extracting DZ file: {dz_file}")
            
            cmd = [
                "python3", str(self.dz_extract),
                "-f", str(dz_file),
                "-s", "-o", str(output_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                extracted_info['extracted_files'].append(str(dz_file))
                extracted_info['partitions'].extend(self._find_partitions(output_dir))
        
        return extracted_info
    
    def _find_partitions(self, output_dir: Path) -> list:
        partition_extensions = ['.img', '.bin', '.raw']
        partitions = []
        
        for ext in partition_extensions:
            partitions.extend([f.name for f in output_dir.glob(f"*{ext}")])
        
        return partitions