import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._load_token_files()
    
    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_token_files(self):
        token_files = {
            '.github_token': ('git', 'github', 'token'),
            '.github_orgname': ('git', 'github', 'organization'),
            '.gitlab_token': ('git', 'gitlab', 'token'),
            '.gitlab_group': ('git', 'gitlab', 'group'),
            '.gitlab_instance': ('git', 'gitlab', 'instance'),
            '.tg_token': ('telegram', 'token'),
            '.tg_chat': ('telegram', 'chat_id')
        }
        
        for file_name, config_path in token_files.items():
            file_path = Path(file_name)
            if file_path.exists() and file_path.stat().st_size > 0:
                with open(file_path, 'r') as f:
                    value = f.read().strip()
                    self._set_nested_config(config_path, value)
    
    def _set_nested_config(self, path: tuple, value: str):
        config_ref = self.config
        for key in path[:-1]:
            config_ref = config_ref[key]
        config_ref[path[-1]] = value
    
    def get(self, *path) -> Any:
        config_ref = self.config
        for key in path:
            config_ref = config_ref[key]
        return config_ref
    
    def get_logging_config(self) -> Dict[str, Any]:
        return self.config['logging']
    
    def get_console_config(self) -> Dict[str, Any]:
        return self.config['console']
    
    def get_git_config(self, provider: str) -> Dict[str, Any]:
        return self.config['git'][provider]
    
    def get_telegram_config(self) -> Dict[str, Any]:
        return self.config['telegram']
    
    def get_download_config(self) -> Dict[str, Any]:
        return self.config['download']
    
    def get_advanced_config(self) -> Dict[str, Any]:
        return self.config['advanced']
    
    def is_telegram_enabled(self) -> bool:
        tg_config = self.get_telegram_config()
        return tg_config['enabled'] and bool(tg_config['token'])