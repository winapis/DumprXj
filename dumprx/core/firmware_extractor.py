import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..vendors.lg import LGExtractor
from ..vendors.htc import HTCExtractor
from ..vendors.oppo import OppoExtractor
from ..vendors.generic import GenericExtractor

logger = logging.getLogger(__name__)

class FirmwareExtractor:
    def __init__(self, config_manager):
        self.config = config_manager
        self.utils_dir = Path("utils")
        self.temp_dir = None
        
        self.lg_extractor = LGExtractor(self.utils_dir)
        self.htc_extractor = HTCExtractor(self.utils_dir)
        self.oppo_extractor = OppoExtractor(self.utils_dir)
        self.generic_extractor = GenericExtractor(self.utils_dir)
        
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
        
        shutil.copy(firmware_path, self.temp_dir)
        os.chdir(self.temp_dir)
        
        extraction_info = self.lg_extractor.extract_kdz(firmware_path, self.temp_dir)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_htc_ruu(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting HTC RUU firmware")
        
        extraction_info = self.htc_extractor.extract_ruu(firmware_path, self.temp_dir)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_oppo_ozip(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting OPPO OZIP firmware")
        
        extraction_info = self.oppo_extractor.extract_ozip(firmware_path, self.temp_dir)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_oppo_ofp(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting OPPO OFP firmware")
        
        extraction_info = self.oppo_extractor.extract_ofp(firmware_path, self.temp_dir)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_ab_ota(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting A/B OTA payload")
        
        if firmware_path.suffix == '.zip':
            self.generic_extractor.extract_archive(firmware_path, self.temp_dir)
            payload_files = list(self.temp_dir.glob("**/payload.bin"))
            if payload_files:
                firmware_path = payload_files[0]
        
        extraction_info = self.generic_extractor.extract_payload(firmware_path, self.temp_dir)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_super_image(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info("Extracting super image")
        
        extraction_info = self.generic_extractor.extract_super_image(firmware_path, self.temp_dir)
        
        return self._process_extracted_files(output_dir)
    
    def _extract_archive(self, firmware_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Extracting archive: {firmware_path.suffix}")
        
        extraction_info = self.generic_extractor.extract_archive(firmware_path, self.temp_dir)
        
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