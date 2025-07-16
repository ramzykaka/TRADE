from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    text = update.message.text
    if text.startswith('/'):
        await update.message.reply_text("⚠️ الأمر غير معروف، جرب /help لعرض الأوامر المتاحة")

def setup(application):
    """إعداد معالجات الرسائل"""
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))