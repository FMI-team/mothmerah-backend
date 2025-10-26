# backend\src\auditing\crud\__init__.py

# استيراد جميع ملفات CRUD الفرعية لجعل دوالها متاحة عند استخدام 'from src.auditing.crud import *'
# هذا يضمن أن جميع تعريفات CRUD يتم تحميلها.

from .system_audit_logs_crud import *
from .user_activity_logs_crud import *
from .search_logs_crud import *
from .security_event_logs_crud import *
from .data_change_audit_logs_crud import *