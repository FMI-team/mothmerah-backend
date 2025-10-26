# backend\src\products\schemas\__init__.py

# استيراد جميع ملفات Schemas الفرعية لجعلها متاحة عند استخدام 'from src.products.schemas import *'
# هذا يضمن أن جميع تعريفات Schemas يتم تحميلها بواسطة Pydantic و FastAPI.

from .attribute_schemas import *
from .category_schemas import *
from .future_offerings_schemas import *
from .image_schemas import *
from .inventory_schemas import *
from .packaging_schemas import *
from .product_lookups_schemas import * # هذا يستورد ProductStatus, InventoryItemStatus, etc.
from .product_schemas import *
from .units_schemas import *
from .variety_schemas import * # استيراد Schemas من Lookups العامة
from src.lookups.schemas import * # <-- تم إضافة هذا السطر الجديد

# استيراد Schemas من Community (المجموعة 6)
from src.community.schemas import reviews_schemas

# استيراد Schemas من Auditing (المجموعة 13) إذا كان هناك أي علاقات متداخلة
from src.auditing.schemas import audit_schemas # <-- تم إضافة هذا السطر الجديد

# استيراد Schemas من System Settings (المجموعة 14)
from src.configuration.schemas import settings_schemas # <-- تم إضافة هذا السطر الجديد