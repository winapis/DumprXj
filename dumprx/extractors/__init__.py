"""
Base extractor class and extraction management.
"""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Any

from ..core.logger import Logger
from ..core.config import Config
from ..core.detector import FirmwareType
from ..utils import run_command, cleanup_temp_files

class ExtractionError(Exception):
    """Exception raised for extraction errors."""
    pass

class BaseExtractor(ABC):
    """Base class for firmware extractors."""
    
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.temp_dir = Path(config.get_temp_dir())
        self.output_dir = Path(config.get_output_dir())
    
    @abstractmethod
    def can_extract(self, firmware_type: FirmwareType) -> bool:
        """Check if this extractor can handle the firmware type."""
        pass
    
    @abstractmethod
    def extract(self, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract firmware and return list of extracted files."""
        pass
    
    def prepare_extraction(self, filename: str = None) -> Path:
        """Prepare extraction environment."""
        # Clean temp directory
        if self.temp_dir.exists():
            cleanup_temp_files(str(self.temp_dir))
        
        # Create directories
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Change to temp directory for extraction
        os.chdir(self.temp_dir)
        
        return self.temp_dir
    
    def copy_input_file(self, filepath: str, temp_dir: Path) -> Path:
        """Copy input file to temp directory."""
        src_path = Path(filepath)
        dst_path = temp_dir / src_path.name
        
        if src_path != dst_path:
            shutil.copy2(src_path, dst_path)
        
        return dst_path
    
    def cleanup(self):
        """Clean up temporary files after extraction."""
        try:
            os.chdir(self.config.project_dir)
        except Exception:
            pass

class ExtractionManager:
    """Manages firmware extraction process."""
    
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.extractors = []
        
        # Import and register extractors
        self._register_extractors()
    
    def _register_extractors(self):
        """Register all available extractors."""
        from .ozip_extractor import OzipExtractor
        from .ops_extractor import OpsExtractor
        from .ofp_extractor import OfpExtractor
        from .kdz_extractor import KdzExtractor
        from .payload_extractor import PayloadExtractor
        from .archive_extractor import ArchiveExtractor
        from .update_app_extractor import UpdateAppExtractor
        from .super_extractor import SuperExtractor
        
        self.extractors = [
            OzipExtractor(self.config, self.logger),
            OpsExtractor(self.config, self.logger),
            OfpExtractor(self.config, self.logger),
            KdzExtractor(self.config, self.logger),
            PayloadExtractor(self.config, self.logger),
            UpdateAppExtractor(self.config, self.logger),
            SuperExtractor(self.config, self.logger),
            ArchiveExtractor(self.config, self.logger),  # Should be last
        ]
    
    def extract_firmware(self, firmware_type: FirmwareType, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """
        Extract firmware using appropriate extractor.
        
        Args:
            firmware_type: Detected firmware type
            filepath: Path to firmware file
            metadata: Firmware metadata
            
        Returns:
            List of extracted files
            
        Raises:
            ExtractionError: If extraction fails
        """
        self.logger.info(f"Starting extraction", f"Type: {firmware_type.value}")
        
        # Find appropriate extractor
        for extractor in self.extractors:
            if extractor.can_extract(firmware_type):
                try:
                    self.logger.debug(f"Using extractor: {extractor.__class__.__name__}")
                    extracted_files = extractor.extract(filepath, metadata)
                    
                    if extracted_files:
                        self.logger.success(f"Extraction completed", f"Files: {len(extracted_files)}")
                        return extracted_files
                    else:
                        self.logger.warning("No files extracted")
                        
                except Exception as e:
                    self.logger.error(f"Extraction failed", f"Error: {str(e)}")
                    raise ExtractionError(f"Extraction failed with {extractor.__class__.__name__}: {str(e)}")
                finally:
                    extractor.cleanup()
        
        raise ExtractionError(f"No extractor available for firmware type: {firmware_type.value}")
    
    def get_supported_types(self) -> List[FirmwareType]:
        """Get list of supported firmware types."""
        supported_types = []
        for extractor in self.extractors:
            # This would need to be implemented in each extractor
            # For now, return common types
            pass
        
        return [
            FirmwareType.OZIP,
            FirmwareType.OPS, 
            FirmwareType.OFP,
            FirmwareType.KDZ,
            FirmwareType.PAYLOAD,
            FirmwareType.UPDATE_APP,
            FirmwareType.SUPER_IMG,
            FirmwareType.ZIP_ARCHIVE
        ]