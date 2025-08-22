"""
Modern CLI interface for DumprX.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .core.logger import Logger
from .core.config import Config
from .core.detector import FirmwareDetector
from .downloaders import DownloadManager
from .extractors import ExtractionManager

class DumprXCLI:
    """Main CLI application for DumprX."""
    
    def __init__(self):
        self.logger = Logger("DumprX")
        self.config = Config()
        self.detector = FirmwareDetector()
        self.download_manager = DownloadManager(self.logger)
        self.extraction_manager = ExtractionManager(self.config, self.logger)
        
    def show_banner(self):
        """Display application banner."""
        banner = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝

Advanced Firmware Extraction Toolkit v2.0.0
        """
        self.logger.banner(banner)
    
    def show_help(self):
        """Display usage help."""
        help_text = """
🔧 USAGE:
   dumprx <firmware_file_or_url> [options]

📁 SUPPORTED FORMATS:
   • Archives: *.zip, *.rar, *.7z, *.tar, *.tar.gz, *.tgz, *.tar.md5
   • Encrypted: *.ozip, *.ofp, *.ops, *.kdz, ruu_*.exe  
   • Images: system.new.dat, system.img, payload.bin, UPDATE.APP
   • Special: *.nb0, *chunk*, *.pac, *super*.img, *system*.sin

🌐 SUPPORTED SERVICES:
   • Direct HTTP/HTTPS links
   • Mega.nz, MediaFire, Google Drive
   • OneDrive, AndroidFileHost, WeTransfer

📋 EXAMPLES:
   dumprx firmware.zip                    # Extract local file
   dumprx 'https://example.com/rom.zip'   # Download and extract
   dumprx /path/to/firmware_folder/       # Process directory

⚙️  OPTIONS:
   -h, --help     Show this help message
   -v, --verbose  Enable verbose output
   -q, --quiet    Minimize output
   --version      Show version information
        """
        print(help_text)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description="DumprX - Advanced Firmware Extraction Toolkit",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False
        )
        
        parser.add_argument(
            "input", 
            nargs="?",
            help="Firmware file, directory, or download URL"
        )
        
        parser.add_argument(
            "-h", "--help",
            action="store_true",
            help="Show help message"
        )
        
        parser.add_argument(
            "-v", "--verbose",
            action="store_true", 
            help="Enable verbose output"
        )
        
        parser.add_argument(
            "-q", "--quiet",
            action="store_true",
            help="Minimize output"
        )
        
        parser.add_argument(
            "--version",
            action="store_true",
            help="Show version information"
        )
        
        return parser
    
    def validate_input(self, input_path: str) -> bool:
        """Validate input path or URL."""
        if not input_path or input_path.isspace():
            self.logger.error("Input cannot be empty")
            return False
        
        # Check if it's a URL
        if self.download_manager.is_url(input_path):
            return True
        
        # Check if local path exists
        path = Path(input_path)
        if not path.exists():
            self.logger.error(f"Path does not exist: {input_path}")
            return False
        
        return True
    
    def process_input(self, input_path: str) -> Optional[str]:
        """
        Process input (download if URL, validate if local path).
        
        Returns:
            Local file/directory path, or None if failed
        """
        if self.download_manager.is_url(input_path):
            self.logger.info("Download detected", f"URL: {input_path}")
            
            try:
                # Create input directory
                self.config.create_directories()
                download_dir = self.config.get_download_dir()
                
                # Download file
                downloaded_file = self.download_manager.download(input_path, download_dir)
                return downloaded_file
                
            except Exception as e:
                self.logger.error("Download failed", str(e))
                return None
        else:
            # Local file/directory
            return input_path
    
    def extract_firmware(self, filepath: str) -> bool:
        """
        Extract firmware from file or directory.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Detect firmware type
            self.logger.info("Analyzing firmware")
            firmware_type, metadata = self.detector.detect_firmware_type(filepath)
            
            if firmware_type.value == "unknown":
                self.logger.error("Unsupported firmware format")
                return False
            
            self.logger.success(f"Firmware detected", f"Type: {firmware_type.value}")
            
            # Validate firmware
            if not self.detector.validate_firmware(firmware_type, filepath):
                self.logger.warning("Firmware validation failed, proceeding anyway")
            
            # Create output directories
            self.config.create_directories()
            
            # Extract firmware
            extracted_files = self.extraction_manager.extract_firmware(
                firmware_type, filepath, metadata
            )
            
            if extracted_files:
                self.logger.success("Extraction completed successfully")
                self.logger.info(f"Output directory: {self.config.get_output_dir()}")
                self.logger.info(f"Extracted {len(extracted_files)} files")
                return True
            else:
                self.logger.error("No files were extracted")
                return False
                
        except Exception as e:
            self.logger.error("Extraction failed", str(e))
            return False
    
    def run(self, args: Optional[list] = None) -> int:
        """
        Main application entry point.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        parser = self.create_parser()
        
        if args is None:
            args = sys.argv[1:]
        
        # Handle no arguments
        if not args:
            self.show_banner()
            self.show_help()
            return 1
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        # Handle help
        if parsed_args.help:
            self.show_banner()
            self.show_help()
            return 0
        
        # Handle version
        if parsed_args.version:
            from . import __version__
            print(f"DumprX v{__version__}")
            return 0
        
        # Configure logging
        if parsed_args.verbose:
            self.logger.level = "DEBUG"
        elif parsed_args.quiet:
            self.logger.level = "ERROR"
        
        # Validate input
        if not parsed_args.input:
            self.logger.error("No input provided")
            self.show_help()
            return 1
        
        if not self.validate_input(parsed_args.input):
            return 1
        
        # Show banner
        if not parsed_args.quiet:
            self.show_banner()
        
        # Process input
        local_path = self.process_input(parsed_args.input)
        if not local_path:
            return 1
        
        # Extract firmware
        success = self.extract_firmware(local_path)
        
        return 0 if success else 1

def main():
    """Main entry point."""
    app = DumprXCLI()
    sys.exit(app.run())

if __name__ == "__main__":
    main()