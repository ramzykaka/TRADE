# trade/handlers/commands.py
# =========================
# الأوامر الأساسية (كما كانت) + الأوامر العربية الجديدة
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
from bot.strategies.trailing import atr_trailing
app.add_handler(CommandHandler("trail", atr_trailing.trail_command))
from trade.service.binance_api import BinanceAPI
from decimal import Decimal
import datetime

# ---------- الأوامر الأساسية ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("📊 تحليل السوق", callback_data="analyze")],
        [InlineKeyboardButton("⚡ تداول سريع", callback_data="quick_trade")],
        [InlineKeyboardButton("🛠 الإعدادات", callback_data="settings")],
    ]
    await update.message.reply_text(
        f"👋 مرحبًا {user.first_name}!\nاختر من القائمة أدناه:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ---------- الأوامر العربية الجديدة ----------
class ModeManager:
    """يدير أوامر الوضع الجديد"""
    def __init__(self):
        self.binance = BinanceAPI()
        self.cfg = {
            "entry_price": Decimal("10"),
            "max_positions": 3,
            "daily_loss_pct": Decimal("5"),
            "silent": False,
            "positions": {},
            "start_balance": None,
            "today": datetime.date.today(),
            "paused": False,
        }

    # أوامر التحكم
    async def set_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("الاستخدام: /حدد_السعر <القيمة>")
            return
        self.cfg["entry_price"] = Decimal(context.args[0])
        await update.message.reply_text(f"✅ تم تحديد السعر إلى {context.args[0]} دولار.")

    async def set_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("الاستخدام: /عدد_الصفقات <عدد>")
            return
        self.cfg["max_positions"] = int(context.args[0])
        await update.message.reply_text(f"✅ تم تحديد العدد إلى {context.args[0]}.")

    async def set_loss(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("الاستخدام: /الحد_اليومي <نسبة>")
            return
        self.cfg["daily_loss_pct"] = Decimal(context.args[0])
        await update.message.reply_text(f"✅ تم تحديد الحد اليومي إلى {context.args[0]}%.")

    async def toggle_silent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or context.args[0] not in ["تشغيل", "إيقاف"]:
            await update.message.reply_text("الاستخدام: /صامت تشغيل | إيقاف")
            return
        self.cfg["silent"] = (context.args[0] == "إيقاف")
        await update.message.reply_text("✅ تم تغيير وضع الإشعارات.")

    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.cfg["paused"] = True
        await update.message.reply_text("⏸️ تم تجميد البوت.")

    async def resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.cfg["paused"] = False
        await update.message.reply_text("▶️ تم إعادة تشغيل البوت.")

    async def start_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        balance = self.binance.get_wallet_balance()
        self.cfg["start_balance"] = Decimal(str(balance))
        self.cfg["today"] = datetime.date.today()
        self.cfg["positions"].clear()
        self.cfg["paused"] = False

        await update.message.reply_text(
            f"🚀 بدأ الوضع الجديد:\n"
            f"سعر الدخول: {self.cfg['entry_price']} $\n"
            f"عدد الصفقات: {self.cfg['max_positions']}\n"
            f"الحد اليومي: {self.cfg['daily_loss_pct']}%"
        )

    # مهام دورية
    async def daily_report(self, context: ContextTypes.DEFAULT_TYPE):
        balance = self.binance.get_wallet_balance()
        start = self.cfg["start_balance"]
        pnl = ((Decimal(str(balance)) - start) / start) * 100
        count = len(self.cfg["positions"])
        msg = (
            f"📊 تقرير يومي {datetime.datetime.utcnow().strftime('%Y-%m-%d')}\n"
            f"📈 عدد الصفقات: {count}\n"
            f"💰 الربح/الخسارة: {pnl:.2f}%"
        )
        await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

    async def monitor_daily_loss(self, context: ContextTypes.DEFAULT_TYPE):
        if not self.cfg["start_balance"] or self.cfg["paused"]:
            return
        balance = Decimal(str(self.binance.get_wallet_balance()))
        loss = (self.cfg["start_balance"] - balance) / self.cfg["start_balance"] * 100
        if loss >= float(self.cfg["daily_loss_pct"]):
            self.cfg["paused"] = True
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=f"⚠️ بلغت الخسارة {loss:.2f}%. تم إيقاف البوت."
            )

# instance جاهزة للاستيراد
mode_manager = ModeManager()

# ---------- تسجيل الأوامر ----------
def setup(app):
    app.add_handler(CommandHandler("حدد_السعر", mode_manager.set_price))
    app.add_handler(CommandHandler("عدد_الصفقات", mode_manager.set_count))
    app.add_handler(CommandHandler("الحد_اليومي", mode_manager.set_loss))
    app.add_handler(CommandHandler("ابدأ", mode_manager.start_mode))
    app.add_handler(CommandHandler("صامت", mode_manager.toggle_silent))
    app.add_handler(CommandHandler("تجميد", mode_manager.pause))
    app.add_handler(CommandHandler("استئناف", mode_manager.resume))