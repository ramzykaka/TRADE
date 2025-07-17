from bot.trading_bot import TradingBot
from bot.handlers.commands import setup   # المسار الصحيح
from bot.strategies.trailing import atr_trailing
job_queue = application.job_queue
job_queue.run_repeating(atr_trailing.monitor_trailing, interval=60, chat_id=CHAT_ID)

if __name__ == "__main__":
    bot = TradingBot()
    application = bot.build_application()   # أو أي دالة تُنشئ الـ application
    setup(application)  # تسجيل الأوامر
    bot.run()           # يبدأ الـ polling