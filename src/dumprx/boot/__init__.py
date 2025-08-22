"""
Boot image analysis module
"""

from pathlib import Path
from ..core.logger import logger
from ..core.config import config


class BootImageAnalyzer:
    """Analyzes boot images with multi-boot support"""
    
    def analyze(self, boot_img: Path) -> dict:
        """Analyze boot image and extract information"""
        logger.info(f"🥾 Analyzing boot image: {boot_img.name}")
        
        analysis = {
            "file": boot_img,
            "type": self._detect_boot_type(boot_img),
            "ramdisk_version": None,
            "compression": None,
            "kernel_version": None,
            "dtb_found": False
        }
        
        # Use unpackboot.sh for detailed analysis
        try:
            self._unpack_boot_image(boot_img)
            analysis.update(self._parse_boot_info(boot_img))
        except Exception as e:
            logger.debug(f"Boot analysis failed: {str(e)}")
        
        return analysis
    
    def _detect_boot_type(self, boot_img: Path) -> str:
        """Detect type of boot image"""
        name = boot_img.name.lower()
        
        if "vendor_boot" in name:
            return "vendor_boot"
        elif "init_boot" in name:
            return "init_boot"
        elif "vendor_kernel_boot" in name:
            return "vendor_kernel_boot"
        elif "recovery" in name:
            return "recovery"
        elif "boot" in name:
            return "boot"
        else:
            return "unknown"
    
    def _unpack_boot_image(self, boot_img: Path):
        """Unpack boot image using unpackboot.sh"""
        import subprocess
        
        script_path = config.get_tool_path("unpackboot")
        output_dir = boot_img.parent / f"{boot_img.stem}_unpacked"
        output_dir.mkdir(exist_ok=True)
        
        cmd = ["bash", str(script_path), str(boot_img), str(output_dir)]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=output_dir
        )
        
        if result.returncode == 0:
            logger.success(f"✅ Unpacked boot image: {boot_img.name}")
        else:
            logger.debug(f"Boot unpacking failed: {result.stderr}")
    
    def _parse_boot_info(self, boot_img: Path) -> dict:
        """Parse boot image information"""
        info = {}
        
        # Look for img_info file
        output_dir = boot_img.parent / f"{boot_img.stem}_unpacked"
        img_info_file = output_dir / "img_info"
        
        if img_info_file.exists():
            try:
                with open(img_info_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            info[key] = value
            except Exception:
                pass
        
        return info