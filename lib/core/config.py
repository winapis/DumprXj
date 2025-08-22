from typing import Dict, Any
import yaml
import os
from pathlib import Path

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        self._apply_defaults()
    
    def _apply_defaults(self) -> None:
        if not self._config.get('paths', {}).get('project_dir'):
            self._config.setdefault('paths', {})['project_dir'] = str(Path.cwd())
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
    
    def save(self) -> None:
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

config = Config()