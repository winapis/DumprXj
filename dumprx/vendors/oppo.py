import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OppoExtractor:
    def __init__(self, utils_dir: Path):
        self.utils_dir = utils_dir
        self.ozip_decrypt = utils_dir / "oppo_ozip_decrypt" / "ozipdecrypt.py"
        self.ofp_qc_decrypt = utils_dir / "oppo_decrypt" / "ofp_qc_decrypt.py"
        self.ofp_mtk_decrypt = utils_dir / "oppo_decrypt" / "ofp_mtk_decrypt.py"
        self.ops_decrypt = utils_dir / "oppo_decrypt" / "opscrypto.py"
    
    def extract_ozip(self, ozip_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting OPPO OZIP: {ozip_path}")
        
        cmd = ["python3", str(self.ozip_decrypt), str(ozip_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
        if result.returncode != 0:
            raise RuntimeError(f"OZIP extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def extract_ofp(self, ofp_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting OPPO OFP: {ofp_path}")
        
        cmd = ["python3", str(self.ofp_qc_decrypt), str(ofp_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
        
        if result.returncode != 0:
            cmd = ["python3", str(self.ofp_mtk_decrypt), str(ofp_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
            
            if result.returncode != 0:
                raise RuntimeError(f"OFP extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def extract_ops(self, ops_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting OPPO OPS: {ops_path}")
        
        cmd = ["python3", str(self.ops_decrypt), str(ops_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
        if result.returncode != 0:
            raise RuntimeError(f"OPS extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def _collect_extracted_files(self, output_dir: Path) -> Dict[str, Any]:
        extracted_info = {
            'extracted_files': [],
            'partitions': []
        }
        
        for img_file in output_dir.glob("*.img"):
            extracted_info['extracted_files'].append(str(img_file))
            extracted_info['partitions'].append(img_file.name)
        
        for bin_file in output_dir.glob("*.bin"):
            extracted_info['extracted_files'].append(str(bin_file))
            extracted_info['partitions'].append(bin_file.name)
        
        return extracted_info