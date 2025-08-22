"""
Sony firmware extractor (FTF/SIN processing)
"""

from pathlib import Path
from .base import BaseExtractor


class SonyExtractor(BaseExtractor):
    """Sony firmware extractor for FTF and SIN files"""
    
    def extract(self, file_path: Path, output_dir: Path) -> bool:
        """Extract Sony firmware"""
        self.logger.info("🔄 Extracting Sony firmware...")
        
        filename = file_path.name.lower()
        
        if filename.endswith('.ftf'):
            return self._extract_ftf(file_path, output_dir)
        elif filename.endswith('.sin'):
            return self._extract_sin(file_path, output_dir)
        else:
            return self._extract_with_7zz(file_path, output_dir)
    
    def _extract_ftf(self, file_path: Path, output_dir: Path) -> bool:
        """Extract FTF file"""
        try:
            # FTF is usually a ZIP archive
            success = self._extract_with_7zz(file_path, output_dir)
            
            if success:
                # Process any SIN files in the extracted content
                for sin_file in output_dir.rglob("*.sin"):
                    self._extract_sin(sin_file, output_dir)
                    
            return success
            
        except Exception as e:
            self.logger.error(f"FTF extraction failed: {str(e)}")
            return False
    
    def _extract_sin(self, file_path: Path, output_dir: Path) -> bool:
        """Extract SIN file using unsin"""
        try:
            cmd = [str(self.config.get_tool_path("unsin")), "-d", str(output_dir)]
            result = self._run_command(cmd, cwd=output_dir, check=False)
            
            if result.returncode == 0:
                # Rename .ext4 files to .img
                for ext4_file in output_dir.glob("*.ext4"):
                    img_file = ext4_file.with_suffix('.img')
                    ext4_file.rename(img_file)
                    
                self.logger.success("✅ SIN extraction completed")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"SIN extraction failed: {str(e)}")
            return False