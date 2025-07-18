# main.py
import asyncio
from telegram.ext import Application
from utils.config import settings
from bot.trading_bot import TradingBot
from bot.handlers.commands import setup
from bot.strategies.unified_strategy import unified

if __name__ == "__main__":
    # إنشاء التطبيق
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()
    setup(application)  # تسجيل الأوامر العربية

    # تشغيل Trailing Stop-Loss كل 60 ثانية
    job_queue = application.job_queue
    job_queue.run_repeating(
        unified.monitor_trailing,
        interval=60,         # 60 ثانية
        first=0              # يبدأ فوراً
    )

    # تشغيل التداول التلقائي في خيط خلفي
    asyncio.create_task(unified.run_forever())

    # بدء الـ polling
    application.run_polling()