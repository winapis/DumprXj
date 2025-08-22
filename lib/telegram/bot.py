import asyncio
import aiohttp
from typing import Optional, Dict, Any
from pathlib import Path
from lib.core.logger import logger
from lib.core.config import config
from lib.core.exceptions import TelegramError

class TelegramBot:
    def __init__(self):
        self.token = self._get_token_from_file('.tg_token')
        self.chat_id = self._get_token_from_file('.tg_chat') or config.get('telegram.chat_id')
        self.enabled = config.get('telegram.enabled', True) and bool(self.token)
        
        if self.enabled:
            self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def _get_token_from_file(self, filename: str) -> Optional[str]:
        try:
            with open(filename, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
    
    async def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        if not self.enabled:
            logger.info("Telegram notifications disabled")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': parse_mode
                }
                
                async with session.post(f"{self.api_url}/sendMessage", data=data) as response:
                    if response.status == 200:
                        logger.success("Telegram notification sent")
                        return True
                    else:
                        logger.error(f"Telegram API error: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def notify_extraction_start(self, firmware_info: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        
        message = f"""
🔄 *DumprX Extraction Started*

📱 *Device:* {firmware_info.get('device', 'Unknown')}
📦 *Firmware:* {firmware_info.get('filename', 'Unknown')}
🔧 *Type:* {firmware_info.get('type', 'Unknown')}
⏰ *Started:* {firmware_info.get('timestamp', 'Unknown')}
        """
        
        await self.send_message(message.strip())
    
    async def notify_extraction_complete(self, result: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        
        status_emoji = "✅" if result.get('success') else "❌"
        status_text = "Success" if result.get('success') else "Failed"
        
        message = f"""
{status_emoji} *DumprX Extraction {status_text}*

📱 *Device:* {result.get('device', 'Unknown')}
📦 *Firmware:* {result.get('filename', 'Unknown')}
⏱ *Duration:* {result.get('duration', 'Unknown')}
📊 *Files Extracted:* {result.get('file_count', 0)}
📁 *Output Size:* {result.get('output_size', 'Unknown')}
        """
        
        if result.get('git_url'):
            message += f"\n🔗 *Repository:* {result['git_url']}"
        
        if not result.get('success') and result.get('error'):
            message += f"\n❌ *Error:* {result['error']}"
        
        await self.send_message(message.strip())
    
    async def notify_error(self, error_info: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        
        message = f"""
❌ *DumprX Error*

🚨 *Error:* {error_info.get('error', 'Unknown error')}
📁 *File:* {error_info.get('file', 'Unknown')}
⏰ *Time:* {error_info.get('timestamp', 'Unknown')}
        """
        
        if error_info.get('traceback'):
            message += f"\n🔍 *Details:* ```{error_info['traceback'][:500]}```"
        
        await self.send_message(message.strip())

telegram_bot = TelegramBot()