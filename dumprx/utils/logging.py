import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )
    
    return logging.getLogger("dumprx")


def log_error(message: str):
    logging.error(message)


def log_warning(message: str):
    logging.warning(message)


def log_info(message: str):
    logging.info(message)


def log_debug(message: str):
    logging.debug(message)