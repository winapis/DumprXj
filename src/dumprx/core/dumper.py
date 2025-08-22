"""
Core dumper functionality - Main extraction engine
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import tempfile
import magic
import hashlib
from urllib.parse import urlparse

from .config import config
from .logger import logger
from ..manufacturers import ManufacturerDetector
from ..downloaders import DownloadManager
from ..boot import BootImageAnalyzer
from ..utils.file_utils import FileUtils
from ..utils.archive_utils import ArchiveUtils


class DumprX:
    """Main firmware extraction engine"""
    
    def __init__(self, input_path: Union[str, Path], output_dir: Optional[Path] = None):
        self.input_path = Path(input_path) if isinstance(input_path, str) else input_path
        self.output_dir = output_dir or config.output_dir
        self.tmp_dir = config.tmp_dir
        
        # Initialize components
        self.manufacturer_detector = ManufacturerDetector()
        self.download_manager = DownloadManager()
        self.boot_analyzer = BootImageAnalyzer()
        self.file_utils = FileUtils()
        self.archive_utils = ArchiveUtils()
        
        # Extraction state
        self.current_file: Optional[Path] = None
        self.detected_manufacturer: Optional[str] = None
        self.detected_format: Optional[str] = None
        self.extracted_files: List[Path] = []
        
        # Clean and create working directories
        self._setup_directories()
    
    def _setup_directories(self):
        """Setup working directories"""
        # Clean tmp directory
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        
        # Create directories
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract(self) -> bool:
        """Main extraction method"""
        try:
            logger.banner()
            logger.info("🚀 Starting firmware extraction...")
            
            # Step 1: Handle input (download or copy)
            if not self._prepare_input():
                return False
            
            # Step 2: Detect manufacturer and format
            if not self._detect_format():
                return False
            
            # Step 3: Extract firmware
            if not self._extract_firmware():
                return False
                
            # Step 4: Analyze extracted files
            self._analyze_extracted_files()
            
            # Step 5: Generate summary
            self._generate_summary()
            
            logger.success("✨ Extraction completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return False
        finally:
            self._cleanup()
    
    def _prepare_input(self) -> bool:
        """Prepare input file (download or copy)"""
        logger.section("📥 Preparing Input", "📥")
        
        input_str = str(self.input_path)
        
        # Check if input is a URL
        if input_str.startswith(('http://', 'https://', 'ftp://')):
            logger.info(f"🌐 Downloading from URL: {input_str}")
            
            downloaded_file = self.download_manager.download(input_str, self.tmp_dir)
            if not downloaded_file:
                logger.error("Failed to download file")
                return False
                
            self.current_file = downloaded_file
            logger.success(f"Downloaded: {downloaded_file.name}")
            
        elif self.input_path.is_file():
            # Copy local file to tmp directory
            logger.info(f"📁 Processing local file: {self.input_path.name}")
            self.current_file = self.tmp_dir / self.input_path.name
            shutil.copy2(self.input_path, self.current_file)
            logger.success(f"Copied: {self.current_file.name}")
            
        elif self.input_path.is_dir():
            # Handle directory input
            logger.info(f"📂 Processing directory: {self.input_path}")
            self.current_file = self.input_path
            logger.success("Directory ready for processing")
            
        else:
            logger.error(f"Input not found: {self.input_path}")
            return False
        
        return True
    
    def _detect_format(self) -> bool:
        """Detect manufacturer and firmware format"""
        logger.section("🔍 Detecting Format", "🔍")
        
        if not self.current_file:
            logger.error("No input file to analyze")
            return False
        
        # Detect manufacturer and format
        manufacturer, format_type = self.manufacturer_detector.detect(self.current_file)
        
        if not manufacturer:
            logger.warning("Could not detect manufacturer, proceeding with generic extraction")
            manufacturer = "Generic"
            format_type = "Unknown"
        
        self.detected_manufacturer = manufacturer
        self.detected_format = format_type
        
        logger.manufacturer_detected(manufacturer, format_type)
        return True
    
    def _extract_firmware(self) -> bool:
        """Extract firmware based on detected format"""
        logger.section("📦 Extracting Firmware", "📦")
        
        if not self.detected_manufacturer or not self.current_file:
            return False
        
        # Get manufacturer-specific extractor
        extractor = self.manufacturer_detector.get_extractor(self.detected_manufacturer)
        
        if extractor:
            logger.info(f"Using {self.detected_manufacturer} extractor...")
            success = extractor.extract(self.current_file, self.tmp_dir)
            
            if not success:
                logger.warning(f"{self.detected_manufacturer} extractor failed, trying generic...")
                success = self._generic_extraction()
        else:
            logger.info("Using generic extraction...")
            success = self._generic_extraction()
        
        if success:
            self._collect_extracted_files()
            logger.success(f"Extracted {len(self.extracted_files)} files")
            return True
        else:
            logger.error("Extraction failed")
            return False
    
    def _generic_extraction(self) -> bool:
        """Generic extraction using archive utilities"""
        try:
            return self.archive_utils.extract(self.current_file, self.tmp_dir)
        except Exception as e:
            logger.error(f"Generic extraction failed: {str(e)}")
            return False
    
    def _collect_extracted_files(self):
        """Collect all extracted files"""
        self.extracted_files = []
        
        for file_path in self.tmp_dir.rglob("*"):
            if file_path.is_file():
                self.extracted_files.append(file_path)
        
        # Sort by size (largest first)
        self.extracted_files.sort(key=lambda x: x.stat().st_size, reverse=True)
    
    def _analyze_extracted_files(self):
        """Analyze extracted files for additional processing"""
        logger.section("🔬 Analyzing Files", "🔬")
        
        # Look for boot images
        boot_images = [f for f in self.extracted_files if 'boot' in f.name.lower()]
        if boot_images:
            logger.info(f"🥾 Found {len(boot_images)} boot images")
            for boot_img in boot_images:
                self.boot_analyzer.analyze(boot_img)
        
        # Look for system images that need additional extraction
        system_images = [f for f in self.extracted_files 
                        if any(part in f.name.lower() for part in ['system', 'vendor', 'product'])]
        
        if system_images:
            logger.info(f"💽 Found {len(system_images)} partition images")
            self._process_partition_images(system_images)
    
    def _process_partition_images(self, images: List[Path]):
        """Process partition images (convert sparse, extract if needed)"""
        for img in images:
            try:
                # Check if it's a sparse image
                if self.file_utils.is_sparse_image(img):
                    logger.info(f"Converting sparse image: {img.name}")
                    converted = self.file_utils.convert_sparse_image(img)
                    if converted:
                        self.extracted_files.append(converted)
                
                # Check if it's an Android sparse image
                elif self.file_utils.is_android_sparse(img):
                    logger.info(f"Converting Android sparse image: {img.name}")
                    converted = self.file_utils.convert_android_sparse(img)
                    if converted:
                        self.extracted_files.append(converted)
                        
            except Exception as e:
                logger.debug(f"Failed to process {img.name}: {str(e)}")
    
    def _generate_summary(self):
        """Generate extraction summary"""
        total_size = sum(f.stat().st_size for f in self.extracted_files)
        total_size_str = self.file_utils.format_size(total_size)
        
        # Move important files to output directory
        important_files = []
        for file_path in self.extracted_files:
            if any(part in file_path.name.lower() for part in config.partitions):
                dest_path = self.output_dir / file_path.name
                shutil.copy2(file_path, dest_path)
                important_files.append(dest_path)
        
        logger.extraction_summary([f.name for f in important_files], total_size_str)
        
        # Generate board-info.txt
        self._generate_board_info()
    
    def _generate_board_info(self):
        """Generate board-info.txt file"""
        board_info_path = self.output_dir / "board-info.txt"
        
        try:
            with open(board_info_path, 'w') as f:
                f.write("# DumprX v2.0 - Board Information\n")
                f.write(f"# Generated from: {self.input_path}\n")
                f.write(f"# Detected manufacturer: {self.detected_manufacturer}\n")
                f.write(f"# Detected format: {self.detected_format}\n")
                f.write(f"# Extracted files: {len(self.extracted_files)}\n")
                f.write("\n")
                
                # Add partition information
                f.write("# Partition Images Found:\n")
                for file_path in self.extracted_files:
                    if file_path.suffix.lower() == '.img':
                        size = self.file_utils.format_size(file_path.stat().st_size)
                        f.write(f"{file_path.name} ({size})\n")
                        
            logger.success(f"Generated board-info.txt")
            
        except Exception as e:
            logger.warning(f"Failed to generate board-info.txt: {str(e)}")
    
    def _cleanup(self):
        """Cleanup temporary files"""
        try:
            # Keep tmp directory for debugging but clean sensitive files
            sensitive_patterns = ['*.token', '*.key', '*.pem']
            for pattern in sensitive_patterns:
                for file_path in self.tmp_dir.glob(pattern):
                    file_path.unlink(missing_ok=True)
                    
        except Exception as e:
            logger.debug(f"Cleanup error: {str(e)}")


# Factory function for easy use
def extract_firmware(input_path: Union[str, Path], 
                    output_dir: Optional[Path] = None) -> bool:
    """
    Convenience function to extract firmware
    
    Args:
        input_path: Path to firmware file/folder or URL
        output_dir: Output directory (optional)
        
    Returns:
        bool: True if extraction successful
    """
    dumper = DumprX(input_path, output_dir)
    return dumper.extract()