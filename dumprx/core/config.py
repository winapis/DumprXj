"""
Configuration management for DumprX.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class Paths:
    """Directory paths configuration."""
    project_dir: str
    input_dir: str
    utils_dir: str
    output_dir: str
    temp_dir: str

@dataclass
class Tools:
    """External tools configuration."""
    sdat2img: str
    simg2img: str
    payload_dumper: str
    lpunpack: str
    kdz_extract: str
    dz_extract: str
    unpackboot: str
    sevenzip: str

@dataclass
class Tokens:
    """Authentication tokens configuration."""
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

class Config:
    """Configuration manager for DumprX."""
    
    def __init__(self, project_dir: Optional[str] = None):
        if project_dir is None:
            project_dir = Path(__file__).parent.parent.parent.absolute()
        
        self.project_dir = Path(project_dir)
        self.config_file = self.project_dir / "dumprx_config.json"
        
        # Initialize paths
        self.paths = Paths(
            project_dir=str(self.project_dir),
            input_dir=str(self.project_dir / "input"),
            utils_dir=str(self.project_dir / "utils"),
            output_dir=str(self.project_dir / "out"),
            temp_dir=str(self.project_dir / "out" / "tmp")
        )
        
        # Initialize tools paths
        utils_dir = self.project_dir / "utils"
        self.tools = Tools(
            sdat2img=str(utils_dir / "sdat2img.py"),
            simg2img=str(utils_dir / "bin" / "simg2img"),
            payload_dumper=str(utils_dir / "bin" / "payload-dumper-go"),
            lpunpack=str(utils_dir / "lpunpack"),
            kdz_extract=str(utils_dir / "kdztools" / "unkdz.py"),
            dz_extract=str(utils_dir / "kdztools" / "undz.py"),
            unpackboot=str(utils_dir / "unpackboot.sh"),
            sevenzip=str(utils_dir / "bin" / "7zz") if (utils_dir / "bin" / "7zz").exists() else "7zz"
        )
        
        # Initialize tokens
        self.tokens = Tokens()
        self._load_tokens()
        
        # Supported partitions
        self.partitions = [
            "system", "system_ext", "system_other", "systemex", "vendor", "cust", 
            "odm", "oem", "factory", "product", "xrom", "modem", "dtbo", "dtb", 
            "boot", "vendor_boot", "recovery", "tz", "oppo_product", "preload_common",
            "opproduct", "reserve", "india", "my_preload", "my_odm", "my_stock",
            "my_operator", "my_country", "my_product", "my_company", "my_engineering",
            "my_heytap", "my_custom", "my_manifest", "my_carrier", "my_region",
            "my_bigball", "my_version", "special_preload", "system_dlkm", "vendor_dlkm",
            "odm_dlkm", "init_boot", "vendor_kernel_boot", "odmko", "socko", "nt_log",
            "mi_ext", "hw_product", "product_h", "preas", "preavs"
        ]
        
        # EXT4 partitions
        self.ext4_partitions = [
            "system", "vendor", "cust", "odm", "oem", "factory", "product", "xrom",
            "systemex", "oppo_product", "preload_common", "hw_product", "product_h",
            "preas", "preavs"
        ]
        
        # External tools to clone
        self.external_tools = [
            "bkerler/oppo_ozip_decrypt",
            "bkerler/oppo_decrypt", 
            "marin-m/vmlinux-to-elf",
            "ShivamKumarJha/android_tools",
            "HemanthJabalpuri/pacextractor"
        ]
        
        # Load configuration file if exists
        self._load_config()
    
    def _load_tokens(self):
        """Load authentication tokens from files."""
        token_files = {
            'github_token': self.project_dir / '.github_token',
            'gitlab_token': self.project_dir / '.gitlab_token', 
            'telegram_token': self.project_dir / '.tg_token',
            'telegram_chat_id': self.project_dir / '.tg_chat'
        }
        
        for attr, file_path in token_files.items():
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        setattr(self.tokens, attr, f.read().strip())
                except Exception:
                    pass
    
    def _load_config(self):
        """Load configuration from JSON file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                # Update paths if in config
                if 'paths' in config_data:
                    for key, value in config_data['paths'].items():
                        if hasattr(self.paths, key):
                            setattr(self.paths, key, value)
                
                # Update tools if in config  
                if 'tools' in config_data:
                    for key, value in config_data['tools'].items():
                        if hasattr(self.tools, key):
                            setattr(self.tools, key, value)
                            
            except Exception:
                pass
    
    def save_config(self):
        """Save current configuration to JSON file."""
        config_data = {
            'paths': asdict(self.paths),
            'tools': asdict(self.tools),
            'partitions': self.partitions,
            'ext4_partitions': self.ext4_partitions,
            'external_tools': self.external_tools
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def create_directories(self):
        """Create necessary directories."""
        dirs_to_create = [
            self.paths.input_dir,
            self.paths.output_dir, 
            self.paths.temp_dir
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get_download_dir(self) -> str:
        """Get download directory path."""
        return self.paths.input_dir
    
    def get_output_dir(self) -> str:
        """Get output directory path."""
        return self.paths.output_dir
    
    def get_temp_dir(self) -> str:
        """Get temporary directory path."""
        return self.paths.temp_dir
    
    def get_utils_dir(self) -> str:
        """Get utils directory path."""
        return self.paths.utils_dir