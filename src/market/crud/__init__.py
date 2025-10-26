# backend\src\market\crud\__init__.py

# استيراد جميع ملفات CRUD الفرعية لجعل دوالها متاحة عند استخدام 'from src.market.crud import *'
# هذا يضمن أن جميع تعريفات CRUD يتم تحميلها.

from .orders_crud import *
from .rfqs_crud import *
from .quotes_crud import *
from .shipments_crud import *