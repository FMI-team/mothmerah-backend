# backend\src\lookups\crud\__init__.py

# استيراد جميع ملفات CRUD الفرعية لجعل دوالها متاحة عند استخدام 'from src.lookups.crud import *'
# هذا يضمن أن جميع تعريفات CRUD يتم تحميلها.

from .currencies_crud import *
from .languages_crud import *
from .dim_dates_crud import *
from .activity_types_crud import *
from .security_event_types_crud import *
from .entity_types_crud import *