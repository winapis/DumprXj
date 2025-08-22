import click
import sys
from pathlib import Path
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from .config_manager import ConfigManager
from .core.firmware_processor import FirmwareProcessor
from .core.logger import setup_logging

console = Console()

def show_banner():
    banner = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
    """
    
    text = Text(banner, style="bold green")
    panel = Panel(text, title="DumprX", border_style="green")
    console.print(panel)

def show_usage():
    usage_info = """
[bold green]Usage:[/bold green] dumprx <firmware_file_or_url>

[bold blue]Supported Files:[/bold blue]
• *.zip | *.rar | *.7z | *.tar | *.tar.gz | *.tgz | *.tar.md5
• *.ozip | *.ofp | *.ops | *.kdz | ruu_*exe
• system.new.dat | system.new.dat.br | system.new.dat.xz
• system.new.img | system.img | system-sign.img | UPDATE.APP
• *.emmc.img | *.img.ext4 | system.bin | system-p | payload.bin
• *.nb0 | .*chunk* | *.pac | *super*.img | *system*.sin

[bold blue]Supported URLs:[/bold blue]
• Direct download links from any website
• mega.nz | mediafire | gdrive | onedrive | androidfilehost

[bold yellow]Examples:[/bold yellow]
dumprx firmware.zip
dumprx /path/to/extracted/folder
dumprx 'https://example.com/firmware.zip'
dumprx 'https://mega.nz/file/...'
    """
    console.print(usage_info)

@click.command()
@click.argument('input_path', required=False)
@click.option('--config', '-c', default='config.yaml', help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--help-examples', is_flag=True, help='Show usage examples')
def main(input_path, config, verbose, help_examples):
    try:
        config_manager = ConfigManager(config)
        
        if config_manager.get_console_config()['banner']:
            show_banner()
        
        if help_examples or not input_path:
            show_usage()
            if not input_path:
                sys.exit(0)
            return
        
        setup_logging(config_manager, verbose)
        
        processor = FirmwareProcessor(config_manager)
        processor.process(input_path)
        
    except KeyboardInterrupt:
        console.print("\n[red]Process interrupted by user[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    main()