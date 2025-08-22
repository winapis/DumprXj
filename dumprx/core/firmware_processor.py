import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .firmware_detector import FirmwareDetector
from .downloader import DownloadManager
from .firmware_extractor import FirmwareExtractor
from .git_manager import GitManager
from .telegram_bot import TelegramBot

logger = logging.getLogger(__name__)
console = Console()

class FirmwareProcessor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.detector = FirmwareDetector()
        self.downloader = DownloadManager(config_manager)
        self.extractor = FirmwareExtractor(config_manager)
        self.git_manager = GitManager(config_manager)
        self.telegram_bot = TelegramBot(config_manager)
        
        self.project_dir = Path.cwd()
        self.input_dir = self.project_dir / "input"
        self.output_dir = self.project_dir / "out"
        self.temp_dir = None
    
    def process(self, input_path: str):
        console.print(f"[bold blue]Processing:[/bold blue] {input_path}")
        
        try:
            self._setup_directories()
            
            input_type, firmware_type = self.detector.detect_input_type(input_path)
            console.print(f"[green]Detected:[/green] {input_type} ({firmware_type})")
            
            if input_type == 'url':
                firmware_path = self._handle_url(input_path, firmware_type)
            elif input_type == 'file':
                firmware_path = Path(input_path)
            elif input_type == 'directory':
                firmware_path = Path(input_path)
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                extract_task = progress.add_task("Extracting firmware...", total=None)
                
                firmware_info = self.extractor.extract(
                    firmware_path, 
                    firmware_type, 
                    self.output_dir
                )
                
                progress.update(extract_task, description="Extraction complete")
            
            console.print("[green]✅ Firmware extraction completed[/green]")
            
            self._generate_file_list()
            
            repo_url = self.git_manager.upload_firmware(firmware_info, self.output_dir)
            
            if repo_url:
                console.print(f"[green]✅ Uploaded to:[/green] {repo_url}")
                
                self.telegram_bot.send_notification_sync(firmware_info, repo_url)
                console.print("[green]✅ Telegram notification sent[/green]")
            else:
                console.print("[yellow]⚠️ Local dump only (no git provider configured)[/yellow]")
            
            self._display_summary(firmware_info, repo_url)
            
        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            logger.error(f"Processing failed: {e}", exc_info=True)
            raise
        
        finally:
            self._cleanup()
    
    def _setup_directories(self):
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="dumprx_temp_"))
    
    def _handle_url(self, url: str, url_type: str) -> Path:
        console.print(f"[blue]Downloading from {url_type}...[/blue]")
        
        download_path = self.input_dir / "downloaded_firmware"
        
        if self.downloader.download(url, download_path, url_type):
            return download_path
        else:
            raise RuntimeError(f"Failed to download from {url}")
    
    def _generate_file_list(self):
        all_files_path = self.output_dir / "all_files.txt"
        
        with open(all_files_path, 'w') as f:
            f.write("all_files.txt\n")
            
            for file_path in self.output_dir.rglob('*'):
                if file_path.is_file() and file_path != all_files_path:
                    relative_path = file_path.relative_to(self.output_dir)
                    f.write(f"{relative_path}\n")
    
    def _display_summary(self, firmware_info: Dict[str, Any], repo_url: str = None):
        console.print("\n[bold green]📱 Firmware Information[/bold green]")
        console.print(f"[cyan]Brand:[/cyan] {firmware_info.get('brand', 'Unknown')}")
        console.print(f"[cyan]Device:[/cyan] {firmware_info.get('codename', 'Unknown')}")
        console.print(f"[cyan]Platform:[/cyan] {firmware_info.get('platform', 'Unknown')}")
        console.print(f"[cyan]Android Version:[/cyan] {firmware_info.get('release', 'Unknown')}")
        
        if firmware_info.get('kernel_version'):
            console.print(f"[cyan]Kernel Version:[/cyan] {firmware_info['kernel_version']}")
        
        console.print(f"[cyan]Fingerprint:[/cyan] {firmware_info.get('fingerprint', 'Unknown')}")
        
        if repo_url:
            console.print(f"\n[bold green]🔗 Repository:[/bold green] {repo_url}")
        
        console.print(f"\n[bold green]📁 Output Directory:[/bold green] {self.output_dir}")
    
    def _cleanup(self):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        downloaded_files = list(self.input_dir.glob("downloaded_*"))
        for file_path in downloaded_files:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path, ignore_errors=True)