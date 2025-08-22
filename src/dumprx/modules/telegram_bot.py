"""
Enhanced Telegram bot and notification module.
"""

import asyncio
import requests
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
        
        self.logger.info("📱 Sending Telegram notification")
        
        try:
            message = self._create_message(extraction_result)
            
            if AIOHTTP_AVAILABLE:
                result = await self._send_message_async(message)
            else:
                result = self._send_message_sync(message)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Telegram notification failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_message(self, extraction_result: Dict[str, Any]) -> str:
        """Create formatted message for Telegram."""
        system_info = extraction_result.get('system_info', {})
        partition_info = extraction_result.get('partition_info', {})
        vendor_info = extraction_result.get('vendor_info', {})
        
        # Header with emoji
        message = "🚀 <b>DumprX v2.0 - Firmware Extraction Complete</b>\n\n"
        
        # Device Information
        if system_info:
            brand = system_info.get('brand', 'Unknown')
            model = system_info.get('model', 'Unknown')
            device = system_info.get('device', 'Unknown')
            
            message += f"📱 <b>Device:</b> {brand} {model}\n"
            message += f"🏷️  <b>Codename:</b> {device}\n"
            message += f"🤖 <b>Android:</b> {system_info.get('android_version', 'Unknown')}\n"
            message += f"🏭 <b>Manufacturer:</b> {system_info.get('manufacturer', 'Unknown')}\n"
            
            if system_info.get('security_patch', 'Unknown') != 'Unknown':
                message += f"🔒 <b>Security Patch:</b> {system_info.get('security_patch')}\n"
            
            if system_info.get('build_id', 'Unknown') != 'Unknown':
                message += f"🔨 <b>Build ID:</b> {system_info.get('build_id')}\n"
        
        # Extraction Statistics
        if partition_info:
            partitions_count = len(partition_info.get('partitions_found', []))
            boot_images_count = len(partition_info.get('boot_images', []))
            
            message += f"\n📊 <b>Extraction Results:</b>\n"
            message += f"• Partitions: {partitions_count}\n"
            message += f"• Boot Images: {boot_images_count}\n"
        
        # Repository Link
        if extraction_result.get('git_upload', {}).get('success'):
            git_info = extraction_result['git_upload']
            repo_url = git_info.get('repository_url')
            platform = git_info.get('platform', 'Git').title()
            
            if repo_url:
                message += f"\n📤 <b>{platform} Repository:</b>\n"
                message += f"🔗 <a href=\"{repo_url}\">View Repository</a>\n"
        
        # Vendor Information
        vendor = extraction_result.get('vendor_info', {}).get('vendor')
        if vendor:
            message += f"\n🏭 <b>Vendor Processing:</b> {vendor.upper()}\n"
        
        # Footer
        message += f"\n✅ <b>Status:</b> Extraction Completed Successfully"
        message += f"\n⚡ <b>Powered by:</b> DumprX v2.0 Python"
        
        return message
    
    async def _send_message_async(self, message: str) -> Dict[str, Any]:
        """Send message via Telegram API asynchronously."""
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
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return {
                            'success': True,
                            'message_id': response_data.get('result', {}).get('message_id')
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False, 
                            'error': f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            return {'success': False, 'error': f"Async send failed: {str(e)}"}
    
    def _send_message_sync(self, message: str) -> Dict[str, Any]:
        """Send message via Telegram API synchronously."""
        token = self.config.telegram_config['token']
        chat_id = self.config.telegram_config.get('chat_id', '@DumprXDumps')
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'message_id': response_data.get('result', {}).get('message_id')
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.RequestException as e:
            return {'success': False, 'error': f"Request failed: {str(e)}"}
    
    def send_file(self, file_path: Path, caption: str = "") -> Dict[str, Any]:
        """Send a file via Telegram."""
        if not self.config.has_telegram_token():
            return {'success': False, 'error': 'No Telegram token configured'}
        
        token = self.config.telegram_config['token']
        chat_id = self.config.telegram_config.get('chat_id', '@DumprXDumps')
        
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        
        try:
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, data=data, files=files, timeout=300)
                
                if response.status_code == 200:
                    return {'success': True}
                else:
                    return {
                        'success': False,
                        'error': f"File send failed: {response.text}"
                    }
                    
        except Exception as e:
            return {'success': False, 'error': f"File send error: {str(e)}"}
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Get information about the Telegram bot."""
        if not self.config.has_telegram_token():
            return {'success': False, 'error': 'No Telegram token configured'}
        
        token = self.config.telegram_config['token']
        url = f"https://api.telegram.org/bot{token}/getMe"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_data = response.json().get('result', {})
                return {
                    'success': True,
                    'bot_info': {
                        'username': bot_data.get('username'),
                        'first_name': bot_data.get('first_name'),
                        'id': bot_data.get('id'),
                        'can_join_groups': bot_data.get('can_join_groups'),
                        'can_read_all_group_messages': bot_data.get('can_read_all_group_messages')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"Bot info request failed: {response.text}"
                }
                
        except Exception as e:
            return {'success': False, 'error': f"Bot info error: {str(e)}"}