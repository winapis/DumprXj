import aiohttp
import asyncio
from typing import Dict, Optional, Any
import json
from urllib.parse import quote

from .ui import UI
from .logging import get_logger

logger = get_logger()


class TelegramError(Exception):
    pass


class TelegramBot:
    def __init__(self, token: str, chat_id: str = "@DumprXDumps", enabled: bool = True):
        self.token = token
        self.chat_id = chat_id
        self.enabled = enabled
        self.base_url = f"https://api.telegram.org/bot{token}"

    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        if not self.enabled or not self.token:
            return False

        url = f"{self.base_url}/sendMessage"
        
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        UI.print_success("Telegram notification sent")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Telegram API error: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_firmware_notification(self, firmware_info: Dict[str, Any], 
                                       git_url: str, branch: str = "main") -> bool:
        """Send a formatted notification about firmware extraction completion"""
        
        info = firmware_info.get('firmware_info')
        partitions = firmware_info.get('partitions', [])
        
        if not info:
            brand = model = version = platform = fingerprint = "Unknown"
            kernel_version = None
        else:
            brand = info.brand or "Unknown"
            model = info.model or "Unknown" 
            version = info.version or "Unknown"
            platform = info.platform or "Unknown"
            fingerprint = info.fingerprint or "Unknown"
            kernel_version = info.kernel_version

        message = self._format_firmware_message(
            brand, model, version, platform, fingerprint, 
            kernel_version, git_url, branch, len(partitions)
        )

        return await self.send_message(message)

    def _format_firmware_message(self, brand: str, model: str, version: str, 
                                platform: str, fingerprint: str, 
                                kernel_version: Optional[str], git_url: str, 
                                branch: str, partition_count: int) -> str:
        """Format the firmware notification message with HTML markup"""
        
        message = f"🎉 <b>New Firmware Dump Available!</b>\n\n"
        message += f"📱 <b>Brand:</b> {self._escape_html(brand)}\n"
        message += f"🔧 <b>Device:</b> {self._escape_html(model)}\n"
        message += f"🤖 <b>Platform:</b> {self._escape_html(platform)}\n"
        message += f"📋 <b>Android Version:</b> {self._escape_html(version)}\n"
        
        if kernel_version:
            message += f"🐧 <b>Kernel Version:</b> {self._escape_html(kernel_version)}\n"
        
        message += f"🔍 <b>Fingerprint:</b> <code>{self._escape_html(fingerprint)}</code>\n"
        message += f"💾 <b>Partitions Extracted:</b> {partition_count}\n\n"
        
        # Create a clean tree URL
        tree_url = f"{git_url.replace('.git', '')}/tree/{branch}" if git_url.endswith('.git') else f"{git_url}/tree/{branch}"
        message += f"📂 <a href=\"{tree_url}\">View Repository</a>\n"
        message += f"🌿 <b>Branch:</b> {self._escape_html(branch)}\n\n"
        message += f"⚡ <i>Extracted with DumprX v2.0</i>"

        return message

    async def send_download_start_notification(self, url: str, firmware_type: str) -> bool:
        """Send notification when download starts"""
        
        message = f"🔄 <b>Download Started</b>\n\n"
        message += f"📥 <b>Source:</b> {self._get_source_name(url)}\n"
        message += f"📱 <b>Type:</b> {self._escape_html(firmware_type)}\n"
        message += f"🔗 <b>URL:</b> <code>{self._truncate_url(url)}</code>\n\n"
        message += f"⏳ <i>Processing firmware...</i>"

        return await self.send_message(message)

    async def send_extraction_complete_notification(self, firmware_type: str, 
                                                   partition_count: int, 
                                                   processing_time: str) -> bool:
        """Send notification when extraction completes"""
        
        message = f"✅ <b>Extraction Complete</b>\n\n"
        message += f"📱 <b>Firmware Type:</b> {self._escape_html(firmware_type)}\n"
        message += f"💾 <b>Partitions:</b> {partition_count}\n"
        message += f"⏱️ <b>Processing Time:</b> {processing_time}\n\n"
        message += f"🚀 <i>Preparing for upload...</i>"

        return await self.send_message(message)

    async def send_error_notification(self, error_message: str, stage: str) -> bool:
        """Send error notification"""
        
        message = f"❌ <b>Error Occurred</b>\n\n"
        message += f"🔧 <b>Stage:</b> {self._escape_html(stage)}\n"
        message += f"💥 <b>Error:</b> <code>{self._escape_html(error_message)}</code>\n\n"
        message += f"🔍 <i>Check logs for more details</i>"

        return await self.send_message(message)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters for Telegram"""
        if not text:
            return ""
        
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;'))

    def _get_source_name(self, url: str) -> str:
        """Get a friendly name for the download source"""
        url_lower = url.lower()
        
        if 'mega.nz' in url_lower:
            return "Mega.nz"
        elif 'mediafire.com' in url_lower:
            return "MediaFire"
        elif 'drive.google.com' in url_lower:
            return "Google Drive"
        elif 'androidfilehost.com' in url_lower:
            return "AndroidFileHost"
        elif 'onedrive' in url_lower:
            return "OneDrive"
        else:
            return "Direct Link"

    def _truncate_url(self, url: str, max_length: int = 50) -> str:
        """Truncate URL for display"""
        if len(url) <= max_length:
            return url
        
        return url[:max_length-3] + "..."

    async def test_connection(self) -> bool:
        """Test if the bot token and chat ID are valid"""
        if not self.enabled or not self.token:
            return False

        try:
            # Test with getMe endpoint
            url = f"{self.base_url}/getMe"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return False
            
            # Test sending a simple message
            test_message = "🤖 DumprX Telegram integration test"
            return await self.send_message(test_message)
            
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False


class TelegramManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('telegram', {})
        self.bot = None
        
        if self.config.get('enabled', True) and self.config.get('token'):
            self.bot = TelegramBot(
                token=self.config['token'],
                chat_id=self.config.get('chat_id', '@DumprXDumps'),
                enabled=self.config.get('enabled', True)
            )

    async def send_firmware_notification(self, firmware_info: Dict[str, Any], 
                                       git_url: str, branch: str = "main") -> bool:
        """Send firmware extraction completion notification"""
        if not self.bot:
            return False
        
        UI.print_info("Sending Telegram notification...")
        return await self.bot.send_firmware_notification(firmware_info, git_url, branch)

    async def send_download_start(self, url: str, firmware_type: str) -> bool:
        """Send download start notification"""
        if not self.bot:
            return False
        
        return await self.bot.send_download_start_notification(url, firmware_type)

    async def send_extraction_complete(self, firmware_type: str, 
                                     partition_count: int, 
                                     processing_time: str) -> bool:
        """Send extraction completion notification"""
        if not self.bot:
            return False
        
        return await self.bot.send_extraction_complete_notification(
            firmware_type, partition_count, processing_time
        )

    async def send_error(self, error_message: str, stage: str) -> bool:
        """Send error notification"""
        if not self.bot:
            return False
        
        return await self.bot.send_error_notification(error_message, stage)

    async def test_connection(self) -> bool:
        """Test Telegram connection"""
        if not self.bot:
            UI.print_warning("Telegram not configured")
            return False
        
        UI.print_info("Testing Telegram connection...")
        success = await self.bot.test_connection()
        
        if success:
            UI.print_success("Telegram connection test successful")
        else:
            UI.print_error("Telegram connection test failed")
        
        return success

    def is_enabled(self) -> bool:
        """Check if Telegram notifications are enabled and configured"""
        return (self.bot is not None and 
                self.config.get('enabled', True) and 
                self.config.get('token'))