#!/usr/bin/env python3

import logging
import logging.handlers
import sys
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from dumprx.config import config


console = Console()

def setup_logging():
    log_level = getattr(logging, config.get('logging', 'level', default='INFO').upper())
    log_file = config.get('logging', 'file')
    max_size = config.get('logging', 'max_size', default='10MB')
    backup_count = config.get('logging', 'backup_count', default=5)
    
    size_bytes = _parse_size(max_size)
    
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=size_bytes, backupCount=backup_count
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        handler = RichHandler(console=console, rich_tracebacks=True)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)


def _parse_size(size_str):
    units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
    size_str = size_str.upper()
    
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            return int(size_str[:-len(unit)]) * multiplier
    
    return int(size_str)


def print_banner():
    banner = """
    ██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
    ██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
    ██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
    ██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
    ██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
    ╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
    """
    console.print(Text(banner, style="bold green"))
    console.print(Text("🚀 Advanced Firmware Dumping Tool", style="bold cyan"))
    console.print()


def success(message: str):
    console.print(f"✅ {message}", style="bold green")


def info(message: str):
    console.print(f"ℹ️  {message}", style="cyan")


def warning(message: str):
    console.print(f"⚠️  {message}", style="yellow")


def error(message: str):
    console.print(f"❌ {message}", style="bold red")


def step(message: str):
    console.print(f"▶️  {message}", style="bold blue")


def create_progress():
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    )