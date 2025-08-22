"""
Enhanced Boot Image Analysis with multi-boot support
Supports boot.img, vendor_boot.img, init_boot.img, recovery.img, vendor_kernel_boot.img
Ramdisk version detection: v2, v3, v4
Compression support: gzip, LZ4, XZ, LZMA, Zstandard
DTB extraction and DTS conversion
Kernel analysis: ELF generation, config extraction, version detection
"""

import os
import subprocess
import struct
import magic
import lz4.frame
import lzma
import gzip
import zstandard as zstd
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class BootImageType(Enum):
    BOOT = "boot.img"
    VENDOR_BOOT = "vendor_boot.img"
    INIT_BOOT = "init_boot.img"
    RECOVERY = "recovery.img"
    VENDOR_KERNEL_BOOT = "vendor_kernel_boot.img"
    DTBO = "dtbo.img"
    VBMETA = "vbmeta.img"

class RamdiskVersion(Enum):
    V2 = "v2"
    V3 = "v3"
    V4 = "v4"
    UNKNOWN = "unknown"

class CompressionType(Enum):
    GZIP = "gzip"
    LZ4 = "lz4"
    XZ = "xz"
    LZMA = "lzma"
    ZSTD = "zstd"
    UNCOMPRESSED = "uncompressed"

@dataclass
class BootImageInfo:
    """Information about boot image"""
    image_type: BootImageType
    ramdisk_version: RamdiskVersion
    compression: CompressionType
    kernel_size: int
    ramdisk_size: int
    second_size: int = 0
    dtb_size: int = 0
    recovery_dtbo_size: int = 0
    header_version: int = 0
    os_version: str = ""
    os_patch_level: str = ""
    product_name: str = ""
    cmdline: str = ""
    extra_cmdline: str = ""
    kernel_offset: int = 0
    ramdisk_offset: int = 0
    second_offset: int = 0
    tags_offset: int = 0
    page_size: int = 0
    hash_algorithm: str = ""

@dataclass
class KernelInfo:
    """Information about kernel"""
    version: str = ""
    build_date: str = ""
    gcc_version: str = ""
    config_extracted: bool = False
    config_path: Optional[Path] = None
    elf_generated: bool = False
    elf_path: Optional[Path] = None
    architecture: str = ""
    endianness: str = ""

@dataclass
class DTBInfo:
    """Information about Device Tree Blob"""
    dtb_count: int = 0
    dtb_extracted: bool = False
    dts_converted: bool = False
    dtb_dir: Optional[Path] = None
    dts_dir: Optional[Path] = None
    board_info: Dict[str, str] = None

class EnhancedBootAnalyzer:
    """Enhanced boot image analyzer with comprehensive support"""
    
    # Boot image magic numbers
    BOOT_MAGIC = b'ANDROID!'
    VENDOR_BOOT_MAGIC = b'VNDRBOOT'
    
    # Compression signatures
    COMPRESSION_SIGNATURES = {
        b'\x1f\x8b': CompressionType.GZIP,
        b'\x04\x22\x4d\x18': CompressionType.LZ4,
        b'\xfd7zXZ': CompressionType.XZ,
        b'\x5d\x00\x00': CompressionType.LZMA,
        b'\x28\xb5\x2f\xfd': CompressionType.ZSTD,
    }

    def __init__(self, config):
        self.config = config
        self.work_dir = Path(config.work_dir)
        self.tools_dir = Path(config.tools_dir)
        
    def analyze_boot_images(self, firmware_dir: Path) -> Dict[str, Any]:
        """Analyze all boot images in firmware directory"""
        
        results = {}
        boot_images = self._find_boot_images(firmware_dir)
        
        for boot_image in boot_images:
            logger.info(f"Analyzing boot image: {boot_image.name}")
            
            try:
                # Determine boot image type
                image_type = self._determine_image_type(boot_image)
                
                # Parse boot image header
                boot_info = self._parse_boot_header(boot_image, image_type)
                
                if boot_info:
                    # Extract components
                    extraction_dir = self.work_dir / f"{boot_image.stem}_extracted"
                    extraction_dir.mkdir(exist_ok=True)
                    
                    components = self._extract_boot_components(boot_image, boot_info, extraction_dir)
                    
                    # Analyze kernel
                    kernel_info = None
                    if components.get('kernel'):
                        kernel_info = self._analyze_kernel(components['kernel'], extraction_dir)
                    
                    # Analyze ramdisk
                    ramdisk_info = None
                    if components.get('ramdisk'):
                        ramdisk_info = self._analyze_ramdisk(components['ramdisk'], boot_info, extraction_dir)
                    
                    # Analyze DTB if present
                    dtb_info = None
                    if components.get('dtb'):
                        dtb_info = self._analyze_dtb(components['dtb'], extraction_dir)
                    
                    results[boot_image.name] = {
                        'boot_info': boot_info,
                        'kernel_info': kernel_info,
                        'ramdisk_info': ramdisk_info,
                        'dtb_info': dtb_info,
                        'components': components,
                        'extraction_dir': extraction_dir
                    }
                
            except Exception as e:
                logger.error(f"Error analyzing {boot_image.name}: {e}")
                results[boot_image.name] = {'error': str(e)}
        
        return results
    
    def _find_boot_images(self, firmware_dir: Path) -> List[Path]:
        """Find all boot-related images in firmware directory"""
        
        boot_patterns = [
            'boot.img', 'boot-*.img', '*boot*.img',
            'vendor_boot.img', 'vendor-boot.img',
            'init_boot.img', 'init-boot.img',
            'recovery.img', 'recovery-*.img',
            'vendor_kernel_boot.img',
            'dtbo.img', 'dtbo-*.img',
            'vbmeta.img', 'vbmeta-*.img'
        ]
        
        boot_images = []
        for pattern in boot_patterns:
            boot_images.extend(firmware_dir.rglob(pattern))
        
        # Remove duplicates and sort
        boot_images = sorted(list(set(boot_images)))
        
        return boot_images
    
    def _determine_image_type(self, boot_image: Path) -> BootImageType:
        """Determine boot image type from filename and content"""
        
        name = boot_image.name.lower()
        
        if 'vendor_boot' in name or 'vendor-boot' in name:
            return BootImageType.VENDOR_BOOT
        elif 'init_boot' in name or 'init-boot' in name:
            return BootImageType.INIT_BOOT
        elif 'vendor_kernel_boot' in name:
            return BootImageType.VENDOR_KERNEL_BOOT
        elif 'recovery' in name:
            return BootImageType.RECOVERY
        elif 'dtbo' in name:
            return BootImageType.DTBO
        elif 'vbmeta' in name:
            return BootImageType.VBMETA
        else:
            return BootImageType.BOOT
    
    def _parse_boot_header(self, boot_image: Path, image_type: BootImageType) -> Optional[BootImageInfo]:
        """Parse boot image header to extract metadata"""
        
        try:
            with open(boot_image, 'rb') as f:
                # Read first 2048 bytes for header analysis
                header_data = f.read(2048)
                
                # Check for Android boot magic
                if header_data[:8] == self.BOOT_MAGIC:
                    return self._parse_android_boot_header(header_data, image_type)
                elif header_data[:8] == self.VENDOR_BOOT_MAGIC:
                    return self._parse_vendor_boot_header(header_data, image_type)
                else:
                    # Try to parse as legacy or other format
                    return self._parse_legacy_boot_header(header_data, image_type)
        
        except Exception as e:
            logger.error(f"Error parsing boot header for {boot_image}: {e}")
            return None
    
    def _parse_android_boot_header(self, header_data: bytes, image_type: BootImageType) -> BootImageInfo:
        """Parse Android boot image header (versions 0-4)"""
        
        # Android boot image header structure
        # https://source.android.com/devices/bootloader/boot-image-header
        
        # Basic header (version 0)
        fmt = '<8s10I16s512s32s1024s'
        header_size = struct.calcsize(fmt)
        
        if len(header_data) < header_size:
            raise ValueError("Invalid boot header size")
        
        unpacked = struct.unpack(fmt, header_data[:header_size])
        
        magic = unpacked[0]
        kernel_size = unpacked[1]
        kernel_addr = unpacked[2]
        ramdisk_size = unpacked[3]
        ramdisk_addr = unpacked[4]
        second_size = unpacked[5]
        second_addr = unpacked[6]
        tags_addr = unpacked[7]
        page_size = unpacked[8]
        header_version = unpacked[9]
        os_version = unpacked[10]
        name = unpacked[11].decode('utf-8', errors='ignore').rstrip('\x00')
        cmdline = unpacked[12].decode('utf-8', errors='ignore').rstrip('\x00')
        id_hash = unpacked[13]
        extra_cmdline = unpacked[14].decode('utf-8', errors='ignore').rstrip('\x00')
        
        # Determine ramdisk version based on header version and other indicators
        ramdisk_version = self._determine_ramdisk_version(header_version, cmdline)
        
        # Extract OS version and patch level
        os_ver_str, patch_level = self._parse_os_version(os_version)
        
        return BootImageInfo(
            image_type=image_type,
            ramdisk_version=ramdisk_version,
            compression=CompressionType.UNKNOWN,  # Will be determined during extraction
            kernel_size=kernel_size,
            ramdisk_size=ramdisk_size,
            second_size=second_size,
            header_version=header_version,
            os_version=os_ver_str,
            os_patch_level=patch_level,
            product_name=name,
            cmdline=cmdline,
            extra_cmdline=extra_cmdline,
            kernel_offset=kernel_addr,
            ramdisk_offset=ramdisk_addr,
            second_offset=second_addr,
            tags_offset=tags_addr,
            page_size=page_size
        )
    
    def _parse_vendor_boot_header(self, header_data: bytes, image_type: BootImageType) -> BootImageInfo:
        """Parse vendor boot image header"""
        
        # Vendor boot header is different from regular boot header
        # This is a simplified version - actual implementation would need
        # to handle vendor boot specific structure
        
        return BootImageInfo(
            image_type=image_type,
            ramdisk_version=RamdiskVersion.V4,  # Vendor boot typically uses v4
            compression=CompressionType.UNKNOWN,
            kernel_size=0,
            ramdisk_size=0
        )
    
    def _parse_legacy_boot_header(self, header_data: bytes, image_type: BootImageType) -> BootImageInfo:
        """Parse legacy or unknown boot header format"""
        
        return BootImageInfo(
            image_type=image_type,
            ramdisk_version=RamdiskVersion.UNKNOWN,
            compression=CompressionType.UNKNOWN,
            kernel_size=0,
            ramdisk_size=0
        )
    
    def _determine_ramdisk_version(self, header_version: int, cmdline: str) -> RamdiskVersion:
        """Determine ramdisk version based on header and cmdline"""
        
        if header_version >= 4:
            return RamdiskVersion.V4
        elif header_version >= 3:
            return RamdiskVersion.V3
        elif header_version >= 2:
            return RamdiskVersion.V2
        else:
            # Check cmdline for version indicators
            if 'ramdisk_version=4' in cmdline:
                return RamdiskVersion.V4
            elif 'ramdisk_version=3' in cmdline:
                return RamdiskVersion.V3
            elif 'ramdisk_version=2' in cmdline:
                return RamdiskVersion.V2
            else:
                return RamdiskVersion.V2  # Default for older images
    
    def _parse_os_version(self, os_version: int) -> Tuple[str, str]:
        """Parse OS version and patch level from integer"""
        
        if os_version == 0:
            return "", ""
        
        # OS version format: ((major << 14) | (minor << 7) | patch) << 11 | patch_level
        patch_level = os_version & 0x7ff
        os_ver = (os_version >> 11) & 0x1fffff
        
        major = (os_ver >> 14) & 0x7f
        minor = (os_ver >> 7) & 0x7f
        patch = os_ver & 0x7f
        
        # Convert patch level to date format
        patch_year = 2000 + ((patch_level >> 4) & 0x7f)
        patch_month = patch_level & 0xf
        
        os_version_str = f"{major}.{minor}.{patch}" if major > 0 else ""
        patch_level_str = f"{patch_year:04d}-{patch_month:02d}" if patch_month > 0 else ""
        
        return os_version_str, patch_level_str
    
    def _extract_boot_components(self, boot_image: Path, boot_info: BootImageInfo, output_dir: Path) -> Dict[str, Path]:
        """Extract boot image components (kernel, ramdisk, dtb, etc.)"""
        
        components = {}
        
        try:
            # Use mkbootimg/unpackbootimg tools
            unpack_cmd = [
                str(self.tools_dir / 'android_tools' / 'unpackbootimg'),
                '-i', str(boot_image),
                '-o', str(output_dir)
            ]
            
            result = subprocess.run(unpack_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Check for extracted components
                kernel_file = output_dir / f"{boot_image.stem}-kernel"
                ramdisk_file = output_dir / f"{boot_image.stem}-ramdisk.gz"
                second_file = output_dir / f"{boot_image.stem}-second"
                dtb_file = output_dir / f"{boot_image.stem}-dtb"
                
                if kernel_file.exists():
                    components['kernel'] = kernel_file
                
                if ramdisk_file.exists():
                    components['ramdisk'] = ramdisk_file
                    # Detect compression type
                    boot_info.compression = self._detect_compression(ramdisk_file)
                elif (output_dir / f"{boot_image.stem}-ramdisk").exists():
                    components['ramdisk'] = output_dir / f"{boot_image.stem}-ramdisk"
                    boot_info.compression = CompressionType.UNCOMPRESSED
                
                if second_file.exists():
                    components['second'] = second_file
                
                if dtb_file.exists():
                    components['dtb'] = dtb_file
            
            else:
                logger.warning(f"unpackbootimg failed, trying alternative method: {result.stderr}")
                # Try alternative extraction method
                components = self._extract_boot_manual(boot_image, boot_info, output_dir)
        
        except Exception as e:
            logger.error(f"Error extracting boot components: {e}")
            # Fallback to manual extraction
            components = self._extract_boot_manual(boot_image, boot_info, output_dir)
        
        return components
    
    def _extract_boot_manual(self, boot_image: Path, boot_info: BootImageInfo, output_dir: Path) -> Dict[str, Path]:
        """Manual boot image extraction when tools fail"""
        
        components = {}
        
        try:
            with open(boot_image, 'rb') as f:
                # Skip header
                header_size = boot_info.page_size or 2048
                f.seek(header_size)
                
                # Extract kernel
                if boot_info.kernel_size > 0:
                    kernel_data = f.read(boot_info.kernel_size)
                    kernel_file = output_dir / f"{boot_image.stem}-kernel"
                    with open(kernel_file, 'wb') as kf:
                        kf.write(kernel_data)
                    components['kernel'] = kernel_file
                    
                    # Skip to next page boundary
                    kernel_pages = (boot_info.kernel_size + header_size - 1) // header_size
                    f.seek(header_size * (1 + kernel_pages))
                
                # Extract ramdisk
                if boot_info.ramdisk_size > 0:
                    ramdisk_data = f.read(boot_info.ramdisk_size)
                    
                    # Detect compression
                    compression = self._detect_compression_from_data(ramdisk_data)
                    boot_info.compression = compression
                    
                    ext = '.gz' if compression == CompressionType.GZIP else ''
                    ramdisk_file = output_dir / f"{boot_image.stem}-ramdisk{ext}"
                    
                    with open(ramdisk_file, 'wb') as rf:
                        rf.write(ramdisk_data)
                    components['ramdisk'] = ramdisk_file
        
        except Exception as e:
            logger.error(f"Manual extraction failed: {e}")
        
        return components
    
    def _detect_compression(self, ramdisk_file: Path) -> CompressionType:
        """Detect compression type of ramdisk"""
        
        try:
            with open(ramdisk_file, 'rb') as f:
                header = f.read(16)
                return self._detect_compression_from_data(header)
        
        except Exception:
            return CompressionType.UNKNOWN
    
    def _detect_compression_from_data(self, data: bytes) -> CompressionType:
        """Detect compression type from data bytes"""
        
        if len(data) < 4:
            return CompressionType.UNKNOWN
        
        # Check known compression signatures
        for signature, compression in self.COMPRESSION_SIGNATURES.items():
            if data.startswith(signature):
                return compression
        
        # Additional checks for formats with variable signatures
        try:
            # Try to use python-magic for more accurate detection
            mime_type = magic.from_buffer(data, mime=True)
            
            if 'gzip' in mime_type:
                return CompressionType.GZIP
            elif 'xz' in mime_type:
                return CompressionType.XZ
            elif 'lzma' in mime_type:
                return CompressionType.LZMA
        
        except Exception:
            pass
        
        return CompressionType.UNCOMPRESSED
    
    def _analyze_kernel(self, kernel_file: Path, output_dir: Path) -> KernelInfo:
        """Analyze kernel image"""
        
        kernel_info = KernelInfo()
        
        try:
            # Extract kernel version
            kernel_info.version = self._extract_kernel_version(kernel_file)
            
            # Extract kernel config
            config_file = self._extract_kernel_config(kernel_file, output_dir)
            if config_file:
                kernel_info.config_extracted = True
                kernel_info.config_path = config_file
            
            # Generate ELF file for analysis
            elf_file = self._generate_kernel_elf(kernel_file, output_dir)
            if elf_file:
                kernel_info.elf_generated = True
                kernel_info.elf_path = elf_file
            
            # Detect architecture
            kernel_info.architecture = self._detect_kernel_architecture(kernel_file)
        
        except Exception as e:
            logger.error(f"Error analyzing kernel: {e}")
        
        return kernel_info
    
    def _extract_kernel_version(self, kernel_file: Path) -> str:
        """Extract kernel version from kernel image"""
        
        try:
            # Search for version string in kernel
            with open(kernel_file, 'rb') as f:
                data = f.read()
            
            # Look for Linux version string
            import re
            version_pattern = rb'Linux version ([0-9]+\.[0-9]+\.[0-9]+[^\s]*)'
            match = re.search(version_pattern, data)
            
            if match:
                return match.group(1).decode('utf-8', errors='ignore')
        
        except Exception as e:
            logger.debug(f"Error extracting kernel version: {e}")
        
        return ""
    
    def _extract_kernel_config(self, kernel_file: Path, output_dir: Path) -> Optional[Path]:
        """Extract kernel configuration"""
        
        try:
            config_file = output_dir / f"{kernel_file.stem}.config"
            
            # Use extract-ikconfig script
            extract_cmd = [
                str(self.tools_dir / 'extract-ikconfig' / 'extract-ikconfig'),
                str(kernel_file)
            ]
            
            result = subprocess.run(extract_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                with open(config_file, 'w') as f:
                    f.write(result.stdout)
                return config_file
        
        except Exception as e:
            logger.debug(f"Error extracting kernel config: {e}")
        
        return None
    
    def _generate_kernel_elf(self, kernel_file: Path, output_dir: Path) -> Optional[Path]:
        """Generate ELF file from kernel for analysis"""
        
        try:
            elf_file = output_dir / f"{kernel_file.stem}.elf"
            
            # Use vmlinux-to-elf tool
            vmlinux_cmd = [
                'python3',
                str(self.tools_dir / 'vmlinux-to-elf' / 'vmlinux_to_elf.py'),
                str(kernel_file),
                str(elf_file)
            ]
            
            result = subprocess.run(vmlinux_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and elf_file.exists():
                return elf_file
        
        except Exception as e:
            logger.debug(f"Error generating kernel ELF: {e}")
        
        return None
    
    def _detect_kernel_architecture(self, kernel_file: Path) -> str:
        """Detect kernel architecture"""
        
        try:
            # Use file command to detect architecture
            result = subprocess.run(
                ['file', str(kernel_file)],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                if 'aarch64' in output or 'arm64' in output:
                    return 'arm64'
                elif 'arm' in output:
                    return 'arm'
                elif 'x86-64' in output or 'x86_64' in output:
                    return 'x86_64'
                elif 'x86' in output:
                    return 'x86'
                elif 'mips' in output:
                    return 'mips'
                elif 'riscv' in output:
                    return 'riscv'
        
        except Exception as e:
            logger.debug(f"Error detecting kernel architecture: {e}")
        
        return "unknown"
    
    def _analyze_ramdisk(self, ramdisk_file: Path, boot_info: BootImageInfo, output_dir: Path) -> Dict[str, Any]:
        """Analyze and extract ramdisk"""
        
        ramdisk_info = {
            'compression': boot_info.compression,
            'extracted': False,
            'extract_dir': None,
            'file_count': 0,
            'init_found': False,
            'version_detected': boot_info.ramdisk_version
        }
        
        try:
            # Decompress ramdisk
            decompressed_file = self._decompress_ramdisk(ramdisk_file, boot_info.compression, output_dir)
            
            if decompressed_file:
                # Extract ramdisk contents
                extract_dir = output_dir / f"{ramdisk_file.stem}_extracted"
                extract_dir.mkdir(exist_ok=True)
                
                if self._extract_ramdisk_contents(decompressed_file, extract_dir):
                    ramdisk_info['extracted'] = True
                    ramdisk_info['extract_dir'] = extract_dir
                    
                    # Count files
                    files = list(extract_dir.rglob('*'))
                    ramdisk_info['file_count'] = len([f for f in files if f.is_file()])
                    
                    # Check for init
                    ramdisk_info['init_found'] = (extract_dir / 'init').exists()
        
        except Exception as e:
            logger.error(f"Error analyzing ramdisk: {e}")
        
        return ramdisk_info
    
    def _decompress_ramdisk(self, ramdisk_file: Path, compression: CompressionType, output_dir: Path) -> Optional[Path]:
        """Decompress ramdisk based on compression type"""
        
        output_file = output_dir / f"{ramdisk_file.stem}_decompressed"
        
        try:
            with open(ramdisk_file, 'rb') as infile:
                data = infile.read()
            
            if compression == CompressionType.GZIP:
                with gzip.open(ramdisk_file, 'rb') as gz:
                    decompressed = gz.read()
            elif compression == CompressionType.LZ4:
                decompressed = lz4.frame.decompress(data)
            elif compression == CompressionType.XZ:
                decompressed = lzma.decompress(data)
            elif compression == CompressionType.LZMA:
                decompressed = lzma.decompress(data, format=lzma.FORMAT_ALONE)
            elif compression == CompressionType.ZSTD:
                dctx = zstd.ZstdDecompressor()
                decompressed = dctx.decompress(data)
            else:
                # Uncompressed or unknown
                decompressed = data
            
            with open(output_file, 'wb') as outfile:
                outfile.write(decompressed)
            
            return output_file
        
        except Exception as e:
            logger.error(f"Error decompressing ramdisk: {e}")
            return None
    
    def _extract_ramdisk_contents(self, ramdisk_file: Path, extract_dir: Path) -> bool:
        """Extract ramdisk contents (usually cpio archive)"""
        
        try:
            # Try cpio extraction
            cpio_cmd = [
                'cpio', '-idmv',
                '--no-absolute-filenames'
            ]
            
            with open(ramdisk_file, 'rb') as f:
                result = subprocess.run(
                    cpio_cmd,
                    stdin=f,
                    cwd=extract_dir,
                    capture_output=True,
                    timeout=60
                )
            
            if result.returncode == 0:
                return True
            
            # Try alternative methods
            # Maybe it's a tar archive
            tar_cmd = ['tar', '-xf', str(ramdisk_file), '-C', str(extract_dir)]
            result = subprocess.run(tar_cmd, capture_output=True, timeout=60)
            
            return result.returncode == 0
        
        except Exception as e:
            logger.error(f"Error extracting ramdisk contents: {e}")
            return False
    
    def _analyze_dtb(self, dtb_file: Path, output_dir: Path) -> DTBInfo:
        """Analyze Device Tree Blob(s)"""
        
        dtb_info = DTBInfo()
        
        try:
            # Check if it's a single DTB or multiple DTBs
            dtb_count = self._count_dtbs(dtb_file)
            dtb_info.dtb_count = dtb_count
            
            # Extract DTBs
            dtb_dir = output_dir / f"{dtb_file.stem}_dtb"
            dtb_dir.mkdir(exist_ok=True)
            
            if self._extract_dtbs(dtb_file, dtb_dir):
                dtb_info.dtb_extracted = True
                dtb_info.dtb_dir = dtb_dir
                
                # Convert DTBs to DTS
                dts_dir = output_dir / f"{dtb_file.stem}_dts"
                dts_dir.mkdir(exist_ok=True)
                
                if self._convert_dtb_to_dts(dtb_dir, dts_dir):
                    dtb_info.dts_converted = True
                    dtb_info.dts_dir = dts_dir
                    
                    # Extract board information
                    dtb_info.board_info = self._extract_board_info(dts_dir)
        
        except Exception as e:
            logger.error(f"Error analyzing DTB: {e}")
        
        return dtb_info
    
    def _count_dtbs(self, dtb_file: Path) -> int:
        """Count number of DTBs in file"""
        
        try:
            # Use dtc to list DTBs
            result = subprocess.run(
                ['python3', str(self.tools_dir / 'extract-dtb.py'), str(dtb_file), '--list'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                # Parse output to count DTBs
                lines = [line for line in result.stdout.split('\n') if 'dtb' in line.lower()]
                return len(lines)
        
        except Exception as e:
            logger.debug(f"Error counting DTBs: {e}")
        
        return 1  # Assume single DTB
    
    def _extract_dtbs(self, dtb_file: Path, output_dir: Path) -> bool:
        """Extract DTB(s) from file"""
        
        try:
            # Use extract-dtb.py
            extract_cmd = [
                'python3',
                str(self.tools_dir / 'extract-dtb.py'),
                str(dtb_file),
                '-o', str(output_dir)
            ]
            
            result = subprocess.run(extract_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return True
            
            # Fallback: copy as single DTB
            import shutil
            shutil.copy2(dtb_file, output_dir / 'dtb.dtb')
            return True
        
        except Exception as e:
            logger.error(f"Error extracting DTBs: {e}")
            return False
    
    def _convert_dtb_to_dts(self, dtb_dir: Path, dts_dir: Path) -> bool:
        """Convert DTB files to DTS (Device Tree Source)"""
        
        try:
            dtb_files = list(dtb_dir.glob('*.dtb'))
            
            for dtb_file in dtb_files:
                dts_file = dts_dir / f"{dtb_file.stem}.dts"
                
                # Use dtc to convert DTB to DTS
                dtc_cmd = [
                    str(self.tools_dir / 'dtc' / 'dtc'),
                    '-I', 'dtb',
                    '-O', 'dts',
                    '-o', str(dts_file),
                    str(dtb_file)
                ]
                
                result = subprocess.run(dtc_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    logger.warning(f"Failed to convert {dtb_file.name} to DTS")
            
            return len(list(dts_dir.glob('*.dts'))) > 0
        
        except Exception as e:
            logger.error(f"Error converting DTB to DTS: {e}")
            return False
    
    def _extract_board_info(self, dts_dir: Path) -> Dict[str, str]:
        """Extract board information from DTS files"""
        
        board_info = {}
        
        try:
            dts_files = list(dts_dir.glob('*.dts'))
            
            for dts_file in dts_files:
                with open(dts_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract common properties
                import re
                
                # Model
                model_match = re.search(r'model\s*=\s*"([^"]+)"', content)
                if model_match:
                    board_info['model'] = model_match.group(1)
                
                # Compatible
                compatible_match = re.search(r'compatible\s*=\s*"([^"]+)"', content)
                if compatible_match:
                    board_info['compatible'] = compatible_match.group(1)
                
                # Board ID
                board_id_match = re.search(r'qcom,board-id\s*=\s*<([^>]+)>', content)
                if board_id_match:
                    board_info['board_id'] = board_id_match.group(1)
                
                # MSM ID
                msm_id_match = re.search(r'qcom,msm-id\s*=\s*<([^>]+)>', content)
                if msm_id_match:
                    board_info['msm_id'] = msm_id_match.group(1)
                
                # Only process first DTS file for now
                break
        
        except Exception as e:
            logger.error(f"Error extracting board info: {e}")
        
        return board_info