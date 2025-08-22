import click
import sys
import time
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

from dumprx.utils.ui import show_banner, show_usage, print_error, print_info, print_success
from dumprx.utils.logging import setup_logging
from dumprx.core.config import Config
from dumprx.core.dumper import FirmwareDumper

console = Console()


@click.command()
@click.argument('firmware_path', required=False)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config-dir', type=click.Path(), help='Custom configuration directory')
@click.version_option(version='2.0.0', prog_name='DumprX')
def cli(firmware_path, verbose, config_dir):
    """DumprX - Advanced firmware extraction and dumping toolkit
    
    FIRMWARE_PATH can be:
    - A firmware file (.zip, .rar, .7z, .ozip, .kdz, etc.)
    - An extracted firmware folder
    - A supported website link (mega.nz, mediafire, gdrive, etc.)
    """
    # Clear screen
    console.clear()
    
    # Setup logging
    logger = setup_logging(verbose)
    
    # Show banner
    show_banner()
    time.sleep(0.3)
    
    # Validate input
    if not firmware_path:
        print_error("No Input Is Given.")
        time.sleep(0.5)
        show_usage()
        time.sleep(1)
        sys.exit(1)
    
    if firmware_path == "" or firmware_path == " ":
        print_error("Enter Firmware Path.")
        time.sleep(0.5)
        show_usage()
        time.sleep(1)
        sys.exit(1)
    
    try:
        # Setup configuration
        project_dir = Path(config_dir) if config_dir else None
        config = Config(project_dir)
        config.validate_project_dir()
        
        # Initialize dumper
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing DumprX...", total=None)
            
            dumper = FirmwareDumper(config)
            dumper.setup()
            
            progress.update(task, description="Processing firmware...")
            
            # Process firmware
            result = dumper.process_firmware(firmware_path)
            
            if result:
                print_success("Firmware processing completed successfully!")
            else:
                print_error("Firmware processing failed!")
                sys.exit(1)
                
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print_error("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()