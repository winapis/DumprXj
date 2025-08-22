import struct
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class BootImageUnpacker:
    def __init__(self):
        self.android_boot_magic = b"ANDROID!"
        self.vendor_boot_magic = b"VNDRBOOT"
    
    def unpack_boot_image(self, boot_img_path: Path, output_dir: Path) -> Dict[str, Any]:
        logger.info(f"Unpacking boot image: {boot_img_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(boot_img_path, 'rb') as f:
            header_data = f.read(1648)
        
        if header_data[:8] == self.android_boot_magic:
            return self._unpack_android_boot(boot_img_path, output_dir, header_data)
        elif header_data[:8] == self.vendor_boot_magic:
            return self._unpack_vendor_boot(boot_img_path, output_dir, header_data)
        else:
            raise ValueError("Invalid boot image format")
    
    def _unpack_android_boot(self, boot_img_path: Path, output_dir: Path, header_data: bytes) -> Dict[str, Any]:
        header = self._parse_android_header(header_data)
        
        with open(boot_img_path, 'rb') as f:
            f.seek(header['page_size'])
            
            kernel_data = f.read(header['kernel_size'])
            self._write_padded_file(kernel_data, output_dir / "kernel", header['page_size'])
            
            if header['ramdisk_size'] > 0:
                ramdisk_data = f.read(header['ramdisk_size'])
                ramdisk_file = output_dir / "ramdisk"
                self._write_padded_file(ramdisk_data, ramdisk_file, header['page_size'])
                self._extract_ramdisk(ramdisk_file, output_dir / "ramdisk")
            
            if header['second_size'] > 0:
                second_data = f.read(header['second_size'])
                self._write_padded_file(second_data, output_dir / "second", header['page_size'])
            
            if header['dtb_size'] > 0:
                dtb_data = f.read(header['dtb_size'])
                self._write_padded_file(dtb_data, output_dir / "dt", header['page_size'])
        
        self._write_img_info(header, output_dir / "img_info")
        
        return {
            'header_version': header['header_version'],
            'kernel_size': header['kernel_size'],
            'ramdisk_size': header['ramdisk_size'],
            'page_size': header['page_size'],
            'cmdline': header['cmdline']
        }
    
    def _parse_android_header(self, header_data: bytes) -> Dict[str, Any]:
        header_format = '<8s10I16s512s32s1024s'
        
        values = struct.unpack(header_format, header_data[:1648])
        
        return {
            'magic': values[0],
            'kernel_size': values[1],
            'kernel_addr': values[2],
            'ramdisk_size': values[3],
            'ramdisk_addr': values[4],
            'second_size': values[5],
            'second_addr': values[6],
            'tags_addr': values[7],
            'page_size': values[8],
            'header_version': values[9],
            'os_version': values[10],
            'name': values[11].rstrip(b'\x00').decode('ascii', errors='ignore'),
            'cmdline': values[12].rstrip(b'\x00').decode('ascii', errors='ignore'),
            'id': values[13],
            'extra_cmdline': values[14].rstrip(b'\x00').decode('ascii', errors='ignore')
        }
    
    def _unpack_vendor_boot(self, boot_img_path: Path, output_dir: Path, header_data: bytes) -> Dict[str, Any]:
        logger.info("Unpacking vendor boot image")
        return {'type': 'vendor_boot'}
    
    def _write_padded_file(self, data: bytes, output_path: Path, page_size: int):
        with open(output_path, 'wb') as f:
            f.write(data)
        
        padded_size = ((len(data) + page_size - 1) // page_size) * page_size
        if len(data) < padded_size:
            with open(output_path, 'ab') as f:
                f.write(b'\x00' * (padded_size - len(data)))
    
    def _extract_ramdisk(self, ramdisk_path: Path, output_dir: Path):
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            ramdisk_formats = [
                (['gzip', '-dc'], '.gz'),
                (['lz4', '-dc'], '.lz4'),
                (['xz', '-dc'], '.xz'),
                (['brotli', '-dc'], '.br')
            ]
            
            for cmd, ext in ramdisk_formats:
                try:
                    import subprocess
                    with open(ramdisk_path, 'rb') as f:
                        result = subprocess.run(cmd, input=f.read(), capture_output=True)
                        if result.returncode == 0:
                            cpio_data = result.stdout
                            self._extract_cpio(cpio_data, output_dir)
                            return
                except:
                    continue
            
            logger.warning("Could not decompress ramdisk")
            
        except Exception as e:
            logger.error(f"Failed to extract ramdisk: {e}")
    
    def _extract_cpio(self, cpio_data: bytes, output_dir: Path):
        import subprocess
        
        try:
            process = subprocess.Popen(
                ['cpio', '-i', '-d', '-m'],
                stdin=subprocess.PIPE,
                cwd=output_dir,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(input=cpio_data)
            
            if process.returncode != 0:
                logger.warning(f"CPIO extraction warning: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Failed to extract CPIO: {e}")
    
    def _write_img_info(self, header: Dict[str, Any], info_path: Path):
        with open(info_path, 'w') as f:
            f.write(f"kernel=kernel\n")
            f.write(f"ramdisk=ramdisk\n")
            f.write(f"page_size={header['page_size']}\n")
            f.write(f"kernel_size={header['kernel_size']}\n")
            f.write(f"ramdisk_size={header['ramdisk_size']}\n")
            f.write(f"base_addr=0x{header['kernel_addr'] - 0x00008000:08x}\n")
            f.write(f"kernel_offset=0x{0x00008000:08x}\n")
            f.write(f"ramdisk_offset=0x{header['ramdisk_addr'] - (header['kernel_addr'] - 0x00008000):08x}\n")
            f.write(f"second_offset=0x{header['second_addr'] - (header['kernel_addr'] - 0x00008000):08x}\n") 
            f.write(f"tags_offset=0x{header['tags_addr'] - (header['kernel_addr'] - 0x00008000):08x}\n")
            f.write(f"cmdline={header['cmdline']}\n")
            
            if header.get('extra_cmdline'):
                f.write(f"extra_cmdline={header['extra_cmdline']}\n")
            
            if header.get('header_version'):
                f.write(f"header_version={header['header_version']}\n")
            
            if header.get('os_version'):
                f.write(f"os_version={header['os_version']}\n")