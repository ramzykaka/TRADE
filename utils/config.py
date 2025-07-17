# utils/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Telegram
    TELEGRAM_TOKEN: str

    # Binance
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    USE_TESTNET: bool = True

    # إعدادات التداول
    LEVERAGE: int = Field(default=1, ge=1, le=125)
    RISK_PERCENT: float = Field(default=1.0, gt=0, le=100)
    RISK_PER_TRADE: float = Field(default=0.01, gt=0, le=1)
    TRADE_AMOUNT_USDT: float = Field(default=15.0, gt=0)
    MAX_TRADES: int = Field(default=3, ge=1)
    MAX_ACTIVE_ORDERS: int = Field(default=3, ge=1)

    # إعدادات المسؤول
    ADMIN_CHAT_ID: int = 0

    # إعدادات ملف .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
# دالة توافقية للكود القديم (اختياري)
load_config = lambda: settings.model_dump()