"""
Logging configuration for DumprX.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


class DumprXLogger:
    """Custom logger for DumprX with rich formatting."""
    
    def __init__(self, name: str = "dumprx", level: int = logging.INFO):
        self.name = name
        self.level = level
        self.console = Console()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with rich handler."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Rich handler for console output
        rich_handler = RichHandler(
            console=self.console,
            show_path=False,
            show_time=True,
            rich_tracebacks=True
        )
        rich_handler.setLevel(self.level)
        
        # Formatter
        formatter = logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
        rich_handler.setFormatter(formatter)
        
        logger.addHandler(rich_handler)
        return logger
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(f"❌ {message}", **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(f"⚠️  {message}", **kwargs)
    
    def success(self, message: str, **kwargs) -> None:
        """Log success message."""
        self.logger.info(f"✅ {message}", **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def banner(self, title: str) -> None:
        """Display a banner."""
        self.console.print(f"\n[bold green]{title}[/bold green]")
        self.console.print("=" * len(title), style="green")
    
    def section(self, title: str) -> None:
        """Display a section header."""
        self.console.print(f"\n[bold blue]→ {title}[/bold blue]")
    
    def progress(self, description: str) -> Progress:
        """Create a progress bar."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=self.console
        )


# Global logger instance
_logger: Optional[DumprXLogger] = None


def get_logger(name: str = "dumprx", level: int = logging.INFO) -> DumprXLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = DumprXLogger(name, level)
    return _logger


def setup_file_logging(log_file: Path, level: int = logging.DEBUG) -> None:
    """Set up file logging in addition to console logging."""
    logger = get_logger().logger
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # File formatter
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(file_handler)