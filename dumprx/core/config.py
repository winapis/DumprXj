"""
Configuration management for DumprX
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DirectoryConfig:
    """Directory configuration"""
    input: str = "input"
    output: str = "out"
    utils: str = "utils"
    temp: str = "out/tmp"


@dataclass
class GitHubConfig:
    """GitHub configuration"""
    token: str = ""
    organization: str = ""


@dataclass
class GitLabConfig:
    """GitLab configuration"""
    token: str = ""
    group: str = ""
    instance: str = "gitlab.com"


@dataclass
class GitConfig:
    """Git configuration"""
    github: GitHubConfig = field(default_factory=GitHubConfig)
    gitlab: GitLabConfig = field(default_factory=GitLabConfig)


@dataclass
class TelegramConfig:
    """Telegram configuration"""
    token: str = ""
    chat_id: str = "@DumprXDumps"
    enabled: bool = True


@dataclass
class DownloadConfig:
    """Download configuration"""
    user_agents: Dict[str, str] = field(default_factory=lambda: {
        "default": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "mega": "MEGAsync/4.8.8.0"
    })
    chunk_size: int = 8192
    timeout: int = 300
    retry_attempts: int = 3
    retry_delay: int = 5


@dataclass
class ExtractionConfig:
    """Extraction configuration"""
    supported_formats: Dict[str, list] = field(default_factory=lambda: {
        "archives": [".zip", ".rar", ".7z", ".tar", ".tar.gz", ".tgz", ".tar.md5"],
        "firmware": [".ozip", ".ofp", ".ops", ".kdz", ".nb0", ".pac"],
        "images": [".img", ".bin", ".sin"],
        "executables": ["ruu_*.exe"]
    })
    partitions: list = field(default_factory=lambda: [
        "system", "vendor", "product", "system_ext", "odm", 
        "boot", "recovery", "vbmeta", "dtbo"
    ])
    ramdisk_formats: list = field(default_factory=lambda: [
        "gzip", "lz4", "lzma", "xz", "lzop", "bzip2"
    ])


@dataclass
class ExternalToolsConfig:
    """External tools configuration"""
    repositories: list = field(default_factory=lambda: [
        "bkerler/oppo_ozip_decrypt",
        "bkerler/oppo_decrypt",
        "marin-m/vmlinux-to-elf",
        "ShivamKumarJha/android_tools",
        "HemanthJabalpuri/pacextractor"
    ])


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = ""
    max_size: str = "10MB"
    backup_count: int = 5


@dataclass
class ConsoleConfig:
    """Console configuration"""
    colors: bool = True
    progress_bars: bool = True
    banner: bool = True
    emoji: bool = True


@dataclass
class AdvancedConfig:
    """Advanced configuration"""
    max_memory_file_size: int = 100
    max_workers: int = 4
    experimental: bool = False


class Config:
    """Main configuration class for DumprX"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.project_dir = Path(__file__).parent.parent.parent.absolute()
        self.config_path = config_path or self.project_dir / "config.yaml"
        
        # Initialize with defaults
        self.directories = DirectoryConfig()
        self.git = GitConfig()
        self.telegram = TelegramConfig()
        self.download = DownloadConfig()
        self.extraction = ExtractionConfig()
        self.external_tools = ExternalToolsConfig()
        self.logging = LoggingConfig()
        self.console = ConsoleConfig()
        self.advanced = AdvancedConfig()
        
        # Load configuration
        self.load_config()
        self.load_token_files()
        
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            self.create_default_config()
            return
            
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
                
            # Update configurations with loaded data
            if 'directories' in config_data:
                self._update_dataclass(self.directories, config_data['directories'])
            if 'git' in config_data:
                if 'github' in config_data['git']:
                    self._update_dataclass(self.git.github, config_data['git']['github'])
                if 'gitlab' in config_data['git']:
                    self._update_dataclass(self.git.gitlab, config_data['git']['gitlab'])
            if 'telegram' in config_data:
                self._update_dataclass(self.telegram, config_data['telegram'])
            if 'download' in config_data:
                self._update_dataclass(self.download, config_data['download'])
            if 'extraction' in config_data:
                self._update_dataclass(self.extraction, config_data['extraction'])
            if 'external_tools' in config_data:
                self._update_dataclass(self.external_tools, config_data['external_tools'])
            if 'logging' in config_data:
                self._update_dataclass(self.logging, config_data['logging'])
            if 'console' in config_data:
                self._update_dataclass(self.console, config_data['console'])
            if 'advanced' in config_data:
                self._update_dataclass(self.advanced, config_data['advanced'])
                
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_path}: {e}")
            print("Using default configuration.")
            
    def load_token_files(self) -> None:
        """Load tokens from files (for backward compatibility)"""
        token_files = {
            '.github_token': lambda x: setattr(self.git.github, 'token', x),
            '.github_orgname': lambda x: setattr(self.git.github, 'organization', x),
            '.gitlab_token': lambda x: setattr(self.git.gitlab, 'token', x),
            '.gitlab_group': lambda x: setattr(self.git.gitlab, 'group', x),
            '.gitlab_instance': lambda x: setattr(self.git.gitlab, 'instance', x),
            '.tg_token': lambda x: setattr(self.telegram, 'token', x),
            '.tg_chat': lambda x: setattr(self.telegram, 'chat_id', x),
        }
        
        for filename, setter in token_files.items():
            file_path = self.project_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read().strip()
                        if content:
                            setter(content)
                except Exception as e:
                    print(f"Warning: Could not read {filename}: {e}")
                    
    def create_default_config(self) -> None:
        """Create default configuration file"""
        try:
            # Copy the existing config.yaml if it exists, otherwise create a basic one
            if not self.config_path.exists():
                default_config = {
                    'directories': {
                        'input': 'input',
                        'output': 'out', 
                        'utils': 'utils',
                        'temp': 'out/tmp'
                    },
                    'git': {
                        'github': {'token': '', 'organization': ''},
                        'gitlab': {'token': '', 'group': '', 'instance': 'gitlab.com'}
                    },
                    'telegram': {
                        'token': '',
                        'chat_id': '@DumprXDumps',
                        'enabled': True
                    }
                }
                
                with open(self.config_path, 'w') as f:
                    yaml.dump(default_config, f, default_flow_style=False, indent=2)
                    
        except Exception as e:
            print(f"Warning: Could not create default config: {e}")
            
    def _update_dataclass(self, obj: Any, data: Dict[str, Any]) -> None:
        """Update dataclass fields with dictionary data"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
                
    def get_absolute_path(self, relative_path: str) -> Path:
        """Convert relative path to absolute path based on project directory"""
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return self.project_dir / relative_path
        
    def get_input_dir(self) -> Path:
        """Get absolute input directory path"""
        return self.get_absolute_path(self.directories.input)
        
    def get_output_dir(self) -> Path:
        """Get absolute output directory path"""
        return self.get_absolute_path(self.directories.output)
        
    def get_utils_dir(self) -> Path:
        """Get absolute utils directory path"""
        return self.get_absolute_path(self.directories.utils)
        
    def get_temp_dir(self) -> Path:
        """Get absolute temp directory path"""
        return self.get_absolute_path(self.directories.temp)
        
    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        for dir_path in [self.get_input_dir(), self.get_output_dir(), 
                        self.get_utils_dir(), self.get_temp_dir()]:
            dir_path.mkdir(parents=True, exist_ok=True)