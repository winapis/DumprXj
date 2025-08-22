"""
Huawei firmware extractor (UPDATE.APP packages)
"""

from pathlib import Path
from .base import BaseExtractor


class HuaweiExtractor(BaseExtractor):
    """Huawei firmware extractor for UPDATE.APP packages"""
    
    def extract(self, file_path: Path, output_dir: Path) -> bool:
        """Extract Huawei firmware"""
        self.logger.info("🔄 Extracting Huawei UPDATE.APP...")
        
        return self._extract_with_python_script(
            "splituapp", file_path, output_dir
        )