"""
Generic firmware extractor for unknown formats
"""

from pathlib import Path
from .base import BaseExtractor


class GenericExtractor(BaseExtractor):
    """Generic firmware extractor for unknown formats"""
    
    def extract(self, file_path: Path, output_dir: Path) -> bool:
        """Extract using generic methods"""
        self.logger.info("🔄 Using generic extraction...")
        
        # Try 7zz first
        if self._extract_with_7zz(file_path, output_dir):
            return True
        
        # If it's a directory, just copy contents
        if file_path.is_dir():
            import shutil
            for item in file_path.iterdir():
                if item.is_file():
                    shutil.copy2(item, output_dir)
                elif item.is_dir():
                    shutil.copytree(item, output_dir / item.name, dirs_exist_ok=True)
            return True
        
        return False