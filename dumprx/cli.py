#!/usr/bin/env python3

import os
import sys
import click
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from dumprx import __version__, PROJECT_DIR
from dumprx.config import config
from dumprx.console import setup_logging, print_banner, info, warning, error, step, success
from dumprx.detector import FirmwareDetector
from dumprx.downloaders import download_firmware
from dumprx.extractors import get_extractor
from dumprx.git_ops import git_manager
from dumprx.telegram import telegram_bot
from dumprx.firmware_analyzer import FirmwareAnalyzer


def validate_input(ctx, param, value):
    if not value:
        raise click.BadParameter('Input path or URL is required')
    return value


@click.group(invoke_without_command=True)
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def cli(ctx, config, verbose, version):
    """🚀 DumprX - Advanced Firmware Dumping Tool"""
    
    if version:
        click.echo(f"DumprX v{__version__}")
        sys.exit(0)
    
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_logging()
    
    if ctx.invoked_subcommand is None:
        print_banner()
        click.echo(ctx.get_help())


@cli.command()
@click.argument('input_path', callback=validate_input)
@click.option('--output', '-o', type=click.Path(), default='./out',
              help='Output directory (default: ./out)')
@click.option('--temp-dir', '-t', type=click.Path(),
              help='Temporary directory for processing')
@click.option('--no-git', is_flag=True, help='Skip Git repository creation')
@click.option('--no-telegram', is_flag=True, help='Skip Telegram notifications')
def dump(input_path, output, temp_dir, no_git, no_telegram):
    """Extract and analyze firmware from file or URL"""
    
    print_banner()
    
    output_dir = Path(output).absolute()
    temp_work_dir = Path(temp_dir) if temp_dir else None
    
    try:
        firmware_processor = FirmwareProcessor(
            input_path=input_path,
            output_dir=output_dir,
            temp_dir=temp_work_dir,
            enable_git=not no_git,
            enable_telegram=not no_telegram
        )
        
        success_result = firmware_processor.process()
        
        if success_result:
            success("✨ Firmware processing completed successfully!")
        else:
            error("❌ Firmware processing failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        warning("⚠️ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('--output', '-o', type=click.Path(), default='./downloads',
              help='Download directory (default: ./downloads)')
def download(url, output):
    """Download firmware from supported URLs"""
    
    print_banner()
    step(f"Downloading firmware from: {url}")
    
    output_dir = Path(output).absolute()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        downloaded_file = download_firmware(url, str(output_dir))
        
        if downloaded_file:
            success(f"Download completed: {downloaded_file}")
        else:
            error("Download failed")
            sys.exit(1)
            
    except Exception as e:
        error(f"Download error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('input_path')
def detect(input_path):
    """Detect firmware type and format"""
    
    print_banner()
    step(f"Analyzing: {input_path}")
    
    try:
        detection_result = FirmwareDetector.detect_input_type(input_path)
        
        info("🔍 Detection Results:")
        for key, value in detection_result.items():
            click.echo(f"  {key}: {value}")
        
        strategy = FirmwareDetector.get_extraction_strategy(detection_result)
        info(f"📋 Extraction Strategy: {strategy}")
        
    except Exception as e:
        error(f"Detection failed: {str(e)}")
        sys.exit(1)


@cli.command()
def config_show():
    """Show current configuration"""
    
    print_banner()
    info("📋 Current Configuration:")
    
    def print_config_section(data, prefix=""):
        for key, value in data.items():
            if isinstance(value, dict):
                click.echo(f"{prefix}{key}:")
                print_config_section(value, prefix + "  ")
            else:
                display_value = value if not (key.lower().find('token') >= 0 and value) else "***"
                click.echo(f"{prefix}{key}: {display_value}")
    
    print_config_section(config.data)


@cli.command()
@click.option('--check-tools', is_flag=True, help='Check required tools availability')
def status(check_tools):
    """Show DumprX status and configuration"""
    
    print_banner()
    
    info("🔧 DumprX Status:")
    click.echo(f"  Version: {__version__}")
    click.echo(f"  Project Directory: {PROJECT_DIR}")
    click.echo(f"  Config File: {config.config_path}")
    
    info("🔗 Git Configuration:")
    click.echo(f"  GitHub: {'✅ Configured' if git_manager.has_github_config() else '❌ Not configured'}")
    click.echo(f"  GitLab: {'✅ Configured' if git_manager.has_gitlab_config() else '❌ Not configured'}")
    
    info("📱 Telegram Configuration:")
    click.echo(f"  Bot: {'✅ Enabled' if telegram_bot.is_enabled() else '❌ Disabled'}")
    
    if check_tools:
        info("🛠️  Tool Availability:")
        tools = [
            ('7zip', ['7z', '7za', '7zz']),
            ('git', ['git']),
            ('git-lfs', ['git-lfs']),
            ('python3', ['python3']),
            ('uv', ['uv'])
        ]
        
        for tool_name, commands in tools:
            found = False
            for cmd in commands:
                if shutil.which(cmd):
                    click.echo(f"  {tool_name}: ✅ {cmd}")
                    found = True
                    break
            if not found:
                click.echo(f"  {tool_name}: ❌ Not found")


class FirmwareProcessor:
    
    def __init__(self, input_path: str, output_dir: Path, temp_dir: Optional[Path] = None,
                 enable_git: bool = True, enable_telegram: bool = True):
        self.input_path = input_path
        self.output_dir = output_dir
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp(prefix='dumprx_'))
        self.enable_git = enable_git
        self.enable_telegram = enable_telegram
        
        self.firmware_info = {}
        self.repo_info = {}
        
    def process(self) -> bool:
        try:
            step("🔍 Detecting input type and format")
            detection_result = FirmwareDetector.detect_input_type(self.input_path)
            
            if detection_result['type'] == 'unknown':
                error("Unsupported input type or format")
                return False
            
            info(f"Detected: {detection_result}")
            
            if detection_result['type'] == 'url':
                if not self._download_firmware(detection_result):
                    return False
            else:
                self.firmware_file = self.input_path
            
            if not self._extract_firmware(detection_result):
                return False
            
            if not self._analyze_firmware():
                return False
            
            if self.enable_telegram:
                telegram_bot.send_start_notification(self.firmware_info)
            
            if self.enable_git:
                self.repo_info = git_manager.create_and_push_repo(self.firmware_info, str(self.output_dir))
                if not self.repo_info:
                    warning("Git repository creation failed")
            
            if self.enable_telegram:
                if self.repo_info:
                    telegram_bot.send_completion_notification(self.firmware_info, self.repo_info)
                else:
                    telegram_bot.send_completion_notification(self.firmware_info, {})
            
            return True
            
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            error(error_msg)
            
            if self.enable_telegram:
                telegram_bot.send_error_notification(self.firmware_info, error_msg)
            
            return False
        finally:
            self._cleanup()
    
    def _download_firmware(self, detection_result) -> bool:
        step("📥 Downloading firmware")
        
        download_dir = self.temp_dir / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_file = download_firmware(self.input_path, str(download_dir))
        
        if not downloaded_file:
            error("Download failed")
            return False
        
        self.firmware_file = downloaded_file
        success(f"Downloaded: {Path(downloaded_file).name}")
        return True
    
    def _extract_firmware(self, detection_result) -> bool:
        step("📦 Extracting firmware")
        
        extract_dir = self.temp_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        extractor = get_extractor(detection_result, self.firmware_file, str(extract_dir))
        
        if not extractor.extract():
            error("Firmware extraction failed")
            return False
        
        self.extracted_dir = extract_dir
        success("Firmware extracted successfully")
        return True
    
    def _analyze_firmware(self) -> bool:
        step("🔬 Analyzing firmware")
        
        try:
            analyzer = FirmwareAnalyzer(str(self.extracted_dir), str(self.output_dir))
            self.firmware_info = analyzer.analyze()
            
            if not self.firmware_info:
                warning("Firmware analysis produced limited results")
                self.firmware_info = {
                    'brand': 'Unknown',
                    'device': 'Unknown',
                    'android_version': 'Unknown',
                    'platform': 'Unknown'
                }
            
            info(f"Analysis complete: {self.firmware_info}")
            return True
            
        except Exception as e:
            error(f"Firmware analysis failed: {str(e)}")
            return False
    
    def _cleanup(self):
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                warning(f"Failed to cleanup temp directory: {str(e)}")


if __name__ == '__main__':
    cli()