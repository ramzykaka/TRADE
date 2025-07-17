# trade/mode_handler.py
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from service.binance_api import place_order, get_wallet_balance
from config import MAX_DAILY_LOSS

# متغيرات الجلسة
session_config = {
    "entry_price": Decimal("10"),
    "max_positions": 3,
    "daily_loss_pct": Decimal("5"),
    "silent": False,
    "positions": {},   # {symbol: {"qty": qty, "side": "BUY", "entry": price}}
    "start_balance": None,
    "today": datetime.utcnow().date()
}

# مساعدة
def _log(msg):
    if not session_config["silent"]:
        print(msg)  # يمكن استبدالها بـ send_message لاحقًا

async def set_price(update: Update, price: str):
    session_config["entry_price"] = Decimal(price)
    await update.message.reply_text(f"✅ تم تحديد سعر الدخول عند {price} دولار.")

async def set_count(update: Update, count: str):
    session_config["max_positions"] = int(count)
    await update.message.reply_text(f"✅ تم تحديد عدد الصفقات النشطة إلى {count}.")

async def set_daily_loss(update: Update, pct: str):
    session_config["daily_loss_pct"] = Decimal(pct)
    await update.message.reply_text(f"✅ تم تحديد الحد اليومي إلى {pct}%.")

async def start_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = await get_wallet_balance()
    session_config["start_balance"] = balance
    session_config["today"] = datetime.utcnow().date()
    session_config["positions"].clear()
    await update.message.reply_text(
        f"🚀 بدأ الوضع الجديد:\n"
        f"سعر الدخول: {session_config['entry_price']} $\n"
        f"عدد الصفقات: {session_config['max_positions']}\n"
        f"الحد اليومي: {session_config['daily_loss_pct']}%"
    )
    await _open_positions_if_needed(update)

async def toggle_silent(update: Update, mode: str):
    session_config["silent"] = (mode == "إيقاف")
    await update.message.reply_text("✅ تم تغيير وضع الإشعارات.")

# منطق فتح/إغلاق الصفقات
async def _open_positions_if_needed(update):
    open_count = len(session_config["positions"])
    needed = session_config["max_positions"] - open_count
    price = session_config["entry_price"]
    symbol = "BTCUSDT"
    qty = Decimal("0.001")  # يمكن جعله متغير لاحقًا
    for _ in range(needed):
        res = await place_order(symbol=symbol, side="BUY", quantity=float(qty), price=float(price), sl_pct=5)
        session_config["positions"][symbol + str(_)] = {"qty": qty, "entry": price}
        await update.message.reply_text(res)

async def _check_daily_loss():
    current = await get_wallet_balance()
    loss = (session_config["start_balance"] - current) / session_config["start_balance"] * 100
    if loss >= float(session_config["daily_loss_pct"]):
        return True
    return False

# استدعاء دوري (يُضاف لاحقاً في main.py)
# asyncio.create_task(_daily_report_loop())