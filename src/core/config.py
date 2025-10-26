# backend/src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # PostgreSQL Settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str
    DATABASE_URL: str

    # Redis Settings - تم تعطيله
    # REDIS_HOST: str
    # REDIS_PORT: int

    # API Settings
    PROJECT_NAME: str
    API_V1_STR: str

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # --- Brute-force إعدادات الحماية من القوة الغاشمة ---
    LOGIN_ATTEMPTS_LIMIT: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # ---  إعدادات Sessions ---
    # CELERY_BROKER_URL: str = "redis://redis:6379/1"  # تم تعطيله
    INACTIVE_SESSION_MINUTES: int = 60 * 24 # 24 ساعة

    # هذا السطر يخبر Pydantic بأن يقرأ المتغيرات من ملف .env
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

