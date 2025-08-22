import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class FirmwareExtractor:
    def __init__(self, config_manager):
        self.config = config_manager
        self.utils_dir = Path("utils")
        self.temp_dir = None
        
    def extract(self, firmware_path: Path, firmware_type: str, output_dir: Path) -> Dict[str, Any]:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="dumprx_"))
        
        try:
            if firmware_type == 'lg_kdz':
                return self._extract_lg_kdz(firmware_path, output_dir)
            elif firmware_type == 'htc_ruu':
                return self._extract_htc_ruu(firmware_path, output_dir)
            elif firmware_type == 'oppo_ozip':
                return self._extract_oppo_ozip(firmware_path, output_dir)
            elif firmware_type == 'oppo_ofp':
                return self._extract_oppo_ofp(firmware_path, output_dir)
            elif firmware_type == 'ab_ota':
                return self._extract_ab_ota(firmware_path, output_dir)
            elif firmware_type == 'super_image':
                return self._extract_super_image(firmware_path, output_dir)
            elif firmware_type == 'archive':
                return self._extract_archive(firmware_path, output_dir)
            else:
                return self._extract_generic(firmware_path, output_dir)
                
        finally:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _extract_lg_kdz(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting LG KDZ firmware")
        
        kdz_extract = self.utils_dir / "kdztools" / "unkdz.py"
        
        shutil.copy(firmware_path, self.temp_dir)
        os.chdir(self.temp_dir)
        
        cmd = ["python3", str(kdz_extract), "-f", firmware_path.name, "-x", "-o", "./"]
        subprocess.run(cmd, check=True, capture_output=True)
        
        dz_files = list(self.temp_dir.glob("*.dz"))
        if dz_files:
            dz_extract = self.utils_dir / "kdztools" / "undz.py"
            cmd = ["python3", str(dz_extract), "-f", dz_files[0].name, "-s", "-o", "./"]
            subprocess.run(cmd, check=True, capture_output=True)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_htc_ruu(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting HTC RUU firmware")
        
        ruu_decrypt = self.utils_dir / "RUU_Decrypt_Tool"
        
        os.chdir(self.temp_dir)
        cmd = [str(ruu_decrypt), str(firmware_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_oppo_ozip(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting OPPO OZIP firmware")
        
        ozip_decrypt = self.utils_dir / "oppo_ozip_decrypt" / "ozipdecrypt.py"
        
        os.chdir(self.temp_dir)
        cmd = ["python3", str(ozip_decrypt), str(firmware_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_oppo_ofp(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting OPPO OFP firmware")
        
        ofp_decrypt = self.utils_dir / "oppo_decrypt" / "ofp_qc_decrypt.py"
        
        os.chdir(self.temp_dir)
        cmd = ["python3", str(ofp_decrypt), str(firmware_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_ab_ota(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting A/B OTA payload")
        
        payload_extractor = self.utils_dir / "bin" / "payload-dumper-go"
        
        os.chdir(self.temp_dir)
        
        if firmware_path.suffix == '.zip':
            self._extract_archive(firmware_path, self.temp_dir)
            payload_files = list(self.temp_dir.glob("**/payload.bin"))
            if payload_files:
                firmware_path = payload_files[0]
        
        cmd = [str(payload_extractor), "-c", str(os.cpu_count()), "-o", str(self.temp_dir), str(firmware_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_super_image(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting super image")
        
        lpunpack = self.utils_dir / "lpunpack"
        
        os.chdir(self.temp_dir)
        cmd = [str(lpunpack), str(firmware_path), str(self.temp_dir)]
        subprocess.run(cmd, check=True, capture_output=True)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_archive(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting archive: {firmware_path.suffix}")
        
        os.chdir(self.temp_dir)
        
        if shutil.which("7zz"):
            cmd = ["7zz", "x", str(firmware_path), f"-o{self.temp_dir}"]
        else:
            sevenzip_bin = self.utils_dir / "bin" / "7zz"
            cmd = [str(sevenzip_bin), "x", str(firmware_path), f"-o{self.temp_dir}"]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_generic(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Processing generic firmware file")
        
        shutil.copy(firmware_path, self.temp_dir)
        
        return self._process_extracted_files(output_dir)
    
    def _process_extracted_files(self, output_dir: Path) -> Dict[str, Any]:
        logger.info("Processing extracted files")
        
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        
        for item in self.temp_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, output_dir)
            elif item.is_dir():
                shutil.copytree(item, output_dir / item.name, dirs_exist_ok=True)
        
        firmware_info = self._extract_firmware_info(output_dir)
        
        return firmware_info
    
    def _extract_firmware_info(self, output_dir: Path) -> Dict[str, Any]:
        info = {
            'brand': 'Unknown',
            'codename': 'Unknown',
            'platform': 'Unknown',
            'release': 'Unknown',
            'fingerprint': 'Unknown',
            'kernel_version': '',
            'branch': 'main'
        }
        
        build_prop_paths = [
            output_dir / "system" / "build.prop",
            output_dir / "build.prop",
            output_dir / "system" / "system" / "build.prop"
        ]
        
        for build_prop_path in build_prop_paths:
            if build_prop_path.exists():
                info.update(self._parse_build_prop(build_prop_path))
                break
        
        ikconfig_paths = [
            output_dir / "bootRE" / "ikconfig",
            output_dir / "boot" / "ikconfig"
        ]
        
        for ikconfig_path in ikconfig_paths:
            if ikconfig_path.exists():
                kernel_version = self._extract_kernel_version(ikconfig_path)
                if kernel_version:
                    info['kernel_version'] = kernel_version
                break
        
        info['branch'] = f"{info['brand'].lower()}-{info['codename'].lower()}-{info['release']}"
        
        return info
    
    def _parse_build_prop(self, build_prop_path: Path) -> Dict[str, str]:
        info = {}
        
        try:
            with open(build_prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        
                        if key == 'ro.product.brand':
                            info['brand'] = value
                        elif key == 'ro.product.device':
                            info['codename'] = value
                        elif key == 'ro.board.platform':
                            info['platform'] = value
                        elif key == 'ro.build.version.release':
                            info['release'] = value
                        elif key == 'ro.build.fingerprint':
                            info['fingerprint'] = value
        
        except Exception as e:
            logger.warning(f"Failed to parse build.prop: {e}")
        
        return info
    
    def _extract_kernel_version(self, ikconfig_path: Path) -> Optional[str]:
        try:
            with open(ikconfig_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if 'Kernel Configuration' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            return parts[2]
        except Exception:
            pass
        
        return None