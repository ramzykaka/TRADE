import os
from dotenv import load_dotenv

# تحميل ملف .env
loaded = load_dotenv()
print(f"📦 .env loaded: {loaded}")

# طباعة التوكنات
print("🔑 BINANCE_API_KEY:", os.getenv("BINANCE_API_KEY"))
print("🔑 BINANCE_API_SECRET:", os.getenv("BINANCE_API_SECRET"))
print("🤖 TELEGRAM_TOKEN:", os.getenv("TELEGRAM_TOKEN"))
print("💬 ADMIN_CHAT_ID:", os.getenv("ADMIN_CHAT_ID"))
print("⚙ MAX_TRADES:", os.getenv("MAX_TRADES"))
print("💵 TRADE_AMOUNT_USDT:", os.getenv("TRADE_AMOUNT_USDT"))
print("📉 RISK_PER_TRADE:", os.getenv("RISK_PER_TRADE"))