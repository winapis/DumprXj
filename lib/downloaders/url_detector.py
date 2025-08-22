import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from lib.core.logger import logger

class URLDetector:
    SUPPORTED_DOMAINS = {
        'mega.nz': 'mega',
        'mediafire.com': 'mediafire',
        'drive.google.com': 'gdrive',
        '1drv.ms': 'onedrive',
        'androidfilehost.com': 'afh',
        'we.tl': 'wetransfer'
    }
    
    def __init__(self):
        self.patterns = {
            'mega': re.compile(r'mega\.nz/(?:file/|#!)([a-zA-Z0-9_-]+)'),
            'mediafire': re.compile(r'mediafire\.com/file/([a-zA-Z0-9]+)'),
            'gdrive': re.compile(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)'),
            'onedrive': re.compile(r'1drv\.ms/[a-zA-Z]/([a-zA-Z0-9_-]+)'),
            'afh': re.compile(r'androidfilehost\.com/\?fid=([0-9]+)'),
            'wetransfer': re.compile(r'we\.tl/t-([a-zA-Z0-9_-]+)')
        }
    
    def detect_url_type(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        for supported_domain, url_type in self.SUPPORTED_DOMAINS.items():
            if supported_domain in domain:
                return url_type
        
        if url.startswith(('http://', 'https://', 'ftp://')):
            return 'direct'
        
        return None
    
    def extract_file_id(self, url: str, url_type: str) -> Optional[str]:
        if url_type in self.patterns:
            match = self.patterns[url_type].search(url)
            return match.group(1) if match else None
        return None
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        url_type = self.detect_url_type(url)
        
        result = {
            'url': url,
            'type': url_type,
            'valid': url_type is not None,
            'file_id': None
        }
        
        if url_type and url_type != 'direct':
            result['file_id'] = self.extract_file_id(url, url_type)
        
        return result