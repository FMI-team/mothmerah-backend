# backend\src\system_settings\schemas\__init__.py

# استيراد جميع Schemas من ملف settings_schemas.py لجعلها متاحة عند استيراد الحزمة
# مثال: 'from src.system_settings.schemas import ApplicationSettingRead'

from .settings_schemas import *

# استيراد Schemas من Community (المجموعة 6)
from src.community.schemas import reviews_schemas # <-- تم إضافة هذا السطر الجديد

