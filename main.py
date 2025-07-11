import os
import asyncio
import logging
import numpy as np
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from binance import AsyncClient
from sklearn.ensemble import RandomForestClassifier
import joblib
from datetime import datetime

# ------------------- Configuration -------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartTraderPro:
    def __init__(self):
        self.client = None
        self.active_trades = {}
        self.strategies = {
            'MA Crossover': self.ma_strategy,
            'Bollinger Bands': self.bollinger_strategy,
            'AI Predictor': self.ai_strategy,
            'Hybrid': self.hybrid_strategy
        }
        self.model = self.load_ai_model()

    async def initialize(self):
        self.client = await AsyncClient.create(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )

    def load_ai_model(self):
        try:
            return joblib.load('ai_model.pkl')
        except:
            logger.warning("Using default AI model")
            return RandomForestClassifier()

    # --------------- Core Trading Methods ---------------
    async def execute_trade(self, symbol, action):
        if len(self.active_trades) >= int(os.getenv('MAX_TRADES', 3)):
            return "❌ Maximum active trades reached"

        balance = float((await self.client.get_asset_balance('USDT'))['free'])
        amount = min(
            float(os.getenv('TRADE_AMOUNT_USDT', 10)) / (await self.get_price(symbol)),
            balance * float(os.getenv('RISK_PER_TRADE', 0.02))
        )

        if action == 'buy':
            order = await self.client.create_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=round(amount, 4)
            )
            self.active_trades[symbol] = {
                'entry_price': float(order['fills'][0]['price']),
                'stop_loss': float(order['fills'][0]['price']) * 0.98,
                'take_profit': float(order['fills'][0]['price']) * 1.05,
                'quantity': float(order['executedQty']),
                'peak_price': float(order['fills'][0]['price'])
            }
            return f"✅ Bought {order['executedQty']} {symbol}"
        
        elif action == 'sell':
            order = await self.client.create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=round(amount, 4)
            )
            if symbol in self.active_trades:
                del self.active_trades[symbol]
            return f"✅ Sold {order['executedQty']} {symbol}"

    # --------------- Smart Stop-Loss System ---------------
    async def update_stop_loss(self, symbol):
        current_price = await self.get_price(symbol)
        trade = self.active_trades[symbol]
        
        # Dynamic Trailing Stop (1.5% from peak)
        trade['peak_price'] = max(trade['peak_price'], current_price)
        new_stop = trade['peak_price'] * 0.985
        
        # Volatility Adjustment
        volatility = await self.get_volatility(symbol)
        if volatility > 0.05:
            new_stop = max(new_stop, current_price * 0.99)
        
        # Update only if beneficial
        trade['stop_loss'] = max(new_stop, trade['stop_loss'])
        logger.info(f"🔄 {symbol} SL updated to {trade['stop_loss']:.4f}")

    # --------------- Trading Strategies ---------------
    async def ma_strategy(self, symbol='BTCUSDT'):
        klines = await self.client.get_klines(symbol=symbol, interval='1h', limit=100)
        closes = [float(k[4]) for k in klines]
        sma9 = np.mean(closes[-9:])
        sma21 = np.mean(closes[-21:])
        return 'buy' if sma9 > sma21 else 'sell' if sma9 < sma21 else 'hold'

    async def bollinger_strategy(self, symbol='BTCUSDT'):
        klines = await self.client.get_klines(symbol=symbol, interval='4h', limit=100)
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['close'] = df['close'].astype(float)
        df['MA20'] = df['close'].rolling(20).mean()
        df['Upper'] = df['MA20'] + 2 * df['close'].rolling(20).std()
        df['Lower'] = df['MA20'] - 2 * df['close'].rolling(20).std()
        last_close = df['close'].iloc[-1]
        return 'buy' if last_close <= df['Lower'].iloc[-1] else 'sell' if last_close >= df['Upper'].iloc[-1] else 'hold'

    async def ai_strategy(self, symbol='BTCUSDT'):
        klines = await self.client.get_klines(symbol=symbol, interval='1h', limit=500)
        features = self.prepare_features(klines)
        prediction = self.model.predict([features])[0]
        return 'buy' if prediction == 1 else 'sell' if prediction == 0 else 'hold'

    async def hybrid_strategy(self, symbol='BTCUSDT'):
        signals = [
            await self.ma_strategy(symbol),
            await self.bollinger_strategy(symbol),
            await self.ai_strategy(symbol)
        ]
        return 'buy' if signals.count('buy') >= 2 else 'sell' if signals.count('sell') >= 2 else 'hold'

    # --------------- Telegram Interface ---------------
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📊 Market Analysis", callback_data='analyze'),
             InlineKeyboardButton("💰 Balance", callback_data='balance')],
            [InlineKeyboardButton("⚡ Auto Trade", callback_data='trade'),
             InlineKeyboardButton("🛑 Close All", callback_data='close')],
            [InlineKeyboardButton("⚙ Settings", callback_data='settings')]
        ]
        await update.message.reply_text(
            "🚀 Smart Trading Bot",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == 'analyze':
            await self.show_analysis(query)
        elif query.data == 'trade':
            await self.auto_trade(query)
        elif query.data == 'close':
            await self.close_trades(query)

    async def show_analysis(self, query):
        analysis = []
        for name, strategy in self.strategies.items():
            signal = await strategy()
            analysis.append(f"{name}: {signal.upper()}")
        
        await query.edit_message_text(
            "📊 Market Analysis:\n" + "\n".join(analysis),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data='analyze')],
                [InlineKeyboardButton("🔙 Back", callback_data='main')]
            ])
        )

    # --------------- Main Loop ---------------
    async def run(self):
        await self.initialize()
        
        app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CallbackQueryHandler(self.handle_button))
        
        await app.initialize()
        await app.start()
        
        try:
            while True:
                await self.monitor_trades()
                await asyncio.sleep(60)
        finally:
            await app.stop()
            await self.client.close_connection()

    async def monitor_trades(self):
        for symbol in list(self.active_trades.keys()):
            try:
                await self.update_stop_loss(symbol)
                current_price = await self.get_price(symbol)
                
                if current_price <= self.active_trades[symbol]['stop_loss']:
                    await self.execute_trade(symbol, 'sell')
                    logger.info(f"🔴 Stop-Loss triggered for {symbol}")
                    
                elif current_price >= self.active_trades[symbol]['take_profit']:
                    await self.execute_trade(symbol, 'sell')
                    logger.info(f"🟢 Take-Profit triggered for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")

if __name__ == '__main__':
    bot = SmartTraderPro()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")