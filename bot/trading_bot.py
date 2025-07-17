# bot/trading_bot.py
import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, Defaults
)
from telegram.constants import ParseMode
from utils.config import settings
from binance.client import Client
from binance.exceptions import BinanceAPIException

class TradingBot:
    def __init__(self):
        self.config = settings
        self.logger = logging.getLogger(__name__)

        # Binance Client
        self.binance = Client(
            self.config.BINANCE_API_KEY,
            self.config.BINANCE_SECRET,
            testnet=self.config.USE_TESTNET
        )

    # -----------------------------------------
    # معالج أمر /start
    async def start(self, update, context):
        await update.message.reply_text(
            "👋 أهلاً! أنا بوت التداول الخاص بك.\n"
            "يمكنك استخدام الأوامر لاحقاً أو إرسال أي رسالة لاختبار الاستجابة."
        )

    # معالج أي رسالة نصية
    async def echo(self, update, context):
        self.logger.info(
            f"📨 Received: '{update.message.text}' from user {update.effective_user.id}"
        )
        await update.message.reply_text(f"✅ استلمت: {update.message.text}")

    # -----------------------------------------
    def run(self):
        defaults = Defaults(parse_mode=ParseMode.HTML)
        application = (
            Application.builder()
            .token(self.config.TELEGRAM_TOKEN)
            .defaults(defaults)
            .build()
        )

        # المعالجات الأساسية
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))

        # تسجيل الأوامر العربية الجديدة
        from bot.handlers import setup
        setup(application)

        self.logger.info("🔄 Bot is now listening for messages...")
        application.run_polling()