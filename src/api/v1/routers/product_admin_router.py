# backend\src\api\v1\routers\product_admin_router.py
# (هذا الراوتر هو الراوتر الإداري المركزي الشامل)

from fastapi import APIRouter # استيراد المكونات الأساسية لـ FastAPI
# لا داعي لاستيراد Depends, status, HTTPException هنا
# لا داعي لاستيراد Session, datetime, date, UUID, User (UserModel) هنا
# لا داعي لاستيراد أي Schemas أو Services هنا مباشرة

# استيراد الراوترات الإدارية المتخصصة التي تم إنشاؤها في ملفات منفصلة
# هذه هي الراوترات التي تحتوي على نقاط الوصول الفعلية
from src.api.v1.routers import (
    # راوترات إدارة المستخدمين (المجموعة 1)
    admin_core_users_router,       # مسؤول عن /admin/users (جلب، تعديل حالة، حذف)
    admin_rbac_router,             # لإدارة الأدوار والصلاحيات (Admin /rbac)
    admin_address_lookups_router,  # لإدارة جداول العناوين (Admin /address-lookups)
    admin_verification_router,     # لإدارة التراخيص والتحقق (Admin /verification)

    # راوترات إدارة المزادات (المجموعة 5)
    admin_auctions_router,         # مسؤول عن /admin/auctions (المزادات، لوطاتها)

    # راوترات إدارة المنتجات والمخزون (المجموعة 2)
    unit_of_measure_admin_router, # مسؤول عن /admin/unit-of-measure
    
    # راوتر الجداول المرجعية العامة (المجموعة 12)
    admin_lookups_router, # <-- هذا هو راوتر Lookups العامة

    # راوتر سجلات التدقيق والأنشطة العامة (المجموعة 13)
    admin_audit_logs_router, # <-- هذا هو راوتر المجموعة 13

    # راوتر إدارة إعدادات وتكوينات النظام (المجموعة 14)
    admin_configuration_router # <-- تم إضافة هذا السطر الجديد لدمج راوتر المجموعة 14

    # راوتر إدارة المراجعات والتقييمات (المجموعة 6)
    admin_community_router # <-- تم إضافة هذا السطر الجديد لدمج راوتر المجموعة 6

    # TODO: تأكد من استيراد أي راوترات إدارية أخرى (مثل للمنتجات، المخزون، عمليات السوق، التسعير)
    #       إذا تم إنشاء راوترات إدارية منفصلة لها.
    #       مثال: from src.api.v1.routers import admin_product_management_router
    #       مثال: from src.api.v1.routers import admin_market_management_router
    #       مثال: from src.api.v1.routers import admin_pricing_router
)


# تعريف الراوتر الرئيسي لإدارة النظام من جانب المسؤولين.
# هذا الراوتر سيكون بمثابة "المدخل" لجميع أقسام الإدارة في لوحة التحكم الإدارية.
# لا نضع له prefix هنا، بل في main.py عند تضمينه كـ /api/v1/admin
router = APIRouter()


# ================================================================
# --- دمج الراوترات الفرعية الإدارية المتخصصة ---
# ================================================================
# كل راوتر فرعي له prefix و tags خاص به معرف في ملفه.
# الترتيب هنا يحدد ترتيب ظهور الأقسام في Swagger UI ضمن لوحة التحكم الإدارية.

# 1. راوترات إدارة المستخدمين (المجموعة 1)
router.include_router(admin_core_users_router.router)
router.include_router(admin_rbac_router.router)
router.include_router(admin_address_lookups_router.router)
router.include_router(admin_verification_router.router)

# 2. راوترات إدارة المزادات (المجموعة 5)
router.include_router(admin_auctions_router.router)

# 3. راوترات إدارة المنتجات والمخزون (المجموعة 2) - جزء من Lookups والإدارة
router.include_router(unit_of_measure_admin_router.router)

# 4. راوتر الجداول المرجعية العامة (المجموعة 12)
router.include_router(admin_lookups_router.router)

# 5. راوتر سجلات التدقيق والأنشطة العامة (المجموعة 13)
router.include_router(admin_audit_logs_router.router)

# 6. راوتر إدارة إعدادات وتكوينات النظام (المجموعة 14)
router.include_router(admin_configuration_router.router) # <-- تم إضافة هذا السطر الجديد

# 7. راوتر إدارة المراجعات والتقييمات (المجموعة 6)
router.include_router(admin_community_router.router) # <-- تم إضافة هذا السطر الجديد

# TODO: دمج راوترات إدارية أخرى إذا تم إنشاؤها
#       مثال: router.include_router(admin_product_management_router.router)
#       مثال: router.include_router(admin_inventory_management_router.router)
#       مثال: router.include_router(admin_pricing_router.router)
#       مثال: router.include_router(admin_market_management_router.router)