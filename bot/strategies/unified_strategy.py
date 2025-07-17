# bot/strategies/unified_strategy.py
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
import requests
from transformers import pipeline
from bot.service.binance_api import BinanceAPI

class UnifiedStrategy:
    # -------------------- 1) إعدادات --------------------
    def __init__(self):
        self.binance   = BinanceAPI()
        self.symbol    = "BTCUSDT"
        self.fixed_usd = Decimal("10")   # قيمة الصفقة القابلة للتعديل
        self.max_loss_pct = Decimal("5")  # حد الخسارة اليومي
        self.news_key  = "YOUR_NEWSAPI_KEY"  # ضع مفتاحك
        self.sentiment = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        self.running   = True

    # -------------------- 2) مولّد الإشارات --------------------
    def ema(self, period: int) -> float:
        klines = self.binance.client.get_klines(symbol=self.symbol,
                                                interval="5m",
                                                limit=period + 5)
        closes = [float(k[4]) for k in klines]
        return pd.Series(closes).ewm(span=period, adjust=False).mean().iloc[-1]

    def rsi(self, period: int = 14) -> float:
        klines = self.binance.client.get_klines(symbol=self.symbol,
                                                interval="5m",
                                                limit=period + 5)
        closes = [float(k[4]) for k in klines]
        delta = pd.Series(closes).diff()
        gain  = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs    = gain / loss
        rsi   = 100 - (100 / (1 + rs)).iloc[-1]
        return rsi

    def news_sentiment_score(self) -> float:
        url = f"https://newsapi.org/v2/everything?q={self.symbol}&sortBy=publishedAt&apiKey={self.news_key}"
        try:
            data = requests.get(url, timeout=5).json()
            texts = [a["title"] for a in data.get("articles", [])[:10]]
            scores = [self.sentiment(t)[0]["score"] for t in texts]
            return sum(scores) / len(scores) if scores else 0.5
        except Exception:
            return 0.5

    def final_signal(self) -> str:
        ema_fast = self.ema(9)
        ema_slow = self.ema(21)
        rsi_val  = self.rsi()
        sent     = self.news_sentiment_score()

        if ema_fast > ema_slow and rsi_val < 35 and sent > 0.6:
            return "BUY"
        elif ema_fast < ema_slow and rsi_val > 65 and sent < 0.4:
            return "SELL"
        return "HOLD"

    # -------------------- 3) Trailing Stop-Loss --------------------
    def atr(self, period: int = 14) -> float:
        klines = self.binance.client.get_klines(symbol=self.symbol,
                                                interval="5m",
                                                limit=period + 1)
        trs = []
        for i in range(1, len(klines)):
            high = float(klines[i][2])
            low  = float(klines[i][3])
            prev_close = float(klines[i-1][4])
            tr = max(high - low,
                     abs(high - prev_close),
                     abs(low - prev_close))
            trs.append(tr)
        return sum(trs[-period:]) / period if trs else 0

    def open_trailing(self, side: str):
        qty   = float(self.fixed_usd) / float(
            self.binance.client.get_ticker(symbol=self.symbol)["lastPrice"])
        atr_v = self.atr()
        sl    = atr_v * 1.5
        self.binance.client.create_order(symbol=self.symbol,
                                         side=side,
                                         type="MARKET",
                                         quantity=qty)
        self.trail.track_position(self.symbol, side, qty, sl)

    # -------------------- 4) وقف حماية يومي --------------------
    def daily_loss(self) -> float:
        try:
            balance = float(self.binance.client.get_asset_balance(asset="USDT")["free"])
            # نفترض أن start_balance محفوظ سابقاً
            return (start_balance - balance) / start_balance * 100
        except Exception:
            return 0

    # -------------------- 5) اللوب الرئيسي --------------------
    async def run_forever(self):
        while self.running:
            signal = self.final_signal()
            if signal == "BUY":
                self.open_trailing("BUY")
            elif signal == "SELL":
                self.open_trailing("SELL")

            # تقرير يومي
            if datetime.utcnow().hour == 0 and datetime.utcnow().minute == 0:
                loss = self.daily_loss()
                if loss >= float(self.max_loss_pct):
                    self.running = False
                    print("⚠️ تم إيقاف البوت بسبب الحد اليومي")
                    break

            await asyncio.sleep(30)

# instance جاهزة
unified = UnifiedStrategy()