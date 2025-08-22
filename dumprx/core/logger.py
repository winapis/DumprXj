import logging
import logging.handlers
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config_manager import ConfigManager

def setup_logging(config_manager: 'ConfigManager', verbose: bool = False):
    log_config = config_manager.get_logging_config()
    
    level = getattr(logging, log_config['level'])
    if verbose:
        level = logging.DEBUG
    
    formatter = logging.Formatter(log_config['format'])
    
    if log_config['file']:
        log_file = Path(log_config['file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        max_size = _parse_size(log_config['max_size'])
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=log_config['backup_count']
        )
    else:
        handler = logging.StreamHandler(sys.stdout)
    
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

def _parse_size(size_str: str) -> int:
    size_str = size_str.upper()
    if size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)