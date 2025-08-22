#!/usr/bin/env python3

import yaml
import os
from pathlib import Path
from typing import Dict, Any

from dumprx import PROJECT_DIR, CONFIG_FILE


class Config:
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or CONFIG_FILE
        self.data = {}
        self.load()
    
    def load(self):
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.data = yaml.safe_load(f) or {}
        
        self._load_token_files()
    
    def _load_token_files(self):
        token_files = {
            '.github_token': ['git', 'github', 'token'],
            '.github_orgname': ['git', 'github', 'organization'],
            '.gitlab_token': ['git', 'gitlab', 'token'],
            '.gitlab_group': ['git', 'gitlab', 'group'],
            '.gitlab_instance': ['git', 'gitlab', 'instance'],
            '.tg_token': ['telegram', 'token'],
            '.tg_chat': ['telegram', 'chat_id']
        }
        
        for filename, path_keys in token_files.items():
            file_path = PROJECT_DIR / filename
            if file_path.exists() and file_path.stat().st_size > 0:
                with open(file_path, 'r') as f:
                    value = f.read().strip()
                    if value:
                        self._set_nested_value(path_keys, value)
    
    def _set_nested_value(self, keys, value):
        current = self.data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def get(self, *keys, default=None):
        current = self.data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def set(self, *keys, value):
        current = self.data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def save(self):
        with open(self.config_path, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False, sort_keys=False)


config = Config()