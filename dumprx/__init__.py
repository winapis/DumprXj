"""
DumprX - Advanced firmware dumper and extractor toolkit
"""

__version__ = "2.0.0"
__author__ = "DumprX Team"
__description__ = "Advanced firmware dumper and extractor toolkit"

from dumprx.core.config import Config
from dumprx.core.dumper import FirmwareDumper

__all__ = ["Config", "FirmwareDumper"]
