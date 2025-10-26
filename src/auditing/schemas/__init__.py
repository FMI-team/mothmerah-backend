# backend\src\auditing\schemas\__init__.py

# استيراد جميع Schemas من ملف audit_schemas.py لجعلها متاحة عند استيراد الحزمة
# مثال: 'from src.auditing.schemas import SystemAuditLogRead'

from .audit_schemas import *


# استيراد Schemas من Community (المجموعة 6)
from src.community.schemas import reviews_schemas

