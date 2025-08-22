"""
Payload (Android OTA payload.bin) extractor.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any

from ..core.detector import FirmwareType
from . import BaseExtractor, ExtractionError

class PayloadExtractor(BaseExtractor):
    """Extractor for Android OTA payload.bin files."""
    
    def can_extract(self, firmware_type: FirmwareType) -> bool:
        """Check if this extractor can handle payload files."""
        return firmware_type == FirmwareType.PAYLOAD
    
    def extract(self, filepath: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract payload.bin file."""
        path = Path(filepath)
        
        if path.is_dir():
            return self._extract_from_directory(path, metadata)
        else:
            return self._extract_payload_file(path, metadata)
    
    def _extract_payload_file(self, file_path: Path, metadata: Dict[str, Any]) -> List[str]:
        """Extract payload.bin file."""
        self.logger.step(1, 3, "Preparing payload extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy file to temp directory
        input_file = self.copy_input_file(str(file_path), temp_dir)
        
        self.logger.step(2, 3, "Extracting payload.bin")
        
        # Path to payload extractor
        payload_tool = Path(self.config.get_utils_dir()) / "bin" / "payload-dumper-go"
        
        if not payload_tool.exists():
            raise ExtractionError(f"Payload extractor not found: {payload_tool}")
        
        try:
            # Make tool executable
            payload_tool.chmod(0o755)
            
            # Extract payload.bin
            cmd = [str(payload_tool), "-o", str(temp_dir), str(input_file)]
            
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            if result.returncode != 0:
                raise ExtractionError(f"Payload extraction failed: {result.stderr}")
            
            self.logger.step(3, 3, "Collecting extracted images")
            
            # Find extracted image files
            extracted_files = []
            for file in temp_dir.glob("*.img"):
                if file != input_file:
                    extracted_files.append(str(file))
            
            if not extracted_files:
                raise ExtractionError("No image files extracted from payload")
            
            # Move extracted files to output directory
            final_files = []
            for file_path in extracted_files:
                file = Path(file_path)
                if file.exists():
                    dest_path = self.output_dir / file.name
                    file.rename(dest_path)
                    final_files.append(str(dest_path))
            
            return final_files
            
        except subprocess.TimeoutExpired:
            raise ExtractionError("Payload extraction timeout")
        except Exception as e:
            raise ExtractionError(f"Payload extraction error: {str(e)}")
    
    def _extract_from_directory(self, dir_path: Path, metadata: Dict[str, Any]) -> List[str]:
        """Extract from directory containing system.new.dat and related files."""
        self.logger.step(1, 4, "Preparing system.new.dat extraction")
        temp_dir = self.prepare_extraction()
        
        # Copy relevant files to temp directory
        dat_files = ["system.new.dat", "system.new.dat.br", "system.new.dat.xz"]
        transfer_list = "system.transfer.list"
        
        copied_files = []
        for filename in dat_files + [transfer_list]:
            src_file = dir_path / filename
            if src_file.exists():
                dst_file = temp_dir / filename
                dst_file.write_bytes(src_file.read_bytes())
                copied_files.append(filename)
        
        if not any(f in copied_files for f in dat_files):
            raise ExtractionError("No system.new.dat files found in directory")
        
        self.logger.step(2, 4, "Decompressing system.new.dat if needed")
        
        # Handle compressed dat files
        dat_file = self._decompress_dat_file(temp_dir, copied_files)
        
        self.logger.step(3, 4, "Converting system.new.dat to system.img")
        
        # Convert using sdat2img
        sdat2img_tool = Path(self.config.get_utils_dir()) / "sdat2img.py"
        
        if not sdat2img_tool.exists():
            raise ExtractionError(f"sdat2img tool not found: {sdat2img_tool}")
        
        try:
            transfer_file = temp_dir / transfer_list
            output_img = temp_dir / "system.img"
            
            if not transfer_file.exists():
                raise ExtractionError("system.transfer.list not found")
            
            cmd = [
                "python3", str(sdat2img_tool),
                str(transfer_file),
                str(dat_file),
                str(output_img)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode != 0:
                raise ExtractionError(f"sdat2img conversion failed: {result.stderr}")
            
            self.logger.step(4, 4, "Collecting converted images")
            
            # Move output image to final destination
            if output_img.exists():
                final_path = self.output_dir / output_img.name
                output_img.rename(final_path)
                return [str(final_path)]
            else:
                raise ExtractionError("No system.img file generated")
                
        except subprocess.TimeoutExpired:
            raise ExtractionError("sdat2img conversion timeout")
        except Exception as e:
            raise ExtractionError(f"sdat2img conversion error: {str(e)}")
    
    def _decompress_dat_file(self, temp_dir: Path, copied_files: List[str]) -> Path:
        """Decompress system.new.dat file if compressed."""
        # Check for compressed versions first
        if "system.new.dat.br" in copied_files:
            self.logger.info("Decompressing brotli compressed dat file")
            compressed_file = temp_dir / "system.new.dat.br"
            output_file = temp_dir / "system.new.dat"
            
            try:
                result = subprocess.run(
                    ["brotli", "-d", str(compressed_file), "-o", str(output_file)],
                    capture_output=True, text=True, timeout=600
                )
                if result.returncode == 0:
                    return output_file
            except Exception:
                pass
        
        if "system.new.dat.xz" in copied_files:
            self.logger.info("Decompressing xz compressed dat file")
            compressed_file = temp_dir / "system.new.dat.xz"
            output_file = temp_dir / "system.new.dat"
            
            try:
                result = subprocess.run(
                    ["xz", "-d", "-c", str(compressed_file)],
                    stdout=open(output_file, 'wb'),
                    stderr=subprocess.PIPE,
                    timeout=600
                )
                if result.returncode == 0:
                    return output_file
            except Exception:
                pass
        
        # Return uncompressed version
        dat_file = temp_dir / "system.new.dat"
        if dat_file.exists():
            return dat_file
        
        raise ExtractionError("No valid system.new.dat file found")