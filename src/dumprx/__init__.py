"""
DumprX - Advanced Android Firmware Extraction Toolkit
======================================================

A comprehensive Python toolkit for extracting and analyzing Android firmware images
from various manufacturers and formats.

Features:
- Multi-format firmware extraction (ZIP, RAR, 7Z, OTA, etc.)
- Manufacturer-specific decryption (Oppo, OnePlus, LG, HTC, etc.)
- Advanced partition detection and analysis
- Telegram bot integration for notifications
- GitHub/GitLab integration for automated dumps
- Modern ramdisk version support (v2, v3, v4)
- Modular and extensible architecture

Usage:
    from dumprx import DumprX
    
    dumper = DumprX()
    dumper.extract_firmware('/path/to/firmware.zip')
"""

__version__ = "2.0.0"
__author__ = "DumprX Contributors"
__license__ = "GPL-3.0"

from .core.dumper import DumprX
from .core.config import Config
from .core.logger import get_logger

__all__ = ["DumprX", "Config", "get_logger", "__version__"]