"""
Firmware type detection and validation utilities.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from enum import Enum

class FirmwareType(Enum):
    """Supported firmware types."""
    OZIP = "ozip"           # Oppo/Realme encrypted zip
    OPS = "ops"             # OnePlus/Oppo ops
    OFP = "ofp"             # Oppo ofp
    KDZ = "kdz"             # LG KDZ
    RUU = "ruu"             # HTC RUU
    AML = "aml"             # Amlogic upgrade package
    TAR_MD5 = "tar.md5"     # Samsung tarmd5
    PAYLOAD = "payload"     # Android OTA payload
    UPDATE_APP = "update.app" # Huawei UPDATE.APP
    PAC = "pac"             # SpreadTrum PAC
    NB0 = "nb0"             # Nokia/Sharp/Infocus nb0
    CHUNK = "chunk"         # Chunk files
    SIN = "sin"             # Sony SIN images
    BIN = "bin"             # Binary images
    P_SUFFIX = "p_suffix"   # P-suffix images
    SIGNED_IMG = "signed"   # Signed images
    ZIP_ARCHIVE = "zip"     # ZIP/RAR/7Z archives
    ROCKCHIP = "rockchip"   # Rockchip firmware
    TGZ = "tgz"             # Xiaomi gzipped tar
    SUPER_IMG = "super"     # Super partition image
    DIRECTORY = "directory" # Directory with firmware files
    UNKNOWN = "unknown"     # Unknown format

class FirmwareDetector:
    """Firmware type detection and validation."""
    
    def __init__(self):
        self.sevenzip_cmd = self._find_sevenzip()
    
    def _find_sevenzip(self) -> str:
        """Find 7zip executable."""
        for cmd in ["7zz", "7z"]:
            if subprocess.run(["which", cmd], capture_output=True).returncode == 0:
                return cmd
        
        # Try utils directory
        utils_7z = Path(__file__).parent.parent.parent / "utils" / "bin" / "7zz"
        if utils_7z.exists():
            return str(utils_7z)
        
        return "7zz"  # Default fallback
    
    def detect_firmware_type(self, filepath: str) -> Tuple[FirmwareType, Dict[str, any]]:
        """
        Detect firmware type and return type with metadata.
        
        Args:
            filepath: Path to firmware file or directory
            
        Returns:
            Tuple of (FirmwareType, metadata_dict)
        """
        path = Path(filepath)
        metadata = {"path": filepath, "size": 0, "extension": ""}
        
        if not path.exists():
            return FirmwareType.UNKNOWN, metadata
        
        if path.is_dir():
            return self._detect_directory_type(path, metadata)
        
        # File detection
        metadata["size"] = path.stat().st_size
        metadata["extension"] = path.suffix.lower()
        
        # Check file magic/content for specific types
        firmware_type = self._detect_file_type(path, metadata)
        
        return firmware_type, metadata
    
    def _detect_directory_type(self, path: Path, metadata: Dict) -> Tuple[FirmwareType, Dict]:
        """Detect firmware type for directories."""
        files = list(path.iterdir())
        
        # Check for specific firmware files in directory
        file_patterns = {
            r".*\.pac$": FirmwareType.PAC,
            r".*\.nb0$": FirmwareType.NB0, 
            r".*chunk.*": FirmwareType.CHUNK,
            r"system\.new\.dat": FirmwareType.PAYLOAD,
            r"payload\.bin": FirmwareType.PAYLOAD,
            r"UPDATE\.APP": FirmwareType.UPDATE_APP,
            r".*\.sin$": FirmwareType.SIN,
            r"system\.img": FirmwareType.BIN,
            r"super.*\.img": FirmwareType.SUPER_IMG
        }
        
        for file in files:
            if file.is_file():
                for pattern, fw_type in file_patterns.items():
                    if re.match(pattern, file.name, re.IGNORECASE):
                        metadata["detected_files"] = [f.name for f in files]
                        return fw_type, metadata
        
        # Check for archives in directory
        for file in files:
            if file.suffix.lower() in ['.zip', '.rar', '.7z', '.tar']:
                metadata["archive_file"] = file.name
                return FirmwareType.ZIP_ARCHIVE, metadata
        
        return FirmwareType.DIRECTORY, metadata
    
    def _detect_file_type(self, path: Path, metadata: Dict) -> FirmwareType:
        """Detect firmware type for files."""
        filename = path.name.lower()
        extension = path.suffix.lower()
        
        # Extension-based detection
        extension_map = {
            '.ozip': FirmwareType.OZIP,
            '.ops': FirmwareType.OPS,
            '.ofp': FirmwareType.OFP,
            '.kdz': FirmwareType.KDZ,
            '.nb0': FirmwareType.NB0,
            '.pac': FirmwareType.PAC,
            '.sin': FirmwareType.SIN,
            '.tgz': FirmwareType.TGZ
        }
        
        if extension in extension_map:
            return extension_map[extension]
        
        # Special filename patterns
        if filename.startswith('ruu_') and filename.endswith('.exe'):
            return FirmwareType.RUU
        
        if filename == 'update.app':
            return FirmwareType.UPDATE_APP
        
        if filename == 'payload.bin':
            return FirmwareType.PAYLOAD
        
        if 'super' in filename and extension == '.img':
            return FirmwareType.SUPER_IMG
        
        # Check for chunk files
        if 'chunk' in filename:
            return FirmwareType.CHUNK
        
        # Check for P-suffix images
        if filename.endswith('-p'):
            return FirmwareType.P_SUFFIX
        
        # Check for signed images  
        if 'sign' in filename and extension == '.img':
            return FirmwareType.SIGNED_IMG
        
        # Check for binary images
        if extension == '.bin':
            return FirmwareType.BIN
        
        # Check for tar.md5 (Samsung)
        if filename.endswith('.tar.md5') or filename.endswith('.tar.gz'):
            if filename.endswith('.tar.md5'):
                return FirmwareType.TAR_MD5
            else:
                return FirmwareType.TGZ
        
        # Check archive formats
        if extension in ['.zip', '.rar', '.7z', '.tar']:
            return self._detect_archive_type(path, metadata)
        
        # Check file content/magic for specific formats
        return self._detect_by_content(path, metadata)
    
    def _detect_archive_type(self, path: Path, metadata: Dict) -> FirmwareType:
        """Detect firmware type within archives."""
        try:
            # List archive contents
            result = subprocess.run(
                [self.sevenzip_cmd, "l", "-ba", str(path)],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                content = result.stdout.lower()
                
                # Check for specific files in archive
                if '.ops' in content:
                    metadata["contains_ops"] = True
                    return FirmwareType.OPS
                
                if '.ofp' in content:
                    metadata["contains_ofp"] = True
                    return FirmwareType.OFP
                
                if 'payload.bin' in content:
                    metadata["contains_payload"] = True
                    return FirmwareType.PAYLOAD
                
                if 'update.app' in content:
                    metadata["contains_update_app"] = True
                    return FirmwareType.UPDATE_APP
                
                if 'system.new.dat' in content:
                    metadata["contains_system_dat"] = True
                    return FirmwareType.PAYLOAD
        
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        
        return FirmwareType.ZIP_ARCHIVE
    
    def _detect_by_content(self, path: Path, metadata: Dict) -> FirmwareType:
        """Detect firmware type by file content/magic bytes."""
        try:
            with open(path, 'rb') as f:
                header = f.read(16)
            
            # Check for OPPO encrypted header
            if header[:12] == b'OPPOENCRYPT!':
                return FirmwareType.OZIP
            
            # Check for other magic bytes here if needed
            
        except Exception:
            pass
        
        return FirmwareType.UNKNOWN
    
    def validate_firmware(self, firmware_type: FirmwareType, filepath: str) -> bool:
        """
        Validate if firmware file is properly formatted.
        
        Args:
            firmware_type: Detected firmware type
            filepath: Path to firmware file
            
        Returns:
            True if valid, False otherwise
        """
        path = Path(filepath)
        
        if not path.exists():
            return False
        
        # Basic size check (firmware should be > 10MB typically)
        if path.is_file() and path.stat().st_size < 10 * 1024 * 1024:
            # Allow smaller files for certain types
            small_file_types = [FirmwareType.CHUNK, FirmwareType.BIN]
            if firmware_type not in small_file_types:
                return False
        
        # Type-specific validation
        if firmware_type == FirmwareType.OZIP:
            return self._validate_ozip(path)
        elif firmware_type == FirmwareType.ZIP_ARCHIVE:
            return self._validate_archive(path)
        elif firmware_type == FirmwareType.PAYLOAD:
            return self._validate_payload(path)
        
        # Default validation passed
        return True
    
    def _validate_ozip(self, path: Path) -> bool:
        """Validate OZIP file."""
        try:
            with open(path, 'rb') as f:
                header = f.read(12)
            return header == b'OPPOENCRYPT!'
        except Exception:
            return False
    
    def _validate_archive(self, path: Path) -> bool:
        """Validate archive file."""
        try:
            result = subprocess.run(
                [self.sevenzip_cmd, "t", str(path)],
                capture_output=True, timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _validate_payload(self, path: Path) -> bool:
        """Validate payload.bin file."""
        if path.name.lower() == 'payload.bin':
            return path.stat().st_size > 1024  # Should be larger than 1KB
        return True
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported firmware formats."""
        return [
            "*.zip, *.rar, *.7z, *.tar, *.tar.gz, *.tgz, *.tar.md5",
            "*.ozip, *.ofp, *.ops, *.kdz, ruu_*.exe",
            "system.new.dat, system.new.dat.br, system.new.dat.xz",
            "system.new.img, system.img, system-sign.img, UPDATE.APP",
            "*.emmc.img, *.img.ext4, system.bin, system-p, payload.bin",
            "*.nb0, .*chunk*, *.pac, *super*.img, *system*.sin"
        ]