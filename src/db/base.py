# backend\src\db\base.py

from sqlalchemy.ext.declarative import declarative_base

# هذا الملف يقوم باستيراد جميع مودلات SQLAlchemy لكي يتمكن SQLAlchemy من اكتشافها
# عند بدء التطبيق أو عند تشغيل عمليات الترحيل (Alembic).

# استيراد مودلات المستخدمين (المجموعة 1)
from src.users.models import core_models
from src.users.models import addresses_models
from src.users.models import roles_models
from src.users.models import security_models
from src.users.models import verification_models

# استيراد مودلات المنتجات (المجموعة 2)
from src.products.models import products_models
from src.products.models import attributes_models
from src.products.models import categories_models
from src.products.models import units_models
# from src.products.models import packaging_models
from src.products.models import inventory_models
from src.products.models import offerings_models

# استيراد مودلات التسعير (المجموعة 3)
from src.pricing.models import tier_pricing_models

# استيراد مودلات عمليات السوق (المجموعة 4)
from src.market.models import orders_models
from src.market.models import rfqs_models
from src.market.models import quotes_models
from src.market.models import shipments_models

# استيراد مودلات المزادات (المجموعة 5)
from src.auctions.models import auctions_models
# from src.auctions.models import auction_statuses_types_models
from src.auctions.models import bidding_models
from src.auctions.models import settlements_models

# استيراد مودلات المراجعات والتقييمات (المجموعة 6)
# هذا هو التعديل الرئيسي ليعكس هيكل المجلدات الجديد لـ Community
from src.community.models import reviews_models # <-- تم التعديل هنا

# استيراد مودلات مخزون إعادة البيع (المجموعة 7)
# TODO: تأكد من هذه المسارات عند بناء المجموعة 7
# from src.reseller_inventory.models import reseller_inventory_models

# استيراد مودلات المحفظة والمدفوعات (المجموعة 8)
# TODO: تأكد من هذه المسارات عند بناء المجموعة 8
# from src.wallet.models import wallet_models
# from src.wallet.models import payment_models

# استيراد مودلات اتفاقيات الدفع الآجل (المجموعة 9)
# TODO: تأكد من هذه المسارات عند بناء المجموعة 9
# from src.deferred_payments.models import deferred_payment_models

# استيراد مودلات الضمان الذهبي (المجموعة 10)
# TODO: تأكد من هذه المسارات عند بناء المجموعة 10
# from src.golden_guarantee.models import gg_models

# استيراد مودلات الإشعارات والاتصالات (المجموعة 11)
# TODO: تأكد من هذه المسارات عند بناء المجموعة 11
# from src.notifications.models import notifications_models

# استيراد مودلات الجداول المرجعية العامة (المجموعة 12)
# هذا هو التعديل الرئيسي ليعكس هيكل المجلدات الجديد
from src.lookups.models import lookups_models 

# استيراد مودلات سجلات التدقيق والأنشطة العامة (المجموعة 13)
# هذا هو التعديل الرئيسي ليعكس هيكل المجلدات الجديد لـ Auditing
from src.auditing.models import logs_models 

# استيراد مودلات إدارة إعدادات وتكوينات النظام (المجموعة 14)
# TODO: تأكد من هذه المسارات عند بناء المجموعة 14
# from src.system_settings.models import system_settings_models


Base = declarative_base() # لا تقم بتغيير هذا السطر