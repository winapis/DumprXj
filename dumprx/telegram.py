#!/usr/bin/env python3

import asyncio
import requests
from typing import Optional

from dumprx.console import info, warning, error, step, success
from dumprx.config import config


class TelegramBot:
    
    def __init__(self):
        self.token = config.get('telegram', 'token')
        self.chat_id = config.get('telegram', 'chat_id', default='@DumprXDumps')
        self.enabled = config.get('telegram', 'enabled', default=True)
        
        if not self.token:
            self.enabled = False
    
    def is_enabled(self) -> bool:
        return self.enabled and bool(self.token)
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        if not self.is_enabled():
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            error(f"Failed to send Telegram message: {str(e)}")
            return False
    
    def send_start_notification(self, firmware_info: dict) -> bool:
        if not self.is_enabled():
            return False
        
        message = self._format_start_message(firmware_info)
        return self.send_message(message)
    
    def send_completion_notification(self, firmware_info: dict, repo_info: dict) -> bool:
        if not self.is_enabled():
            return False
        
        message = self._format_completion_message(firmware_info, repo_info)
        return self.send_message(message)
    
    def send_error_notification(self, firmware_info: dict, error_message: str) -> bool:
        if not self.is_enabled():
            return False
        
        message = self._format_error_message(firmware_info, error_message)
        return self.send_message(message)
    
    def _format_start_message(self, firmware_info: dict) -> str:
        brand = firmware_info.get('brand', 'Unknown')
        device = firmware_info.get('device', 'Unknown')
        
        message = f"""🚀 <b>DumprX - Firmware Processing Started</b>
        
<b>Brand:</b> {brand}
<b>Device:</b> {device}
<b>Status:</b> Processing...

⏳ Extraction and analysis in progress"""
        
        return message
    
    def _format_completion_message(self, firmware_info: dict, repo_info: dict) -> str:
        brand = firmware_info.get('brand', 'Unknown')
        device = firmware_info.get('device', 'Unknown')
        platform = firmware_info.get('platform', 'Unknown')
        android_version = firmware_info.get('android_version', 'Unknown')
        kernel_version = firmware_info.get('kernel_version', '')
        fingerprint = firmware_info.get('fingerprint', 'Unknown')
        
        git_org = repo_info.get('organization', 'Unknown')
        repo_name = repo_info.get('name', 'Unknown')
        branch = repo_info.get('branch', 'main')
        repo_url = repo_info.get('url', '')
        
        message = f"""✅ <b>DumprX - Firmware Dump Complete</b>

<b>Brand:</b> {brand}
<b>Device:</b> {device}
<b>Platform:</b> {platform}
<b>Android Version:</b> {android_version}"""
        
        if kernel_version:
            message += f"\n<b>Kernel Version:</b> {kernel_version}"
        
        message += f"""
<b>Fingerprint:</b> {fingerprint}

📁 <a href="{repo_url}">Repository Link</a>

🎉 Firmware successfully extracted and uploaded!"""
        
        return message
    
    def _format_error_message(self, firmware_info: dict, error_message: str) -> str:
        brand = firmware_info.get('brand', 'Unknown')
        device = firmware_info.get('device', 'Unknown')
        
        message = f"""❌ <b>DumprX - Processing Failed</b>

<b>Brand:</b> {brand}
<b>Device:</b> {device}
<b>Error:</b> {error_message}

💡 Please check the logs and try again."""
        
        return message


async def send_telegram_notification_async(message: str) -> bool:
    bot = TelegramBot()
    if not bot.is_enabled():
        return False
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, bot.send_message, message)


def send_telegram_notification(message: str) -> bool:
    bot = TelegramBot()
    return bot.send_message(message)


telegram_bot = TelegramBot()