import logging
import sys
from typing import Optional
from pathlib import Path

class Logger:
    def __init__(self, name: str = "dumprx", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, emoji: str = "ℹ️") -> None:
        self.logger.info(f"{emoji} {message}")
    
    def success(self, message: str, emoji: str = "✅") -> None:
        self.logger.info(f"{emoji} {message}")
    
    def warning(self, message: str, emoji: str = "⚠️") -> None:
        self.logger.warning(f"{emoji} {message}")
    
    def error(self, message: str, emoji: str = "❌") -> None:
        self.logger.error(f"{emoji} {message}")
    
    def processing(self, message: str, emoji: str = "🔄") -> None:
        self.logger.info(f"{emoji} {message}")

logger = Logger()