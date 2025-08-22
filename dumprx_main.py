#!/usr/bin/env python3
"""
DumprX - Advanced Firmware Extraction Toolkit

Main executable script for the refactored Python version.
"""

import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from dumprx.cli import main

if __name__ == "__main__":
    main()