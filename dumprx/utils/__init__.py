"""
Utility functions for DumprX.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

def run_command(cmd: List[str], cwd: Optional[str] = None, timeout: int = 300) -> subprocess.CompletedProcess:
    """
    Run a command with proper error handling.
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        timeout: Timeout in seconds
        
    Returns:
        CompletedProcess object
        
    Raises:
        subprocess.CalledProcessError: If command fails
        subprocess.TimeoutExpired: If command times out
    """
    return subprocess.run(
        cmd, 
        cwd=cwd, 
        capture_output=True, 
        text=True, 
        timeout=timeout,
        check=True
    )

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove problematic characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename

def get_file_size_human(size_bytes: int) -> str:
    """
    Convert bytes to human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human readable size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def ensure_executable(path: str) -> bool:
    """
    Ensure file is executable.
    
    Args:
        path: Path to file
        
    Returns:
        True if made executable, False if failed
    """
    try:
        file_path = Path(path)
        if file_path.exists():
            file_path.chmod(file_path.stat().st_mode | 0o755)
            return True
    except Exception:
        pass
    return False

def copy_with_progress(src: str, dst: str, callback=None):
    """
    Copy file with progress callback.
    
    Args:
        src: Source file path
        dst: Destination file path  
        callback: Progress callback function
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    # Create destination directory if needed
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    total_size = src_path.stat().st_size
    copied = 0
    
    with open(src_path, 'rb') as src_file, open(dst_path, 'wb') as dst_file:
        while True:
            chunk = src_file.read(8192)  # 8KB chunks
            if not chunk:
                break
            dst_file.write(chunk)
            copied += len(chunk)
            
            if callback:
                callback(copied, total_size)

def find_files_by_pattern(directory: str, pattern: str) -> List[str]:
    """
    Find files matching pattern in directory.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern
        
    Returns:
        List of matching file paths
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    
    return [str(f) for f in dir_path.glob(pattern) if f.is_file()]

def cleanup_temp_files(temp_dir: str):
    """
    Clean up temporary files and directories.
    
    Args:
        temp_dir: Temporary directory to clean
    """
    temp_path = Path(temp_dir)
    if temp_path.exists():
        try:
            shutil.rmtree(temp_path)
        except Exception:
            # Try to remove individual files if rmtree fails
            for item in temp_path.rglob("*"):
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        item.rmdir()
                except Exception:
                    continue

def is_tool_available(tool: str) -> bool:
    """
    Check if a command-line tool is available.
    
    Args:
        tool: Tool name/command
        
    Returns:
        True if tool is available, False otherwise
    """
    return shutil.which(tool) is not None

def get_terminal_size() -> tuple:
    """
    Get terminal size.
    
    Returns:
        Tuple of (columns, rows)
    """
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except Exception:
        return 80, 24  # Default size

def create_progress_bar(current: int, total: int, width: int = 30) -> str:
    """
    Create a text progress bar.
    
    Args:
        current: Current progress
        total: Total items
        width: Width of progress bar
        
    Returns:
        Progress bar string
    """
    if total == 0:
        percentage = 100
    else:
        percentage = int((current / total) * 100)
    
    filled_length = int(width * current // total) if total > 0 else width
    bar = "█" * filled_length + "░" * (width - filled_length)
    
    return f"[{bar}] {percentage}%"