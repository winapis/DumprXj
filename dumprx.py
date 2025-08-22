import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional
from lib.core.logger import logger
from lib.core.config import config
from lib.core.exceptions import DumprXException
from lib.extractors.manager import ExtractionManager
from lib.downloaders.manager import DownloadManager
from lib.utils.filesystem import is_url, ensure_dir

class CLI:
    def __init__(self):
        self.banner = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
        """
    
    def show_banner(self) -> None:
        print(f"\033[32m{self.banner}\033[0m")
        print("\033[36mModern Firmware Dumping Toolkit\033[0m\n")
    
    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="DumprX - Modern Firmware Dumping Toolkit",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument(
            'input',
            nargs='?',
            help='Firmware file path or URL'
        )
        
        parser.add_argument(
            '--output', '-o',
            type=str,
            default='out',
            help='Output directory (default: out)'
        )
        
        parser.add_argument(
            '--config', '-c',
            type=str,
            default='config.yaml',
            help='Configuration file path (default: config.yaml)'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        
        parser.add_argument(
            '--no-upload',
            action='store_true',
            help='Skip uploading to git repository'
        )
        
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate workflow components'
        )
        
        return parser
    
    async def validate_workflow(self) -> int:
        from lib.core.validator import WorkflowValidator
        
        validator = WorkflowValidator()
        return await validator.validate_all()
    
    async def process_firmware(self, args) -> int:
        try:
            ensure_dir(args.output)
            
            input_path = Path(args.input)
            
            if is_url(args.input):
                logger.processing("Downloading firmware from URL")
                async with DownloadManager() as dm:
                    input_dir = ensure_dir(config.get('paths.input_dir'))
                    input_path = await dm.download(args.input, input_dir / "firmware")
            
            elif not input_path.exists():
                logger.error(f"Input file/directory does not exist: {args.input}")
                return 1
            
            extraction_manager = ExtractionManager()
            result = await extraction_manager.extract(input_path, Path(args.output))
            
            if not args.no_upload:
                from lib.git.manager import GitManager
                git_manager = GitManager()
                await git_manager.upload_results(Path(args.output))
            
            logger.success("Firmware processing completed successfully")
            return 0
            
        except DumprXException as e:
            logger.error(str(e))
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return 1
    
    async def run(self, args: list = None) -> int:
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        config.config_path = parsed_args.config
        config.load()
        
        if parsed_args.verbose:
            config.set('logging.level', 'DEBUG')
        
        self.show_banner()
        
        if parsed_args.validate:
            return await self.validate_workflow()
        
        if not parsed_args.input:
            parser.error("Input is required unless using --validate")
        
        return await self.process_firmware(parsed_args)

async def main():
    cli = CLI()
    return await cli.run()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)