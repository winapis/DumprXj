"""
Enhanced logging system for DumprX with colorized output and emojis
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Any
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
import colorama
from colorama import Fore, Style

# Initialize colorama for Windows compatibility
colorama.init(autoreset=True)


class EmojiFormatter(logging.Formatter):
    """Custom formatter that adds emojis and colors to log messages"""
    
    LEVEL_EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️", 
        logging.ERROR: "❌",
        logging.CRITICAL: "💥"
    }
    
    LEVEL_COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA
    }
    
    def format(self, record):
        emoji = self.LEVEL_EMOJIS.get(record.levelno, "")
        color = self.LEVEL_COLORS.get(record.levelno, "")
        
        # Add emoji and color to the message
        record.msg = f"{emoji} {record.msg}"
        
        formatted = super().format(record)
        return f"{color}{formatted}{Style.RESET_ALL}"


class Logger:
    """Enhanced logger with rich formatting and progress tracking"""
    
    def __init__(self, name: str = "dumprx", level: int = logging.INFO, 
                 log_file: Optional[Path] = None):
        self.console = Console()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with rich formatting
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            markup=True
        )
        console_handler.setLevel(level)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        self.progress: Optional[Progress] = None
    
    def banner(self, title: str = "DumprX"):
        """Display the main banner"""
        banner_text = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
        """
        
        panel = Panel(
            Text(banner_text, style="bold green"),
            title=f"[bold blue]{title} v2.0[/bold blue]",
            subtitle="[italic]Advanced Firmware Extraction Toolkit[/italic]",
            border_style="green"
        )
        self.console.print(panel)
    
    def section(self, title: str, emoji: str = "📋"):
        """Display a section header"""
        self.console.print(f"\n{emoji} [bold blue]{title}[/bold blue]")
        self.console.print("─" * 50)
    
    def success(self, message: str):
        """Log success message with green color and checkmark"""
        self.console.print(f"✅ [bold green]{message}[/bold green]")
    
    def error(self, message: str):
        """Log error message with red color and X mark"""
        self.console.print(f"❌ [bold red]{message}[/bold red]")
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message with yellow color and warning emoji"""
        self.console.print(f"⚠️ [bold yellow]{message}[/bold yellow]")
        self.logger.warning(message)
    
    def info(self, message: str, emoji: str = "ℹ️"):
        """Log info message with emoji"""
        self.console.print(f"{emoji} {message}")
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def progress_start(self, description: str = "Processing...") -> Any:
        """Start a progress bar"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
        self.progress.start()
        return self.progress.add_task(description, total=100)
    
    def progress_update(self, task_id: Any, completed: int, description: str = None):
        """Update progress bar"""
        if self.progress:
            self.progress.update(task_id, completed=completed, description=description)
    
    def progress_stop(self):
        """Stop progress bar"""
        if self.progress:
            self.progress.stop()
            self.progress = None
    
    def manufacturer_detected(self, manufacturer: str, format_type: str):
        """Log manufacturer detection with special formatting"""
        emoji_map = {
            "Samsung": "📱",
            "Xiaomi": "🔥", 
            "OPPO": "💎",
            "OnePlus": "⚡",
            "Huawei": "🌸",
            "LG": "📺",
            "HTC": "📲",
            "Sony": "🎮",
            "Nokia": "📞",
            "Motorola": "📻"
        }
        
        emoji = emoji_map.get(manufacturer, "📱")
        self.console.print(f"\n{emoji} [bold cyan]Manufacturer Detected:[/bold cyan] [bold white]{manufacturer}[/bold white]")
        self.console.print(f"📦 [bold cyan]Format:[/bold cyan] [bold white]{format_type}[/bold white]")
    
    def extraction_summary(self, extracted_files: list, total_size: str):
        """Display extraction summary"""
        self.console.print("\n🎉 [bold green]Extraction Complete![/bold green]")
        self.console.print(f"📁 [bold]Files extracted:[/bold] {len(extracted_files)}")
        self.console.print(f"💾 [bold]Total size:[/bold] {total_size}")
        
        if extracted_files:
            self.console.print("\n📋 [bold]Extracted files:[/bold]")
            for file in extracted_files[:10]:  # Show first 10 files
                self.console.print(f"  • {file}")
            if len(extracted_files) > 10:
                self.console.print(f"  ... and {len(extracted_files) - 10} more files")


# Global logger instance
logger = Logger()