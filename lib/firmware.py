import os
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import magic
from dataclasses import dataclass

from .ui import UI, ProgressBar
from .logging import get_logger

logger = get_logger()


@dataclass
class FirmwareInfo:
    type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    version: Optional[str] = None
    build_id: Optional[str] = None
    fingerprint: Optional[str] = None
    platform: Optional[str] = None
    kernel_version: Optional[str] = None


class FirmwareDetector:
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir

    def detect_firmware_type(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        if os.path.isdir(file_path):
            return self._detect_directory_type(file_path)
        else:
            return self._detect_file_type(file_path)

    def _detect_file_type(self, file_path: str) -> str:
        filename = os.path.basename(file_path).lower()
        
        with open(file_path, 'rb') as f:
            header = f.read(12)
        
        if header.startswith(b'OPPOENCRYPT!'):
            return 'ozip'
        elif filename.endswith('.kdz'):
            return 'kdz'
        elif filename.endswith('.ofp'):
            return 'ofp'
        elif filename.endswith('.ops'):
            return 'ops'
        elif filename.endswith('.pac'):
            return 'pac'
        elif filename.endswith('.nb0'):
            return 'nb0'
        elif 'ruu_' in filename and filename.endswith('.exe'):
            return 'ruu'
        elif filename == 'payload.bin':
            return 'payload'
        elif filename == 'update.app':
            return 'update_app'
        elif 'super' in filename and filename.endswith('.img'):
            return 'super'
        elif filename.endswith('.new.dat') or filename.endswith('.new.dat.br') or filename.endswith('.new.dat.xz'):
            return 'new_dat'
        elif filename.endswith('.sin'):
            return 'sin'
        elif filename.endswith(('.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz')):
            return 'archive'
        elif filename.endswith('.img'):
            return self._detect_img_type(file_path)
        else:
            return 'unknown'

    def _detect_directory_type(self, dir_path: str) -> str:
        files = os.listdir(dir_path)
        
        if any('payload.bin' in f for f in files):
            return 'payload_dir'
        elif any('.new.dat' in f for f in files):
            return 'new_dat_dir'
        elif any('super' in f and f.endswith('.img') for f in files):
            return 'super_dir'
        elif any(f == 'system' for f in files if os.path.isdir(os.path.join(dir_path, f))):
            return 'extracted_dir'
        else:
            return 'firmware_dir'

    def _detect_img_type(self, file_path: str) -> str:
        try:
            file_type = magic.from_file(file_path)
            if 'Android sparse image' in file_type:
                return 'sparse_img'
            elif 'ext' in file_type.lower():
                return 'ext_img'
            else:
                return 'raw_img'
        except:
            return 'img'

    def extract_firmware_info(self, extracted_path: str) -> FirmwareInfo:
        info = FirmwareInfo(type="unknown")
        
        build_prop_paths = [
            os.path.join(extracted_path, 'system', 'build.prop'),
            os.path.join(extracted_path, 'build.prop'),
            os.path.join(extracted_path, 'system', 'system', 'build.prop')
        ]
        
        for build_prop_path in build_prop_paths:
            if os.path.exists(build_prop_path):
                info = self._parse_build_prop(build_prop_path)
                break

        kernel_path = os.path.join(extracted_path, 'bootRE', 'ikconfig')
        if os.path.exists(kernel_path):
            try:
                with open(kernel_path, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'Kernel Configuration' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                info.kernel_version = parts[2]
                            break
            except:
                pass

        return info

    def _parse_build_prop(self, build_prop_path: str) -> FirmwareInfo:
        info = FirmwareInfo(type="android")
        
        try:
            with open(build_prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        
                        if key == 'ro.product.brand':
                            info.brand = value
                        elif key == 'ro.product.model':
                            info.model = value
                        elif key == 'ro.build.version.release':
                            info.version = value
                        elif key == 'ro.build.display.id':
                            info.build_id = value
                        elif key == 'ro.build.fingerprint':
                            info.fingerprint = value
                        elif key == 'ro.product.platform' or key == 'ro.board.platform':
                            info.platform = value
        except Exception as e:
            logger.warning(f"Failed to parse build.prop: {e}")
        
        return info


class PartitionDetector:
    COMMON_PARTITIONS = [
        'system', 'vendor', 'product', 'system_ext', 'odm',
        'boot', 'recovery', 'dtbo', 'vbmeta', 'super',
        'system_dlkm', 'vendor_dlkm', 'odm_dlkm'
    ]

    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir

    def detect_partitions(self, directory: str) -> List[str]:
        found_partitions = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.img'):
                    partition_name = file.replace('.img', '')
                    if partition_name in self.COMMON_PARTITIONS:
                        found_partitions.append(partition_name)
                
                for partition in self.COMMON_PARTITIONS:
                    if partition in file.lower():
                        if partition not in found_partitions:
                            found_partitions.append(partition)
        
        return sorted(list(set(found_partitions)))

    def get_partition_info(self, partition_path: str) -> Dict[str, Any]:
        if not os.path.exists(partition_path):
            return {}

        info = {
            'size': os.path.getsize(partition_path),
            'type': 'unknown'
        }

        try:
            file_type = magic.from_file(partition_path)
            if 'ext' in file_type.lower():
                info['type'] = 'ext'
                info['filesystem'] = file_type
            elif 'Android sparse image' in file_type:
                info['type'] = 'sparse'
            elif 'squashfs' in file_type.lower():
                info['type'] = 'squashfs'
            elif 'erofs' in file_type.lower():
                info['type'] = 'erofs'
        except:
            pass

        return info


class RamdiskExtractor:
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir
        self.unpackboot_script = os.path.join(utils_dir, 'unpackboot.sh')

    def extract_ramdisk(self, boot_img_path: str, output_dir: str) -> Optional[str]:
        if not os.path.exists(boot_img_path):
            return None

        ramdisk_dir = os.path.join(output_dir, 'ramdisk')
        os.makedirs(ramdisk_dir, exist_ok=True)
        
        old_cwd = os.getcwd()
        os.chdir(ramdisk_dir)
        
        try:
            if os.path.exists(self.unpackboot_script):
                cmd = ['bash', self.unpackboot_script, boot_img_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return ramdisk_dir
                else:
                    logger.warning(f"unpackboot.sh failed: {result.stderr}")
            
            return self._extract_ramdisk_manual(boot_img_path, ramdisk_dir)
            
        finally:
            os.chdir(old_cwd)

    def _extract_ramdisk_manual(self, boot_img_path: str, output_dir: str) -> Optional[str]:
        try:
            with open(boot_img_path, 'rb') as f:
                data = f.read()
            
            magic_signatures = [
                b'\x1f\x8b\x08\x00',  # gzip
                b'\x89\x50\x4e\x47',  # PNG (sometimes used)
                b'070701',            # cpio
                b'070707',            # old cpio
            ]
            
            ramdisk_start = None
            for magic in magic_signatures:
                pos = data.find(magic)
                if pos != -1:
                    ramdisk_start = pos
                    break
            
            if ramdisk_start is None:
                return None
            
            ramdisk_data = data[ramdisk_start:]
            
            ramdisk_file = os.path.join(output_dir, 'ramdisk.cpio.gz')
            with open(ramdisk_file, 'wb') as f:
                f.write(ramdisk_data)
            
            subprocess.run(['gunzip', ramdisk_file], check=True)
            cpio_file = os.path.join(output_dir, 'ramdisk.cpio')
            
            if os.path.exists(cpio_file):
                subprocess.run(['cpio', '-i', '-d', '-F', cpio_file], 
                             cwd=output_dir, check=True)
                os.remove(cpio_file)
                return output_dir
            
        except Exception as e:
            logger.warning(f"Manual ramdisk extraction failed: {e}")
        
        return None

    def detect_ramdisk_version(self, ramdisk_dir: str) -> str:
        if not os.path.exists(ramdisk_dir):
            return "unknown"
        
        if os.path.exists(os.path.join(ramdisk_dir, 'first_stage_ramdisk')):
            return "v4"
        elif os.path.exists(os.path.join(ramdisk_dir, 'system')):
            return "v3"
        elif any(f.startswith('init') for f in os.listdir(ramdisk_dir)):
            return "v2"
        else:
            return "v1"


class FirmwareAnalyzer:
    def __init__(self, utils_dir: str):
        self.utils_dir = utils_dir
        self.detector = FirmwareDetector(utils_dir)
        self.partition_detector = PartitionDetector(utils_dir)
        self.ramdisk_extractor = RamdiskExtractor(utils_dir)

    def analyze_firmware(self, file_path: str, output_dir: str) -> Dict[str, Any]:
        firmware_type = self.detector.detect_firmware_type(file_path)
        
        analysis = {
            'input_path': file_path,
            'firmware_type': firmware_type,
            'partitions': [],
            'firmware_info': None,
            'ramdisk_info': None
        }

        UI.print_firmware_detected(firmware_type)

        if os.path.isdir(file_path):
            extracted_dir = file_path
        else:
            extracted_dir = output_dir

        if os.path.exists(extracted_dir):
            analysis['partitions'] = self.partition_detector.detect_partitions(extracted_dir)
            analysis['firmware_info'] = self.detector.extract_firmware_info(extracted_dir)
            
            boot_img_path = os.path.join(extracted_dir, 'boot.img')
            if os.path.exists(boot_img_path):
                ramdisk_dir = self.ramdisk_extractor.extract_ramdisk(boot_img_path, extracted_dir)
                if ramdisk_dir:
                    version = self.ramdisk_extractor.detect_ramdisk_version(ramdisk_dir)
                    analysis['ramdisk_info'] = {
                        'extracted': True,
                        'version': version,
                        'path': ramdisk_dir
                    }

        return analysis