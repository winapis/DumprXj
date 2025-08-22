#!/usr/bin/env python3

import os
import sys
import logging
from pathlib import Path

__version__ = "2.0.0"
__author__ = "DumprX Team"

PROJECT_DIR = Path(__file__).parent.parent.absolute()
CONFIG_FILE = PROJECT_DIR / "config.yaml"
UTILS_DIR = PROJECT_DIR / "utils"