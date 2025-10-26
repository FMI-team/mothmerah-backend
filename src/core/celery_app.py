# backend/src/core/celery_app.py

from celery import Celery
from src.core.config import settings

# إنشاء نسخة من تطبيق Celery
celery = Celery(
    "mothmerah_worker",
    broker=settings.CELERY_BROKER_URL,
    include=["src.users.tasks"] # <-- تحديد مكان ملفات المهام
)

# إعداد المهام المجدولة (Cron jobs)
celery.conf.beat_schedule = {
    'cleanup-inactive-sessions-every-hour': {
        'task': 'src.users.tasks.cleanup_inactive_sessions',
        'schedule': 3600.0,  # <-- كل 3600 ثانية (كل ساعة)
    },
}
celery.conf.timezone = 'UTC'