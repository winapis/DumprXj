import asyncio
from pathlib import Path
from typing import List, Dict, Any
from lib.core.logger import logger
from lib.core.config import config
from lib.core.exceptions import ExtractionError
from lib.utils.filesystem import ensure_dir
from .detector import FirmwareDetector
from .extractors import (
    ArchiveExtractor, PayloadExtractor, KDZExtractor,
    OZipExtractor, SDATextractor, HuaweiExtractor,
    SuperImageExtractor
)

class ExtractionManager:
    def __init__(self):
        self.detector = FirmwareDetector()
        self.utils_dir = Path(config.get('paths.utils_dir'))
        
        self.extractors = [
            ArchiveExtractor(self.utils_dir),
            PayloadExtractor(self.utils_dir),
            KDZExtractor(self.utils_dir),
            OZipExtractor(self.utils_dir),
            SDATextractor(self.utils_dir),
            HuaweiExtractor(self.utils_dir),
            SuperImageExtractor(self.utils_dir)
        ]
    
    async def extract(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        ensure_dir(output_path)
        
        logger.processing(f"Analyzing firmware: {input_path}")
        
        if input_path.is_file():
            return await self._extract_single_file(input_path, output_path)
        elif input_path.is_dir():
            return await self._extract_directory(input_path, output_path)
        else:
            raise ExtractionError(f"Invalid input path: {input_path}")
    
    async def _extract_single_file(self, file_path: Path, output_path: Path) -> Dict[str, Any]:
        firmware_type = self.detector.detect_type(file_path)
        
        if not firmware_type:
            raise ExtractionError(f"Unsupported firmware type: {file_path}")
        
        logger.info(f"Detected firmware type: {firmware_type}")
        
        extractor = self._get_extractor(file_path)
        if not extractor:
            raise ExtractionError(f"No suitable extractor found for {file_path}")
        
        temp_extract_dir = output_path / "extracted"
        ensure_dir(temp_extract_dir)
        
        success = await extractor.extract(file_path, temp_extract_dir)
        
        if success:
            await self._process_extracted_content(temp_extract_dir, output_path)
        
        return {
            'input': str(file_path),
            'output': str(output_path),
            'type': firmware_type,
            'success': success
        }
    
    async def _extract_directory(self, directory: Path, output_path: Path) -> Dict[str, Any]:
        found_firmware = self.detector.analyze_directory(directory)
        
        if not found_firmware:
            logger.warning(f"No recognized firmware files found in {directory}")
            return {'success': False, 'reason': 'No firmware files found'}
        
        results = []
        for firmware_info in found_firmware:
            logger.processing(f"Processing {firmware_info['path'].name}")
            
            extractor = self._get_extractor(firmware_info['path'])
            if extractor:
                temp_dir = output_path / f"extracted_{firmware_info['path'].stem}"
                ensure_dir(temp_dir)
                
                try:
                    success = await extractor.extract(firmware_info['path'], temp_dir)
                    if success:
                        await self._process_extracted_content(temp_dir, output_path)
                    results.append({'file': str(firmware_info['path']), 'success': success})
                except Exception as e:
                    logger.error(f"Failed to extract {firmware_info['path']}: {e}")
                    results.append({'file': str(firmware_info['path']), 'success': False, 'error': str(e)})
        
        return {'results': results, 'success': any(r['success'] for r in results)}
    
    def _get_extractor(self, file_path: Path):
        for extractor in self.extractors:
            if extractor.can_handle(file_path):
                return extractor
        return None
    
    async def _process_extracted_content(self, temp_dir: Path, final_output: Path) -> None:
        await self._extract_partitions(temp_dir, final_output)
        await self._organize_output(temp_dir, final_output)
    
    async def _extract_partitions(self, source_dir: Path, output_dir: Path) -> None:
        partitions = config.get('extraction.partitions', [])
        
        for partition in partitions:
            partition_files = list(source_dir.glob(f"**/*{partition}*.img"))
            
            for partition_file in partition_files:
                logger.processing(f"Extracting partition: {partition}")
                
                partition_output = output_dir / partition
                ensure_dir(partition_output)
                
                await self._extract_partition_image(partition_file, partition_output)
    
    async def _extract_partition_image(self, img_file: Path, output_dir: Path) -> None:
        from lib.utils.command import run_command
        
        bin_7zz = self.utils_dir / "bin" / "7zz"
        if not bin_7zz.exists():
            bin_7zz = "7zz"
        
        cmd = [str(bin_7zz), "x", "-snld", str(img_file), "-y", f"-o{output_dir}"]
        result = await run_command(cmd)
        
        if result.returncode != 0:
            fsck_erofs = self.utils_dir / "bin" / "fsck.erofs"
            if fsck_erofs.exists():
                logger.processing("Trying EROFS extraction")
                cmd = [str(fsck_erofs), f"--extract={output_dir}", str(img_file)]
                result = await run_command(cmd)
                
                if result.returncode != 0:
                    logger.warning(f"Could not extract {img_file}")
            else:
                logger.warning(f"Could not extract {img_file} with 7z")
        else:
            img_file.unlink()
    
    async def _organize_output(self, temp_dir: Path, output_dir: Path) -> None:
        for item in temp_dir.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(temp_dir)
                dest_path = output_dir / relative_path
                ensure_dir(dest_path.parent)
                
                if not dest_path.exists():
                    item.rename(dest_path)