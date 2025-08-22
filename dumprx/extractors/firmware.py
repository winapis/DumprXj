"""
Firmware-specific extraction functionality
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole


class FirmwareExtractor:
    """Handles extraction of firmware-specific formats"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        
    def extract(self, file_path: Path, output_dir: Path, 
               firmware_info: Dict[str, Any]) -> bool:
        """Extract firmware file"""
        try:
            firmware_type = firmware_info.get('type', '')
            manufacturer = firmware_info.get('manufacturer', '')
            
            self.console.step(f"Extracting {firmware_type} firmware...")
            
            if firmware_type == 'ozip':
                return self._extract_ozip(file_path, output_dir)
            elif firmware_type == 'ofp':
                return self._extract_ofp(file_path, output_dir)
            elif firmware_type == 'ops':
                return self._extract_ops(file_path, output_dir)
            elif firmware_type == 'kdz':
                return self._extract_kdz(file_path, output_dir)
            elif firmware_type == 'nb0':
                return self._extract_nb0(file_path, output_dir)
            elif firmware_type == 'pac':
                return self._extract_pac(file_path, output_dir)
            elif firmware_type == 'ruu':
                return self._extract_ruu(file_path, output_dir)
            else:
                self.console.warning(f"Firmware type {firmware_type} not yet implemented")
                return False
                
        except Exception as e:
            self.console.error(f"Firmware extraction failed: {e}")
            return False
            
    def _extract_ozip(self, file_path: Path, output_dir: Path) -> bool:
        """Extract OZIP (Oppo encrypted ZIP)"""
        try:
            utils_dir = self.config.get_utils_dir()
            ozip_tool = utils_dir / "oppo_ozip_decrypt" / "ozipdecrypt.py"
            
            if not ozip_tool.exists():
                self.console.error("OZIP decryption tool not found")
                return False
                
            # Run OZIP decryption
            cmd = [
                "python3", str(ozip_tool),
                str(file_path)
            ]
            
            result = subprocess.run(
                cmd, 
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.console.success("OZIP extraction completed")
                return True
            else:
                self.console.error(f"OZIP extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"OZIP extraction error: {e}")
            return False
            
    def _extract_ofp(self, file_path: Path, output_dir: Path) -> bool:
        """Extract OFP (Oppo firmware package)"""
        try:
            utils_dir = self.config.get_utils_dir()
            ofp_tool = utils_dir / "oppo_decrypt" / "ofp_qc_extract.py"
            
            if not ofp_tool.exists():
                self.console.error("OFP extraction tool not found")
                return False
                
            # Run OFP extraction
            cmd = [
                "python3", str(ofp_tool),
                str(file_path),
                str(output_dir)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.console.success("OFP extraction completed")
                return True
            else:
                self.console.error(f"OFP extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"OFP extraction error: {e}")
            return False
            
    def _extract_ops(self, file_path: Path, output_dir: Path) -> bool:
        """Extract OPS (OnePlus/Oppo firmware)"""
        try:
            utils_dir = self.config.get_utils_dir()
            ops_tool = utils_dir / "oppo_decrypt" / "opscrypto.py"
            
            if not ops_tool.exists():
                self.console.error("OPS decryption tool not found")
                return False
                
            # Run OPS decryption
            cmd = [
                "python3", str(ops_tool),
                "decrypt", str(file_path)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.console.success("OPS extraction completed")
                return True
            else:
                self.console.error(f"OPS extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"OPS extraction error: {e}")
            return False
            
    def _extract_kdz(self, file_path: Path, output_dir: Path) -> bool:
        """Extract KDZ (LG firmware)"""
        try:
            utils_dir = self.config.get_utils_dir()
            kdz_tool = utils_dir / "kdztools" / "unkdz.py"
            dz_tool = utils_dir / "kdztools" / "undz.py"
            
            if not kdz_tool.exists():
                self.console.error("KDZ extraction tool not found")
                return False
                
            # First extract KDZ to get DZ file
            cmd = [
                "python3", str(kdz_tool),
                "-f", str(file_path),
                "-x", "-o", str(output_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.console.error(f"KDZ extraction failed: {result.stderr}")
                return False
                
            # Find DZ file and extract partitions
            dz_files = list(output_dir.glob("*.dz"))
            if dz_files and dz_tool.exists():
                dz_file = dz_files[0]
                cmd = [
                    "python3", str(dz_tool),
                    "-f", str(dz_file),
                    "-s", "-o", str(output_dir)
                ]
                
                subprocess.run(cmd, capture_output=True, text=True)
                
            self.console.success("KDZ extraction completed")
            return True
            
        except Exception as e:
            self.console.error(f"KDZ extraction error: {e}")
            return False
            
    def _extract_nb0(self, file_path: Path, output_dir: Path) -> bool:
        """Extract NB0 (Nokia/Sharp/Infocus)"""
        try:
            utils_dir = self.config.get_utils_dir()
            nb0_tool = utils_dir / "nb0-extract"
            
            if not nb0_tool.exists():
                self.console.error("NB0 extraction tool not found")
                return False
                
            # Run NB0 extraction
            cmd = [str(nb0_tool), str(file_path)]
            
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.console.success("NB0 extraction completed")
                return True
            else:
                self.console.error(f"NB0 extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"NB0 extraction error: {e}")
            return False
            
    def _extract_pac(self, file_path: Path, output_dir: Path) -> bool:
        """Extract PAC (SpreadTrum firmware)"""
        try:
            utils_dir = self.config.get_utils_dir()
            pac_tool = utils_dir / "pacextractor" / "python" / "pacExtractor.py"
            
            if not pac_tool.exists():
                self.console.error("PAC extraction tool not found")
                return False
                
            # Run PAC extraction
            cmd = [
                "python3", str(pac_tool),
                str(file_path), str(output_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console.success("PAC extraction completed")
                return True
            else:
                self.console.error(f"PAC extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"PAC extraction error: {e}")
            return False
            
    def _extract_ruu(self, file_path: Path, output_dir: Path) -> bool:
        """Extract RUU (HTC ROM update utility)"""
        try:
            utils_dir = self.config.get_utils_dir()
            ruu_tool = utils_dir / "RUU_Decrypt_Tool"
            
            if not ruu_tool.exists():
                self.console.error("RUU decryption tool not found")
                return False
                
            # Run RUU extraction
            cmd = [str(ruu_tool), "-s", str(file_path)]
            
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.console.success("RUU extraction completed")
                return True
            else:
                self.console.error(f"RUU extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.console.error(f"RUU extraction error: {e}")
            return False