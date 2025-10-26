# backend\src\users\crud\__init__.py

# استيراد جميع ملفات CRUD الفرعية لجعل دوالها متاحة عند استخدام 'from src.users.crud import *'
# هذا يضمن أن جميع تعريفات CRUD يتم تحميلها.

from .core_crud import *
from .address_lookups_crud import *
from .address_crud import *
from .rbac_crud import *
from .license_crud import *
from .security_crud import *
from .verification_history_log_crud import *
from .user_lookups_crud import * # <-- تم إضافة هذا السطر المفقود