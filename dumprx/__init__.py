"""
DumprX - Advanced Firmware Extraction Toolkit

A modular Python framework for extracting various firmware formats.
Originally based on Phoenix Firmware Dumper with comprehensive improvements.
"""

__version__ = "2.0.0"
__author__ = "DumprX Contributors"
__description__ = "Advanced Firmware Extraction Toolkit"

from .core.logger import Logger
from .core.config import Config

__all__ = ["Logger", "Config", "__version__"]