import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from lib.core.logger import logger
from lib.core.exceptions import ExtractionError
from lib.utils.command import run_command
from lib.utils.filesystem import ensure_dir

class BaseExtractor(ABC):
    def __init__(self, utils_dir: Path):
        self.utils_dir = utils_dir
    
    @abstractmethod
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        pass
    
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        pass

class ArchiveExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        bin_7zz = self.utils_dir / "bin" / "7zz"
        if not bin_7zz.exists():
            bin_7zz = "7zz"
        
        cmd = [str(bin_7zz), "x", "-y", str(input_path), f"-o{output_path}"]
        
        result = await run_command(cmd)
        if result.returncode != 0:
            raise ExtractionError(f"Archive extraction failed: {result.stderr}")
        
        logger.success(f"Extracted archive to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        extensions = ['.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz']
        return any(str(file_path).lower().endswith(ext) for ext in extensions)

class PayloadExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        payload_dumper = self.utils_dir / "bin" / "payload-dumper-go"
        cmd = [str(payload_dumper), "-o", str(output_path), str(input_path)]
        
        result = await run_command(cmd)
        if result.returncode != 0:
            raise ExtractionError(f"Payload extraction failed: {result.stderr}")
        
        logger.success(f"Extracted payload.bin to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.name.lower() == "payload.bin"

class KDZExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        kdz_extract = self.utils_dir / "kdztools" / "unkdz.py"
        dz_extract = self.utils_dir / "kdztools" / "undz.py"
        
        cmd = ["python3", str(kdz_extract), "-f", str(input_path), "-x", "-o", str(output_path)]
        result = await run_command(cmd, cwd=output_path)
        
        if result.returncode != 0:
            raise ExtractionError(f"KDZ extraction failed: {result.stderr}")
        
        dz_files = list(output_path.glob("*.dz"))
        if dz_files:
            for dz_file in dz_files:
                logger.processing(f"Extracting DZ file: {dz_file.name}")
                cmd = ["python3", str(dz_extract), "-f", str(dz_file), "-s", "-o", str(output_path)]
                await run_command(cmd, cwd=output_path)
        
        logger.success(f"Extracted KDZ file to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".kdz"

class OZipExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        ozip_decrypt = self.utils_dir / "oppo_ozip_decrypt" / "ozipdecrypt.py"
        cmd = ["python3", str(ozip_decrypt), str(input_path)]
        
        result = await run_command(cmd, cwd=output_path)
        if result.returncode != 0:
            raise ExtractionError(f"OZIP extraction failed: {result.stderr}")
        
        logger.success(f"Extracted OZIP file to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".ozip"

class SDATextractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        sdat2img = self.utils_dir / "sdat2img.py"
        
        base_name = input_path.stem.replace('.new', '')
        transfer_list = input_path.parent / f"{base_name}.transfer.list"
        output_img = output_path / f"{base_name}.img"
        
        if not transfer_list.exists():
            raise ExtractionError(f"Transfer list not found: {transfer_list}")
        
        cmd = ["python3", str(sdat2img), str(transfer_list), str(input_path), str(output_img)]
        
        result = await run_command(cmd)
        if result.returncode != 0:
            raise ExtractionError(f"SDAT extraction failed: {result.stderr}")
        
        logger.success(f"Converted {input_path.name} to {output_img}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return 'new.dat' in str(file_path).lower()

class HuaweiExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        splituapp = self.utils_dir / "splituapp.py"
        cmd = ["python3", str(splituapp), "-f", str(input_path)]
        
        result = await run_command(cmd, cwd=output_path)
        if result.returncode != 0:
            raise ExtractionError(f"Huawei UPDATE.APP extraction failed: {result.stderr}")
        
        logger.success(f"Extracted UPDATE.APP to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.name.lower() == "update.app"

class SuperImageExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        lpunpack = self.utils_dir / "lpunpack"
        cmd = [str(lpunpack), str(input_path), str(output_path)]
        
        result = await run_command(cmd)
        if result.returncode != 0:
            raise ExtractionError(f"Super image extraction failed: {result.stderr}")
        
        logger.success(f"Extracted super image to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return 'super' in file_path.name.lower() and file_path.suffix.lower() == '.img'