import os
import shutil
from pathlib import Path
from typing import Optional, List


class Config:
    def __init__(self, project_dir: Optional[Path] = None):
        if project_dir is None:
            project_dir = Path(__file__).parent.parent.parent
        
        self.project_dir = project_dir.resolve()
        self.input_dir = self.project_dir / "input"
        self.utils_dir = self.project_dir / "utils"
        self.out_dir = self.project_dir / "out"
        self.tmp_dir = self.out_dir / "tmp"
        
        # External tools that need to be cloned
        self.external_tools = [
            "bkerler/oppo_ozip_decrypt",
            "bkerler/oppo_decrypt", 
            "marin-m/vmlinux-to-elf",
            "ShivamKumarJha/android_tools",
            "HemanthJabalpuri/pacextractor"
        ]
        
        # Supported partitions
        self.partitions = [
            "system", "system_ext", "system_other", "systemex", "vendor", "cust", "odm", "oem", 
            "factory", "product", "xrom", "modem", "dtbo", "dtb", "boot", "vendor_boot", 
            "recovery", "tz", "oppo_product", "preload_common", "opproduct", "reserve", 
            "india", "my_preload", "my_odm", "my_stock", "my_operator", "my_country", 
            "my_product", "my_company", "my_engineering", "my_heytap", "my_custom", 
            "my_manifest", "my_carrier", "my_region", "my_bigball", "my_version", 
            "special_preload", "system_dlkm", "vendor_dlkm", "odm_dlkm", "init_boot", 
            "vendor_kernel_boot", "odmko", "socko", "nt_log", "mi_ext", "hw_product", 
            "product_h", "preas", "preavs"
        ]
        
        self.ext4_partitions = [
            "system", "vendor", "cust", "odm", "oem", "factory", "product", "xrom", 
            "systemex", "oppo_product", "preload_common", "hw_product", "product_h", 
            "preas", "preavs"
        ]
        
        self.other_partitions = [
            "tz.mbn:tz", "tz.img:tz", "modem.img:modem", "NON-HLOS:modem", 
            "boot-verified.img:boot", "recovery-verified.img:recovery", 
            "dtbo-verified.img:dtbo"
        ]
        
        # Binary tool paths
        self._setup_tool_paths()
    
    def _setup_tool_paths(self):
        self.tools = {}
        
        # Check for system 7zz first, fallback to bundled
        if shutil.which("7zz"):
            self.tools["7zz"] = "7zz"
        else:
            self.tools["7zz"] = str(self.utils_dir / "bin" / "7zz")
            
        # Other tools
        tool_map = {
            "sdat2img": "sdat2img.py",
            "simg2img": "bin/simg2img", 
            "packsparseimg": "bin/packsparseimg",
            "unsin": "unsin",
            "payload_extractor": "bin/payload-dumper-go",
            "dtc": "dtc",
            "vmlinux2elf": "vmlinux-to-elf/vmlinux-to-elf",
            "kallsyms_finder": "vmlinux-to-elf/kallsyms-finder",
            "ozipdecrypt": "oppo_ozip_decrypt/ozipdecrypt.py",
            "ofp_qc_decrypt": "oppo_decrypt/ofp_qc_decrypt.py",
            "ofp_mtk_decrypt": "oppo_decrypt/ofp_mtk_decrypt.py",
            "opsdecrypt": "oppo_decrypt/opscrypto.py",
            "lpunpack": "lpunpack",
            "splituapp": "splituapp.py",
            "pacextractor": "pacextractor/python/pacExtractor.py",
            "nb0_extract": "nb0-extract",
            "kdz_extract": "kdztools/unkdz.py",
            "dz_extract": "kdztools/undz.py",
            "ruudecrypt": "RUU_Decrypt_Tool",
            "extract_ikconfig": "extract-ikconfig",
            "aml_extract": "aml-upgrade-package-extract",
            "afptool_extract": "bin/afptool",
            "rk_extract": "bin/rkImageMaker",
            "transfer": "bin/transfer",
            "fsck_erofs": "bin/fsck.erofs"
        }
        
        for tool, path in tool_map.items():
            self.tools[tool] = str(self.utils_dir / path)
    
    def setup_directories(self):
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean tmp directory
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_project_dir(self):
        if " " in str(self.project_dir):
            raise ValueError("Project Directory Path Contains Empty Space. Place The Script In A Proper UNIX-Formatted Folder")
    
    def get_tool_path(self, tool_name: str) -> str:
        return self.tools.get(tool_name, tool_name)