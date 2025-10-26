# backend\src\auction\crud\__init__.py

# استيراد جميع ملفات CRUD الفرعية لجعل دوالها متاحة عند استخدام 'from src.auction.crud import *'
# هذا يضمن أن جميع تعريفات CRUD يتم تحميلها.

from .auctions_crud import *
from .bidding_crud import *
from .settlements_crud import *