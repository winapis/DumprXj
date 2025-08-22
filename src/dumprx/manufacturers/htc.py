"""
HTC firmware extractor (RUU decryption)
"""

from pathlib import Path
from .base import BaseExtractor


class HTCExtractor(BaseExtractor):
    """HTC firmware extractor for RUU files"""
    
    def extract(self, file_path: Path, output_dir: Path) -> bool:
        """Extract HTC firmware"""
        self.logger.info("🔄 Extracting HTC RUU...")
        
        # Use RUU_Decrypt_Tool for system and firmware partitions
        cmd_system = [str(self.config.get_tool_path("ruu_decrypt")), "-s", str(file_path)]
        cmd_firmware = [str(self.config.get_tool_path("ruu_decrypt")), "-f", str(file_path)]
        
        try:
            self._run_command(cmd_system, cwd=output_dir, check=False)
            self._run_command(cmd_firmware, cwd=output_dir, check=False)
            
            # Move extracted IMG files from OUT* directories
            for out_dir in output_dir.glob("OUT*"):
                for img_file in out_dir.glob("*.img"):
                    dest = output_dir / img_file.name
                    import shutil
                    shutil.move(str(img_file), str(dest))
            
            self.logger.success("✅ HTC RUU extraction completed")
            return True
            
        except Exception as e:
            self.logger.error(f"HTC RUU extraction failed: {str(e)}")
            return False