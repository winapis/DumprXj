import subprocess
import re
import base64
import json
from pathlib import Path
from typing import Optional
import logging

from rich.progress import Progress, DownloadColumn, TransferSpeedColumn, TimeElapsedColumn, BarColumn, TextColumn
from rich.console import Console

from dumprx.utils.ui import print_info, print_error, print_success

logger = logging.getLogger(__name__)
console = Console()


def download_from_url(url: str, output_dir: Path) -> Optional[Path]:
    """Download firmware from various URL types"""
    
    if "mega" in url.lower():
        return download_mega(url, output_dir)
    elif "mediafire" in url.lower():
        return download_mediafire(url, output_dir)
    elif "drive.google.com" in url.lower():
        return download_gdrive(url, output_dir)
    elif "androidfilehost" in url.lower():
        return download_afh(url, output_dir)
    else:
        return download_direct(url, output_dir)


def download_direct(url: str, output_dir: Path) -> Optional[Path]:
    """Download file using aria2c or wget"""
    print_info(f"Downloading from: {url}")
    
    # Try to get filename from URL
    filename = url.split('/')[-1].split('?')[0]
    if not filename or '.' not in filename:
        filename = "firmware_file"
    
    output_path = output_dir / filename
    
    # Try aria2c first
    aria_cmd = [
        "aria2c", "-c", "-s16", "-x8", "-m10",
        "--console-log-level=warn", "--summary-interval=0",
        "--check-certificate=false", "-o", filename, url
    ]
    
    try:
        result = subprocess.run(aria_cmd, cwd=output_dir, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0 and output_path.exists():
            print_success(f"Downloaded: {filename}")
            return output_path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fallback to wget
    wget_cmd = [
        "wget", "-O", str(output_path), "--no-check-certificate",
        "--show-progress", "--progress=bar:force", url
    ]
    
    try:
        result = subprocess.run(wget_cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0 and output_path.exists():
            print_success(f"Downloaded: {filename}")
            return output_path
    except subprocess.TimeoutExpired:
        print_error("Download timeout")
    
    return None


def download_mega(url: str, output_dir: Path) -> Optional[Path]:
    """Download from Mega.nz using mega-cmd or custom implementation"""
    print_info("Mega.NZ Website Link Detected")
    
    # Try using mega-cmd if available
    try:
        # Check if mega-cmd is available
        result = subprocess.run(["mega-get", "--help"], capture_output=True, text=True)
        if result.returncode == 0:
            return _download_mega_cmd(url, output_dir)
    except FileNotFoundError:
        pass
    
    # Fallback to custom implementation (simplified version)
    return _download_mega_custom(url, output_dir)


def _download_mega_cmd(url: str, output_dir: Path) -> Optional[Path]:
    """Download using mega-cmd"""
    cmd = ["mega-get", url, str(output_dir)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            # Find downloaded file
            downloaded_files = [f for f in output_dir.iterdir() if f.is_file() and f.stat().st_size > 0]
            if downloaded_files:
                return max(downloaded_files, key=lambda f: f.stat().st_mtime)
    except subprocess.TimeoutExpired:
        print_error("Mega download timeout")
    
    return None


def _download_mega_custom(url: str, output_dir: Path) -> Optional[Path]:
    """Custom Mega.nz download implementation (simplified)"""
    # This is a simplified version - in production you'd want to use
    # the full implementation from mega-media-drive_dl.sh
    
    print_info("Using simplified Mega download (install mega-cmd for better support)")
    
    # Extract file ID from URL
    file_id_match = re.search(r'#!([A-Za-z0-9_-]+)!([A-Za-z0-9_-]+)', url)
    if not file_id_match:
        print_error("Invalid Mega URL format")
        return None
    
    # For now, suggest manual download
    print_error("Mega download requires mega-cmd. Please install it or download manually.")
    return None


def download_mediafire(url: str, output_dir: Path) -> Optional[Path]:
    """Download from MediaFire"""
    print_info("Mediafire Website Link Detected")
    
    try:
        # Get the actual download URL
        wget_result = subprocess.run(
            ["wget", "-q", "-O-", url], 
            capture_output=True, text=True, timeout=60
        )
        
        if wget_result.returncode != 0:
            print_error("Failed to fetch MediaFire page")
            return None
        
        # Extract download URL
        download_match = re.search(r'href="(https://download[^"]+)"', wget_result.stdout)
        if not download_match:
            print_error("Could not find download link in MediaFire page")
            return None
        
        download_url = download_match.group(1)
        
        # Extract filename
        filename_match = re.search(r'/([^/]+)$', download_url)
        filename = filename_match.group(1) if filename_match else "mediafire_download"
        
        # Download file
        return download_direct(download_url, output_dir)
        
    except subprocess.TimeoutExpired:
        print_error("MediaFire page fetch timeout")
        return None
    except Exception as e:
        print_error(f"MediaFire download error: {e}")
        return None


def download_gdrive(url: str, output_dir: Path) -> Optional[Path]:
    """Download from Google Drive"""
    print_info("Google Drive URL detected")
    
    # Extract file ID
    file_id_match = re.search(r'([0-9a-zA-Z_-]{33})', url)
    if not file_id_match:
        print_error("Invalid Google Drive URL")
        return None
    
    file_id = file_id_match.group(1)
    
    try:
        # Get confirmation token
        confirm_url = f"https://docs.google.com/uc?export=download&id={file_id}"
        
        wget_result = subprocess.run([
            "wget", "--quiet", "--save-cookies", "/tmp/cookies.txt",
            "--keep-session-cookies", "--no-check-certificate",
            confirm_url, "-O-"
        ], capture_output=True, text=True, timeout=60)
        
        if wget_result.returncode != 0:
            print_error("Failed to get Google Drive confirmation")
            return None
        
        # Extract confirmation code
        confirm_match = re.search(r'confirm=([0-9A-Za-z_]+)', wget_result.stdout)
        if not confirm_match:
            print_error("No confirmation needed, trying direct download")
            confirm_code = ""
        else:
            confirm_code = confirm_match.group(1)
        
        # Download with confirmation
        download_url = f"https://docs.google.com/uc?export=download&confirm={confirm_code}&id={file_id}"
        
        # Use aria2c with cookies
        output_file = output_dir / f"gdrive_{file_id}"
        aria_cmd = [
            "aria2c", "-c", "-s16", "-x16", "-m10",
            "--console-log-level=warn", "--summary-interval=0",
            "--check-certificate=false", "--load-cookies", "/tmp/cookies.txt",
            "--out", output_file.name, download_url
        ]
        
        result = subprocess.run(aria_cmd, cwd=output_dir, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0 and output_file.exists():
            print_success(f"Downloaded from Google Drive: {output_file.name}")
            return output_file
        
    except subprocess.TimeoutExpired:
        print_error("Google Drive download timeout")
    except Exception as e:
        print_error(f"Google Drive download error: {e}")
    
    return None


def download_afh(url: str, output_dir: Path) -> Optional[Path]:
    """Download from AndroidFileHost using afh_dl.py"""
    print_info("AndroidFileHost URL detected")
    
    # Use existing afh_dl.py script
    from dumprx.core.config import Config
    config = Config()
    
    afh_script = config.utils_dir / "downloaders" / "afh_dl.py"
    if not afh_script.exists():
        print_error("afh_dl.py not found")
        return None
    
    try:
        result = subprocess.run([
            "python3", str(afh_script), url
        ], cwd=output_dir, capture_output=True, text=True, timeout=1800)
        
        if result.returncode == 0:
            # Find downloaded file
            downloaded_files = [f for f in output_dir.iterdir() if f.is_file() and f.stat().st_size > 0]
            if downloaded_files:
                latest_file = max(downloaded_files, key=lambda f: f.stat().st_mtime)
                print_success(f"Downloaded from AFH: {latest_file.name}")
                return latest_file
        
        print_error(f"AFH download failed: {result.stderr}")
        
    except subprocess.TimeoutExpired:
        print_error("AFH download timeout")
    except Exception as e:
        print_error(f"AFH download error: {e}")
    
    return None