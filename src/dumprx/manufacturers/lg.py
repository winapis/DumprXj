"""
LG firmware extractor (KDZ/DZ extraction)
"""

from pathlib import Path
from .base import BaseExtractor


class LGExtractor(BaseExtractor):
    """LG firmware extractor for KDZ and DZ files"""
    
    def extract(self, file_path: Path, output_dir: Path) -> bool:
        """Extract LG firmware"""
        self.logger.info("🔄 Extracting LG firmware...")
        
        filename = file_path.name.lower()
        
        if filename.endswith('.kdz'):
            return self._extract_with_python_script(
                "kdz_extract", file_path, output_dir, "-x"
            )
        elif filename.endswith('.dz'):
            return self._extract_with_python_script(
                "dz_extract", file_path, output_dir, "-f"
            )
        else:
            return self._extract_with_7zz(file_path, output_dir)