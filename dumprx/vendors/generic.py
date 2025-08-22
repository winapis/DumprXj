import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GenericExtractor:
    def __init__(self, utils_dir: Path):
        self.utils_dir = utils_dir
        self.lpunpack = utils_dir / "lpunpack"
        self.payload_dumper = utils_dir / "bin" / "payload-dumper-go"
        self.sdat2img = utils_dir / "sdat2img.py"
        self.pacextractor = utils_dir / "pacextractor" / "python" / "pacExtractor.py"
        self.nb0_extract = utils_dir / "nb0-extract"
        self.unsin = utils_dir / "unsin"
        self.splituapp = utils_dir / "splituapp.py"
        self.sevenzip = utils_dir / "bin" / "7zz"
    
    def extract_super_image(self, super_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting super image: {super_path}")
        
        cmd = [str(self.lpunpack), str(super_path), str(output_dir)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Super image extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def extract_payload(self, payload_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting payload.bin: {payload_path}")
        
        cmd = [str(self.payload_dumper), "-c", "4", "-o", str(output_dir), str(payload_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Payload extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def extract_sdat(self, transfer_list: Path, sdat_file: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Converting SDAT to IMG: {sdat_file}")
        
        output_img = output_dir / f"{sdat_file.stem}.img"
        
        cmd = ["python3", str(self.sdat2img), str(transfer_list), str(sdat_file), str(output_img)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"SDAT conversion failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def extract_pac(self, pac_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting PAC file: {pac_path}")
        
        cmd = ["python3", str(self.pacextractor), "-f", str(pac_path), "-o", str(output_dir)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"PAC extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def extract_nb0(self, nb0_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting NB0 file: {nb0_path}")
        
        cmd = [str(self.nb0_extract), str(nb0_path), str(output_dir)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"NB0 extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def extract_sin(self, sin_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting SIN file: {sin_path}")
        
        cmd = [str(self.unsin), str(sin_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
        if result.returncode != 0:
            raise RuntimeError(f"SIN extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def extract_update_app(self, update_app_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting UPDATE.APP: {update_app_path}")
        
        cmd = ["python3", str(self.splituapp), str(update_app_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
        if result.returncode != 0:
            raise RuntimeError(f"UPDATE.APP extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def extract_archive(self, archive_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting archive: {archive_path}")
        
        if shutil.which("7zz"):
            cmd = ["7zz", "x", str(archive_path), f"-o{output_dir}"]
        else:
            cmd = [str(self.sevenzip), "x", str(archive_path), f"-o{output_dir}"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Archive extraction failed: {result.stderr}")
        
        return self._collect_extracted_files(output_dir)
    
    def _collect_extracted_files(self, output_dir: Path) -> Dict[str, Any]:
        extracted_info = {
            'extracted_files': [],
            'partitions': []
        }
        
        partition_extensions = ['.img', '.bin', '.raw', '.ext4']
        
        for ext in partition_extensions:
            for file_path in output_dir.glob(f"*{ext}"):
                if file_path.is_file():
                    extracted_info['extracted_files'].append(str(file_path))
                    extracted_info['partitions'].append(file_path.name)
        
        return extracted_info