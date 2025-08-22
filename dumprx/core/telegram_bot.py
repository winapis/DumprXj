import asyncio
import logging
from typing import Dict, Any, Optional
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, config_manager):
        self.config = config_manager.get_telegram_config()
        self.enabled = config_manager.is_telegram_enabled()
        self.bot = None
        
        if self.enabled:
            self.bot = Bot(token=self.config['token'])
    
    async def send_notification(self, firmware_info: Dict[str, Any], repo_url: str):
        if not self.enabled:
            return
        
        try:
            message = self._format_message(firmware_info, repo_url)
            await self.bot.send_message(
                chat_id=self.config['chat_id'],
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            logger.info("Telegram notification sent successfully")
            
        except TelegramError as e:
            logger.error(f"Failed to send Telegram notification: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram notification: {e}")
    
    def send_notification_sync(self, firmware_info: Dict[str, Any], repo_url: str):
        if not self.enabled:
            return
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self.send_notification(firmware_info, repo_url))
                loop.run_until_complete(task)
            else:
                asyncio.run(self.send_notification(firmware_info, repo_url))
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    
    def _format_message(self, firmware_info: Dict[str, Any], repo_url: str) -> str:
        brand = firmware_info.get('brand', 'Unknown')
        device = firmware_info.get('codename', 'Unknown')
        platform = firmware_info.get('platform', 'Unknown')
        android_version = firmware_info.get('release', 'Unknown')
        kernel_version = firmware_info.get('kernel_version', '')
        fingerprint = firmware_info.get('fingerprint', 'Unknown')
        
        message_parts = [
            f"🔥 <b>New Firmware Dump</b>",
            f"",
            f"📱 <b>Brand:</b> {brand}",
            f"📱 <b>Device:</b> {device}",
            f"🔧 <b>Platform:</b> {platform}",
            f"🤖 <b>Android Version:</b> {android_version}"
        ]
        
        if kernel_version:
            message_parts.append(f"🔩 <b>Kernel Version:</b> {kernel_version}")
        
        message_parts.extend([
            f"🔍 <b>Fingerprint:</b> <code>{fingerprint}</code>",
            f"",
            f"📁 <a href=\"{repo_url}\">View Repository</a>"
        ])
        
        return "\n".join(message_parts)