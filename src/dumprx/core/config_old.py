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
    
    # External tools
    external_tools: Dict[str, str] = field(default_factory=dict)
    
    # Supported partitions
    partitions: list = field(default_factory=list)
    ext4_partitions: list = field(default_factory=list)
    
    other_partitions: Dict[str, str] = field(default_factory=lambda: {
        "tz.mbn": "tz",
        "tz.img": "tz", 
        "modem.img": "modem",
        "NON-HLOS": "modem",
        "boot-verified.img": "boot",
        "recovery-verified.img": "recovery",
        "dtbo-verified.img": "dtbo"
    })
    
    # Tool paths (will be set in __post_init__)
    tools: Dict[str, Path] = field(default_factory=dict)
    
    # Telegram settings
    telegram_enabled: bool = False
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # GitHub/GitLab settings
    git_provider: str = "github"
    github_token: Optional[str] = None
    github_orgname: Optional[str] = None
    gitlab_token: Optional[str] = None
    gitlab_group: Optional[str] = None
    gitlab_instance: str = "gitlab.com"
    
    def __post_init__(self):
        """Initialize directory paths and tool paths"""
        self.input_dir = self.project_dir / "input"
        self.utils_dir = self.project_dir / "utils"
        self.output_dir = self.project_dir / "out"
        self.tmp_dir = self.output_dir / "tmp"
        
        # Create directories
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.tmp_dir.mkdir(exist_ok=True)
        
        # Initialize tool paths
        self._init_tool_paths()
        
        # Load tokens from files if they exist
        self._load_tokens()
    
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
            
            # Shell scripts
            "unpackboot": utils / "unpackboot.sh",
            "megamediadrive_dl": utils / "downloaders" / "mega-media-drive_dl.sh",
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