# backend\src\auctions\schemas\__init__.py

# استيراد جميع ملفات Schemas الفرعية لجعلها متاحة عند استخدام 'from src.auctions.schemas import *'
# هذا يضمن أن جميع تعريفات Schemas يتم تحميلها بواسطة Pydantic و FastAPI.

from .auction_schemas import *
from .bidding_schemas import *
from .settlement_schemas import *

# استيراد Schemas من Lookups العامة
from src.lookups.schemas import * 

# استيراد Schemas من Community (المجموعة 6)
from src.community.schemas import reviews_schemas

# استيراد Schemas من Auditing (المجموعة 13)
from src.auditing.schemas import audit_schemas 
