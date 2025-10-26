# backend\src\configuration\crud\__init__.py

# استيراد جميع دوال CRUD من الملفات المتخصصة في هذا المجلد.
# هذا يضمن أن جميع تعريفات CRUD يتم تحميلها.

from .application_settings_crud import *
from .feature_flags_crud import *
from .system_maintenance_schedule_crud import *