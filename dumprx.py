#!/usr/bin/env python3

import asyncio
import argparse
import os
import sys
import tempfile
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any

from lib.config import Config
from lib.logging import setup_logging, get_logger
from lib.ui import UI, print_usage, ProgressBar
from lib.download import DownloadManager
from lib.firmware import FirmwareAnalyzer
from lib.extractor import FirmwareExtractor
from lib.git import GitManager
from lib.telegram import TelegramManager


class DumprX:
    def __init__(self, config_path: Optional[str] = None):
        self.config = Config(config_path)
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.utils_dir = os.path.join(self.project_dir, 'utils')
        self.input_dir = os.path.join(self.project_dir, 'input')
        self.output_dir = os.path.join(self.project_dir, 'out')
        
        # Load tokens from files if they exist
        self.config.load_tokens_from_files(self.project_dir)
        
        # Initialize components
        self.download_manager = DownloadManager(self.config.config_data)
        self.firmware_analyzer = FirmwareAnalyzer(self.utils_dir)
        self.firmware_extractor = FirmwareExtractor(self.utils_dir)
        self.git_manager = GitManager(self.config.get('git', {}))
        self.telegram_manager = TelegramManager(self.config.config_data)
        
        self.logger = get_logger()

    async def process_firmware(self, input_path: str, upload_to_git: bool = True) -> None:
        """Main firmware processing pipeline"""
        
        start_time = time.time()
        
        try:
            # Prepare directories
            os.makedirs(self.input_dir, exist_ok=True)
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Clean output directory
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
            os.makedirs(self.output_dir)

            # Step 1: Download or copy firmware
            UI.section_header("FIRMWARE ACQUISITION")
            firmware_path = await self._acquire_firmware(input_path)
            
            # Step 2: Analyze firmware
            UI.section_header("FIRMWARE ANALYSIS")
            firmware_info = self.firmware_analyzer.analyze_firmware(firmware_path, self.output_dir)
            
            # Send download start notification
            await self.telegram_manager.send_download_start(
                input_path, firmware_info['firmware_type']
            )
            
            # Step 3: Extract firmware
            UI.section_header("FIRMWARE EXTRACTION")
            extracted_files = await self._extract_firmware(firmware_path, firmware_info)
            
            # Step 4: Post-process extracted files
            UI.section_header("POST-PROCESSING")
            await self._post_process_files()
            
            # Calculate processing time
            processing_time = self._format_time(time.time() - start_time)
            
            # Send extraction complete notification
            await self.telegram_manager.send_extraction_complete(
                firmware_info['firmware_type'],
                len(firmware_info.get('partitions', [])),
                processing_time
            )
            
            # Step 5: Upload to Git repository (if enabled)
            if upload_to_git:
                UI.section_header("GIT REPOSITORY UPLOAD")
                git_url = await self._upload_to_git(firmware_info)
                
                # Send final notification
                await self.telegram_manager.send_firmware_notification(
                    firmware_info, git_url
                )
            
            # Final summary
            UI.section_header("EXTRACTION COMPLETE")
            file_count = len([f for f in os.listdir(self.output_dir) 
                            if os.path.isfile(os.path.join(self.output_dir, f))])
            UI.print_extraction_complete(file_count, self.output_dir)
            
        except Exception as e:
            await self.telegram_manager.send_error(str(e), "firmware_processing")
            UI.print_error(f"Firmware processing failed: {e}")
            raise

    async def _acquire_firmware(self, input_path: str) -> str:
        """Download or copy firmware to working directory"""
        
        if self.download_manager.is_url(input_path):
            UI.print_info("Downloading firmware from URL")
            return await self.download_manager.download(input_path, self.input_dir)
        else:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input path not found: {input_path}")
            
            UI.print_info("Using local firmware file/directory")
            
            if os.path.isfile(input_path):
                # Copy file to input directory
                filename = os.path.basename(input_path)
                dest_path = os.path.join(self.input_dir, filename)
                shutil.copy2(input_path, dest_path)
                return dest_path
            else:
                # Directory - use directly
                return input_path

    async def _extract_firmware(self, firmware_path: str, firmware_info: Dict[str, Any]) -> list:
        """Extract firmware using appropriate extractor"""
        
        firmware_type = firmware_info['firmware_type']
        
        if firmware_type == 'unknown':
            UI.print_warning("Unknown firmware type, attempting generic extraction")
        
        try:
            return await self.firmware_extractor.extract(firmware_path, self.output_dir)
        except Exception as e:
            UI.print_error(f"Primary extraction failed: {e}")
            
            # Try fallback extraction methods
            if os.path.isdir(firmware_path):
                UI.print_info("Copying directory contents as fallback")
                for item in os.listdir(firmware_path):
                    src = os.path.join(firmware_path, item)
                    dst = os.path.join(self.output_dir, item)
                    
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                
                return [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir)]
            else:
                raise

    async def _post_process_files(self) -> None:
        """Post-process extracted files"""
        
        UI.print_processing("Generating file lists and checksums")
        
        # Generate file list
        self.git_manager.generate_file_list(self.output_dir)
        
        # Generate checksums
        self.git_manager.generate_checksums(self.output_dir)
        
        # Clean up temporary directories
        temp_dirs = ['tmp', 'temp', 'ozip_temp', 'kdz_extracted']
        for temp_dir in temp_dirs:
            temp_path = os.path.join(self.output_dir, temp_dir)
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path, ignore_errors=True)
        
        UI.print_success("Post-processing complete")

    async def _upload_to_git(self, firmware_info: Dict[str, Any]) -> str:
        """Upload extracted firmware to Git repository"""
        
        info = firmware_info.get('firmware_info')
        
        if info and info.brand and info.model:
            repo_name = f"{info.brand}_{info.model}".replace(' ', '_').lower()
            branch = f"{info.version}_{info.build_id}".replace(' ', '_').lower() if info.version and info.build_id else "main"
        else:
            repo_name = "firmware_dump"
            branch = "main"
        
        # Generate README and documentation
        self.git_manager.generate_readme(
            firmware_info, 
            firmware_info.get('partitions', []), 
            self.output_dir
        )
        
        # Determine git provider from environment or config
        use_gitlab = os.environ.get('PUSH_TO_GITLAB', '').lower() == 'true'
        
        # Setup repository
        git_url = await self.git_manager.setup_repository(repo_name, self.output_dir, use_gitlab)
        
        # Commit and push
        commit_message = f"Add {info.brand} {info.model} firmware dump" if info else "Add firmware dump"
        await self.git_manager.commit_and_push(self.output_dir, branch, commit_message)
        
        UI.print_success(f"Uploaded to: {git_url}")
        return git_url

    def _format_time(self, seconds: float) -> str:
        """Format time duration as human readable string"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds//60:.0f}m {seconds%60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"

    async def validate_setup(self) -> bool:
        """Validate that all required tools and dependencies are available"""
        
        UI.subsection_header("VALIDATING SETUP")
        
        required_tools = [
            'git', 'git-lfs', '7z', 'unzip', 'tar', 
            'python3', 'aria2c', 'brotli', 'xz'
        ]
        
        missing_tools = []
        
        for tool in required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            UI.print_error(f"Missing required tools: {', '.join(missing_tools)}")
            UI.print_info("Please run setup.sh to install dependencies")
            return False
        
        # Test Telegram if configured
        if self.telegram_manager.is_enabled():
            await self.telegram_manager.test_connection()
        
        UI.print_success("Setup validation complete")
        return True


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DumprX v2.0 - Advanced Firmware Extraction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dumprx firmware.zip                    # Extract local firmware
  dumprx 'https://example.com/fw.zip'    # Download and extract
  dumprx --validate                      # Validate setup
  dumprx --config custom.yaml firmware   # Use custom config

Supported formats: .zip, .rar, .7z, .kdz, .ozip, .ofp, .ops, payload.bin, etc.
        """
    )
    
    parser.add_argument(
        'firmware_path',
        nargs='?',
        help='Path to firmware file/directory or download URL'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--no-upload',
        action='store_true',
        help='Skip Git repository upload'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate setup and dependencies'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='DumprX v2.0.0'
    )
    
    return parser


async def main() -> int:
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Show banner
    UI.banner()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)
    
    # Initialize DumprX
    try:
        dumprx = DumprX(config_path=args.config)
    except Exception as e:
        UI.print_error(f"Failed to initialize DumprX: {e}")
        return 1
    
    # Validate setup if requested
    if args.validate:
        success = await dumprx.validate_setup()
        return 0 if success else 1
    
    # Check if firmware path is provided
    if not args.firmware_path:
        print_usage()
        return 1
    
    # Validate setup before processing
    if not await dumprx.validate_setup():
        return 1
    
    # Process firmware
    try:
        await dumprx.process_firmware(
            args.firmware_path,
            upload_to_git=not args.no_upload
        )
        return 0
    except KeyboardInterrupt:
        UI.print_warning("Process interrupted by user")
        return 1
    except Exception as e:
        UI.print_error(f"Process failed: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)