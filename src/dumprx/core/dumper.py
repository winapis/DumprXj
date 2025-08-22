"""
Main DumprX class - Core firmware extraction functionality.
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio

from ..core.config import Config
from ..core.logger import get_logger
from ..modules.detector import FileDetector
from ..modules.downloader import Downloader
from ..modules.extractor import Extractor
from ..modules.partition import PartitionManager
from ..modules.vendor import VendorManager
from ..modules.git_manager import GitManager
from ..modules.telegram_bot import TelegramManager


class DumprX:
    """
    Main DumprX class for firmware extraction and analysis.
    
    This class orchestrates all the different modules to provide a unified
    interface for firmware extraction, analysis, and processing.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize DumprX with configuration."""
        self.config = config or Config()
        self.logger = get_logger()
        
        # Initialize modules
        self.detector = FileDetector(self.config)
        self.downloader = Downloader(self.config)
        self.extractor = Extractor(self.config)
        self.partition_manager = PartitionManager(self.config)
        self.vendor_manager = VendorManager(self.config)
        self.git_manager = GitManager(self.config)
        self.telegram_manager = TelegramManager(self.config)
        
        # Ensure directories exist
        self.config.ensure_directories()
    
    def extract_firmware(
        self, 
        input_path: str, 
        output_dir: Optional[str] = None,
        upload_to_git: bool = True,
        send_telegram: bool = True
    ) -> Dict[str, Any]:
        """
        Extract firmware from the given input path.
        
        Args:
            input_path: Path to firmware file/folder or URL
            output_dir: Optional custom output directory
            upload_to_git: Whether to upload results to Git
            send_telegram: Whether to send Telegram notifications
            
        Returns:
            Dictionary with extraction results and metadata
        """
        self.logger.banner("🚀 DumprX Firmware Extraction Started")
        
        try:
            # Set custom output directory if provided
            if output_dir:
                self.config.output_dir = Path(output_dir)
                self.config.temp_dir = self.config.output_dir / "tmp"
                self.config.ensure_directories()
            
            # Clean and prepare workspace
            self._prepare_workspace()
            
            # Detect input type and handle accordingly
            input_info = self.detector.detect_input(input_path)
            self.logger.info(f"📁 Detected input type: {input_info['type']}")
            
            # Handle URL downloads
            if input_info['type'] == 'url':
                self.logger.section("⬇️  Downloading firmware")
                downloaded_path = asyncio.run(
                    self.downloader.download(input_path, self.config.input_dir)
                )
                input_path = str(downloaded_path)
                input_info = self.detector.detect_input(input_path)
            
            # Validate and process the input
            if not self.detector.is_supported_format(input_info):
                raise ValueError(f"Unsupported format: {input_info.get('format', 'unknown')}")
            
            # Extract the firmware
            self.logger.section("📦 Extracting firmware")
            extraction_result = self.extractor.extract(input_path, self.config.temp_dir)
            
            # Analyze partitions
            self.logger.section("🔍 Analyzing partitions")
            partition_info = self.partition_manager.analyze_partitions(self.config.temp_dir)
            
            # Apply vendor-specific processing
            self.logger.section("🏭 Applying vendor-specific processing")
            vendor_info = self.vendor_manager.process_vendor_specific(
                self.config.temp_dir, 
                input_info
            )
            
            # Organize output
            self.logger.section("📋 Organizing extracted files")
            organized_files = self._organize_output(extraction_result, partition_info)
            
            # Prepare result metadata
            result = {
                'input_info': input_info,
                'extraction_result': extraction_result,
                'partition_info': partition_info,
                'vendor_info': vendor_info,
                'organized_files': organized_files,
                'output_dir': str(self.config.output_dir),
                'extraction_date': datetime.now().isoformat(),
                'success': True
            }
            
            # Upload to Git if requested and configured
            if upload_to_git and (self.config.has_github_token() or self.config.has_gitlab_token()):
                self.logger.section("📤 Uploading to Git repository")
                git_result = self.git_manager.upload_firmware_dump(result)
                result['git_upload'] = git_result
            
            # Send Telegram notification if requested and configured
            if send_telegram and self.config.has_telegram_token():
                self.logger.section("📱 Sending Telegram notification")
                telegram_result = asyncio.run(
                    self.telegram_manager.send_notification(result)
                )
                result['telegram_notification'] = telegram_result
            
            self.logger.success("🎉 Firmware extraction completed successfully!")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Extraction failed: {str(e)}")
            raise
        finally:
            # Cleanup if needed
            self._cleanup_workspace()
    
    def _prepare_workspace(self) -> None:
        """Prepare the workspace for extraction."""
        # Clean temp directory
        if self.config.temp_dir.exists():
            shutil.rmtree(self.config.temp_dir)
        
        # Ensure all directories exist
        self.config.ensure_directories()
        
        self.logger.debug(f"Workspace prepared at: {self.config.output_dir}")
    
    def _organize_output(
        self, 
        extraction_result: Dict[str, Any], 
        partition_info: Dict[str, Any]
    ) -> Dict[str, List[Path]]:
        """Organize extracted files in the output directory."""
        organized = {
            'partitions': [],
            'boot_images': [],
            'firmware_files': [],
            'metadata': []
        }
        
        # Move files from temp to output directory
        temp_files = list(self.config.temp_dir.rglob('*'))
        
        for file_path in temp_files:
            if file_path.is_file():
                relative_path = file_path.relative_to(self.config.temp_dir)
                output_path = self.config.output_dir / relative_path
                
                # Ensure parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                shutil.move(str(file_path), str(output_path))
                
                # Categorize file
                if self._is_partition_file(output_path):
                    organized['partitions'].append(output_path)
                elif self._is_boot_image(output_path):
                    organized['boot_images'].append(output_path)
                elif self._is_firmware_file(output_path):
                    organized['firmware_files'].append(output_path)
                else:
                    organized['metadata'].append(output_path)
        
        return organized
    
    def _is_partition_file(self, file_path: Path) -> bool:
        """Check if file is a partition image."""
        partition_extensions = ['.img', '.ext4', '.bin']
        partition_names = self.config.partitions
        
        return (
            file_path.suffix in partition_extensions and
            any(part in file_path.stem for part in partition_names)
        )
    
    def _is_boot_image(self, file_path: Path) -> bool:
        """Check if file is a boot image."""
        boot_names = ['boot', 'recovery', 'vendor_boot', 'init_boot', 'vendor_kernel_boot']
        return any(boot in file_path.stem for boot in boot_names)
    
    def _is_firmware_file(self, file_path: Path) -> bool:
        """Check if file is a firmware-related file."""
        firmware_extensions = ['.zip', '.tar', '.gz', '.ozip', '.kdz', '.nb0']
        return file_path.suffix in firmware_extensions
    
    def _cleanup_workspace(self) -> None:
        """Clean up temporary files if needed."""
        # Only clean temp directory, keep output
        if self.config.temp_dir.exists():
            try:
                shutil.rmtree(self.config.temp_dir)
                self.logger.debug("Temporary workspace cleaned up")
            except Exception as e:
                self.logger.warning(f"Could not clean up temp directory: {e}")
    
    def list_supported_formats(self) -> List[str]:
        """Return list of supported firmware formats."""
        return self.config.supported_formats.copy()
    
    def get_vendor_support(self) -> List[str]:
        """Return list of supported vendors/manufacturers."""
        return self.vendor_manager.get_supported_vendors()
    
    def get_extraction_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file without extracting it."""
        return self.detector.detect_input(file_path)