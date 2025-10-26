# backend\src\api\v1\routers\inventory_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين والمنتجات من نوع UUID

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User # مودل المستخدم، للتحقق من الصلاحيات

# استيراد Schemas (هياكل البيانات) الخاصة بالمخزون والمنتجات
from src.products import schemas # استيراد عام لـ schemas المنتجات
from src.products.schemas import inventory_schemas # schemas الخاصة بالمخزون
from src.products.schemas import packaging_schemas # schemas الخاصة بخيارات التعبئة (قد تكون هناك حاجة لها في الـ services)

# استيراد الخدمات (منطق العمل) المتعلقة بالمخزون
from src.products.services import inventory_service # خدمة إدارة المخزون

# تعريف الراوتر الرئيسي لوحدة المخزون.
# هذا الراوتر سيتعامل مع نقاط الوصول المتعلقة بإدارة المخزون للبائعين بشكل أساسي.
router = APIRouter(
    prefix="/inventory", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/inventory)
    tags=["Seller - Inventory Management"] # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI) لتنظيم نقاط الوصول
)

# ================================================================
# --- نقاط الوصول لإدارة المخزون (InventoryItem) للبائعين ---
#    (تتطلب صلاحية INVENTORY_MANAGE_OWN أو ما يعادلها)
# ================================================================

@router.post(
    "/adjust-stock", # المسار الكامل: /api/v1/inventory/adjust-stock
    response_model=inventory_schemas.InventoryItemRead, # نوع الاستجابة المتوقع عند النجاح
    status_code=status.HTTP_200_OK, # كود الحالة HTTP عند النجاح
    summary="[Seller] تعديل مستوى المخزون (إضافة/خصم يدوي)", # ملخص يظهر في وثائق API
    description="""
    يسمح للبائع بتعديل كميات المخزون (إضافة أو خصم) لخيار تعبئة معين لمنتجاته.
    تُسجل كل عملية تعديل تلقائيًا كـ 'حركة مخزون' في سجلات النظام لتوفير مسار تدقيق كامل.
    يتطلب هذا الإجراء صلاحية 'INVENTORY_MANAGE_OWN'.
    """, # وصف مفصل يظهر في وثائق API
)
async def adjust_stock_level_endpoint(
    adjustment: inventory_schemas.StockAdjustmentCreate, # بيانات طلب التعديل (القادمة من الـ Request Body)
    db: Session = Depends(get_db), # تبعية لجلسة قاعدة البيانات
    current_user: User = Depends(dependencies.has_permission("INVENTORY_MANAGE_OWN")) # تبعية لفرض الصلاحية على المستخدم الحالي
):
    """
    نقطة وصول لضبط كميات المخزون.
    """
    # استدعاء دالة الخدمة التي تحتوي على منطق العمل والتحققات اللازمة.
    # دالة الخدمة ستتأكد من ملكية البائع للمنتج، وتحديث الكميات، وتسجيل الحركة.
    return inventory_service.adjust_stock_level(db=db, adjustment=adjustment, current_user=current_user)

@router.get(
    "/me", # المسار الكامل: /api/v1/inventory/me
    response_model=List[inventory_schemas.InventoryItemRead], # نوع الاستجابة المتوقع: قائمة ببنود المخزون
    summary="[Seller] جلب جميع بنود المخزون الخاصة بي",
    description="""
    يجلب قائمة بجميع بنود المخزون التي يمتلكها البائع الحالي.
    تتضمن تفاصيل الكميات المتاحة والمحجوزة والكلية، بالإضافة إلى حالة بند المخزون.
    يتطلب هذا الإجراء صلاحية 'INVENTORY_MANAGE_OWN' (أو صلاحية عرض المخزون).
    """,
)
async def get_my_inventory_items_endpoint(
    db: Session = Depends(get_db), # تبعية لجلسة قاعدة البيانات
    current_user: User = Depends(dependencies.has_permission("INVENTORY_MANAGE_OWN")), # تبعية لفرض الصلاحية
    skip: int = 0, # معلمة استعلام (Query Parameter) لتخطي عدد معين من النتائج (للترقيم)
    limit: int = 100 # معلمة استعلام لتحديد الحد الأقصى لعدد النتائج
):
    """
    نقطة وصول لعرض المخزون الخاص بالبائع.
    """
    # استدعاء دالة الخدمة لجلب بنود المخزون الخاصة بالبائع.
    return inventory_service.get_my_inventory_items(db=db, current_user=current_user, skip=skip, limit=limit)

@router.get(
    "/{inventory_item_id}", # المسار الكامل: /api/v1/inventory/{inventory_item_id}
    response_model=inventory_schemas.InventoryItemRead, # نوع الاستجابة المتوقع
    summary="[Seller] جلب تفاصيل بند مخزون واحد",
    description="""
    يجلب تفاصيل بند مخزون محدد باستخدام الـ ID الخاص به.
    تتضمن التفاصيل الحالة الحالية للمخزون وسجل حركاته.
    يتطلب هذا الإجراء صلاحية 'INVENTORY_MANAGE_OWN' ويتم التحقق من ملكية البائع للبند المطلوب.
    """,
)
async def get_single_inventory_item_endpoint(
    inventory_item_id: int, # معلمة مسار (Path Parameter): ID بند المخزون
    db: Session = Depends(get_db), # تبعية لجلسة قاعدة البيانات
    current_user: User = Depends(dependencies.has_permission("INVENTORY_MANAGE_OWN")) # تبعية لفرض الصلاحية
):
    """
    نقطة وصول لجلب تفاصيل بند مخزون محدد.
    """
    # استدعاء دالة الخدمة لجلب التفاصيل، والتي ستتأكد أيضًا من ملكية البائع للبند.
    return inventory_service.get_inventory_item_by_id(db=db, inventory_item_id=inventory_item_id, current_user=current_user)

