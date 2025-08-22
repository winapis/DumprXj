"""
Enhanced Telegram bot and notification module.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from ..core.config import Config
from ..core.logger import get_logger


class TelegramManager:
    """Enhanced Telegram bot and notification system."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
    
    async def send_notification(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Send enhanced Telegram notification."""
        if not self.config.has_telegram_token():
            return {'success': False, 'error': 'No Telegram token configured'}
        
        if not AIOHTTP_AVAILABLE:
            return {'success': False, 'error': 'aiohttp not available for Telegram notifications'}
        
        self.logger.info("📱 Sending Telegram notification")
        
        try:
            message = self._create_message(extraction_result)
            result = await self._send_message(message)
            return result
            
        except Exception as e:
            self.logger.error(f"Telegram notification failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_message(self, extraction_result: Dict[str, Any]) -> str:
        """Create formatted message for Telegram."""
        system_info = extraction_result.get('system_info', {})
        
        message = "🚀 <b>DumprX Firmware Extraction Complete</b>\n\n"
        
        if system_info:
            message += f"📱 <b>Device:</b> {system_info.get('brand', 'Unknown')} {system_info.get('model', 'Unknown')}\n"
            message += f"🤖 <b>Android:</b> {system_info.get('android_version', 'Unknown')}\n"
            message += f"🏭 <b>Manufacturer:</b> {system_info.get('manufacturer', 'Unknown')}\n"
            message += f"🔒 <b>Security Patch:</b> {system_info.get('security_patch', 'Unknown')}\n"
        
        if extraction_result.get('git_upload', {}).get('success'):
            git_info = extraction_result['git_upload']
            message += f"\n📤 <b>Repository:</b> {git_info.get('repository_url', 'Available')}\n"
        
        message += f"\n✅ <b>Extraction Status:</b> Completed Successfully"
        
        return message
    
    async def _send_message(self, message: str) -> Dict[str, Any]:
        """Send message via Telegram API."""
        if not AIOHTTP_AVAILABLE:
            return {'success': False, 'error': 'aiohttp not available'}
            
        token = self.config.telegram_config['token']
        chat_id = self.config.telegram_config.get('chat_id', '@DumprXDumps')
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    return {'success': True}
                else:
                    error_text = await response.text()
                    return {'success': False, 'error': f"HTTP {response.status}: {error_text}"}