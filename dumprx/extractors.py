#!/usr/bin/env python3

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from dumprx import UTILS_DIR
from dumprx.console import info, warning, error, step, success
from dumprx.config import config


class BaseExtractor(ABC):
    
    def __init__(self, input_path: str, output_dir: str):
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.temp_dir = None
        self.max_workers = config.get('advanced', 'max_workers', default=4)
    
    def setup_temp_dir(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix='dumprx_'))
        return self.temp_dir
    
    def cleanup_temp_dir(self):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @abstractmethod
    def extract(self) -> bool:
        pass
    
    def run_command(self, cmd: List[str], cwd: Path = None, env: Dict = None) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd or self.temp_dir,
                env=env,
                capture_output=True,
                text=True,
                check=False
            )
            return result
        except Exception as e:
            error(f"Command failed: {' '.join(cmd)}")
            error(f"Error: {str(e)}")
            raise


class ArchiveExtractor(BaseExtractor):
    
    def extract(self) -> bool:
        step(f"Extracting archive: {self.input_path.name}")
        
        temp_dir = self.setup_temp_dir()
        
        try:
            seven_zip = UTILS_DIR / "bin" / "7zz"
            if not seven_zip.exists():
                seven_zip = shutil.which("7z") or shutil.which("7za")
                if not seven_zip:
                    error("7zip not found")
                    return False
            
            cmd = [str(seven_zip), "x", str(self.input_path), f"-o{temp_dir}", "-y"]
            result = self.run_command(cmd)
            
            if result.returncode != 0:
                error(f"Archive extraction failed: {result.stderr}")
                return False
            
            extracted_files = list(temp_dir.rglob("*"))
            if not extracted_files:
                error("No files extracted from archive")
                return False
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            for item in temp_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, self.output_dir)
                elif item.is_dir():
                    shutil.copytree(item, self.output_dir / item.name, dirs_exist_ok=True)
            
            success(f"Archive extracted successfully to {self.output_dir}")
            return True
            
        except Exception as e:
            error(f"Archive extraction error: {str(e)}")
            return False
        finally:
            self.cleanup_temp_dir()


class AndroidExtractor(BaseExtractor):
    
    def extract(self) -> bool:
        file_name = self.input_path.name.lower()
        
        if "payload.bin" in file_name:
            return self._extract_payload()
        elif "system.new.dat" in file_name:
            return self._extract_sdat()
        elif "super" in file_name and file_name.endswith(".img"):
            return self._extract_super()
        elif file_name.endswith(".img"):
            return self._extract_img()
        else:
            error(f"Unsupported Android format: {file_name}")
            return False
    
    def _extract_payload(self) -> bool:
        step("Extracting Android OTA payload")
        
        temp_dir = self.setup_temp_dir()
        
        try:
            payload_dumper = UTILS_DIR / "bin" / "payload-dumper-go"
            if not payload_dumper.exists():
                error("payload-dumper-go not found")
                return False
            
            cmd = [
                str(payload_dumper),
                "-c", str(self.max_workers),
                "-o", str(temp_dir),
                str(self.input_path)
            ]
            
            result = self.run_command(cmd)
            if result.returncode != 0:
                error(f"Payload extraction failed: {result.stderr}")
                return False
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            for item in temp_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, self.output_dir)
            
            success("Payload extracted successfully")
            return True
            
        except Exception as e:
            error(f"Payload extraction error: {str(e)}")
            return False
        finally:
            self.cleanup_temp_dir()
    
    def _extract_sdat(self) -> bool:
        step("Converting system.new.dat to img")
        
        try:
            sdat2img = UTILS_DIR / "sdat2img.py"
            if not sdat2img.exists():
                error("sdat2img.py not found")
                return False
            
            transfer_list = self.input_path.parent / "system.transfer.list"
            if not transfer_list.exists():
                error("system.transfer.list not found")
                return False
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_img = self.output_dir / "system.img"
            
            cmd = [
                "python3", str(sdat2img),
                str(transfer_list),
                str(self.input_path),
                str(output_img)
            ]
            
            result = self.run_command(cmd)
            if result.returncode != 0:
                error(f"sdat2img failed: {result.stderr}")
                return False
            
            success("system.new.dat converted successfully")
            return True
            
        except Exception as e:
            error(f"sdat conversion error: {str(e)}")
            return False
    
    def _extract_super(self) -> bool:
        step("Extracting super image")
        
        try:
            lpunpack = UTILS_DIR / "lpunpack"
            if not lpunpack.exists():
                error("lpunpack not found")
                return False
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [str(lpunpack), str(self.input_path), str(self.output_dir)]
            result = self.run_command(cmd)
            
            if result.returncode != 0:
                error(f"Super image extraction failed: {result.stderr}")
                return False
            
            success("Super image extracted successfully")
            return True
            
        except Exception as e:
            error(f"Super image extraction error: {str(e)}")
            return False
    
    def _extract_img(self) -> bool:
        step("Converting sparse image to raw image")
        
        try:
            simg2img = UTILS_DIR / "bin" / "simg2img"
            if not simg2img.exists():
                error("simg2img not found")
                return False
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_img = self.output_dir / f"{self.input_path.stem}_raw.img"
            
            cmd = [str(simg2img), str(self.input_path), str(output_img)]
            result = self.run_command(cmd)
            
            if result.returncode != 0:
                info("File might already be a raw image, copying as-is")
                shutil.copy2(self.input_path, output_img)
            
            success("Image processed successfully")
            return True
            
        except Exception as e:
            error(f"Image processing error: {str(e)}")
            return False


class OppoExtractor(BaseExtractor):
    
    def extract(self) -> bool:
        file_name = self.input_path.name.lower()
        
        if file_name.endswith('.ozip'):
            return self._extract_ozip()
        elif file_name.endswith('.ofp'):
            return self._extract_ofp()
        elif file_name.endswith('.ops'):
            return self._extract_ops()
        else:
            error(f"Unsupported Oppo format: {file_name}")
            return False
    
    def _extract_ozip(self) -> bool:
        step("Decrypting Oppo/Realme ozip")
        
        temp_dir = self.setup_temp_dir()
        
        try:
            ozip_decrypt = UTILS_DIR / "oppo_ozip_decrypt" / "ozipdecrypt.py"
            requirements = UTILS_DIR / "oppo_decrypt" / "requirements.txt"
            
            if not ozip_decrypt.exists():
                error("ozipdecrypt.py not found")
                return False
            
            shutil.copy2(self.input_path, temp_dir / self.input_path.name)
            
            cmd = [
                "uv", "run", "--with-requirements", str(requirements),
                str(ozip_decrypt), str(temp_dir / self.input_path.name)
            ]
            
            result = self.run_command(cmd, cwd=temp_dir)
            if result.returncode != 0:
                error(f"ozip decryption failed: {result.stderr}")
                return False
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            zip_file = temp_dir / f"{self.input_path.stem}.zip"
            out_dir = temp_dir / "out"
            
            if zip_file.exists():
                shutil.move(zip_file, self.output_dir)
            elif out_dir.exists():
                for item in out_dir.iterdir():
                    if item.is_file():
                        shutil.copy2(item, self.output_dir)
                    elif item.is_dir():
                        shutil.copytree(item, self.output_dir / item.name, dirs_exist_ok=True)
            
            success("ozip decrypted successfully")
            return True
            
        except Exception as e:
            error(f"ozip decryption error: {str(e)}")
            return False
        finally:
            self.cleanup_temp_dir()
    
    def _extract_ofp(self) -> bool:
        step("Decrypting Oppo ofp")
        
        temp_dir = self.setup_temp_dir()
        
        try:
            ofp_qc_decrypt = UTILS_DIR / "oppo_decrypt" / "ofp_qc_decrypt.py"
            ofp_mtk_decrypt = UTILS_DIR / "oppo_decrypt" / "ofp_mtk_decrypt.py"
            requirements = UTILS_DIR / "oppo_decrypt" / "requirements.txt"
            
            shutil.copy2(self.input_path, temp_dir / self.input_path.name)
            out_dir = temp_dir / "out"
            out_dir.mkdir()
            
            cmd_qc = [
                "uv", "run", "--with-requirements", str(requirements),
                str(ofp_qc_decrypt), str(temp_dir / self.input_path.name), str(out_dir)
            ]
            
            result = self.run_command(cmd_qc, cwd=temp_dir)
            
            if result.returncode != 0 or not any(out_dir.glob("*.img")):
                info("QC decryption failed, trying MTK...")
                
                cmd_mtk = [
                    "uv", "run", "--with-requirements", str(requirements),
                    str(ofp_mtk_decrypt), str(temp_dir / self.input_path.name), str(out_dir)
                ]
                
                result = self.run_command(cmd_mtk, cwd=temp_dir)
                if result.returncode != 0:
                    error("Both QC and MTK decryption failed")
                    return False
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            for item in out_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, self.output_dir)
            
            success("ofp decrypted successfully")
            return True
            
        except Exception as e:
            error(f"ofp decryption error: {str(e)}")
            return False
        finally:
            self.cleanup_temp_dir()
    
    def _extract_ops(self) -> bool:
        step("Decrypting Oppo ops")
        
        temp_dir = self.setup_temp_dir()
        
        try:
            ops_decrypt = UTILS_DIR / "oppo_decrypt" / "opscrypto.py"
            requirements = UTILS_DIR / "oppo_decrypt" / "requirements.txt"
            
            if not ops_decrypt.exists():
                error("opscrypto.py not found")
                return False
            
            seven_zip = UTILS_DIR / "bin" / "7zz"
            if not seven_zip.exists():
                seven_zip = shutil.which("7z")
                if not seven_zip:
                    error("7zip not found")
                    return False
            
            cmd_extract = [str(seven_zip), "e", "-y", str(self.input_path), "*.ops"]
            result = self.run_command(cmd_extract, cwd=temp_dir)
            
            if result.returncode != 0:
                error("Failed to extract ops files")
                return False
            
            ops_files = list(temp_dir.glob("*.ops"))
            if not ops_files:
                error("No ops files found")
                return False
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            for ops_file in ops_files:
                cmd_decrypt = [
                    "uv", "run", "--with-requirements", str(requirements),
                    str(ops_decrypt), str(ops_file)
                ]
                
                result = self.run_command(cmd_decrypt, cwd=temp_dir)
                if result.returncode == 0:
                    for item in temp_dir.iterdir():
                        if item.is_file() and not item.name.endswith('.ops'):
                            shutil.copy2(item, self.output_dir)
            
            success("ops decrypted successfully")
            return True
            
        except Exception as e:
            error(f"ops decryption error: {str(e)}")
            return False
        finally:
            self.cleanup_temp_dir()


class LGExtractor(BaseExtractor):
    
    def extract(self) -> bool:
        if self.input_path.name.lower().endswith('.kdz'):
            return self._extract_kdz()
        elif self.input_path.name.lower().endswith('.dz'):
            return self._extract_dz()
        else:
            error(f"Unsupported LG format: {self.input_path.name}")
            return False
    
    def _extract_kdz(self) -> bool:
        step("Extracting LG KDZ file")
        
        temp_dir = self.setup_temp_dir()
        
        try:
            kdz_extract = UTILS_DIR / "kdztools" / "unkdz.py"
            if not kdz_extract.exists():
                error("unkdz.py not found")
                return False
            
            shutil.copy2(self.input_path, temp_dir)
            
            cmd = [
                "python3", str(kdz_extract),
                "-f", str(self.input_path.name),
                "-x", "-o", "."
            ]
            
            result = self.run_command(cmd, cwd=temp_dir)
            if result.returncode != 0:
                error(f"KDZ extraction failed: {result.stderr}")
                return False
            
            dz_files = list(temp_dir.glob("*.dz"))
            if dz_files:
                for dz_file in dz_files:
                    if not self._extract_dz_file(dz_file, temp_dir):
                        warning(f"Failed to extract {dz_file.name}")
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            for item in temp_dir.iterdir():
                if item.is_file() and not item.name.endswith(('.kdz', '.dz')):
                    shutil.copy2(item, self.output_dir)
            
            success("KDZ extracted successfully")
            return True
            
        except Exception as e:
            error(f"KDZ extraction error: {str(e)}")
            return False
        finally:
            self.cleanup_temp_dir()
    
    def _extract_dz(self) -> bool:
        step("Extracting LG DZ file")
        
        temp_dir = self.setup_temp_dir()
        
        try:
            return self._extract_dz_file(self.input_path, temp_dir)
        finally:
            self.cleanup_temp_dir()
    
    def _extract_dz_file(self, dz_file: Path, work_dir: Path) -> bool:
        try:
            dz_extract = UTILS_DIR / "kdztools" / "undz.py"
            if not dz_extract.exists():
                error("undz.py not found")
                return False
            
            cmd = [
                "python3", str(dz_extract),
                "-f", str(dz_file.name),
                "-s", "-o", "."
            ]
            
            result = self.run_command(cmd, cwd=work_dir)
            if result.returncode != 0:
                error(f"DZ extraction failed: {result.stderr}")
                return False
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            for item in work_dir.iterdir():
                if item.is_file() and not item.name.endswith('.dz'):
                    shutil.copy2(item, self.output_dir)
            
            return True
            
        except Exception as e:
            error(f"DZ extraction error: {str(e)}")
            return False


def get_extractor(detection_result: Dict[str, str], input_path: str, output_dir: str) -> BaseExtractor:
    format_type = detection_result.get('format', 'unknown')
    
    extractors = {
        'archive': ArchiveExtractor,
        'android_ota': AndroidExtractor,
        'android_sdat': AndroidExtractor,
        'android_super': AndroidExtractor,
        'android_img': AndroidExtractor,
        'oppo_ozip': OppoExtractor,
        'oppo_ofp': OppoExtractor,
        'oppo_ops': OppoExtractor,
        'lg_kdz': LGExtractor,
        'lg_dz': LGExtractor,
    }
    
    extractor_class = extractors.get(format_type, ArchiveExtractor)
    return extractor_class(input_path, output_dir)