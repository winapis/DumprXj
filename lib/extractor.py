import os
import subprocess
import tempfile
import shutil
import asyncio
from typing import Dict, List, Optional, Any, Protocol
from pathlib import Path
from abc import ABC, abstractmethod

from .ui import UI, ProgressBar
from .logging import get_logger

logger = get_logger()


class ExtractorPlugin(ABC):
    @abstractmethod
    def can_extract(self, file_path: str) -> bool:
        pass

    @abstractmethod
    async def extract(self, file_path: str, output_dir: str) -> List[str]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class ArchiveExtractor(ExtractorPlugin):
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir

    @property
    def name(self) -> str:
        return "archive"

    def can_extract(self, file_path: str) -> bool:
        filename = os.path.basename(file_path).lower()
        return filename.endswith(('.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz', '.tar.md5'))

    async def extract(self, file_path: str, output_dir: str) -> List[str]:
        UI.print_step(1, 2, "Extracting archive")
        
        filename = os.path.basename(file_path).lower()
        
        if filename.endswith('.tar.md5'):
            await self._extract_tar_md5(file_path, output_dir)
        elif filename.endswith(('.tar', '.tar.gz', '.tgz')):
            await self._extract_tar(file_path, output_dir)
        elif filename.endswith('.zip'):
            await self._extract_zip(file_path, output_dir)
        elif filename.endswith('.rar'):
            await self._extract_rar(file_path, output_dir)
        elif filename.endswith('.7z'):
            await self._extract_7z(file_path, output_dir)

        UI.print_step(2, 2, "Archive extraction complete")
        return self._get_extracted_files(output_dir)

    async def _extract_tar_md5(self, file_path: str, output_dir: str) -> None:
        cmd = ['tar', '-xf', file_path, '-C', output_dir]
        await self._run_command(cmd)

    async def _extract_tar(self, file_path: str, output_dir: str) -> None:
        cmd = ['tar', '-xf', file_path, '-C', output_dir]
        await self._run_command(cmd)

    async def _extract_zip(self, file_path: str, output_dir: str) -> None:
        cmd = ['unzip', '-q', file_path, '-d', output_dir]
        await self._run_command(cmd)

    async def _extract_rar(self, file_path: str, output_dir: str) -> None:
        cmd = ['unrar', 'x', '-y', file_path, output_dir + os.sep]
        await self._run_command(cmd)

    async def _extract_7z(self, file_path: str, output_dir: str) -> None:
        cmd = ['7z', 'x', '-y', f'-o{output_dir}', file_path]
        await self._run_command(cmd)

    async def _run_command(self, cmd: List[str]) -> None:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Command failed: {' '.join(cmd)}\n{stderr.decode()}")

    def _get_extracted_files(self, output_dir: str) -> List[str]:
        files = []
        for root, dirs, filenames in os.walk(output_dir):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        return files


class KDZExtractor(ExtractorPlugin):
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir
        self.unkdz_script = os.path.join(utils_dir, 'kdztools', 'unkdz.py')

    @property
    def name(self) -> str:
        return "kdz"

    def can_extract(self, file_path: str) -> bool:
        return file_path.lower().endswith('.kdz')

    async def extract(self, file_path: str, output_dir: str) -> List[str]:
        if not os.path.exists(self.unkdz_script):
            raise Exception("KDZ extractor not found")

        UI.print_step(1, 4, "Preparing KDZ extraction")
        
        kdz_output = os.path.join(output_dir, 'kdz_extracted')
        os.makedirs(kdz_output, exist_ok=True)

        UI.print_step(2, 4, "Extracting KDZ file")
        cmd = ['python3', self.unkdz_script, '-f', file_path, '-x', '-o', kdz_output]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"KDZ extraction failed: {stderr.decode()}")

        UI.print_step(3, 4, "Extracting DZ partitions")
        dz_files = [f for f in os.listdir(kdz_output) if f.endswith('.dz')]
        
        for dz_file in dz_files:
            await self._extract_dz_file(os.path.join(kdz_output, dz_file), output_dir)

        UI.print_step(4, 4, "Collecting extracted partitions")
        return self._get_extracted_files(output_dir)

    async def _extract_dz_file(self, dz_path: str, output_dir: str) -> None:
        undz_script = os.path.join(self.utils_dir, 'kdztools', 'undz.py')
        
        if os.path.exists(undz_script):
            cmd = ['python3', undz_script, '-f', dz_path, '-x', '-o', output_dir]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

    def _get_extracted_files(self, output_dir: str) -> List[str]:
        files = []
        for root, dirs, filenames in os.walk(output_dir):
            for filename in filenames:
                if filename.endswith('.img'):
                    files.append(os.path.join(root, filename))
        return files


class OZIPExtractor(ExtractorPlugin):
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir
        self.ozip_decrypt = os.path.join(utils_dir, 'oppo_ozip_decrypt', 'ozipdecrypt.py')

    @property
    def name(self) -> str:
        return "ozip"

    def can_extract(self, file_path: str) -> bool:
        if file_path.lower().endswith('.ozip'):
            return True
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
                return header.startswith(b'OPPOENCRYPT!')
        except:
            return False

    async def extract(self, file_path: str, output_dir: str) -> List[str]:
        if not os.path.exists(self.ozip_decrypt):
            raise Exception("OZIP decrypter not found")

        UI.print_step(1, 3, "Preparing OZIP decryption")
        
        temp_dir = os.path.join(output_dir, 'ozip_temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.copy2(file_path, temp_file)

        UI.print_step(2, 3, "Decrypting OZIP file")
        
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            cmd = ['python3', self.ozip_decrypt, temp_file]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"OZIP decryption failed: {stderr.decode()}")

            UI.print_step(3, 3, "Extracting decrypted content")
            
            decrypted_files = []
            for file in os.listdir('.'):
                if file.endswith('.zip') or os.path.isdir(file):
                    dest_path = os.path.join(output_dir, file)
                    if os.path.isdir(file):
                        shutil.copytree(file, dest_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(file, dest_path)
                        decrypted_files.append(dest_path)
            
            return decrypted_files
            
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir, ignore_errors=True)


class PayloadExtractor(ExtractorPlugin):
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir
        self.payload_dumper = os.path.join(utils_dir, 'bin', 'payload-dumper-go')

    @property
    def name(self) -> str:
        return "payload"

    def can_extract(self, file_path: str) -> bool:
        return os.path.basename(file_path).lower() == 'payload.bin'

    async def extract(self, file_path: str, output_dir: str) -> List[str]:
        if not os.path.exists(self.payload_dumper):
            raise Exception("Payload dumper not found")

        UI.print_step(1, 2, "Extracting payload.bin")
        
        cmd = [self.payload_dumper, '-o', output_dir, file_path]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Payload extraction failed: {stderr.decode()}")

        UI.print_step(2, 2, "Payload extraction complete")
        
        extracted_files = []
        for file in os.listdir(output_dir):
            if file.endswith('.img'):
                extracted_files.append(os.path.join(output_dir, file))
        
        return extracted_files


class SuperImageExtractor(ExtractorPlugin):
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir
        self.lpunpack = os.path.join(utils_dir, 'lpunpack')
        self.simg2img = os.path.join(utils_dir, 'bin', 'simg2img')

    @property
    def name(self) -> str:
        return "super"

    def can_extract(self, file_path: str) -> bool:
        filename = os.path.basename(file_path).lower()
        return 'super' in filename and filename.endswith('.img')

    async def extract(self, file_path: str, output_dir: str) -> List[str]:
        if not os.path.exists(self.lpunpack):
            raise Exception("lpunpack not found")

        UI.print_step(1, 3, "Converting sparse super image")
        
        raw_super = os.path.join(output_dir, 'super.img.raw')
        
        if os.path.exists(self.simg2img):
            cmd = [self.simg2img, file_path, raw_super]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await process.communicate()
        
        if not os.path.exists(raw_super) or os.path.getsize(raw_super) == 0:
            shutil.copy2(file_path, raw_super)

        UI.print_step(2, 3, "Extracting partitions from super image")
        
        partitions = ['system', 'vendor', 'product', 'system_ext', 'odm']
        extracted_files = []
        
        for partition in partitions:
            for suffix in ['_a', '']:
                partition_name = f"{partition}{suffix}"
                
                cmd = [self.lpunpack, f'--partition={partition_name}', raw_super]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.DEVNULL, 
                    stderr=asyncio.subprocess.DEVNULL, cwd=output_dir
                )
                await process.communicate()
                
                extracted_file = os.path.join(output_dir, f'{partition_name}.img')
                target_file = os.path.join(output_dir, f'{partition}.img')
                
                if os.path.exists(extracted_file):
                    if suffix == '_a':
                        os.rename(extracted_file, target_file)
                        extracted_files.append(target_file)
                    else:
                        extracted_files.append(extracted_file)
                    break

        if os.path.exists(raw_super):
            os.remove(raw_super)

        UI.print_step(3, 3, "Super image extraction complete")
        return extracted_files


class NewDatExtractor(ExtractorPlugin):
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir
        self.sdat2img = os.path.join(utils_dir, 'sdat2img.py')

    @property
    def name(self) -> str:
        return "new_dat"

    def can_extract(self, file_path: str) -> bool:
        if os.path.isdir(file_path):
            files = os.listdir(file_path)
            return any('.new.dat' in f for f in files)
        else:
            return file_path.endswith(('.new.dat', '.new.dat.br', '.new.dat.xz'))

    async def extract(self, file_path: str, output_dir: str) -> List[str]:
        if not os.path.exists(self.sdat2img):
            raise Exception("sdat2img not found")

        if os.path.isdir(file_path):
            return await self._extract_from_directory(file_path, output_dir)
        else:
            return await self._extract_single_file(file_path, output_dir)

    async def _extract_from_directory(self, dir_path: str, output_dir: str) -> List[str]:
        extracted_files = []
        
        for file in os.listdir(dir_path):
            if '.new.dat' in file:
                base_name = file.split('.new.dat')[0]
                transfer_list = os.path.join(dir_path, f'{base_name}.transfer.list')
                new_dat_file = os.path.join(dir_path, file)
                
                if os.path.exists(transfer_list):
                    output_img = os.path.join(output_dir, f'{base_name}.img')
                    
                    if await self._decompress_if_needed(new_dat_file, output_dir):
                        new_dat_file = os.path.join(output_dir, f'{base_name}.new.dat')
                    
                    await self._convert_dat_to_img(transfer_list, new_dat_file, output_img)
                    extracted_files.append(output_img)
        
        return extracted_files

    async def _extract_single_file(self, file_path: str, output_dir: str) -> List[str]:
        base_name = os.path.basename(file_path).split('.new.dat')[0]
        dir_name = os.path.dirname(file_path)
        
        transfer_list = os.path.join(dir_name, f'{base_name}.transfer.list')
        
        if not os.path.exists(transfer_list):
            raise Exception(f"Transfer list not found: {transfer_list}")
        
        new_dat_file = file_path
        if await self._decompress_if_needed(file_path, output_dir):
            new_dat_file = os.path.join(output_dir, f'{base_name}.new.dat')
        
        output_img = os.path.join(output_dir, f'{base_name}.img')
        await self._convert_dat_to_img(transfer_list, new_dat_file, output_img)
        
        return [output_img]

    async def _decompress_if_needed(self, file_path: str, output_dir: str) -> bool:
        if file_path.endswith('.br'):
            cmd = ['brotli', '-d', file_path, '-o', 
                   os.path.join(output_dir, os.path.basename(file_path)[:-3])]
        elif file_path.endswith('.xz'):
            cmd = ['xz', '-d', '-c', file_path]
            output_file = os.path.join(output_dir, os.path.basename(file_path)[:-3])
            
            with open(output_file, 'wb') as f:
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=f, stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
            return True
        else:
            return False
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return True

    async def _convert_dat_to_img(self, transfer_list: str, new_dat: str, output_img: str) -> None:
        cmd = ['python3', self.sdat2img, transfer_list, new_dat, output_img]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"sdat2img failed: {stderr.decode()}")


class FirmwareExtractor:
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir
        self.plugins: List[ExtractorPlugin] = [
            ArchiveExtractor(utils_dir),
            KDZExtractor(utils_dir),
            OZIPExtractor(utils_dir),
            PayloadExtractor(utils_dir),
            SuperImageExtractor(utils_dir),
            NewDatExtractor(utils_dir)
        ]

    async def extract(self, file_path: str, output_dir: str) -> List[str]:
        os.makedirs(output_dir, exist_ok=True)
        
        for plugin in self.plugins:
            if plugin.can_extract(file_path):
                UI.print_info(f"Using {plugin.name} extractor")
                try:
                    return await plugin.extract(file_path, output_dir)
                except Exception as e:
                    UI.print_error(f"Extraction failed with {plugin.name}: {e}")
                    raise
        
        raise Exception(f"No suitable extractor found for: {file_path}")

    def get_supported_types(self) -> List[str]:
        return [plugin.name for plugin in self.plugins]