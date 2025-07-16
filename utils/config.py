# utils/config.py
from pydantic import BaseSettings, Field, validator
from typing import Optional

class Settings(BaseSettings):
    # Telegram
    TELEGRAM_TOKEN: str = Field(..., env="TELEGRAM_TOKEN")

    # Binance
    BINANCE_API_KEY: str = Field(..., env="BINANCE_API_KEY")
    BINANCE_API_SECRET: str = Field(..., env="BINANCE_API_SECRET")
    USE_TESTNET: bool = Field(True, env="USE_TESTNET")

    # Trading defaults
    LEVERAGE: int = Field(1, env="LEVERAGE", ge=1, le=125)
    RISK_PERCENT: float = Field(1.0, env="RISK_PERCENT", gt=0, le=100)
    MAX_ACTIVE_ORDERS: int = Field(3, env="MAX_ACTIVE_ORDERS", ge=1)

    # Admins
    ADMIN_CHAT_ID: int = Field(0, env="ADMIN_CHAT_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("*", pre=True)
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

# كائن جاهز للاستيراد
settings = Settings()

# دالة توافقية للكود القديم (اختياري)
load_config = lambda: settings.dict()
