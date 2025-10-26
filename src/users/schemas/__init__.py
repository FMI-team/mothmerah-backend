# backend\src\users\schemas\__init__.py

# استيراد جميع ملفات Schemas الفرعية لجعلها متاحة عند استخدام 'from src.users.schemas import *'
# هذا يضمن أن جميع تعريفات Schemas يتم تحميلها بواسطة Pydantic و FastAPI.

from .core_schemas import *
from .address_lookups_schemas import *
from .address_schemas import *
from .rbac_schemas import *
from .license_schemas import *
from .management_schemas import *
from .security_schemas import *
from .verification_lookups_schemas import *

# استيراد Schemas من Lookups العامة
from src.lookups.schemas import * # <-- تم إضافة هذا السطر الجديد

# استيراد Schemas من Community (المجموعة 6)
from src.community.schemas import reviews_schemas

# استيراد Schemas من Auditing (المجموعة 13) إذا كان هناك أي علاقات متداخلة
from src.auditing.schemas import audit_schemas # <-- تم إضافة هذا السطر الجديد

# استيراد Schemas من System Settings (المجموعة 14)
from src.configuration.schemas import settings_schemas # <-- تم إضافة هذا السطر الجديد

# TODO: استيراد Schemas من Market, Products, Auctions لضمان حل مراجع UserRead
# إذا كانت هذه الاستيرادات لم تتم بالفعل، فيمكن وضعها هنا (أو التأكد من أنها تتم في __init__.py الخاصة بحزمها)
# from src.market.schemas import order_schemas, rfq_schemas, quote_schemas, shipment_schemas
# from src.products.schemas import product_schemas, packaging_schemas # تأكد من packaging_schemas
# from src.auctions.schemas import auction_schemas, bidding_schemas, settlement_schemas


# في النهاية، وبعد أن يتم استيراد كل شيء، نقوم بفرض حل المراجع الأمامية لـ UserRead
# هذا يعالج مشكلة "not fully defined" عندما يكون هناك العديد من المراجع المتداخلة.
# core_schemas.UserRead.update_forward_refs() # <-- أضف هذا السطر
# إذا كان هناك Schemas أخرى في core_schemas.py تستخدم مراجع أمامية معقدة،
# يمكن أيضاً استدعاء update_forward_refs() لها هنا.
# core_schemas.AccountStatusHistoryRead.update_forward_refs()