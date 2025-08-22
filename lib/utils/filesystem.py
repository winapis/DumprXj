import os
import sys
import shutil
from pathlib import Path
from typing import Optional, Union

def find_binary(name: str, paths: Optional[list] = None) -> Optional[str]:
    if paths:
        for path in paths:
            binary_path = Path(path) / name
            if binary_path.exists() and binary_path.is_file():
                return str(binary_path)
    
    return shutil.which(name)

def sanitize_filename(filename: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def ensure_dir(path: Union[str, Path]) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_size(path: Union[str, Path]) -> int:
    return Path(path).stat().st_size

def is_url(text: str) -> bool:
    return text.startswith(('http://', 'https://', 'ftp://'))

def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip('.')

def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"