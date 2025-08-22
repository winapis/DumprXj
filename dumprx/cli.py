import click
import sys
import time
import asyncio
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.live import Live

from dumprx.utils.ui import show_banner, show_usage, print_error, print_info, print_success, print_warning
from dumprx.utils.logging import setup_logging
from dumprx.core.config import Config
from dumprx.core.dumper import FirmwareDumper
from dumprx.extractors.manufacturer_detector import ManufacturerDetector
from dumprx.extractors.enhanced_boot_analyzer import EnhancedBootAnalyzer
from dumprx.downloaders.enhanced_downloader import EnhancedDownloader

console = Console()


@click.group(invoke_without_command=True)
@click.argument('firmware_path', required=False)
@click.option('--verbose', '-v', is_flag=True, help='🔊 Enable verbose output')
@click.option('--config-dir', type=click.Path(), help='📁 Custom configuration directory')
@click.option('--dumper-version', type=click.Choice(['v2', 'legacy']), default='v2', help='🔧 Choose dumper version')
@click.option('--debug', is_flag=True, help='🐛 Enable debug mode')
@click.option('--telegram-bot', is_flag=True, help='🤖 Start Telegram bot')
@click.version_option(version='2.0.0', prog_name='DumprX')
@click.pass_context
def cli(ctx, firmware_path, verbose, config_dir, dumper_version, debug, telegram_bot):
    """
    🚀 DumprX v2.0 - Advanced Firmware Extraction Toolkit
    
    ✨ Enhanced with 12+ manufacturer support, intelligent auto-detection,
    beautiful CLI interface, and advanced Telegram bot integration.
    
    FIRMWARE_PATH can be:
    📦 A firmware file (.zip, .rar, .7z, .ozip, .kdz, etc.)
    📁 An extracted firmware folder  
    🔗 A supported website link (mega.nz, mediafire, gdrive, etc.)
    """
    
    # If no command and no firmware path, show help
    if ctx.invoked_subcommand is None:
        if not firmware_path and not telegram_bot:
            # Clear screen and show interactive interface
            console.clear()
            show_enhanced_banner()
            time.sleep(0.5)
            
            if not firmware_path:
                firmware_path = show_interactive_prompt()
                if not firmware_path:
                    sys.exit(0)
        
        # Start Telegram bot if requested
        if telegram_bot:
            return start_telegram_bot(config_dir, verbose)
        
        # Process firmware
        if firmware_path:
            return process_firmware_enhanced(firmware_path, verbose, config_dir, dumper_version, debug)


@cli.command()
@click.argument('firmware_path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config-dir', type=click.Path(), help='Custom configuration directory')
@click.option('--dumper-version', type=click.Choice(['v2', 'legacy']), default='v2', help='Choose dumper version')
def extract(firmware_path, verbose, config_dir, dumper_version):
    """📦 Extract firmware with enhanced v2.0 features"""
    process_firmware_enhanced(firmware_path, verbose, config_dir, dumper_version, False)


@cli.command()
@click.argument('firmware_path')
@click.option('--config-dir', type=click.Path(), help='Custom configuration directory')
def detect(firmware_path, config_dir):
    """🔍 Detect manufacturer and device information"""
    
    console.clear()
    show_enhanced_banner()
    
    try:
        # Setup configuration
        project_dir = Path(config_dir) if config_dir else None
        config = Config(project_dir)
        
        # Initialize detector
        detector = ManufacturerDetector(config)
        firmware_path_obj = Path(firmware_path)
        
        with console.status("[cyan]🔍 Analyzing firmware..."):
            manufacturer_info = detector.detect_manufacturer(firmware_path_obj)
        
        if manufacturer_info:
            show_manufacturer_info(manufacturer_info)
        else:
            print_warning("Could not detect manufacturer information")
            
    except Exception as e:
        print_error(f"Detection failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('boot_image_path')
@click.option('--config-dir', type=click.Path(), help='Custom configuration directory')
def analyze_boot(boot_image_path, config_dir):
    """🥾 Analyze boot images with enhanced features"""
    
    console.clear()
    show_enhanced_banner()
    
    try:
        # Setup configuration
        project_dir = Path(config_dir) if config_dir else None
        config = Config(project_dir)
        
        # Initialize analyzer
        analyzer = EnhancedBootAnalyzer(config)
        boot_path = Path(boot_image_path)
        
        with console.status("[cyan]🔍 Analyzing boot images..."):
            if boot_path.is_file():
                # Analyze single boot image
                results = {boot_path.name: analyzer.analyze_boot_images(boot_path.parent)}
            else:
                # Analyze all boot images in directory
                results = analyzer.analyze_boot_images(boot_path)
        
        show_boot_analysis_results(results)
            
    except Exception as e:
        print_error(f"Boot analysis failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('firmware_url')
@click.option('--output', '-o', help='Output filename')
@click.option('--config-dir', type=click.Path(), help='Custom configuration directory')
def download(firmware_url, output, config_dir):
    """🌐 Download firmware from supported services"""
    
    console.clear()
    show_enhanced_banner()
    
    try:
        # Setup configuration
        project_dir = Path(config_dir) if config_dir else None
        config = Config(project_dir)
        
        # Initialize downloader
        downloader = EnhancedDownloader(config)
        
        # Get download info
        with console.status("[cyan]🔍 Analyzing download URL..."):
            info = downloader.get_download_info(firmware_url)
        
        show_download_info(info)
        
        if Confirm.ask("🚀 Start download?"):
            # Download with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Downloading...", total=100)
                
                def progress_callback(percent, downloaded, total):
                    progress.update(task, completed=percent, description=f"Downloading {info.filename}")
                
                result = downloader.download(firmware_url, output, progress_callback)
                
                if result:
                    print_success(f"Downloaded: {result}")
                else:
                    print_error("Download failed!")
                    sys.exit(1)
            
    except Exception as e:
        print_error(f"Download failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--config-dir', type=click.Path(), help='Custom configuration directory')
def telegram_bot(config_dir):
    """🤖 Start Telegram bot for automated extractions"""
    start_telegram_bot(config_dir, False)


@cli.command()
def info():
    """ℹ️ Show DumprX information and capabilities"""
    
    console.clear()
    show_enhanced_banner()
    
    # Create information panels
    panels = []
    
    # Supported manufacturers
    manufacturers_table = Table(title="🏭 Supported Manufacturers", show_header=True)
    manufacturers_table.add_column("Manufacturer", style="cyan")
    manufacturers_table.add_column("Formats", style="green")
    manufacturers_table.add_column("Features", style="yellow")
    
    manufacturers = [
        ("Samsung", "TAR.MD5, PIT", "Multi-partition support"),
        ("Xiaomi", "MIUI, Fastboot", "Global/China ROMs"),
        ("OPPO/OnePlus", "OZIP, OFP, OPS", "Decryption support"),
        ("Huawei", "UPDATE.APP", "HiSilicon support"),
        ("LG", "KDZ, DZ, TOT", "Latest firmware support"),
        ("HTC", "RUU", "Decryption tools"),
        ("Sony", "FTF, SIN", "Xperia support"),
        ("Motorola", "XML.ZIP", "Service files"),
        ("ASUS", "ZIP, RAW", "ZenFone/ROG"),
        ("Realme", "OZIP", "ColorOS support"),
        ("Vivo", "ZIP, QSB", "Funtouch OS"),
        ("Generic", "Various", "OTA, Fastboot, Super")
    ]
    
    for mfg, formats, features in manufacturers:
        manufacturers_table.add_row(mfg, formats, features)
    
    panels.append(Panel(manufacturers_table, border_style="blue"))
    
    # Download services
    services_table = Table(title="🌐 Download Services", show_header=True)
    services_table.add_column("Service", style="cyan")
    services_table.add_column("Features", style="green")
    
    services = [
        ("Direct HTTP/HTTPS", "Resume support, headers"),
        ("Mega.nz", "Official client integration"),
        ("Google Drive", "Direct download links"),
        ("OneDrive", "Share link conversion"),
        ("Dropbox", "Direct download support"),
        ("MediaFire", "Page parsing, direct links"),
        ("AndroidFileHost", "API integration"),
        ("GitHub/GitLab", "Release downloads")
    ]
    
    for service, features in services:
        services_table.add_row(service, features)
    
    panels.append(Panel(services_table, border_style="green"))
    
    # Boot analysis features
    boot_table = Table(title="🥾 Boot Analysis Features", show_header=True)
    boot_table.add_column("Feature", style="cyan")
    boot_table.add_column("Support", style="green")
    
    boot_features = [
        ("Multi-boot images", "boot, vendor_boot, init_boot, recovery"),
        ("Ramdisk versions", "v2, v3, v4 detection"),
        ("Compression", "gzip, LZ4, XZ, LZMA, Zstandard"),
        ("DTB extraction", "Device tree blob analysis"),
        ("Kernel analysis", "Version, config, ELF generation"),
        ("Architecture", "ARM, ARM64, x86, x86_64, MIPS")
    ]
    
    for feature, support in boot_features:
        boot_table.add_row(feature, support)
    
    panels.append(Panel(boot_table, border_style="yellow"))
    
    # Display panels
    for panel in panels:
        console.print(panel)
        console.print()


def show_enhanced_banner():
    """Show enhanced banner with version 2.0 branding"""
    
    banner_text = """
[bold cyan]
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║    ██████╗ ██╗   ██╗███╗   ███╗██████╗ ██████╗ ██╗  ██╗    ██╗   ██╗██████╗  ║
║    ██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔══██╗╚██╗██╔╝    ██║   ██║╚════██╗ ║
║    ██║  ██║██║   ██║██╔████╔██║██████╔╝██████╔╝ ╚███╔╝     ██║   ██║ █████╔╝ ║
║    ██║  ██║██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══██╗ ██╔██╗     ╚██╗ ██╔╝██╔═══╝  ║
║    ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║     ██║  ██║██╔╝ ██╗     ╚████╔╝ ███████╗ ║
║    ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝      ╚═══╝  ╚══════╝ ║
║                                                                               ║
║                   🚀 Advanced Firmware Extraction Toolkit                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
[/bold cyan]

[bold green]✨ Version 2.0 - Now with Enhanced Features:[/bold green]

[yellow]🏭 12+ Manufacturer Support[/yellow] • [blue]🥾 Enhanced Boot Analysis[/blue] • [magenta]🌐 8 Download Services[/magenta]
[cyan]🤖 Telegram Bot Integration[/cyan] • [green]🎨 Beautiful CLI Interface[/green] • [red]⚡ Dual Dumper Support[/red]

"""
    
    console.print(banner_text)


def show_interactive_prompt():
    """Show interactive prompt for firmware input"""
    
    console.print(Panel.fit(
        "[bold cyan]Welcome to DumprX v2.0![/bold cyan]\n\n"
        "Please provide a firmware file, folder, or download URL:",
        title="🚀 Interactive Mode",
        border_style="blue"
    ))
    
    firmware_input = Prompt.ask(
        "\n[bold]Enter firmware path or URL[/bold]",
        default="",
        show_default=False
    )
    
    return firmware_input.strip() if firmware_input else None


def show_manufacturer_info(manufacturer_info):
    """Display manufacturer detection results"""
    
    table = Table(title="🔍 Manufacturer Detection Results", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Manufacturer", manufacturer_info.name.title())
    table.add_row("Model", manufacturer_info.model or "Unknown")
    table.add_row("Android Version", manufacturer_info.android_version or "Unknown")
    table.add_row("Build ID", manufacturer_info.build_id or "Unknown")
    table.add_row("Firmware Type", manufacturer_info.firmware_type or "Unknown")
    table.add_row("Extraction Method", manufacturer_info.extraction_method or "Unknown")
    
    console.print(Panel(table, border_style="green"))


def show_download_info(info):
    """Display download information"""
    
    table = Table(title="🌐 Download Information", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Service", info.service.value.replace('_', ' ').title())
    table.add_row("Filename", info.filename or "Unknown")
    table.add_row("File Size", f"{info.filesize / (1024*1024):.1f} MB" if info.filesize > 0 else "Unknown")
    table.add_row("Resume Support", "✅ Yes" if info.resume_supported else "❌ No")
    table.add_row("Auth Required", "⚠️ Yes" if info.auth_required else "✅ No")
    
    console.print(Panel(table, border_style="blue"))


def show_boot_analysis_results(results):
    """Display boot analysis results"""
    
    for image_name, analysis in results.items():
        if 'error' in analysis:
            print_error(f"Failed to analyze {image_name}: {analysis['error']}")
            continue
        
        boot_info = analysis.get('boot_info')
        if not boot_info:
            continue
        
        table = Table(title=f"🥾 Boot Analysis: {image_name}", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Image Type", boot_info.image_type.value)
        table.add_row("Ramdisk Version", boot_info.ramdisk_version.value)
        table.add_row("Compression", boot_info.compression.value)
        table.add_row("Kernel Size", f"{boot_info.kernel_size / 1024:.1f} KB")
        table.add_row("Ramdisk Size", f"{boot_info.ramdisk_size / 1024:.1f} KB")
        table.add_row("Header Version", str(boot_info.header_version))
        table.add_row("OS Version", boot_info.os_version or "Unknown")
        table.add_row("Product Name", boot_info.product_name or "Unknown")
        
        console.print(Panel(table, border_style="yellow"))
        
        # Show kernel info if available
        kernel_info = analysis.get('kernel_info')
        if kernel_info and kernel_info.version:
            kernel_table = Table(title="🐧 Kernel Information", show_header=True)
            kernel_table.add_column("Property", style="cyan")
            kernel_table.add_column("Value", style="green")
            
            kernel_table.add_row("Version", kernel_info.version)
            kernel_table.add_row("Architecture", kernel_info.architecture)
            kernel_table.add_row("Config Extracted", "✅ Yes" if kernel_info.config_extracted else "❌ No")
            kernel_table.add_row("ELF Generated", "✅ Yes" if kernel_info.elf_generated else "❌ No")
            
            console.print(Panel(kernel_table, border_style="green"))


def process_firmware_enhanced(firmware_path, verbose, config_dir, dumper_version, debug):
    """Process firmware with enhanced v2.0 features"""
    
    console.clear()
    show_enhanced_banner()
    time.sleep(0.5)
    
    # Validate input
    if not firmware_path or firmware_path.strip() == "":
        print_error("No firmware path provided")
        show_usage()
        sys.exit(1)
    
    try:
        # Setup configuration
        project_dir = Path(config_dir) if config_dir else None
        config = Config(project_dir)
        config.validate_project_dir()
        
        # Setup logging
        logger = setup_logging(verbose or debug)
        
        # Show dumper version selection
        dumper_emoji = "⚡" if dumper_version == "v2" else "🔧"
        print_info(f"{dumper_emoji} Using DumprX {dumper_version.upper()} dumper")
        
        # Initialize components
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Initialization phase
            init_task = progress.add_task("🚀 Initializing DumprX v2.0...", total=100)
            
            # Setup dumper
            progress.update(init_task, advance=25, description="🔧 Setting up dumper...")
            dumper = FirmwareDumper(config)
            dumper.setup()
            
            # Initialize manufacturer detector
            progress.update(init_task, advance=25, description="🔍 Loading manufacturer detector...")
            manufacturer_detector = ManufacturerDetector(config)
            
            # Initialize enhanced downloader
            progress.update(init_task, advance=25, description="🌐 Setting up downloader...")
            downloader = EnhancedDownloader(config)
            
            progress.update(init_task, advance=25, description="✅ Initialization complete!")
            
            # Detection phase
            detect_task = progress.add_task("🔍 Analyzing firmware...", total=100)
            
            firmware_path_obj = Path(firmware_path)
            
            # Detect if it's a URL
            if firmware_path.startswith(('http://', 'https://')):
                progress.update(detect_task, advance=50, description="🌐 Detected download URL...")
                
                # Get download info
                download_info = downloader.get_download_info(firmware_path)
                progress.update(detect_task, advance=50, description=f"📦 Service: {download_info.service.value}")
                
                # Download with progress
                download_task = progress.add_task("📥 Downloading firmware...", total=100)
                
                def download_progress(percent, downloaded, total):
                    progress.update(download_task, completed=percent)
                
                firmware_path_obj = downloader.download(firmware_path, progress_callback=download_progress)
                
                if not firmware_path_obj:
                    print_error("Download failed!")
                    sys.exit(1)
                
                progress.update(download_task, completed=100, description="✅ Download complete!")
            
            else:
                progress.update(detect_task, advance=100, description="📁 Local file/folder detected")
            
            # Manufacturer detection
            manufacturer_task = progress.add_task("🏭 Detecting manufacturer...", total=100)
            
            manufacturer_info = manufacturer_detector.detect_manufacturer(firmware_path_obj)
            
            if manufacturer_info:
                progress.update(manufacturer_task, advance=100, 
                              description=f"✅ Detected: {manufacturer_info.name.title()}")
                
                # Show manufacturer info panel
                console.print()
                show_manufacturer_info(manufacturer_info)
                console.print()
            else:
                progress.update(manufacturer_task, advance=100, description="⚠️ Unknown manufacturer")
            
            # Processing phase
            process_task = progress.add_task("⚙️ Processing firmware...", total=100)
            
            # Use appropriate dumper based on version
            if dumper_version == "v2":
                result = dumper.process_firmware_v2(str(firmware_path_obj), manufacturer_info)
            else:
                result = dumper.process_firmware(str(firmware_path_obj))
            
            progress.update(process_task, advance=100, description="✅ Processing complete!")
        
        # Show results
        if result:
            console.print()
            print_success("🎉 Firmware extraction completed successfully!")
            
            # Show summary
            show_extraction_summary(firmware_path_obj, manufacturer_info, result)
        else:
            print_error("❌ Firmware extraction failed!")
            sys.exit(1)
            
    except ValueError as e:
        print_error(f"Configuration error: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        print_warning("⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error occurred") if 'logger' in locals() else None
        print_error(f"❌ Unexpected error: {str(e)}")
        if debug:
            console.print_exception()
        sys.exit(1)


def show_extraction_summary(firmware_path, manufacturer_info, result):
    """Show extraction summary"""
    
    summary_table = Table(title="📊 Extraction Summary", show_header=True)
    summary_table.add_column("Property", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Source File", str(firmware_path.name))
    summary_table.add_row("File Size", f"{firmware_path.stat().st_size / (1024*1024):.1f} MB" if firmware_path.exists() else "Unknown")
    
    if manufacturer_info:
        summary_table.add_row("Manufacturer", manufacturer_info.name.title())
        summary_table.add_row("Model", manufacturer_info.model or "Unknown")
        summary_table.add_row("Extraction Method", manufacturer_info.extraction_method)
    
    summary_table.add_row("Status", "✅ Success" if result else "❌ Failed")
    summary_table.add_row("Output Directory", str(result.get('output_dir', 'Unknown')) if isinstance(result, dict) else "Check work directory")
    
    console.print(Panel(summary_table, border_style="green"))


def start_telegram_bot(config_dir, verbose):
    """Start Telegram bot"""
    
    console.clear()
    show_enhanced_banner()
    
    try:
        # Setup configuration
        project_dir = Path(config_dir) if config_dir else None
        config = Config(project_dir)
        
        # Setup logging
        logger = setup_logging(verbose)
        
        print_info("🤖 Starting Telegram bot...")
        
        # Import and start bot
        from dumprx.integrations.telegram_bot import run_telegram_bot
        dumper = FirmwareDumper(config)
        
        # Run bot
        asyncio.run(run_telegram_bot(config, dumper))
        
    except ImportError:
        print_error("❌ Telegram bot dependencies not installed")
        print_info("📦 Install with: pip install python-telegram-bot")
        sys.exit(1)
    except Exception as e:
        print_error(f"❌ Failed to start Telegram bot: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()