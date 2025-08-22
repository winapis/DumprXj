#!/usr/bin/env python3
"""
DumprX v2.0 - Advanced Firmware Extraction Toolkit
Main entry point with CLI interface
"""

import sys
import click
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dumprx import DumprX, logger, config


@click.command()
@click.argument('input_path')
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.version_option(version='2.0.0')
def main(input_path: str, output: str, verbose: bool, debug: bool):
    """
    DumprX - Advanced Firmware Extraction Toolkit
    
    Extract firmware from various manufacturers with intelligent auto-detection.
    
    INPUT_PATH: Path to firmware file, directory, or download URL
    """
    
    # Set logging level
    if debug:
        import logging
        logger.logger.setLevel(logging.DEBUG)
    elif verbose:
        import logging
        logger.logger.setLevel(logging.INFO)
    
    # Validate input
    input_path_obj = Path(input_path)
    
    # Handle URL inputs
    if input_path.startswith(('http://', 'https://', 'ftp://')):
        # URL input - will be handled by download manager
        input_path_obj = input_path
    elif not input_path_obj.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)
    
    # Setup output directory
    output_dir = Path(output) if output else config.output_dir
    
    # Show usage information
    _show_usage()
    
    # Create and run dumper
    try:
        dumper = DumprX(input_path_obj, output_dir)
        success = dumper.extract()
        
        if success:
            logger.success("🎉 Extraction completed successfully!")
            sys.exit(0)
        else:
            logger.error("💥 Extraction failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Extraction cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _show_usage():
    """Display usage information"""
    logger.section("📋 Usage Information", "📋")
    
    logger.info("🎯 Supported Input Types:")
    logger.info("  • Firmware files: .zip, .rar, .7z, .tar, .tar.md5, .ozip, .ofp, .ops, .kdz, .dz")
    logger.info("  • RUU files: ruu_*.exe")
    logger.info("  • System images: system.img, boot.img, recovery.img, super.img")
    logger.info("  • Special formats: UPDATE.APP, payload.bin, *.pac, *.sin, *.ftf")
    logger.info("  • Download URLs: Mega.nz, Google Drive, MediaFire, AndroidFileHost")
    
    logger.info("\n📱 Supported Manufacturers:")
    manufacturers = [
        "Samsung (TAR.MD5, PIT files)",
        "Xiaomi (MIUI packages, Fastboot images)", 
        "OPPO/OnePlus (OZIP, OFP, OPS decryption)",
        "Huawei (UPDATE.APP packages)",
        "LG (KDZ/DZ extraction)",
        "HTC (RUU decryption)",
        "Sony (FTF/SIN processing)",
        "Generic Android images"
    ]
    
    for manufacturer in manufacturers:
        logger.info(f"  • {manufacturer}")
    
    logger.info("\n🚀 Enhanced Features:")
    logger.info("  • Multi-boot support: boot.img, vendor_boot.img, init_boot.img")
    logger.info("  • Compression support: gzip, LZ4, XZ, LZMA, Zstandard")
    logger.info("  • DTB extraction and DTS conversion")
    logger.info("  • Kernel analysis and config extraction")
    logger.info("  • Download resume support")
    
    print()  # Extra spacing


if __name__ == '__main__':
    main()