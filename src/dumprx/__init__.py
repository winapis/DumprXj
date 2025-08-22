"""
DumprX - Advanced Firmware Extraction Toolkit
==============================================

A comprehensive Python-based firmware extraction toolkit supporting 12+ manufacturers
with intelligent auto-detection and specialized extraction methods.

Features:
- Multi-manufacturer support (Samsung, Xiaomi, OPPO, Huawei, LG, HTC, Sony, etc.)
- Enhanced boot image analysis with multi-boot support
- Advanced download services with resume capability
- Telegram bot integration with queue management
- Beautiful CLI interface with progress tracking
- Modular architecture for extensibility
"""

__version__ = "2.0.0"
__author__ = "DumprX Team"
__license__ = "GPL-3.0"

from .core.dumper import DumprX
from .core.config import Config, config
from .core.logger import Logger, logger

__all__ = ["DumprX", "Config", "config", "Logger", "logger"]