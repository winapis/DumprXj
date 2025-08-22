"""
Advanced Telegram Bot Integration for DumprX
Interactive commands: /extract, /status, /queue, /cancel, /help
Queue management with intelligent queuing
Real-time progress notifications
Beautiful formatted messages with device info and emojis
Comprehensive error handling and debugging
"""

import asyncio
import logging
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

try:
    from telegram import Update, Bot, BotCommand
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("python-telegram-bot not installed. Telegram bot features disabled.")

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ExtractionJob:
    """Represents a firmware extraction job"""
    id: str
    user_id: int
    username: str
    firmware_url: str
    filename: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    error_message: str = ""
    device_info: Dict[str, str] = None
    file_size: int = 0
    extracted_files: List[str] = None
    git_repo_url: str = ""

class TelegramBotManager:
    """Advanced Telegram bot for DumprX automation"""
    
    def __init__(self, config, dumper):
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot not installed")
        
        self.config = config
        self.dumper = dumper
        self.bot_token = self._get_bot_token()
        self.chat_id = self._get_chat_id()
        
        if not self.bot_token:
            raise ValueError("Telegram bot token not found")
        
        self.application = Application.builder().token(self.bot_token).build()
        self.bot = self.application.bot
        
        # Job management
        self.jobs: Dict[str, ExtractionJob] = {}
        self.job_queue = asyncio.Queue()
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.max_concurrent_jobs = 2
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'cancelled_jobs': 0,
            'total_data_processed': 0,
            'bot_start_time': datetime.now()
        }
        
        self._setup_handlers()
    
    def _get_bot_token(self) -> Optional[str]:
        """Get Telegram bot token from config or environment"""
        
        # Try environment variable first
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if token:
            return token
        
        # Try config file
        token_file = Path(self.config.project_dir) / '.tg_token'
        if token_file.exists():
            return token_file.read_text().strip()
        
        return None
    
    def _get_chat_id(self) -> Optional[str]:
        """Get Telegram chat ID from config"""
        
        # Try environment variable first
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if chat_id:
            return chat_id
        
        # Try config file
        chat_file = Path(self.config.project_dir) / '.tg_chat'
        if chat_file.exists():
            return chat_file.read_text().strip()
        
        return None
    
    def _setup_handlers(self):
        """Setup Telegram command handlers"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("extract", self._cmd_extract))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("queue", self._cmd_queue))
        self.application.add_handler(CommandHandler("cancel", self._cmd_cancel))
        self.application.add_handler(CommandHandler("stats", self._cmd_stats))
        self.application.add_handler(CommandHandler("logs", self._cmd_logs))
        
        # Message handler for URLs
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self._handle_message
        ))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
    
    async def start_bot(self):
        """Start the Telegram bot"""
        
        logger.info("Starting Telegram bot...")
        
        # Set bot commands
        commands = [
            BotCommand("start", "🚀 Start the bot"),
            BotCommand("help", "❓ Show help message"),
            BotCommand("extract", "📦 Extract firmware from URL"),
            BotCommand("status", "📊 Show extraction status"),
            BotCommand("queue", "📋 Show job queue"),
            BotCommand("cancel", "❌ Cancel extraction job"),
            BotCommand("stats", "📈 Show bot statistics"),
            BotCommand("logs", "📄 Get recent logs")
        ]
        
        await self.bot.set_my_commands(commands)
        
        # Start job processor
        asyncio.create_task(self._process_job_queue())
        
        # Send startup notification
        if self.chat_id:
            await self._send_startup_notification()
        
        # Start polling
        await self.application.run_polling()
    
    async def _send_startup_notification(self):
        """Send bot startup notification"""
        
        message = (
            "🤖 **DumprX Bot Started!**\n\n"
            "✅ Bot is online and ready to process firmware extractions\n"
            f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"⚙️ Max concurrent jobs: {self.max_concurrent_jobs}\n\n"
            "Send me a firmware URL or use /help for commands!"
        )
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        
        welcome_message = (
            "🚀 **Welcome to DumprX Bot!**\n\n"
            "I can help you extract and analyze firmware files automatically.\n\n"
            "**What I can do:**\n"
            "📦 Extract firmware from various formats\n"
            "🔍 Auto-detect device information\n"
            "🌐 Download from multiple cloud services\n"
            "📊 Track extraction progress\n"
            "📋 Manage extraction queue\n\n"
            "**Quick Start:**\n"
            "1. Send me a firmware URL\n"
            "2. Use /extract <url> command\n"
            "3. Check progress with /status\n\n"
            "Use /help for full command list!"
        )
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        
        help_message = (
            "🤖 **DumprX Bot Commands**\n\n"
            "**Main Commands:**\n"
            "/extract <url> - 📦 Extract firmware from URL\n"
            "/status [job_id] - 📊 Show extraction status\n"
            "/queue - 📋 Show job queue\n"
            "/cancel <job_id> - ❌ Cancel extraction job\n\n"
            "**Information:**\n"
            "/stats - 📈 Show bot statistics\n"
            "/logs - 📄 Get recent logs\n"
            "/help - ❓ Show this help\n\n"
            "**Supported Services:**\n"
            "🔗 Direct HTTP/HTTPS downloads\n"
            "☁️ Mega.nz, Google Drive, OneDrive\n"
            "📁 MediaFire, AndroidFileHost\n"
            "🐙 GitHub/GitLab releases\n\n"
            "**Supported Formats:**\n"
            "📦 ZIP, RAR, 7Z, TAR archives\n"
            "🤖 Android OTA, Fastboot images\n"
            "🏭 Manufacturer-specific formats\n"
            "   • Samsung TAR.MD5\n"
            "   • Xiaomi MIUI packages\n"
            "   • OPPO/OnePlus OZIP, OFP, OPS\n"
            "   • Huawei UPDATE.APP\n"
            "   • LG KDZ/DZ\n"
            "   • HTC RUU\n"
            "   • Sony FTF/SIN\n"
            "   • And more!\n\n"
            "💡 **Tips:**\n"
            "• Simply send a URL to start extraction\n"
            "• Use job IDs for specific operations\n"
            "• Check queue regularly for status updates"
        )
        
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _cmd_extract(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /extract command"""
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a firmware URL!\n\n"
                "**Usage:** `/extract <firmware_url>`\n\n"
                "**Example:**\n"
                "`/extract https://example.com/firmware.zip`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        firmware_url = context.args[0]
        await self._queue_extraction(update, firmware_url)
    
    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot errors"""
        
        logger.error(f"Telegram bot error: {context.error}")
        
        if update and hasattr(update, 'effective_message'):
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred while processing your request. Please try again later."
                )
            except Exception:
                pass