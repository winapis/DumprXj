"""
CLI interface for DumprX.
"""

import click
import sys
from pathlib import Path
from typing import Optional

from ..core.dumper import DumprX
from ..core.config import Config
from ..core.logger import get_logger, setup_file_logging


def print_banner():
    """Print the DumprX banner."""
    banner = """
    ██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
    ██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
    ██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
    ██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
    ██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
    ╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
    
    🚀 Advanced Android Firmware Extraction Toolkit v2.0
    """
    click.echo(click.style(banner, fg='green', bold=True))


@click.group(invoke_without_command=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Custom config file')
@click.pass_context
def cli(ctx, verbose, debug, config):
    """DumprX - Advanced Android Firmware Extraction Toolkit."""
    # Set up logging level
    import logging
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    logger = get_logger(level=level)
    
    # Print banner
    if ctx.invoked_subcommand is None:
        print_banner()
        ctx.invoke(help_command)
    
    # Store common options in context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    ctx.obj['config_file'] = config


@cli.command()
@click.argument('input_path', type=str)
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--no-git', is_flag=True, help='Skip Git upload')
@click.option('--no-telegram', is_flag=True, help='Skip Telegram notification')
@click.option('--config-dir', type=click.Path(), help='Custom config directory')
@click.pass_context
def extract(ctx, input_path, output, no_git, no_telegram, config_dir):
    """
    Extract firmware from a file, folder, or URL.
    
    INPUT_PATH can be:
    - Local firmware file (.zip, .rar, .ozip, .kdz, etc.)
    - Local directory containing firmware files
    - URL from supported services (mega.nz, mediafire, gdrive, etc.)
    
    Examples:
    
        dumprx extract firmware.zip
        
        dumprx extract 'https://mega.nz/file/...'
        
        dumprx extract /path/to/firmware/folder --output /custom/output
    """
    logger = get_logger()
    
    try:
        # Initialize configuration
        if config_dir:
            config = Config(project_dir=Path(config_dir))
        else:
            config = Config()
        
        # Set up file logging
        log_file = config.output_dir / "dumprx.log"
        setup_file_logging(log_file)
        
        # Initialize DumprX
        dumper = DumprX(config)
        
        # Extract firmware
        result = dumper.extract_firmware(
            input_path=input_path,
            output_dir=output,
            upload_to_git=not no_git,
            send_telegram=not no_telegram
        )
        
        # Display results
        logger.success(f"Extraction completed! Output: {result['output_dir']}")
        
        if result.get('git_upload'):
            git_info = result['git_upload']
            if git_info.get('success'):
                logger.success(f"📤 Uploaded to: {git_info.get('repository_url', 'Git repository')}")
        
        if result.get('telegram_notification'):
            tg_info = result['telegram_notification']
            if tg_info.get('success'):
                logger.success("📱 Telegram notification sent")
        
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        if ctx.obj.get('debug'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--format', 'format_filter', help='Filter by format (zip, rar, ozip, etc.)')
def formats(format_filter):
    """List supported firmware formats."""
    logger = get_logger()
    config = Config()
    dumper = DumprX(config)
    
    formats = dumper.list_supported_formats()
    
    if format_filter:
        formats = [f for f in formats if format_filter.lower() in f.lower()]
    
    logger.info("📋 Supported firmware formats:")
    for fmt in sorted(formats):
        click.echo(f"  • {fmt}")


@cli.command()
def vendors():
    """List supported vendors/manufacturers."""
    logger = get_logger()
    config = Config()
    dumper = DumprX(config)
    
    vendors = dumper.get_vendor_support()
    
    logger.info("🏭 Supported vendors/manufacturers:")
    for vendor in sorted(vendors):
        click.echo(f"  • {vendor}")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def info(file_path):
    """Get information about a firmware file without extracting it."""
    logger = get_logger()
    config = Config()
    dumper = DumprX(config)
    
    try:
        info_data = dumper.get_extraction_info(file_path)
        
        logger.info(f"📄 File information for: {file_path}")
        click.echo(f"  Type: {info_data.get('type', 'Unknown')}")
        click.echo(f"  Format: {info_data.get('format', 'Unknown')}")
        click.echo(f"  Size: {info_data.get('size', 'Unknown')}")
        
        if 'vendor' in info_data:
            click.echo(f"  Vendor: {info_data['vendor']}")
        
        if 'encrypted' in info_data:
            click.echo(f"  Encrypted: {'Yes' if info_data['encrypted'] else 'No'}")
        
    except Exception as e:
        logger.error(f"Could not analyze file: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--token', prompt='Telegram Bot Token', hide_input=True, help='Telegram bot token')
@click.option('--chat-id', help='Default chat ID for notifications')
def setup_telegram(token, chat_id):
    """Set up Telegram bot integration."""
    logger = get_logger()
    config = Config()
    
    # Save token
    token_file = config.project_dir / ".tg_token"
    token_file.write_text(token)
    
    if chat_id:
        chat_file = config.project_dir / ".tg_chat"
        chat_file.write_text(chat_id)
    
    logger.success("✅ Telegram configuration saved!")
    click.echo(f"Token saved to: {token_file}")
    if chat_id:
        click.echo(f"Chat ID saved to: {config.project_dir / '.tg_chat'}")


@cli.command()
@click.option('--github-token', help='GitHub personal access token')
@click.option('--gitlab-token', help='GitLab access token')
@click.option('--gitlab-host', help='GitLab host URL')
@click.option('--org', help='GitHub/GitLab organization name')
def setup_git(github_token, gitlab_token, gitlab_host, org):
    """Set up Git integration (GitHub or GitLab)."""
    logger = get_logger()
    config = Config()
    
    if github_token:
        token_file = config.project_dir / ".github_token"
        token_file.write_text(github_token)
        logger.success("✅ GitHub token saved!")
    
    if gitlab_token:
        token_file = config.project_dir / ".gitlab_token"
        token_file.write_text(gitlab_token)
        logger.success("✅ GitLab token saved!")
    
    if gitlab_host:
        host_file = config.project_dir / ".gitlab_host"
        host_file.write_text(gitlab_host)
        logger.success("✅ GitLab host saved!")
    
    if org:
        org_file = config.project_dir / ".git_org"
        org_file.write_text(org)
        logger.success("✅ Git organization saved!")


@cli.command()
def config_info():
    """Show current configuration."""
    logger = get_logger()
    config = Config()
    
    click.echo("📋 Current DumprX Configuration:")
    click.echo(f"  Project Directory: {config.project_dir}")
    click.echo(f"  Input Directory: {config.input_dir}")
    click.echo(f"  Output Directory: {config.output_dir}")
    click.echo(f"  Utils Directory: {config.utils_dir}")
    click.echo()
    
    click.echo("🔧 Integration Status:")
    click.echo(f"  GitHub: {'✅ Configured' if config.has_github_token() else '❌ Not configured'}")
    click.echo(f"  GitLab: {'✅ Configured' if config.has_gitlab_token() else '❌ Not configured'}")
    click.echo(f"  Telegram: {'✅ Configured' if config.has_telegram_token() else '❌ Not configured'}")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory for test extraction')
@click.option('--dry-run', is_flag=True, help='Only analyze without extracting')
@click.pass_context
def test(ctx, file_path, output, dry_run):
    """
    Test extraction of a firmware file without full processing.
    
    This command allows you to test if a firmware file can be processed
    by DumprX without doing a full extraction with Git upload and notifications.
    
    Examples:
    
        dumprx test firmware.zip
        
        dumprx test firmware.ozip --dry-run
        
        dumprx test /path/to/firmware.kdz --output /tmp/test
    """
    logger = get_logger()
    
    try:
        # Initialize configuration
        config = Config()
        
        # Set custom output if provided
        if output:
            config.output_dir = Path(output)
            config.temp_dir = config.output_dir / "tmp"
        else:
            # Use a test directory
            config.output_dir = config.project_dir / "test_output"
            config.temp_dir = config.output_dir / "tmp"
        
        config.ensure_directories()
        
        # Set up file logging
        log_file = config.output_dir / "test.log"
        setup_file_logging(log_file)
        
        # Initialize DumprX
        dumper = DumprX(config)
        
        if dry_run:
            # Only analyze the file
            logger.info(f"🔍 Analyzing file: {file_path}")
            info_data = dumper.get_extraction_info(file_path)
            
            logger.info("📄 Analysis results:")
            click.echo(f"  Type: {info_data.get('type', 'Unknown')}")
            click.echo(f"  Format: {info_data.get('format', 'Unknown')}")
            click.echo(f"  Size: {info_data.get('size', 'Unknown')} bytes")
            
            if 'vendor' in info_data:
                click.echo(f"  Vendor: {info_data['vendor']}")
            
            if 'encrypted' in info_data:
                click.echo(f"  Encrypted: {'Yes' if info_data['encrypted'] else 'No'}")
            
            supported = dumper.detector.is_supported_format(info_data)
            click.echo(f"  Supported: {'✅ Yes' if supported else '❌ No'}")
            
        else:
            # Test extraction
            logger.info(f"🧪 Test extracting: {file_path}")
            
            result = dumper.extract_firmware(
                input_path=str(file_path),
                upload_to_git=False,
                send_telegram=False
            )
            
            # Display test results
            logger.success("🎉 Test extraction completed!")
            click.echo(f"\nTest Results:")
            click.echo(f"  Input: {result['input_info'].get('format', 'Unknown')} file")
            click.echo(f"  Partitions found: {len(result.get('partition_info', {}).get('partitions_found', []))}")
            click.echo(f"  Boot images: {len(result.get('partition_info', {}).get('boot_images', []))}")
            click.echo(f"  Output directory: {result['output_dir']}")
            
            system_info = result.get('partition_info', {}).get('system_info', {})
            if system_info.get('brand') != 'Unknown':
                click.echo(f"  Device: {system_info.get('brand', '')} {system_info.get('model', '')}")
                click.echo(f"  Android: {system_info.get('android_version', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        if ctx.obj.get('debug'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
def help_command():
    """Show help and usage examples."""
    print_banner()
    
    click.echo("🔧 Quick Start:")
    click.echo("  1. Extract a firmware file:")
    click.echo("     dumprx extract firmware.zip")
    click.echo()
    click.echo("  2. Extract from URL:")
    click.echo("     dumprx extract 'https://mega.nz/file/...'")
    click.echo()
    click.echo("  3. Set up integrations:")
    click.echo("     dumprx setup-telegram")
    click.echo("     dumprx setup-git")
    click.echo()
    
    click.echo("📚 Available Commands:")
    click.echo("  extract     - Extract firmware files")
    click.echo("  test        - Test extraction without full processing")
    click.echo("  formats     - List supported formats")
    click.echo("  vendors     - List supported vendors")
    click.echo("  info        - Get file information")
    click.echo("  config-info - Show configuration")
    click.echo()
    
    click.echo("🆘 For detailed help on any command:")
    click.echo("  dumprx <command> --help")


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n❌ Operation cancelled by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()