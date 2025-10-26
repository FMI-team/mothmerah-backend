# backend\src\market\schemas\__init__.py

# استيراد Schemas من ملفاتها الفردية أولاً.
# استيراد الأسماء المحددة يقلل من فرص التهيئة الجزئية.
# from .order_schemas import OrderRead, OrderItemRead
# from .rfq_schemas import RfqRead, RfqItemRead
# from .quote_schemas import QuoteRead, QuoteItemRead
# from .shipment_schemas import ShipmentRead, ShipmentItemRead

# استيراد Schemas من Lookups العامة
from src.lookups.schemas import *

# استيراد Schemas من Community (المجموعة 6)
from src.community.schemas import reviews_schemas

# استيراد Schemas من Auditing (المجموعة 13)
from src.auditing.schemas import audit_schemas

# استيراد Schemas من System Settings (المجموعة 14)
from src.configuration.schemas import settings_schemas # <-- تم إضافة هذا السطر الجديد

