import logging
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE + Style.BRIGHT
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


class DumprXLogger:
    def __init__(self, name: str = "dumprx"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self._handlers_added = False

    def setup(self, level: str = "INFO", log_file: Optional[str] = None, 
              max_size: str = "10MB", backup_count: int = 5) -> None:
        if self._handlers_added:
            return

        self.logger.handlers.clear()
        
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        console_format = ColoredFormatter(
            '%(levelname)s %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        if log_file:
            max_bytes = self._parse_size(max_size)
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setLevel(numeric_level)
            
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

        self._handlers_added = True

    def _parse_size(self, size_str: str) -> int:
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def critical(self, message: str) -> None:
        self.logger.critical(message)


_global_logger = DumprXLogger()

def get_logger() -> DumprXLogger:
    return _global_logger

def setup_logging(level: str = "INFO", log_file: Optional[str] = None,
                  max_size: str = "10MB", backup_count: int = 5) -> None:
    _global_logger.setup(level, log_file, max_size, backup_count)