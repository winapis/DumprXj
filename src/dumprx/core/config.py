"""
Configuration management for DumprX.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """Main configuration class for DumprX."""
    
    # Directory paths
    project_dir: Path = field(default_factory=lambda: Path.cwd())
    input_dir: Path = field(init=False)
    utils_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    temp_dir: Path = field(init=False)
    
    # External tools
    external_tools: Dict[str, str] = field(default_factory=lambda: {
        'oppo_ozip_decrypt': 'bkerler/oppo_ozip_decrypt',
        'oppo_decrypt': 'bkerler/oppo_decrypt',
        'vmlinux_to_elf': 'marin-m/vmlinux-to-elf',
        'android_tools': 'ShivamKumarJha/android_tools',
        'pacextractor': 'HemanthJabalpuri/pacextractor',
    })
    
    # Supported partitions
    partitions: list = field(default_factory=lambda: [
        "system", "system_ext", "system_other", "systemex", "vendor", "cust", 
        "odm", "oem", "factory", "product", "xrom", "modem", "dtbo", "dtb", 
        "boot", "vendor_boot", "recovery", "tz", "oppo_product", "preload_common",
        "init_boot", "vendor_kernel_boot", "odmko", "socko", "system_dlkm",
        "vendor_dlkm", "odm_dlkm"
    ])
    
    # File format support
    supported_formats: list = field(default_factory=lambda: [
        'zip', 'rar', '7z', 'tar', 'tar.gz', 'tgz', 'tar.md5',
        'ozip', 'ofp', 'ops', 'kdz', 'exe', 'dat', 'br', 'xz',
        'img', 'bin', 'pac', 'nb0', 'sin', 'chunk'
    ])
    
    # Git configuration
    git_config: Dict[str, Any] = field(default_factory=dict)
    
    # Telegram configuration
    telegram_config: Dict[str, Any] = field(default_factory=dict)
    
    # Tool configurations
    tools_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize derived paths."""
        self.input_dir = self.project_dir / "input"
        self.utils_dir = self.project_dir / "utils"
        self.output_dir = self.project_dir / "out"
        self.temp_dir = self.output_dir / "tmp"
        
        # Load configuration from files
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from config files."""
        config_file = self.project_dir / "dumprx_config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                if config_data:
                    self._update_from_dict(config_data)
        
        # Load token files
        self._load_tokens()
    
    def _load_tokens(self) -> None:
        """Load authentication tokens from files."""
        # GitHub token
        github_token_file = self.project_dir / ".github_token"
        if github_token_file.exists():
            self.git_config['github_token'] = github_token_file.read_text().strip()
        
        # GitLab token
        gitlab_token_file = self.project_dir / ".gitlab_token"
        if gitlab_token_file.exists():
            self.git_config['gitlab_token'] = gitlab_token_file.read_text().strip()
        
        # GitLab group
        gitlab_group_file = self.project_dir / ".gitlab_group"
        if gitlab_group_file.exists():
            self.git_config['gitlab_group'] = gitlab_group_file.read_text().strip()
        
        # Telegram token
        tg_token_file = self.project_dir / ".tg_token"
        if tg_token_file.exists():
            self.telegram_config['token'] = tg_token_file.read_text().strip()
        
        # Telegram chat
        tg_chat_file = self.project_dir / ".tg_chat"
        if tg_chat_file.exists():
            self.telegram_config['chat_id'] = tg_chat_file.read_text().strip()
        else:
            self.telegram_config['chat_id'] = "@DumprXDumps"  # Default channel
    
    def _update_from_dict(self, config_data: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in config_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def save_config(self, config_file: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if config_file is None:
            config_file = self.project_dir / "dumprx_config.yaml"
        
        config_data = {
            'external_tools': self.external_tools,
            'partitions': self.partitions,
            'supported_formats': self.supported_formats,
            'git_config': {k: v for k, v in self.git_config.items() if 'token' not in k},
            'telegram_config': {k: v for k, v in self.telegram_config.items() if 'token' not in k},
            'tools_config': self.tools_config,
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [self.input_dir, self.utils_dir, self.output_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_tool_path(self, tool_name: str) -> Optional[Path]:
        """Get the path to a specific tool."""
        tool_path = self.utils_dir / tool_name
        if tool_path.exists():
            return tool_path
        return None
    
    def has_github_token(self) -> bool:
        """Check if GitHub token is available."""
        return 'github_token' in self.git_config and self.git_config['github_token']
    
    def has_gitlab_token(self) -> bool:
        """Check if GitLab token is available."""
        return 'gitlab_token' in self.git_config and self.git_config['gitlab_token']
    
    def has_telegram_token(self) -> bool:
        """Check if Telegram token is available."""
        return 'token' in self.telegram_config and self.telegram_config['token']