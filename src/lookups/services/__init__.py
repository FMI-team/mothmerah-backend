# backend\src\lookups\services\__init__.py

# استيراد جميع ملفات الخدمات الفرعية لجعل دوالها متاحة عند استخدام 'from src.lookups.services import *'
# هذا يضمن أن جميع تعريفات الخدمات يتم تحميلها.

from .currencies_service import *
from .languages_service import *
from .dim_dates_service import *
from .activity_types_service import *
from .security_event_types_service import *
from .entity_types_service import *