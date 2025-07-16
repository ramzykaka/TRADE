from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
from services.binance_api import BinanceAPI
from utils.config import load_config
from db.trade_logger import TradeLogger
import logging
from datetime import datetime

# إعداد المسجل (logger)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /start مع واجهة محسنة"""
    try:
        user = update.effective_user
        welcome_msg = (
            f"👋 مرحبًا {user.first_name}!\n\n"
            "🚀 أنا بوت التداول الذكي الذي يساعدك في:\n"
            "• تتبع محفظتك على Binance\n"
            "• تحليل السوق باحترافية\n"
            "• تنفيذ الصفقات التلقائية\n\n"
            "📌 استخدم الأزرار أدناه للتحكم:"
        )

        keyboard = [
            [
                InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
                InlineKeyboardButton("📊 تحليل السوق", callback_data="analyze")
            ],
            [
                InlineKeyboardButton("⚡ تداول سريع", callback_data="quick_trade"),
                InlineKeyboardButton("🛠 الإعدادات", callback_data="settings")
            ],
            [
                InlineKeyboardButton("📚 التعليمات", callback_data="help"),
                InlineKeyboardButton("📞 الدعم", callback_data="support")
            ]
        ]

        await update.message.reply_text(
            welcome_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}", exc_info=True)
        await update.message.reply_text("⚠️ حدث خطأ غير متوقع. يرجى المحاولة لاحقًا.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رصيد Binance مع تفاصيل كاملة"""
    try:
        # إظهار رسالة انتظار
        wait_msg = await update.message.reply_text("🔄 جاري جلب بيانات الرصيد...")
        
        binance = BinanceAPI()
        balances = binance.get_balances()
        total_usdt = binance.get_total_usdt_value()
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # تحضير الرسالة
        balance_msg = f"💼 <b>ملخص المحفظة</b>\n"
        balance_msg += f"⏱ <i>آخر تحديث: {update_time}</i>\n\n"
        balance_msg += f"💰 <b>القيمة الإجمالية:</b> {total_usdt:,.2f} USDT\n\n"
        balance_msg += "📊 <b>تفاصيل الأرصدة:</b>\n"

        # تصنيف العملات
        stable_coins = []
        crypto_assets = []
        
        for asset in balances:
            if asset['asset'] in ['USDT', 'BUSD', 'USDC']:
                stable_coins.append(asset)
            else:
                crypto_assets.append(asset)

        # إضافة العملات المستقرة
        if stable_coins:
            balance_msg += "\n💵 <b>العملات المستقرة:</b>\n"
            for asset in stable_coins:
                balance_msg += f"│ {asset['asset']}: {asset['free']:,.2f} (متاح)"
                if asset['locked'] > 0:
                    balance_msg += f" | 🔒 {asset['locked']:,.2f} (مقفل)"
                balance_msg += "\n"

        # إضافة العملات الرقمية
        if crypto_assets:
            balance_msg += "\n🪙 <b>العملات الرقمية:</b>\n"
            for asset in crypto_assets:
                usdt_value = binance.get_asset_value(asset['asset'])
                balance_msg += f"│ {asset['asset']}: {asset['free']:,.4f} ≈ {usdt_value:,.2f} USDT\n"

        # إضافة أزرار التحكم
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_balance")],
            [InlineKeyboardButton("📈 تحليل", callback_data="analyze_portfolio")]
        ]

        # تعديل الرسالة الأصلية بدل إرسال رسالة جديدة
        await wait_msg.edit_text(
            balance_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Balance error: {str(e)}", exc_info=True)
        error_msg = "⚠️ تعذر جلب بيانات الرصيد. يرجى:\n"
        error_msg += "1. التحقق من اتصال الإنترنت\n"
        error_msg += "2. التأكد من صحة مفاتيح API\n"
        error_msg += "3. المحاولة لاحقًا"
        await update.message.reply_text(error_msg)

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحليل السوق مع بيانات متقدمة"""
    try:
        wait_msg = await update.message.reply_text("📊 جاري تحليل ظروف السوق...")
        
        binance = BinanceAPI()
        top_coins = binance.get_top_movers()
        btc_analysis = binance.get_technical_analysis('BTCUSDT')
        eth_analysis = binance.get_technical_analysis('ETHUSDT')
        
        analysis_msg = "📈 <b>تحليل السوق الشامل</b>\n\n"
        analysis_msg += "🪙 <b>أفضل أداء (24h):</b>\n"
        
        for coin in top_coins['gainers'][:3]:
            analysis_msg += f"│ 🟢 {coin['symbol']}: +{coin['change']:.2f}%\n"
        
        analysis_msg += "\n🔻 <b>أسوأ أداء (24h):</b>\n"
        
        for coin in top_coins['losers'][:3]:
            analysis_msg += f"│ 🔴 {coin['symbol']}: {coin['change']:.2f}%\n"
        
        analysis_msg += "\n₿ <b>تحليل BTC/USDT:</b>\n"
        analysis_msg += f"│ السعر: {btc_analysis['price']:,.2f}\n"
        analysis_msg += f"│ الإتجاه: {btc_analysis['trend']}\n"
        analysis_msg += f"│ RSI: {btc_analysis['rsi']:.2f}\n"
        
        analysis_msg += "\nΞ <b>تحليل ETH/USDT:</b>\n"
        analysis_msg += f"│ السعر: {eth_analysis['price']:,.2f}\n"
        analysis_msg += f"│ الإتجاه: {eth_analysis['trend']}\n"
        analysis_msg += f"│ RSI: {eth_analysis['rsi']:.2f}\n"
        
        analysis_msg += f"\n⏱ <i>آخر تحديث: {datetime.now().strftime('%H:%M:%S')}</i>"
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_analysis")],
            [InlineKeyboardButton("📊 المزيد", callback_data="full_analysis")]
        ]
        
        await wait_msg.edit_text(
            analysis_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        await update.message.reply_text("⚠️ تعذر تحليل السوق حالياً. يرجى المحاولة لاحقاً.")

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """واجهة التداول المتقدمة"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("🛒 شراء", callback_data="buy_menu"),
                InlineKeyboardButton("🛒 بيع", callback_data="sell_menu")
            ],
            [
                InlineKeyboardButton("⚡ تداول سريع", callback_data="quick_trade"),
                InlineKeyboardButton("🛑 أوامر الوقف", callback_data="stop_orders")
            ],
            [
                InlineKeyboardButton("📊 محفظتي", callback_data="portfolio"),
                InlineKeyboardButton("📈 التحليل", callback_data="analysis")
            ]
        ]
        
        trade_msg = "📊 <b>واجهة التداول المتقدمة</b>\n\n"
        trade_msg += "اختر نوع العملية التي تريد تنفيذها:\n"
        trade_msg += "• 🛒 شراء: لشراء الأصول\n"
        trade_msg += "• 🛒 بيع: لبيع الأصول\n"
        trade_msg += "• ⚡ تداول سريع: لصفقات سريعة\n"
        trade_msg += "• 🛑 أوامر الوقف: لإدارة أوامر الوقف\n"
        
        await update.message.reply_text(
            trade_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Trade command error: {str(e)}", exc_info=True)
        await update.message.reply_text("⚠️ تعذر فتح واجهة التداول. يرجى المحاولة لاحقاً.")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نظام المساعدة المتكامل"""
    help_msg = "🆘 <b>مركز المساعدة</b>\n\n"
    help_msg += "📌 <b>الأوامر الأساسية:</b>\n"
    help_msg += "• /start - عرض القائمة الرئيسية\n"
    help_msg += "• /balance - عرض رصيد Binance\n"
    help_msg += "• /analyze - تحليل فني للسوق\n"
    help_msg += "• /trade - واجهة التداول\n\n"
    
    help_msg += "📚 <b>الدليل الشامل:</b>\n"
    help_msg += "1. تأكد من صحة مفاتيح API\n"
    help_msg += "2. استخدم الأوامر عبر الأزرار\n"
    help_msg += "3. يمكنك تحديث البيانات بأي وقت\n\n"
    
    help_msg += "📞 <b>الدعم الفني:</b>\n"
    help_msg += "للإبلاغ عن مشاكل أو اقتراحات:\n"
    help_msg += "@TradingBotSupport"
    
    keyboard = [
        [InlineKeyboardButton("📹 فيديو تعليمي", url="https://youtube.com/tutorial")],
        [InlineKeyboardButton("📒 الوثائق", url="https://docs.tradingbot.com")]
    ]
    
    await update.message.reply_text(
        help_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

def setup(application):
    """إعداد جميع معالجات الأوامر"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("analyze", analyze))
    application.add_handler(CommandHandler("trade", trade))
    application.add_handler(CommandHandler("help", help))