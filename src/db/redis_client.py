# backend/src/db/redis_client.py

import redis
from src.core.config import settings

# إنشاء عميل اتصال بـ Redis
# decode_responses=True يجعل النتائج تعود كنصوص (strings) بدلاً من بايتات (bytes)
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,  # نستخدم قاعدة البيانات 0 للبيانات العامة
    decode_responses=True
)

# يمكنك إضافة دالة للتحقق من الاتصال إذا أردت
def ping_redis():
    try:
        redis_client.ping()
        print("Successfully connected to Redis!")
    except redis.exceptions.ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")


