"""
Telegram bot integration
"""

import asyncio
from typing import Dict, Any, Optional
import requests
import html

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole


class TelegramBot:
    """Handles Telegram notifications"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        self.base_url = f"https://api.telegram.org/bot{self.config.telegram.token}"
        
    def send_firmware_notification(self, firmware_info: Dict[str, Any], 
                                 git_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send firmware extraction notification
        
        Args:
            firmware_info: Information about the extracted firmware
            git_info: Information about git upload if available
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.config.telegram.token:
                self.console.warning("Telegram token not configured")
                return False
                
            message = self._create_firmware_message(firmware_info, git_info)
            
            return self._send_message(message)
            
        except Exception as e:
            self.console.error(f"Error sending Telegram notification: {e}")
            return False
            
    def send_error_notification(self, error_message: str, context: Dict[str, Any] = None) -> bool:
        """Send error notification to Telegram"""
        try:
            if not self.config.telegram.token:
                return False
                
            message = self._create_error_message(error_message, context)
            return self._send_message(message)
            
        except Exception as e:
            self.console.error(f"Error sending Telegram error notification: {e}")
            return False
            
    def send_status_update(self, status: str, details: Dict[str, Any] = None) -> bool:
        """Send status update to Telegram"""
        try:
            if not self.config.telegram.token:
                return False
                
            message = self._create_status_message(status, details)
            return self._send_message(message)
            
        except Exception as e:
            self.console.error(f"Error sending Telegram status update: {e}")
            return False
            
    def _create_firmware_message(self, firmware_info: Dict[str, Any], 
                               git_info: Optional[Dict[str, Any]] = None) -> str:
        """Create firmware notification message"""
        
        # Get firmware information
        brand = html.escape(firmware_info.get('brand', 'Unknown'))
        device = html.escape(firmware_info.get('device_name', 'Unknown'))
        model = html.escape(firmware_info.get('model', 'Unknown'))
        android_version = html.escape(firmware_info.get('android_version', 'Unknown'))
        fingerprint = html.escape(firmware_info.get('build_fingerprint', 'Unknown'))
        partitions = firmware_info.get('partitions', [])
        
        # Create message
        message = f"""🔥 <b>New Firmware Dump Available!</b>

📱 <b>Device Info:</b>
• <b>Brand:</b> {brand}
• <b>Device:</b> {device}
• <b>Model:</b> {model}
• <b>Android Version:</b> {android_version}

🔧 <b>Build Info:</b>
• <b>Fingerprint:</b> <code>{fingerprint}</code>

📦 <b>Extracted Partitions:</b>"""
        
        if partitions:
            # Group partitions for better display
            partition_list = ", ".join(sorted(partitions)[:10])  # Show first 10
            if len(partitions) > 10:
                partition_list += f" and {len(partitions) - 10} more..."
            message += f"\n• {partition_list}"
        else:
            message += "\n• No partitions detected"
            
        # Add git repository link if available
        if git_info:
            service = git_info.get('service', 'Git').title()
            repo_url = git_info.get('url', '')
            
            if repo_url:
                message += f"""

🔗 <b>{service} Repository:</b>
<a href="{repo_url}">Download Firmware</a>"""
                
        # Add footer
        message += f"""

⚡ Extracted with <b>DumprX v2.0.0</b>
🤖 Automated firmware dumping"""
        
        return message
        
    def _create_error_message(self, error_message: str, context: Dict[str, Any] = None) -> str:
        """Create error notification message"""
        
        message = f"""❌ <b>DumprX Error</b>

<b>Error:</b> <code>{html.escape(error_message)}</code>"""
        
        if context:
            if 'url' in context:
                message += f"\n<b>URL:</b> {html.escape(context['url'])}"
            if 'firmware_type' in context:
                message += f"\n<b>Type:</b> {html.escape(context['firmware_type'])}"
                
        message += f"\n\n🤖 DumprX v2.0.0"
        
        return message
        
    def _create_status_message(self, status: str, details: Dict[str, Any] = None) -> str:
        """Create status update message"""
        
        status_emoji = {
            'starting': '🚀',
            'downloading': '⬇️',
            'extracting': '📦',
            'uploading': '⬆️',
            'completed': '✅',
            'failed': '❌'
        }
        
        emoji = status_emoji.get(status.lower(), '🔄')
        
        message = f"""{emoji} <b>DumprX Status Update</b>

<b>Status:</b> {html.escape(status.title())}"""
        
        if details:
            for key, value in details.items():
                if value:
                    message += f"\n<b>{key.replace('_', ' ').title()}:</b> {html.escape(str(value))}"
                    
        return message
        
    def _send_message(self, message: str) -> bool:
        """Send message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                'chat_id': self.config.telegram.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                self.console.success("Telegram notification sent successfully")
                return True
            else:
                self.console.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.console.error(f"Error sending Telegram message: {e}")
            return False
            
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            if not self.config.telegram.token:
                self.console.error("Telegram token not configured")
                return False
                
            # Get bot info
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    bot_name = bot_info['result']['first_name']
                    self.console.success(f"Telegram bot connected: {bot_name}")
                    return True
                else:
                    self.console.error(f"Telegram API error: {bot_info}")
                    return False
            else:
                self.console.error(f"Telegram connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.console.error(f"Error testing Telegram connection: {e}")
            return False