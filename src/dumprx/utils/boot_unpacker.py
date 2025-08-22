"""
Boot image unpacking utilities converted from shell script
Originally by @xiaolu, with MTK Header Detection by @carlitros900
"""

import os
import sys
import struct
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict
import tempfile
import shutil


class BootUnpacker:
    """Boot image unpacking utility"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def log(self, message: str):
        """Print log message if verbose"""
        if self.verbose:
            print(f"[BootUnpacker] {message}")
    
    def error(self, message: str):
        """Print error message"""
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def find_android_header(self, boot_img: Path) -> Optional[int]:
        """Find ANDROID! or VNDRBOOT header offset in boot image"""
        try:
            with open(boot_img, 'rb') as f:
                data = f.read()
            
            android_offset = data.find(b'ANDROID!')
            vndr_offset = data.find(b'VNDRBOOT')
            
            if android_offset != -1:
                return android_offset
            elif vndr_offset != -1:
                return vndr_offset
            else:
                return None
                
        except Exception as e:
            self.error(f"Failed to find header: {e}")
            return None
    
    def extract_header_info(self, boot_img: Path, offset: int) -> Dict[str, any]:
        """Extract boot image header information"""
        try:
            with open(boot_img, 'rb') as f:
                f.seek(offset)
                header = f.read(1648)  # Boot header size
            
            if header[:8] == b'ANDROID!':
                return self._parse_android_header(header)
            elif header[:8] == b'VNDRBOOT':
                return self._parse_vndr_header(header)
            else:
                raise ValueError("Unknown header format")
                
        except Exception as e:
            self.error(f"Failed to extract header info: {e}")
            return {}
    
    def _parse_android_header(self, header: bytes) -> Dict[str, any]:
        """Parse Android boot header"""
        # Android boot header structure
        fmt = '<8s10I16s512s32s1024s'
        fields = struct.unpack(fmt, header[:1648])
        
        return {
            'magic': fields[0],
            'kernel_size': fields[1],
            'kernel_addr': fields[2],
            'ramdisk_size': fields[3],
            'ramdisk_addr': fields[4],
            'second_size': fields[5],
            'second_addr': fields[6],
            'tags_addr': fields[7],
            'page_size': fields[8],
            'header_version': fields[9],
            'os_version': fields[10],
            'name': fields[11].decode('utf-8', errors='ignore').rstrip('\x00'),
            'cmdline': fields[12].decode('utf-8', errors='ignore').rstrip('\x00'),
            'id': fields[13],
            'extra_cmdline': fields[14].decode('utf-8', errors='ignore').rstrip('\x00')
        }
    
    def _parse_vndr_header(self, header: bytes) -> Dict[str, any]:
        """Parse vendor boot header"""
        # This is a simplified version - actual vendor boot header is more complex
        fmt = '<8s10I'
        fields = struct.unpack(fmt, header[:48])
        
        return {
            'magic': fields[0],
            'header_version': fields[1],
            'page_size': fields[2],
            'kernel_addr': fields[3],
            'ramdisk_addr': fields[4],
            'vendor_ramdisk_size': fields[5],
            'cmdline_size': fields[6],
            'tags_addr': fields[7],
            'name_size': fields[8],
            'header_size': fields[9],
            'dtb_size': fields[10]
        }
    
    def extract_sections(self, boot_img: Path, output_dir: Path, header_info: Dict[str, any], offset: int):
        """Extract kernel, ramdisk, and other sections from boot image"""
        try:
            page_size = header_info.get('page_size', 2048)
            
            with open(boot_img, 'rb') as f:
                f.seek(offset)
                
                # Calculate section offsets
                kernel_offset = offset + self._align_to_page(header_info.get('header_size', page_size), page_size)
                kernel_size = header_info.get('kernel_size', 0)
                
                ramdisk_offset = kernel_offset + self._align_to_page(kernel_size, page_size)
                ramdisk_size = header_info.get('ramdisk_size', 0)
                
                second_offset = ramdisk_offset + self._align_to_page(ramdisk_size, page_size)
                second_size = header_info.get('second_size', 0)
                
                # Extract kernel
                if kernel_size > 0:
                    f.seek(kernel_offset)
                    kernel_data = f.read(kernel_size)
                    kernel_path = output_dir / 'kernel'
                    with open(kernel_path, 'wb') as kf:
                        kf.write(kernel_data)
                    self.log(f"Extracted kernel ({kernel_size} bytes)")
                
                # Extract ramdisk
                if ramdisk_size > 0:
                    f.seek(ramdisk_offset)
                    ramdisk_data = f.read(ramdisk_size)
                    ramdisk_path = output_dir / 'ramdisk.gz'
                    with open(ramdisk_path, 'wb') as rf:
                        rf.write(ramdisk_data)
                    self.log(f"Extracted ramdisk ({ramdisk_size} bytes)")
                    
                    # Decompress ramdisk
                    self._decompress_ramdisk(ramdisk_path, output_dir)
                
                # Extract second stage if present
                if second_size > 0:
                    f.seek(second_offset)
                    second_data = f.read(second_size)
                    second_path = output_dir / 'second'
                    with open(second_path, 'wb') as sf:
                        sf.write(second_data)
                    self.log(f"Extracted second stage ({second_size} bytes)")
                    
        except Exception as e:
            self.error(f"Failed to extract sections: {e}")
    
    def _align_to_page(self, size: int, page_size: int) -> int:
        """Align size to page boundary"""
        return ((size + page_size - 1) // page_size) * page_size
    
    def _decompress_ramdisk(self, ramdisk_path: Path, output_dir: Path):
        """Decompress ramdisk using appropriate method"""
        ramdisk_dir = output_dir / 'ramdisk'
        ramdisk_dir.mkdir(exist_ok=True)
        
        # Try different decompression methods
        methods = [
            (['gzip', '-dc'], 'gzip'),
            (['lz4', '-dc'], 'lz4'),
            (['xz', '-dc'], 'xz'),
            (['lzma', '-dc'], 'lzma'),
            (['zstd', '-dc'], 'zstd')
        ]
        
        for cmd, method in methods:
            try:
                # Test if we can decompress
                with open(ramdisk_path, 'rb') as f:
                    proc = subprocess.Popen(
                        cmd + [str(ramdisk_path)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    # Extract using cpio
                    cpio_proc = subprocess.Popen(
                        ['cpio', '-idm'],
                        stdin=proc.stdout,
                        cwd=ramdisk_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    proc.stdout.close()
                    _, cpio_err = cpio_proc.communicate()
                    _, decomp_err = proc.communicate()
                    
                    if proc.returncode == 0 and cpio_proc.returncode == 0:
                        self.log(f"Decompressed ramdisk using {method}")
                        return
                        
            except FileNotFoundError:
                continue
            except Exception as e:
                self.log(f"Failed to decompress with {method}: {e}")
                continue
        
        self.log("Could not decompress ramdisk - trying as uncompressed")
        try:
            # Try extracting as uncompressed cpio
            with open(ramdisk_path, 'rb') as f:
                proc = subprocess.Popen(
                    ['cpio', '-idm'],
                    stdin=f,
                    cwd=ramdisk_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                _, err = proc.communicate()
                
                if proc.returncode == 0:
                    self.log("Extracted uncompressed ramdisk")
                else:
                    self.log(f"Failed to extract ramdisk: {err.decode()}")
                    
        except Exception as e:
            self.error(f"Failed to extract ramdisk: {e}")
    
    def save_image_info(self, output_dir: Path, header_info: Dict[str, any], format_type: str = "android"):
        """Save image information to file"""
        info_file = output_dir / 'img_info'
        
        try:
            with open(info_file, 'w') as f:
                f.write(f"format={format_type}\n")
                f.write(f"magic={header_info.get('magic', b'').decode('utf-8', errors='ignore')}\n")
                f.write(f"kernel_size={header_info.get('kernel_size', 0)}\n")
                f.write(f"kernel_addr=0x{header_info.get('kernel_addr', 0):08x}\n")
                f.write(f"ramdisk_size={header_info.get('ramdisk_size', 0)}\n")
                f.write(f"ramdisk_addr=0x{header_info.get('ramdisk_addr', 0):08x}\n")
                f.write(f"second_size={header_info.get('second_size', 0)}\n")
                f.write(f"second_addr=0x{header_info.get('second_addr', 0):08x}\n")
                f.write(f"tags_addr=0x{header_info.get('tags_addr', 0):08x}\n")
                f.write(f"page_size={header_info.get('page_size', 2048)}\n")
                f.write(f"header_version={header_info.get('header_version', 0)}\n")
                f.write(f"os_version={header_info.get('os_version', 0)}\n")
                f.write(f"name={header_info.get('name', '')}\n")
                f.write(f"cmdline={header_info.get('cmdline', '')}\n")
                if 'extra_cmdline' in header_info:
                    f.write(f"extra_cmdline={header_info.get('extra_cmdline', '')}\n")
                    
            self.log(f"Saved image info to {info_file}")
            
        except Exception as e:
            self.error(f"Failed to save image info: {e}")
    
    def unpack(self, boot_img_path: str, output_dir_path: str) -> bool:
        """Main unpack function"""
        boot_img = Path(boot_img_path)
        output_dir = Path(output_dir_path)
        
        if not boot_img.exists():
            self.error(f"Boot image not found: {boot_img}")
            return False
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log(f"Unpacking {boot_img} to {output_dir}")
        
        # Find Android header
        offset = self.find_android_header(boot_img)
        if offset is None:
            self.error("No Android boot header found")
            return False
        
        self.log(f"Found header at offset {offset}")
        
        # Extract a clean boot image if offset > 0
        clean_boot = boot_img
        if offset > 0:
            clean_boot = output_dir / 'bootimg'
            try:
                with open(boot_img, 'rb') as src, open(clean_boot, 'wb') as dst:
                    src.seek(offset)
                    shutil.copyfileobj(src, dst)
                self.log(f"Extracted clean boot image")
            except Exception as e:
                self.error(f"Failed to extract clean boot image: {e}")
                return False
        
        # Parse header
        header_info = self.extract_header_info(clean_boot, 0)
        if not header_info:
            self.error("Failed to parse boot header")
            return False
        
        self.log(f"Header info: {header_info}")
        
        # Determine format
        format_type = "vendor_boot" if header_info.get('magic') == b'VNDRBOOT' else "android"
        
        # Extract sections
        self.extract_sections(clean_boot, output_dir, header_info, 0)
        
        # Save image info
        self.save_image_info(output_dir, header_info, format_type)
        
        self.log("Unpack completed")
        return True


def main():
    """Command line interface"""
    if len(sys.argv) < 3:
        print("\n >>  Unpack boot.img tool, Originally by @xiaolu  <<")
        print("     - w/ MTK Header Detection, by @carlitros900")
        print("     - Python conversion by DumprX")
        print("-----------------------------------------------------")
        print(" Not enough parameters or parameter error!")
        print(" unpack boot.img & decompress ramdisk:")
        print(f"    {sys.argv[0]} [img] [output dir]")
        print(f"    {sys.argv[0]} boot.img boot20130905\n")
        sys.exit(1)
    
    boot_img = sys.argv[1]
    output_dir = sys.argv[2]
    verbose = len(sys.argv) > 3 and sys.argv[3] == '-v'
    
    unpacker = BootUnpacker(verbose=verbose)
    success = unpacker.unpack(boot_img, output_dir)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()