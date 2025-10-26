# backend\src\auditing\models\__init__.py

# استيراد جميع المودلات من ملف logs_models.py لجعلها متاحة عند استيراد الحزمة
# مثال: 'from src.auditing.models import SystemAuditLog'

from .logs_models import *

# استيراد مودلات من Community (المجموعة 6)
from src.community.models import reviews_models 
