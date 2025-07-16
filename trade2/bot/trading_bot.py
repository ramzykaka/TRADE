# trading_bot.py
from telegram.ext import Application, Defaults
from telegram.constants import ParseMode
from utils.config import load_config
import logging

class TradingBot:
    def __init__(self):
        self.config = load_config()  # تحميل الإعدادات هنا
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        defaults = Defaults(parse_mode=ParseMode.HTML)
        application = Application.builder() \
            .token(self.config['TELEGRAM_TOKEN']) \
            .defaults(defaults) \
            .build()
        
        from bot.handlers import setup
        setup(application)  # تسجيل جميع المعالجات
        
        application.run_polling()