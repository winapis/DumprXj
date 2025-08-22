"""
Main CLI interface for DumprX
"""

import sys
import click
from pathlib import Path
from typing import Optional

from dumprx.core.config import Config
from dumprx.core.dumper import FirmwareDumper
from dumprx.utils.console import DumprXConsole
from dumprx import __version__


@click.group(invoke_without_command=True)
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose output')
@click.option('--no-colors', is_flag=True, 
              help='Disable colored output')
@click.option('--no-emoji', is_flag=True, 
              help='Disable emoji in output')
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool, 
        no_colors: bool, no_emoji: bool) -> None:
    """DumprX - Advanced firmware dumper and extractor toolkit"""
    
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)
    
    # Load configuration
    try:
        ctx.obj['config'] = Config(config)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)
        
    # Override console settings from CLI options
    if no_colors:
        ctx.obj['config'].console.colors = False
    if no_emoji:
        ctx.obj['config'].console.emoji = False
    if verbose:
        ctx.obj['config'].logging.level = "DEBUG"
        
    # Initialize console
    ctx.obj['console'] = DumprXConsole(
        colors=ctx.obj['config'].console.colors,
        emoji=ctx.obj['config'].console.emoji
    )
    
    # If no command is given, show usage
    if ctx.invoked_subcommand is None:
        if ctx.obj['config'].console.banner:
            ctx.obj['console'].print_banner()
        ctx.obj['console'].print_usage()


@cli.command()
@click.argument('source', type=str)
@click.option('--output', '-o', type=click.Path(), 
              help='Output directory (default: from config)')
@click.option('--force', '-f', is_flag=True, 
              help='Force extraction even if output exists')
@click.option('--no-cleanup', is_flag=True, 
              help='Do not cleanup temporary files')
@click.pass_context
def dump(ctx: click.Context, source: str, output: Optional[str], 
         force: bool, no_cleanup: bool) -> None:
    """Extract firmware from file or URL"""
    
    config = ctx.obj['config']
    console = ctx.obj['console']
    
    try:
        # Initialize dumper
        dumper = FirmwareDumper(config, console)
        
        # Set output directory if provided
        if output:
            config.directories.output = output
            
        # Ensure directories exist
        config.ensure_directories()
        
        # Run extraction
        result = dumper.dump_firmware(
            source=source,
            force=force,
            cleanup=not no_cleanup
        )
        
        if result:
            console.success("Firmware extraction completed successfully!")
        else:
            console.error("Firmware extraction failed!")
            sys.exit(1)
            
    except Exception as e:
        console.error(f"Error during firmware extraction: {e}")
        if config.logging.level == "DEBUG":
            import traceback
            console.debug(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument('url', type=str)
@click.option('--output', '-o', type=click.Path(), 
              help='Output file/directory (default: from config)')
@click.pass_context
def download(ctx: click.Context, url: str, output: Optional[str]) -> None:
    """Download firmware from supported sources"""
    
    config = ctx.obj['config']
    console = ctx.obj['console']
    
    try:
        # Initialize dumper
        dumper = FirmwareDumper(config, console)
        
        # Set output directory if provided
        if output:
            config.directories.input = output
            
        # Ensure directories exist
        config.ensure_directories()
        
        # Download firmware
        result = dumper.download_firmware(url)
        
        if result:
            console.success(f"Download completed: {result}")
        else:
            console.error("Download failed!")
            sys.exit(1)
            
    except Exception as e:
        console.error(f"Error during download: {e}")
        if config.logging.level == "DEBUG":
            import traceback
            console.debug(traceback.format_exc())
        sys.exit(1)


@cli.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Manage configuration settings"""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Show current configuration"""
    
    config_obj = ctx.obj['config']
    console = ctx.obj['console']
    
    table = console.create_table("Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # Add configuration values to table
    table.add_row("Project Directory", str(config_obj.project_dir))
    table.add_row("Config File", str(config_obj.config_path))
    table.add_row("Input Directory", str(config_obj.get_input_dir()))
    table.add_row("Output Directory", str(config_obj.get_output_dir()))
    table.add_row("Utils Directory", str(config_obj.get_utils_dir()))
    table.add_row("Temp Directory", str(config_obj.get_temp_dir()))
    
    if config_obj.git.github.token:
        table.add_row("GitHub Token", "Configured ✓")
    if config_obj.git.gitlab.token:
        table.add_row("GitLab Token", "Configured ✓")
    if config_obj.telegram.token:
        table.add_row("Telegram Token", "Configured ✓")
        
    console.console.print(table)


@config.command('init')
@click.pass_context
def config_init(ctx: click.Context) -> None:
    """Initialize configuration file"""
    
    config_obj = ctx.obj['config']
    console = ctx.obj['console']
    
    try:
        config_obj.create_default_config()
        console.success(f"Configuration file created: {config_obj.config_path}")
    except Exception as e:
        console.error(f"Failed to create configuration file: {e}")
        sys.exit(1)


@cli.command()
@click.option('--force', '-f', is_flag=True, 
              help='Force reinstall of dependencies')
@click.pass_context
def setup(ctx: click.Context, force: bool) -> None:
    """Setup dependencies and tools"""
    
    config = ctx.obj['config']
    console = ctx.obj['console']
    
    try:
        # Initialize dumper for setup operations
        dumper = FirmwareDumper(config, console)
        
        # Run setup
        result = dumper.setup_dependencies(force=force)
        
        if result:
            console.success("Setup completed successfully!")
        else:
            console.error("Setup failed!")
            sys.exit(1)
            
    except Exception as e:
        console.error(f"Error during setup: {e}")
        if config.logging.level == "DEBUG":
            import traceback
            console.debug(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.pass_context
def test(ctx: click.Context) -> None:
    """Test integrations (git, telegram)"""
    
    config = ctx.obj['config']
    console = ctx.obj['console']
    
    try:
        console.step("Testing integrations...")
        
        # Test Telegram if configured
        if config.telegram.token:
            console.step("Testing Telegram bot connection...")
            from dumprx.utils.telegram_bot import TelegramBot
            telegram_bot = TelegramBot(config, console)
            
            if telegram_bot.test_connection():
                console.success("Telegram bot test passed")
                
                # Send test message
                telegram_bot.send_status_update("Testing", {
                    "message": "DumprX integration test",
                    "version": "2.0.0"
                })
            else:
                console.error("Telegram bot test failed")
        else:
            console.warning("Telegram not configured - skipping test")
            
        # Test Git credentials
        if config.git.github.token:
            console.step("Testing GitHub credentials...")
            from dumprx.utils.git_integration import GitIntegration
            git_integration = GitIntegration(config, console)
            
            # Test by getting username
            username = git_integration._get_github_username()
            console.success(f"GitHub credentials valid for user: {username}")
            
        elif config.git.gitlab.token:
            console.step("Testing GitLab credentials...")
            console.success("GitLab credentials configured")
        else:
            console.warning("No git credentials configured - skipping test")
            
        console.success("Integration tests completed!")
        
    except Exception as e:
        console.error(f"Error during integration tests: {e}")
        if config.logging.level == "DEBUG":
            import traceback
            console.debug(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Show version information"""
    
    console = ctx.obj['console']
    
    version_info = f"""
[bold green]DumprX[/bold green] [cyan]v{__version__}[/cyan]

Advanced firmware dumper and extractor toolkit
Repository: https://github.com/Eduardob3677/DumprX

Python: {sys.version.split()[0]}
Platform: {sys.platform}
    """
    
    console.console.print(version_info.strip())


def main() -> None:
    """Main entry point for the CLI"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()