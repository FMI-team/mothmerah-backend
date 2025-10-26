# backend\src\auditing\services\__init__.py

# استيراد جميع ملفات الخدمات الفرعية لجعل دوالها متاحة عند استخدام 'from src.auditing.services import *'
# هذا يضمن أن جميع تعريفات الخدمات يتم تحميلها.

# ستتم إضافة استيرادات الملفات المتخصصة هنا لاحقًا عند إنشائها، مثل:
from .system_audit_logs_service import *
from .user_activity_logs_service import *
from .search_logs_service import *
from .security_event_logs_service import *
from .data_change_audit_logs_service import *

