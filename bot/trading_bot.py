# bot/trading_bot.py
import asyncio
import logging
from telegram.ext import Application, Defaults
from telegram.constants import ParseMode
from utils.config import settings
from binance.client import Client  # pip install python-binance
from binance.exceptions import BinanceAPIException

class TradingBot:
    def __init__(self):
        self.config = settings
        self.logger = logging.getLogger(__name__)

        # إعداد Binance Client
        self.binance = Client(
            self.config.get('BINANCE_API_KEY'),
            self.config.get('BINANCE_SECRET'),
            testnet=self.config.get('USE_TESTNET', True)
        )

    # دالة مساعدة لفتح أمر شراء مع Stop-Loss
    async def buy_with_sl(self, symbol: str, usdt_amount: float, sl_pct: float = 2.0):
        try:
            # 1) احصل على سعر السوق
            ticker = self.binance.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])

            # 2) حدّد الكمية بالدقة المناسبة
            qty = round(usdt_amount / price, 5)

            # 3) أمر شراء سوقي
            buy_order = self.binance.order_market_buy(symbol=symbol, quantity=qty)
            self.logger.info(f"✅ شراء منفّذ: {buy_order}")

            # 4) حساب سعر Stop-Loss
            stop_price = round(price * (1 - sl_pct / 100), 2)

            # 5) أمر Stop-Loss
            sl_order = self.binance.create_order(
                symbol=symbol,
                side='SELL',
                type='STOP_LOSS_LIMIT',
                quantity=qty,
                stopPrice=stop_price,
                price=round(stop_price * 0.99, 2),  # أقل بقليل
                timeInForce='GTC'
            )
            self.logger.info(f"⛔️ Stop-Loss موضوع: {sl_order}")
            return buy_order, sl_order

        except BinanceAPIException as e:
            self.logger.error(f"خطأ Binance: {e}")
            return None, None

    # تشغيل البوت (كما كان)
    def run(self):
        defaults = Defaults(parse_mode=ParseMode.HTML)
        application = Application.builder() \
            .token(self.config['TELEGRAM_TOKEN']) \
            .defaults(defaults) \
            .build()

        from bot.handlers import setup
        setup(application)
        application.run_polling()
