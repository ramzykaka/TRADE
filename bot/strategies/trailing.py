# bot/strategies/trailing.py
import asyncio
from decimal import Decimal
from datetime import datetime
from bot.service.binance_api import BinanceAPI
from bot.handlers.commands import setup_extended
setup_extended(application)
from telegram import Update
from telegram.ext import ContextTypes

class ATRTrailingStop:
    def __init__(self):
        self.binance = BinanceAPI()
        self.positions = {}        # {symbol: data}
        self.running = True

    # ---------- حساب ATR ----------
    def atr(self, symbol: str, period: int = 14) -> float:
        klines = self.binance.get_klines(symbol, interval="15m", limit=period + 1)
        trs = []
        for i in range(1, len(klines)):
            high  = float(klines[i][2])
            low   = float(klines[i][3])
            prev_close = float(klines[i-1][4])
            tr = max(high - low,
                     abs(high - prev_close),
                     abs(low  - prev_close))
            trs.append(tr)
        atr = sum(trs[-period:]) / period if len(trs) >= period else trs[-1]
        return atr

    # ---------- فتح مركز مع تريلينج ----------
    async def open_trailing_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     symbol: str, side: str, qty: float):
        # سعر الدخول
        ticker = self.binance.get_ticker(symbol)
        entry_price = float(ticker["lastPrice"])
        atr_val = self.atr(symbol)
        distance = atr_val * 1.5
        sl_price = entry_price - distance if side.upper() == "BUY" else entry_price + distance

        # أمر الدخول
        order = self.binance.place_market_order(symbol, side.upper(), qty)
        if "error" in order:
            await update.message.reply_text(order["error"])
            return

        # تسجيل المركز
        self.positions[symbol] = {
            "side": side.upper(),
            "qty": qty,
            "entry": entry_price,
            "sl_price": sl_price,
            "max_price": entry_price,
            "atr": atr_val,
            "tighten_pct": Decimal("0.3"),
            "profit_target_pct": Decimal("1")
        }

        msg = (
            f"✅ تم فتح مركز {side.upper()} {symbol}\n"
            f"السعر: {entry_price}\n"
            f"وقف أولي: {sl_price:.2f}"
        )
        await update.message.reply_text(msg)

    # ---------- مراقبة التريلينج ----------
    async def monitor_trailing(self, context: ContextTypes.DEFAULT_TYPE):
        while self.running:
            for symbol, data in list(self.positions.items()):
                ticker = self.binance.get_ticker(symbol)
                current_price = float(ticker["lastPrice"])

                # تحديث أعلى سعر
                if data["side"] == "BUY":
                    data["max_price"] = max(data["max_price"], current_price)
                    profit_pct = (current_price - data["entry"]) / data["entry"] * 100
                else:
                    data["max_price"] = min(data["max_price"], current_price)
                    profit_pct = (data["entry"] - current_price) / data["entry"] * 100

                # التضييق بعد 1 % ربح
                if Decimal(str(profit_pct)) >= data["profit_target_pct"]:
                    new_sl = data["max_price"] * (1 - data["tighten_pct"]/100)
                    if data["side"] == "SELL":
                        new_sl = data["max_price"] * (1 + data["tighten_pct"]/100)

                    # تحديث الوقف إذا تحرّك لصالحنا
                    if (data["side"] == "BUY" and new_sl > data["sl_price"]) or \
                       (data["side"] == "SELL" and new_sl < data["sl_price"]):
                        data["sl_price"] = new_sl
                        if not self.cfg.get("silent", False):
                            await context.bot.send_message(
                                chat_id=context.job.chat_id,
                                text=f"📈 تم تحريك الوقف إلى {new_sl:.2f}"
                            )

                # إغلاق عند الوصول للوقف
                if (data["side"] == "BUY" and current_price <= data["sl_price"]) or \
                   (data["side"] == "SELL" and current_price >= data["sl_price"]):
                    self.binance.place_market_order(symbol,
                                                    "SELL" if data["side"] == "BUY" else "BUY",
                                                    data["qty"])
                    await context.bot.send_message(
                        chat_id=context.job.chat_id,
                        text=f"🔒 تم إغلاق {symbol} عند {current_price:.2f}"
                    )
                    del self.positions[symbol]

            await asyncio.sleep(60)  # مراقبة كل دقيقة

    # ---------- أمر /trail ----------
    async def trail_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 2:
            await update.message.reply_text(
                "الاستخدام: /trail <رمز> <كمية> <BUY|SELL>"
            )
            return
        symbol, qty, side = context.args[0], float(context.args[1]), context.args[2]
        await self.open_trailing_position(update, context, symbol, side, qty)

# instance جاهزة
atr_trailing = ATRTrailingStop()