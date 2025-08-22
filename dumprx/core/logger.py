"""
Modern logger with minimalist and attractive output formatting.
"""

import logging
import sys
from datetime import datetime
from typing import Optional
from enum import Enum

class LogLevel(Enum):
    """Log levels with colors and symbols."""
    DEBUG = ("🔍", "\033[0;37m", "DEBUG")     # Gray
    INFO = ("ℹ️", "\033[0;36m", "INFO")       # Cyan
    SUCCESS = ("✅", "\033[0;32m", "SUCCESS") # Green
    WARNING = ("⚠️", "\033[0;33m", "WARNING") # Yellow
    ERROR = ("❌", "\033[0;31m", "ERROR")     # Red
    CRITICAL = ("💥", "\033[0;35m", "CRITICAL") # Magenta

class Logger:
    """Minimalist logger with attractive formatting."""
    
    def __init__(self, name: str = "DumprX", level: str = "INFO"):
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self._reset = "\033[0m"
        self._bold = "\033[1m"
        self._dim = "\033[2m"
        
        # Configure logging
        logging.basicConfig(
            level=self.level,
            format="%(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(name)
    
    def _format_message(self, level: LogLevel, message: str, details: Optional[str] = None) -> str:
        """Format log message with colors and symbols."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Main message
        formatted = f"{level.value[1]}{level.value[0]} {self._bold}{message}{self._reset}"
        
        # Add details if provided
        if details:
            formatted += f" {self._dim}({details}){self._reset}"
        
        # Add timestamp for errors and critical
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            formatted += f" {self._dim}[{timestamp}]{self._reset}"
        
        return formatted
    
    def debug(self, message: str, details: Optional[str] = None):
        """Log debug message."""
        if self.level <= logging.DEBUG:
            print(self._format_message(LogLevel.DEBUG, message, details))
    
    def info(self, message: str, details: Optional[str] = None):
        """Log info message."""
        print(self._format_message(LogLevel.INFO, message, details))
    
    def success(self, message: str, details: Optional[str] = None):
        """Log success message."""
        print(self._format_message(LogLevel.SUCCESS, message, details))
    
    def warning(self, message: str, details: Optional[str] = None):
        """Log warning message."""
        print(self._format_message(LogLevel.WARNING, message, details))
    
    def error(self, message: str, details: Optional[str] = None):
        """Log error message."""
        print(self._format_message(LogLevel.ERROR, message, details))
    
    def critical(self, message: str, details: Optional[str] = None):
        """Log critical message."""
        print(self._format_message(LogLevel.CRITICAL, message, details))
    
    def banner(self, text: str):
        """Display attractive banner."""
        lines = text.strip().split('\n')
        max_length = max(len(line) for line in lines)
        
        print(f"\n{self._bold}\033[0;32m" + "═" * (max_length + 4) + f"{self._reset}")
        for line in lines:
            padding = max_length - len(line)
            print(f"{self._bold}\033[0;32m║ {line}{' ' * padding} ║{self._reset}")
        print(f"{self._bold}\033[0;32m" + "═" * (max_length + 4) + f"{self._reset}\n")
    
    def progress(self, message: str, current: int, total: int):
        """Display progress bar."""
        if total == 0:
            percentage = 100
        else:
            percentage = int((current / total) * 100)
        
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else bar_length
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        print(f"\r\033[0;36m⏳ {message}: [{bar}] {percentage}%{self._reset}", end="", flush=True)
        
        if current >= total:
            print()  # New line when complete
    
    def step(self, step_num: int, total_steps: int, message: str):
        """Display step progress."""
        print(f"\033[0;34m📋 Step {step_num}/{total_steps}: {self._bold}{message}{self._reset}")