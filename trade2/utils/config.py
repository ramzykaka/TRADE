import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    
    # القيم الافتراضية الاحتياطية
    DEFAULT_CONFIG = {
        'TELEGRAM_TOKEN': '',
        'BINANCE_API_KEY': '',
        'BINANCE_API_SECRET': '',
        'ADMIN_CHAT_ID': 0,  # قيمة افتراضية
        'MAX_ORDERS': 3      # قيمة افتراضية
    }
    
    try:
        return {
            'TELEGRAM_TOKEN': os.getenv("TELEGRAM_TOKEN") or DEFAULT_CONFIG['TELEGRAM_TOKEN'],
            'BINANCE_API_KEY': os.getenv("BINANCE_API_KEY") or DEFAULT_CONFIG['BINANCE_API_KEY'],
            'BINANCE_API_SECRET': os.getenv("BINANCE_API_SECRET") or DEFAULT_CONFIG['BINANCE_API_SECRET'],
            'ADMIN_CHAT_ID': int(os.getenv("ADMIN_CHAT_ID", DEFAULT_CONFIG['ADMIN_CHAT_ID'])),
            'MAX_ACTIVE_ORDERS': int(os.getenv("MAX_ORDERS", DEFAULT_CONFIG['MAX_ORDERS']))
        }
    except ValueError as e:
        raise ValueError(f"خطأ في تحويل القيم الرقمية: {e}. تأكد من صحة القيم في ملف .env")