from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from .commands import analyze, balance, trade, help

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أحداث الأزرار"""
    query = update.callback_query
    await query.answer()

    if query.data == "analyze":
        await analyze(query, context)
    elif query.data == "balance":
        await balance(query, context)
    elif query.data == "trade":
        await trade(query, context)
    elif query.data == "stop":
        await query.edit_message_text("🛑 تم إيقاف البوت بنجاح")
    elif query.data == "help":
        await help(query, context)

def setup(application):
    application.add_handler(CallbackQueryHandler(button_handler))