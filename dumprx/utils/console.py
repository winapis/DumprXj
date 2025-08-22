"""
Console utilities for DumprX
"""

import sys
from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table


class DumprXConsole:
    """Enhanced console output for DumprX"""
    
    def __init__(self, colors: bool = True, emoji: bool = True):
        self.console = Console(color_system="auto" if colors else None)
        self.emoji = emoji
        
    def print_banner(self) -> None:
        """Print the DumprX banner"""
        banner = """
[green]██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝[/green]
        """
        self.console.print(banner)
        
    def success(self, message: str) -> None:
        """Print success message"""
        emoji = "✅ " if self.emoji else ""
        self.console.print(f"[green]{emoji}{message}[/green]")
        
    def error(self, message: str) -> None:
        """Print error message"""
        emoji = "❌ " if self.emoji else ""
        self.console.print(f"[red]{emoji}{message}[/red]")
        
    def warning(self, message: str) -> None:
        """Print warning message"""
        emoji = "⚠️ " if self.emoji else ""
        self.console.print(f"[yellow]{emoji}{message}[/yellow]")
        
    def info(self, message: str) -> None:
        """Print info message"""
        emoji = "ℹ️ " if self.emoji else ""
        self.console.print(f"[blue]{emoji}{message}[/blue]")
        
    def debug(self, message: str) -> None:
        """Print debug message"""
        emoji = "🐛 " if self.emoji else ""
        self.console.print(f"[dim]{emoji}{message}[/dim]")
        
    def step(self, message: str) -> None:
        """Print step message"""
        emoji = "🔄 " if self.emoji else ">> "
        self.console.print(f"[cyan]{emoji}{message}[/cyan]")
        
    def detected(self, message: str) -> None:
        """Print detection message"""
        emoji = "🔍 " if self.emoji else ""
        self.console.print(f"[magenta]{emoji}{message}[/magenta]")
        
    def progress_spinner(self, description: str = "Processing..."):
        """Create a progress spinner"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )
        
    def progress_bar(self, description: str = "Processing..."):
        """Create a progress bar"""
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        )
        
    def create_table(self, title: Optional[str] = None) -> Table:
        """Create a rich table"""
        return Table(title=title, show_header=True, header_style="bold magenta")
        
    def print_panel(self, content: str, title: Optional[str] = None, 
                   style: str = "blue") -> None:
        """Print content in a panel"""
        panel = Panel(content, title=title, border_style=style)
        self.console.print(panel)
        
    def print_usage(self) -> None:
        """Print usage information"""
        usage_text = """
[bold green]DumprX - Advanced Firmware Dumper & Extractor[/bold green]

[bold]Usage:[/bold]
  dumprx [OPTIONS] COMMAND [ARGS]...

[bold]Commands:[/bold]
  [cyan]dump[/cyan]      Extract firmware from file or URL
  [cyan]download[/cyan]  Download firmware from supported sources
  [cyan]config[/cyan]    Manage configuration settings
  [cyan]setup[/cyan]     Setup dependencies and tools
  [cyan]version[/cyan]   Show version information

[bold]Examples:[/bold]
  dumprx dump firmware.zip
  dumprx dump https://example.com/firmware.zip
  dumprx download https://mega.nz/file/...
  dumprx config show
  dumprx setup

[bold]Supported Sources:[/bold]
  • Direct download links
  • Mega.nz links
  • MediaFire links  
  • Google Drive links
  • AndroidFileHost links
  • OneDrive links

[bold]Supported Formats:[/bold]
  • Archives: .zip, .rar, .7z, .tar, .tar.gz, .tgz
  • Firmware: .ozip, .ofp, .ops, .kdz, .nb0, .pac
  • Images: .img, .bin, .sin
  • Executables: ruu_*.exe

For more information, visit: https://github.com/Eduardob3677/DumprX
        """
        self.console.print(usage_text)
        
    def print_error_and_exit(self, message: str, exit_code: int = 1) -> None:
        """Print error message and exit"""
        self.error(message)
        sys.exit(exit_code)