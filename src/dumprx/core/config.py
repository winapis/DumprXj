"""
Core configuration management for DumprX
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dataclasses import dataclass, field


@dataclass
class Config:
    """Main configuration class for DumprX"""
    
    # Directories
    project_dir: Path = field(init=False)
    input_dir: Path = field(init=False)
    utils_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    tmp_dir: Path = field(init=False)
    
    # Configuration data from YAML
    external_tools: Dict[str, str] = field(default_factory=dict)
    partitions: list = field(default_factory=list)
    ext4_partitions: list = field(default_factory=list)
    other_partitions: Dict[str, str] = field(default_factory=dict)
    
    # Tool paths (will be set in __post_init__)
    tools: Dict[str, Path] = field(default_factory=dict)
    
    # Logging configuration
    log_level: str = "INFO"
    use_colors: bool = True
    use_emojis: bool = True
    show_progress: bool = True
    
    # Download configuration
    chunk_size: int = 8192
    max_retries: int = 3
    timeout: int = 30
    user_agent: str = "DumprX/2.0"
    
    # Telegram configuration
    telegram_enabled: bool = False
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_queue_size: int = 10
    
    # Git provider settings
    git_provider: str = "github"
    github_token: Optional[str] = None
    github_orgname: Optional[str] = None
    gitlab_token: Optional[str] = None
    gitlab_group: Optional[str] = None
    gitlab_instance: str = "gitlab.com"
    
    def __post_init__(self):
        """Initialize configuration from YAML file"""
        # Set project directory
        self.project_dir = Path(__file__).parent.parent.parent.parent
        
        # Load configuration from YAML
        self._load_config()
        
        # Initialize directory paths
        self._init_directories()
        
        # Initialize tool paths
        self._init_tool_paths()
        
        # Load tokens from files if they exist
        self._load_tokens()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = self.project_dir / "config.yaml"
        
        if not config_path.exists():
            # Use default configuration if no config file exists
            self._set_defaults()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Load directories configuration
            if 'directories' in config_data:
                dirs = config_data['directories']
                if dirs.get('project_dir'):
                    self.project_dir = Path(dirs['project_dir']).expanduser().resolve()
            
            # Load external tools
            if 'external_tools' in config_data:
                self.external_tools = config_data['external_tools']
            
            # Load partitions
            if 'partitions' in config_data:
                self.partitions = config_data['partitions']
            
            if 'ext4_partitions' in config_data:
                self.ext4_partitions = config_data['ext4_partitions']
            
            if 'other_partitions' in config_data:
                self.other_partitions = config_data['other_partitions']
            
            # Load logging configuration
            if 'logging' in config_data:
                log_config = config_data['logging']
                self.log_level = log_config.get('level', self.log_level)
                self.use_colors = log_config.get('use_colors', self.use_colors)
                self.use_emojis = log_config.get('use_emojis', self.use_emojis)
                self.show_progress = log_config.get('show_progress', self.show_progress)
            
            # Load download configuration
            if 'download' in config_data:
                dl_config = config_data['download']
                self.chunk_size = dl_config.get('chunk_size', self.chunk_size)
                self.max_retries = dl_config.get('max_retries', self.max_retries)
                self.timeout = dl_config.get('timeout', self.timeout)
                self.user_agent = dl_config.get('user_agent', self.user_agent)
            
            # Load telegram configuration
            if 'telegram' in config_data:
                tg_config = config_data['telegram']
                self.telegram_enabled = tg_config.get('enabled', self.telegram_enabled)
                self.telegram_token = tg_config.get('token') or None
                self.telegram_chat_id = tg_config.get('chat_id') or None
                self.telegram_queue_size = tg_config.get('queue_size', self.telegram_queue_size)
                
        except Exception as e:
            print(f"Warning: Failed to load config.yaml: {e}")
            print("Using default configuration.")
            self._set_defaults()
    
    def _set_defaults(self):
        """Set default configuration values"""
        self.external_tools = {
            "oppo_ozip_decrypt": "bkerler/oppo_ozip_decrypt",
            "oppo_decrypt": "bkerler/oppo_decrypt",
            "vmlinux-to-elf": "marin-m/vmlinux-to-elf",
            "android_tools": "ShivamKumarJha/android_tools",
            "pacextractor": "HemanthJabalpuri/pacextractor",
        }
        
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
        
        self.ext4_partitions = [
            "system", "vendor", "cust", "odm", "oem", "factory", "product", "xrom",
            "systemex", "oppo_product", "preload_common", "hw_product", "product_h",
            "preas", "preavs"
        ]
        
        self.other_partitions = {
            "tz.mbn": "tz",
            "tz.img": "tz", 
            "modem.img": "modem",
            "NON-HLOS": "modem",
            "boot-verified.img": "boot",
            "recovery-verified.img": "recovery",
            "dtbo-verified.img": "dtbo"
        }
    
    def _init_directories(self):
        """Initialize directory paths"""
        # Load custom directory names from config if available
        config_path = self.project_dir / "config.yaml"
        custom_dirs = {}
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                if 'directories' in config_data:
                    custom_dirs = config_data['directories']
            except Exception:
                pass
        
        # Set directory paths
        self.input_dir = self.project_dir / custom_dirs.get('input_dir', 'input')
        self.utils_dir = self.project_dir / custom_dirs.get('utils_dir', 'utils')
        self.output_dir = self.project_dir / custom_dirs.get('output_dir', 'out')
        self.tmp_dir = self.project_dir / custom_dirs.get('tmp_dir', 'tmp')
        
        # Create directories
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.tmp_dir.mkdir(exist_ok=True)
    
    def _init_tool_paths(self):
        """Initialize paths to external tools"""
        utils = self.utils_dir
        
        self.tools = {
            # Python scripts  
            "sdat2img": utils / "sdat2img.py",
            "ozipdecrypt": utils / "oppo_ozip_decrypt" / "ozipdecrypt.py",
            "ofp_qc_decrypt": utils / "oppo_decrypt" / "ofp_qc_decrypt.py", 
            "ofp_mtk_decrypt": utils / "oppo_decrypt" / "ofp_mtk_decrypt.py",
            "opsdecrypt": utils / "oppo_decrypt" / "opscrypto.py",
            "splituapp": utils / "splituapp.py",
            "pacextractor": utils / "pacextractor" / "python" / "pacExtractor.py",
            "kdz_extract": utils / "kdztools" / "unkdz.py",
            "dz_extract": utils / "kdztools" / "undz.py",
            "vmlinux2elf": utils / "vmlinux-to-elf" / "vmlinux-to-elf",
            "kallsyms_finder": utils / "vmlinux-to-elf" / "kallsyms-finder",
            
            # Binary tools
            "7zz": utils / "bin" / "7zz",
            "simg2img": utils / "bin" / "simg2img",
            "packsparseimg": utils / "bin" / "packsparseimg",
            "payload_extractor": utils / "bin" / "payload-dumper-go",
            "unsin": utils / "unsin",
            "dtc": utils / "dtc",
            "lpunpack": utils / "lpunpack",
            "nb0_extract": utils / "nb0-extract",
            "ruu_decrypt": utils / "RUU_Decrypt_Tool",
            "extract_ikconfig": utils / "extract-ikconfig",
            "aml_extract": utils / "aml-upgrade-package-extract",
            "afptool": utils / "bin" / "afptool",
            "rk_extract": utils / "bin" / "rkImageMaker",
            "transfer": utils / "bin" / "transfer",
            "fsck_erofs": utils / "bin" / "fsck.erofs",
            
            # Python modules (replaced shell scripts)
            "unpackboot": "dumprx.utils.boot_unpacker",  # Python module instead of shell script
            "advanced_downloader": "dumprx.utils.advanced_downloader",  # Python module
            "afh_dl": utils / "downloaders" / "afh_dl.py",
        }
    
    def _load_tokens(self):
        """Load authentication tokens from files"""
        token_files = {
            "telegram_token": ".tg_token",
            "telegram_chat_id": ".tg_chat", 
            "github_token": ".github_token",
            "github_orgname": ".github_orgname",
            "gitlab_token": ".gitlab_token",
            "gitlab_group": ".gitlab_group",
            "gitlab_instance": ".gitlab_instance"
        }
        
        for attr, filename in token_files.items():
            filepath = self.project_dir / filename
            if filepath.exists():
                try:
                    value = filepath.read_text().strip()
                    if value:
                        setattr(self, attr, value)
                        if attr in ["telegram_token", "telegram_chat_id"]:
                            self.telegram_enabled = True
                except Exception:
                    continue
    
    def get_tool_path(self, tool_name: str) -> Path:
        """Get path to a specific tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return self.tools[tool_name]
    
    def validate_tools(self) -> Dict[str, bool]:
        """Validate that all required tools exist"""
        results = {}
        for name, path in self.tools.items():
            results[name] = path.exists()
        return results


# Global config instance
config = Config()