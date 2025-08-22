import struct
import os
import gzip
import lzma
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple
import logging

from dumprx.utils.ui import print_info, print_error, print_success

logger = logging.getLogger(__name__)


class BootImageUnpacker:
    """Python implementation of unpackboot.sh functionality"""
    
    def __init__(self):
        self.img_info = {}
        
    def unpack_boot_image(self, boot_img_path: Path, output_dir: Path) -> bool:
        """Unpack boot.img and decompress ramdisk"""
        try:
            print_info(f"Unpack & decompress {boot_img_path.name} to {output_dir.name}")
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy boot image to output directory
            boot_img = output_dir / boot_img_path.name
            if boot_img_path != boot_img:
                import shutil
                shutil.copy2(boot_img_path, boot_img)
            
            os.chdir(output_dir)
            
            # Find Android boot magic
            with open(boot_img, 'rb') as f:
                content = f.read()
            
            android_offset = content.find(b"ANDROID!")
            vndrboot_offset = content.find(b"VNDRBOOT")
            
            if android_offset == -1 and vndrboot_offset == -1:
                print_error("No Android boot magic found")
                return False
                
            offset = android_offset if android_offset != -1 else vndrboot_offset
            vndrboot = vndrboot_offset != -1
            
            if offset > 0:
                # Strip any header before Android magic
                with open(boot_img, 'rb') as f:
                    f.seek(offset)
                    boot_data = f.read()
                with open("bootimg", 'wb') as f:
                    f.write(boot_data)
                boot_img = Path("bootimg")
            
            # Parse boot image header
            info = self._parse_boot_header(boot_img, vndrboot)
            if not info:
                return False
            
            # Extract components
            self._extract_components(boot_img, info)
            
            # Decompress ramdisk
            self._decompress_ramdisk()
            
            # Write img_info file
            self._write_img_info(info)
            
            print_success("Unpack completed.")
            return True
            
        except Exception as e:
            logger.exception("Error unpacking boot image")
            print_error(f"Unpack failed: {e}")
            return False
    
    def _parse_boot_header(self, boot_img: Path, vndrboot: bool = False) -> Optional[Dict]:
        """Parse Android boot image header"""
        try:
            with open(boot_img, 'rb') as f:
                header = f.read(2048)  # Read enough for any header version
            
            # Header format varies by version
            info = {}
            
            if vndrboot:
                header_addr = 8
                info['vndrboot'] = True
            else:
                header_addr = 40
                info['vndrboot'] = False
            
            # Read basic header fields
            info['kernel_addr'] = struct.unpack('<I', header[12:16])[0]
            info['ramdisk_addr'] = struct.unpack('<I', header[20:24])[0]
            info['second_addr'] = struct.unpack('<I', header[28:32])[0]
            info['tags_addr'] = struct.unpack('<I', header[32:36])[0]
            
            info['kernel_size'] = struct.unpack('<I', header[8:12])[0]
            info['ramdisk_size'] = struct.unpack('<I', header[16:20])[0]
            info['second_size'] = struct.unpack('<I', header[24:28])[0]
            info['page_size'] = struct.unpack('<I', header[36:40])[0]
            info['dtb_size'] = struct.unpack('<I', header[40:44])[0]
            
            # Version and additional fields
            info['version'] = struct.unpack('<I', header[header_addr:header_addr+4])[0]
            
            # Command line and board name
            info['cmd_line'] = header[64:576].rstrip(b'\x00').decode('utf-8', errors='ignore')
            info['board'] = header[48:64].rstrip(b'\x00').decode('utf-8', errors='ignore')
            
            # Handle different versions
            if info['version'] >= 2:
                info['dtb_size'] = struct.unpack('<I', header[1648:1652])[0]
                if len(header) > 1652:
                    info['dtb_addr'] = struct.unpack('<I', header[1652:1656])[0]
            
            if info['version'] >= 3:
                info['page_size'] = 4096
                if vndrboot:
                    info['kernel_addr'] = struct.unpack('<I', header[16:20])[0]
                    info['ramdisk_addr'] = struct.unpack('<I', header[20:24])[0]
                    info['ramdisk_size'] = struct.unpack('<I', header[24:28])[0]
                    info['cmd_line'] = header[28:2076].rstrip(b'\x00').decode('utf-8', errors='ignore')
                    if len(header) > 2076:
                        info['tags_addr'] = struct.unpack('<I', header[2076:2080])[0]
                    if len(header) > 2100:
                        info['dtb_size'] = struct.unpack('<I', header[2100:2104])[0]
                        info['dtb_addr'] = struct.unpack('<I', header[2104:2108])[0]
                else:
                    info['kernel_addr'] = 0x00008000
                    info['cmd_line'] = header[44:1580].rstrip(b'\x00').decode('utf-8', errors='ignore')
                    if len(header) > 16:
                        os_version = struct.unpack('<I', header[16:20])[0]
                        info['os_version'] = f"{(os_version>>22)}.{(os_version>>14)&0x7f}.{(os_version>>7)&0x7f}"
                        patch_level = os_version & 0x7ff
                        info['os_patch_level'] = f"{(patch_level>>4)+2000}:{patch_level&0xf:02d}"
            
            # Calculate offsets
            base_addr = info['kernel_addr'] - 0x00008000
            info['base_addr'] = base_addr
            info['kernel_offset'] = info['kernel_addr'] - base_addr
            info['ramdisk_offset'] = info['ramdisk_addr'] - base_addr
            info['second_offset'] = info['second_addr'] - base_addr
            info['tags_offset'] = info['tags_addr'] - base_addr
            
            return info
            
        except Exception as e:
            logger.exception("Error parsing boot header")
            return None
    
    def _extract_components(self, boot_img: Path, info: Dict):
        """Extract kernel, ramdisk, etc. from boot image"""
        page_size = info['page_size']
        
        # Calculate page counts
        k_count = (info['kernel_size'] + page_size - 1) // page_size
        r_count = (info['ramdisk_size'] + page_size - 1) // page_size
        s_count = (info['second_size'] + page_size - 1) // page_size
        d_count = (info['dtb_size'] + page_size - 1) // page_size
        
        # Calculate offsets in pages
        k_offset = 1
        r_offset = k_offset + k_count
        s_offset = r_offset + r_count
        d_offset = s_offset + s_count
        
        with open(boot_img, 'rb') as f:
            # Extract kernel
            if info['kernel_size'] > 0:
                f.seek(k_offset * page_size)
                kernel_data = f.read(info['kernel_size'])
                with open("kernel", 'wb') as kf:
                    kf.write(kernel_data)
            
            # Extract ramdisk
            if info['ramdisk_size'] > 0:
                f.seek(r_offset * page_size)
                ramdisk_data = f.read(info['ramdisk_size'])
                with open("ramdisk.packed", 'wb') as rf:
                    rf.write(ramdisk_data)
            
            # Extract second
            if info['second_size'] > 0:
                f.seek(s_offset * page_size)
                second_data = f.read(info['second_size'])
                with open("second.img", 'wb') as sf:
                    sf.write(second_data)
            
            # Extract DTB
            if info['dtb_size'] > 0:
                f.seek(d_offset * page_size)
                dtb_data = f.read(info['dtb_size'])
                dtb_name = "dtb.img" if info['version'] > 1 else "dt.img"
                with open(dtb_name, 'wb') as df:
                    df.write(dtb_data)
    
    def _decompress_ramdisk(self) -> bool:
        """Decompress ramdisk using various compression methods"""
        if not Path("ramdisk.packed").exists():
            return False
        
        # Check for MTK header
        with open("ramdisk.packed", 'rb') as f:
            header = f.read(8)
        
        if header[:4] == b'\x88\x16\x88\x58':  # MTK magic
            print_info("ramdisk has a MTK header")
            # Remove MTK header (512 bytes)
            with open("ramdisk.packed", 'rb') as f:
                f.seek(512)
                data = f.read()
            with open("ramdisk.packed", 'wb') as f:
                f.write(data)
        
        # Create ramdisk directory
        ramdisk_dir = Path("ramdisk")
        ramdisk_dir.mkdir(exist_ok=True)
        os.chdir(ramdisk_dir)
        
        ramdisk_packed = Path("../ramdisk.packed")
        
        # Try different compression formats
        formats = [
            ("gzip", self._try_gzip),
            ("lzma", self._try_lzma), 
            ("xz", self._try_xz),
            ("lzo", self._try_lzo),
            ("lz4", self._try_lz4)
        ]
        
        for format_name, decompress_func in formats:
            try:
                if decompress_func(ramdisk_packed):
                    print_info(f"ramdisk is {format_name} format.")
                    return True
            except Exception as e:
                logger.debug(f"Failed to decompress as {format_name}: {e}")
                continue
        
        print_error("ramdisk is unknown format, can't unpack ramdisk")
        return False
    
    def _try_gzip(self, ramdisk_file: Path) -> bool:
        """Try to decompress as gzip"""
        with open(ramdisk_file, 'rb') as f:
            if f.read(2) != b'\x1f\x8b':
                return False
        
        with gzip.open(ramdisk_file, 'rb') as f:
            data = f.read()
        
        return self._extract_cpio(data)
    
    def _try_lzma(self, ramdisk_file: Path) -> bool:
        """Try to decompress as LZMA"""
        try:
            with lzma.open(ramdisk_file, 'rb') as f:
                data = f.read()
            return self._extract_cpio(data)
        except:
            return False
    
    def _try_xz(self, ramdisk_file: Path) -> bool:
        """Try to decompress as XZ"""
        try:
            result = subprocess.run([
                "xz", "-t", str(ramdisk_file)
            ], capture_output=True, timeout=10)
            
            if result.returncode != 0:
                return False
            
            result = subprocess.run([
                "xz", "-d", "-c", str(ramdisk_file)
            ], capture_output=True, timeout=60)
            
            if result.returncode == 0:
                return self._extract_cpio(result.stdout)
        except:
            pass
        return False
    
    def _try_lzo(self, ramdisk_file: Path) -> bool:
        """Try to decompress as LZO"""
        try:
            result = subprocess.run([
                "lzop", "-t", str(ramdisk_file)
            ], capture_output=True, timeout=10)
            
            if result.returncode != 0:
                return False
            
            result = subprocess.run([
                "lzop", "-d", "-c", str(ramdisk_file)
            ], capture_output=True, timeout=60)
            
            if result.returncode == 0:
                return self._extract_cpio(result.stdout)
        except:
            pass
        return False
    
    def _try_lz4(self, ramdisk_file: Path) -> bool:
        """Try to decompress as LZ4"""
        try:
            result = subprocess.run([
                "lz4", "-d", str(ramdisk_file), "/dev/stdout"
            ], capture_output=True, timeout=60)
            
            if result.returncode == 0:
                return self._extract_cpio(result.stdout)
        except:
            pass
        return False
    
    def _extract_cpio(self, data: bytes) -> bool:
        """Extract CPIO archive from decompressed data"""
        try:
            result = subprocess.run([
                "cpio", "-i", "-d", "-m", "--no-absolute-filenames"
            ], input=data, timeout=60)
            
            return result.returncode == 0
        except:
            return False
    
    def _write_img_info(self, info: Dict):
        """Write boot image information to img_info file"""
        os.chdir("..")  # Go back to parent directory
        
        with open("img_info", 'w') as f:
            f.write(f"kernel=kernel\n")
            f.write(f"ramdisk=ramdisk\n")
            
            if info.get('second_size', 0) > 0:
                f.write(f"second=second.img\n")
                f.write(f"second_size={info['second_size']}\n")
            
            f.write(f"page_size={info['page_size']}\n")
            f.write(f"kernel_size={info['kernel_size']}\n")
            f.write(f"ramdisk_size={info['ramdisk_size']}\n")
            
            if info.get('dtb_size', 0) > 0:
                dtb_name = "dtb.img" if info['version'] > 1 else "dt.img"
                f.write(f"dt={dtb_name}\n")
                f.write(f"dtb_size={info['dtb_size']}\n")
                if info['version'] > 1:
                    f.write(f"dtb_offset=0x{info.get('dtb_offset', 0):08x}\n")
            
            f.write(f"base_addr=0x{info['base_addr']:08x}\n")
            f.write(f"kernel_offset=0x{info['kernel_offset']:08x}\n")
            f.write(f"ramdisk_offset=0x{info['ramdisk_offset']:08x}\n")
            f.write(f"tags_offset=0x{info['tags_offset']:08x}\n")
            
            if info.get('os_version'):
                f.write(f"os_version={info['os_version']}\n")
                f.write(f"os_patch_level={info['os_patch_level']}\n")
            
            # Escape command line properly
            cmd_line = info['cmd_line'].replace("'", "'\"'\"'")
            f.write(f"cmd_line='{cmd_line}'\n")
            f.write(f"board=\"{info['board']}\"\n")