"""
Universal extractor module for various firmware formats.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import zipfile
import tarfile

try:
    import py7zlib
    PY7Z_AVAILABLE = True
except ImportError:
    PY7Z_AVAILABLE = False

from ..core.config import Config
from ..core.logger import get_logger


class Extractor:
    """Universal firmware extractor supporting multiple formats."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
    
    def extract(self, input_path: str, output_dir: Path) -> Dict[str, Any]:
        """
        Extract firmware from various formats.
        
        Args:
            input_path: Path to firmware file or directory
            output_dir: Directory to extract to
            
        Returns:
            Dictionary with extraction results
        """
        self.logger.info(f"🗂️  Extracting: {Path(input_path).name}")
        
        input_path = Path(input_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            'input_path': str(input_path),
            'output_dir': str(output_dir),
            'extracted_files': [],
            'format': None,
            'success': False
        }
        
        try:
            if input_path.is_file():
                result['format'] = input_path.suffix.lower().lstrip('.')
                self._extract_file(input_path, output_dir, result)
            elif input_path.is_dir():
                result['format'] = 'directory'
                self._extract_directory(input_path, output_dir, result)
            else:
                raise ValueError(f"Input path does not exist: {input_path}")
            
            result['success'] = True
            self.logger.success(f"✅ Extraction completed: {len(result['extracted_files'])} files")
            
        except Exception as e:
            self.logger.error(f"❌ Extraction failed: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def _extract_file(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract a single file based on its format."""
        format_name = result['format']
        
        # Route to appropriate extractor based on format
        if format_name in ['zip']:
            self._extract_zip(file_path, output_dir, result)
        elif format_name in ['rar']:
            self._extract_rar(file_path, output_dir, result)
        elif format_name in ['7z']:
            self._extract_7z(file_path, output_dir, result)
        elif format_name in ['tar', 'tar.gz', 'tgz', 'tar.md5']:
            self._extract_tar(file_path, output_dir, result)
        elif format_name in ['ozip']:
            self._extract_ozip(file_path, output_dir, result)
        elif format_name in ['kdz']:
            self._extract_kdz(file_path, output_dir, result)
        elif format_name in ['ops']:
            self._extract_ops(file_path, output_dir, result)
        elif format_name in ['ofp']:
            self._extract_ofp(file_path, output_dir, result)
        elif format_name in ['nb0']:
            self._extract_nb0(file_path, output_dir, result)
        elif format_name in ['pac']:
            self._extract_pac(file_path, output_dir, result)
        elif format_name in ['exe'] and 'ruu' in file_path.name.lower():
            self._extract_ruu(file_path, output_dir, result)
        elif format_name in ['sin']:
            self._extract_sin(file_path, output_dir, result)
        elif format_name in ['img', 'bin']:
            self._extract_image(file_path, output_dir, result)
        else:
            # Try generic extraction
            self._extract_generic(file_path, output_dir, result)
    
    def _extract_directory(self, dir_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract/copy directory contents."""
        for item in dir_path.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(dir_path)
                dest_path = output_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
                result['extracted_files'].append(str(dest_path))
    
    def _extract_zip(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract ZIP files."""
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
            result['extracted_files'] = [str(output_dir / name) for name in zip_ref.namelist()]
    
    def _extract_rar(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract RAR files using unrar."""
        try:
            cmd = ['unrar', 'x', '-y', str(file_path), str(output_dir)]
            subprocess.run(cmd, check=True, capture_output=True)
            result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file()]
        except subprocess.CalledProcessError as e:
            raise ValueError(f"RAR extraction failed: {e}")
    
    def _extract_7z(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract 7Z files."""
        bin_7zz = self.config.get_tool_path('bin/7zz') or '7zz'
        try:
            cmd = [str(bin_7zz), 'x', '-y', f'-o{output_dir}', str(file_path)]
            subprocess.run(cmd, check=True, capture_output=True)
            result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file()]
        except subprocess.CalledProcessError as e:
            raise ValueError(f"7Z extraction failed: {e}")
    
    def _extract_tar(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract TAR files."""
        # Determine compression type
        if file_path.name.endswith('.tar.gz') or file_path.name.endswith('.tgz'):
            mode = 'r:gz'
        elif file_path.name.endswith('.tar.bz2'):
            mode = 'r:bz2'
        elif file_path.name.endswith('.tar.xz'):
            mode = 'r:xz'
        else:
            mode = 'r'
        
        with tarfile.open(file_path, mode) as tar_ref:
            tar_ref.extractall(output_dir)
            result['extracted_files'] = [str(output_dir / member.name) for member in tar_ref.getmembers() if member.isfile()]
    
    def _extract_ozip(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract OZIP files (Oppo/Realme encrypted)."""
        ozip_decrypt = self.config.get_tool_path('oppo_ozip_decrypt/ozipdecrypt.py')
        if not ozip_decrypt:
            raise ValueError("OZIP decryption tool not found")
        
        try:
            # Copy file to temp location for extraction
            temp_file = output_dir / file_path.name
            shutil.copy2(file_path, temp_file)
            
            # Run decryption
            cmd = ['python3', str(ozip_decrypt), str(temp_file)]
            result_proc = subprocess.run(cmd, cwd=str(output_dir), capture_output=True, text=True)
            
            if result_proc.returncode == 0:
                # Find extracted files
                result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file() and f != temp_file]
            else:
                raise ValueError(f"OZIP decryption failed: {result_proc.stderr}")
        
        except Exception as e:
            raise ValueError(f"OZIP extraction failed: {e}")
    
    def _extract_kdz(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract KDZ files (LG)."""
        kdz_extract = self.config.get_tool_path('kdztools/unkdz.py')
        dz_extract = self.config.get_tool_path('kdztools/undz.py')
        
        if not kdz_extract or not dz_extract:
            raise ValueError("KDZ extraction tools not found")
        
        try:
            # Copy file to temp location
            temp_file = output_dir / file_path.name
            shutil.copy2(file_path, temp_file)
            
            # Extract KDZ
            cmd = ['python3', str(kdz_extract), '-f', str(temp_file), '-x', '-o', str(output_dir)]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Find DZ file and extract it
            dz_files = list(output_dir.glob('*.dz'))
            if dz_files:
                dz_file = dz_files[0]
                cmd = ['python3', str(dz_extract), '-f', str(dz_file), '-s', '-o', str(output_dir)]
                subprocess.run(cmd, check=True, capture_output=True)
            
            result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file()]
        
        except subprocess.CalledProcessError as e:
            raise ValueError(f"KDZ extraction failed: {e}")
    
    def _extract_ops(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract OPS files (OnePlus/Oppo)."""
        ops_decrypt = self.config.get_tool_path('oppo_decrypt/opscrypto.py')
        if not ops_decrypt:
            raise ValueError("OPS decryption tool not found")
        
        try:
            cmd = ['python3', str(ops_decrypt), 'decrypt', str(file_path)]
            subprocess.run(cmd, cwd=str(output_dir), check=True, capture_output=True)
            result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file()]
        
        except subprocess.CalledProcessError as e:
            raise ValueError(f"OPS extraction failed: {e}")
    
    def _extract_ofp(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract OFP files (Oppo firmware packages)."""
        # Try both QC and MTK extractors
        qc_extract = self.config.get_tool_path('oppo_decrypt/ofp_qc_decrypt.py')
        mtk_extract = self.config.get_tool_path('oppo_decrypt/ofp_mtk_decrypt.py')
        
        for tool in [qc_extract, mtk_extract]:
            if tool and tool.exists():
                try:
                    cmd = ['python3', str(tool), str(file_path), str(output_dir)]
                    subprocess.run(cmd, check=True, capture_output=True)
                    result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file()]
                    return
                except subprocess.CalledProcessError:
                    continue
        
        raise ValueError("OFP extraction failed with all available tools")
    
    def _extract_nb0(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract NB0 files (Nokia/Sharp/Essential)."""
        nb0_extract = self.config.get_tool_path('nb0-extract')
        if not nb0_extract:
            raise ValueError("NB0 extraction tool not found")
        
        try:
            cmd = [str(nb0_extract), str(file_path), str(output_dir)]
            subprocess.run(cmd, check=True, capture_output=True)
            result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file()]
        
        except subprocess.CalledProcessError as e:
            raise ValueError(f"NB0 extraction failed: {e}")
    
    def _extract_pac(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract PAC files (Spreadtrum)."""
        pac_extractor = self.config.get_tool_path('pacextractor/python/pacExtractor.py')
        if not pac_extractor:
            raise ValueError("PAC extractor not found")
        
        try:
            cmd = ['python3', str(pac_extractor), str(file_path), str(output_dir)]
            subprocess.run(cmd, check=True, capture_output=True)
            result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file()]
        
        except subprocess.CalledProcessError as e:
            raise ValueError(f"PAC extraction failed: {e}")
    
    def _extract_ruu(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract RUU files (HTC)."""
        ruu_decrypt = self.config.get_tool_path('RUU_Decrypt_Tool')
        if not ruu_decrypt:
            raise ValueError("RUU decryption tool not found")
        
        try:
            # RUU tool typically needs to be run in its own directory
            cmd = [str(ruu_decrypt), str(file_path)]
            subprocess.run(cmd, cwd=str(ruu_decrypt.parent), check=True, capture_output=True)
            
            # Move extracted files to output directory
            for extracted_file in ruu_decrypt.parent.glob('*'):
                if extracted_file.is_file() and extracted_file != ruu_decrypt:
                    dest = output_dir / extracted_file.name
                    shutil.move(str(extracted_file), str(dest))
                    result['extracted_files'].append(str(dest))
        
        except subprocess.CalledProcessError as e:
            raise ValueError(f"RUU extraction failed: {e}")
    
    def _extract_sin(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract SIN files (Sony Xperia)."""
        unsin = self.config.get_tool_path('unsin')
        if not unsin:
            raise ValueError("UNSIN tool not found")
        
        try:
            cmd = [str(unsin), '-d', str(output_dir), str(file_path)]
            subprocess.run(cmd, check=True, capture_output=True)
            result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file()]
        
        except subprocess.CalledProcessError as e:
            raise ValueError(f"SIN extraction failed: {e}")
    
    def _extract_image(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Handle IMG/BIN files - copy and analyze."""
        dest_path = output_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        result['extracted_files'] = [str(dest_path)]
        
        # Try to extract if it's a special format
        if 'super' in file_path.name.lower():
            self._extract_super_image(dest_path, output_dir, result)
        elif 'payload.bin' in file_path.name.lower():
            self._extract_payload(dest_path, output_dir, result)
    
    def _extract_super_image(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract super.img files."""
        lpunpack = self.config.get_tool_path('lpunpack')
        if not lpunpack:
            self.logger.warning("lpunpack tool not found, skipping super image extraction")
            return
        
        try:
            # Convert sparse to raw if needed
            simg2img = self.config.get_tool_path('bin/simg2img')
            if simg2img:
                raw_path = file_path.with_suffix('.raw')
                cmd = [str(simg2img), str(file_path), str(raw_path)]
                result_proc = subprocess.run(cmd, capture_output=True)
                if result_proc.returncode == 0:
                    file_path = raw_path
            
            # Extract partitions
            for partition in self.config.partitions:
                for suffix in ['', '_a']:
                    cmd = [str(lpunpack), f'--partition={partition}{suffix}', str(file_path)]
                    subprocess.run(cmd, cwd=str(output_dir), capture_output=True)
            
            # Add any newly created partition files
            new_files = [str(f) for f in output_dir.glob('*.img') if str(f) not in result['extracted_files']]
            result['extracted_files'].extend(new_files)
        
        except Exception as e:
            self.logger.debug(f"Super image extraction error: {e}")
    
    def _extract_payload(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Extract payload.bin files."""
        payload_extractor = self.config.get_tool_path('bin/payload-dumper-go')
        if not payload_extractor:
            self.logger.warning("payload-dumper-go not found, skipping payload extraction")
            return
        
        try:
            cmd = [str(payload_extractor), '-o', str(output_dir), str(file_path)]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Add extracted files
            new_files = [str(f) for f in output_dir.glob('*.img') if str(f) not in result['extracted_files']]
            result['extracted_files'].extend(new_files)
        
        except subprocess.CalledProcessError as e:
            self.logger.debug(f"Payload extraction error: {e}")
    
    def _extract_generic(self, file_path: Path, output_dir: Path, result: Dict[str, Any]) -> None:
        """Generic extraction fallback."""
        # Try 7z as last resort
        bin_7zz = self.config.get_tool_path('bin/7zz') or '7zz'
        try:
            cmd = [str(bin_7zz), 'x', '-y', f'-o{output_dir}', str(file_path)]
            subprocess.run(cmd, check=True, capture_output=True)
            result['extracted_files'] = [str(f) for f in output_dir.rglob('*') if f.is_file()]
        except subprocess.CalledProcessError:
            # If extraction fails, just copy the file
            dest_path = output_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            result['extracted_files'] = [str(dest_path)]