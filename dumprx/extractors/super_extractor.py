"""
Super partition image extractor.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any

from ..core.detector import FirmwareType
from . import BaseExtractor, ExtractionError

class SuperExtractor(BaseExtractor):
    """Extractor for super partition images."""
    
    def can_extract(self, firmware_type: FirmwareType) -> bool:
        """Check if this extractor can handle super images."""
        return firmware_type == FirmwareType.SUPER_IMG
    
    def extract(self, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract super partition image."""
        self.logger.step(1, 4, "Preparing super image extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy file to temp directory
        input_file = self.copy_input_file(filepath, temp_dir)
        
        self.logger.step(2, 4, "Converting sparse to raw image")
        
        # Convert sparse image to raw if needed
        raw_file = self._convert_sparse_to_raw(input_file)
        
        self.logger.step(3, 4, "Extracting partitions from super image")
        
        # Extract partitions using lpunpack
        extracted_files = self._extract_partitions(raw_file)
        
        self.logger.step(4, 4, "Processing extracted partitions")
        
        # Move extracted files to output directory
        final_files = []
        for file_path in extracted_files:
            file = Path(file_path)
            if file.exists():
                dest_path = self.output_dir / file.name
                file.rename(dest_path)
                final_files.append(str(dest_path))
        
        return final_files
    
    def _convert_sparse_to_raw(self, input_file: Path) -> Path:
        """Convert sparse image to raw image if needed."""
        raw_file = input_file.with_suffix('.raw')
        
        # Check if already raw or needs conversion
        simg2img_tool = Path(self.config.get_utils_dir()) / "bin" / "simg2img"
        
        if not simg2img_tool.exists():
            self.logger.warning("simg2img tool not found, assuming image is already raw")
            return input_file
        
        try:
            # Make tool executable
            simg2img_tool.chmod(0o755)
            
            # Try to convert sparse to raw
            cmd = [str(simg2img_tool), str(input_file), str(raw_file)]
            
            result = subprocess.run(
                cmd,
                cwd=input_file.parent,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            if result.returncode == 0 and raw_file.exists():
                self.logger.success("Sparse image converted to raw")
                return raw_file
            else:
                # Not a sparse image, use original
                self.logger.info("Image is already in raw format")
                return input_file
                
        except subprocess.TimeoutExpired:
            raise ExtractionError("Sparse to raw conversion timeout")
        except Exception as e:
            self.logger.warning(f"Sparse conversion failed: {str(e)}, using original file")
            return input_file
    
    def _extract_partitions(self, raw_file: Path) -> List[str]:
        """Extract partitions from super image using lpunpack."""
        lpunpack_tool = Path(self.config.get_utils_dir()) / "lpunpack"
        
        if not lpunpack_tool.exists():
            raise ExtractionError(f"lpunpack tool not found: {lpunpack_tool}")
        
        try:
            # Make tool executable
            lpunpack_tool.chmod(0o755)
            
            extracted_files = []
            
            # Try to extract each known partition
            for partition in self.config.partitions:
                for suffix in ["", "_a"]:
                    partition_name = f"{partition}{suffix}"
                    
                    cmd = [str(lpunpack_tool), f"--partition={partition_name}", str(raw_file)]
                    
                    result = subprocess.run(
                        cmd,
                        cwd=raw_file.parent,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes per partition
                    )
                    
                    # Check if partition was extracted
                    extracted_partition = raw_file.parent / f"{partition_name}.img"
                    if extracted_partition.exists():
                        # Rename _a suffix partitions to remove suffix
                        if suffix == "_a":
                            final_name = raw_file.parent / f"{partition}.img"
                            if not final_name.exists():  # Don't overwrite if both exist
                                extracted_partition.rename(final_name)
                                extracted_files.append(str(final_name))
                            else:
                                extracted_files.append(str(extracted_partition))
                        else:
                            extracted_files.append(str(extracted_partition))
                        
                        self.logger.debug(f"Extracted partition: {partition_name}")
                        break  # Stop trying suffixes for this partition
            
            if not extracted_files:
                raise ExtractionError("No partitions extracted from super image")
            
            return extracted_files
            
        except subprocess.TimeoutExpired:
            raise ExtractionError("Partition extraction timeout")
        except Exception as e:
            raise ExtractionError(f"Partition extraction error: {str(e)}")