from typing import Dict, Any, Optional
import yaml
import json
import os
from pathlib import Path


class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config_data: Dict[str, Any] = {}
        self.load()

    def _find_config_file(self) -> str:
        possible_paths = [
            "config.yaml",
            "config.yml", 
            "config.json",
            os.path.expanduser("~/.dumprx/config.yaml"),
            "/etc/dumprx/config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return "config.yaml"

    def load(self) -> None:
        if not os.path.exists(self.config_path):
            self.config_data = self._get_default_config()
            return

        try:
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.json'):
                    self.config_data = json.load(f)
                else:
                    self.config_data = yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config from {self.config_path}: {e}")

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.config_path) or '.', exist_ok=True)
        
        try:
            with open(self.config_path, 'w') as f:
                if self.config_path.endswith('.json'):
                    json.dump(self.config_data, f, indent=2)
                else:
                    yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save config to {self.config_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set(self, key: str, value: Any) -> None:
        keys = key.split('.')
        config = self.config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "logging": {
                "level": "INFO",
                "file": "",
                "max_size": "10MB",
                "backup_count": 5
            },
            "advanced": {
                "max_memory_file_size": 100,
                "max_workers": 4,
                "experimental": False
            },
            "git": {
                "github": {
                    "token": "",
                    "organization": ""
                },
                "gitlab": {
                    "token": "",
                    "group": "",
                    "instance": "gitlab.com"
                }
            },
            "telegram": {
                "token": "",
                "chat_id": "@DumprXDumps",
                "enabled": True
            },
            "download": {
                "user_agents": {
                    "default": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "mega": "MEGAsync/4.8.8.0"
                },
                "chunk_size": 8192,
                "timeout": 300,
                "retry_attempts": 3,
                "retry_delay": 5
            }
        }

    def load_tokens_from_files(self, project_dir: str) -> None:
        token_files = {
            'git.github.token': '.github_token',
            'git.github.organization': '.github_orgname', 
            'git.gitlab.token': '.gitlab_token',
            'git.gitlab.group': '.gitlab_group',
            'telegram.token': '.tg_token',
            'telegram.chat_id': '.tg_chat'
        }
        
        for config_key, filename in token_files.items():
            filepath = os.path.join(project_dir, filename)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                try:
                    with open(filepath, 'r') as f:
                        value = f.read().strip()
                        if value:
                            self.set(config_key, value)
                except Exception:
                    pass