# backend/src/api/v1/routers/product_admin_router.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
# استيرادات عامة
from src.db.session import get_db
from src.api.v1 import dependencies

# استيراد Schemas الخاصة بالمستخدمين (المجموعة 1)
from src.users.schemas import ( # <-- أضف هذا الاستيراد
    core_schemas,
    address_lookups_schemas,
    address_schemas,
    rbac_schemas,
    license_schemas,
    management_schemas, # لـ AdminUserStatusUpdate
    security_schemas,
    verification_lookups_schemas )
# استيراد Schemas وخدمات المنتجات
from src.products.schemas import (
    attribute_schemas,
    inventory_schemas,
    product_schemas,
    category_schemas,
    units_schemas,
    future_offerings_schemas )
from src.products.schemas.product_lookups_schemas import ProductStatusUpdate
# استيراد Schemas الخاصة بعمليات السوق (Market Operations)
from src.market.schemas import (
    order_schemas,
    rfq_schemas,
    quote_schemas,
    shipment_schemas )
# استيراد Schemas الخاصة بالمزادات
from src.auctions.schemas import (
    auction_schemas,
    bidding_schemas,
    settlement_schemas )

########### الخدمات
# استيراد خدمات المستخدمين (المجموعة 1)
from src.users.services import ( # <-- أضف هذا الاستيراد
    core_service,
    address_lookups_service,
    address_service,
    rbac_service,
    license_service,
    management_service,
    phone_change_service,
    security_service,
    verification_service )
# استيراد الخدمات الجديدة والمحدثة
from src.products.services import (
    attribute_service, # لخدمات Attribute والترجمات
    attribute_value_service, # لخدمات AttributeValue والترجمات
    product_variety_attribute_service, # لخدمات ProductVarietyAttribute
    inventory_service,
    category_service,
    product_service,
    unit_of_measure_service,
    future_offerings_service )
# استيراد خدمات عمليات السوق (Market Operations)
from src.market.services import (
    orders_service,
    rfqs_service,
    quotes_service,
    shipments_service )
# استيراد خدمات المزادات
from src.auctions.services import (
    auctions_service,
    bidding_service,
    settlements_service )


# استيراد راوترات المجموعات الأخرى (المجموعة 4، 3، 2)
from src.api.v1.routers import (
    admin_core_users_router, # <-- المجموعة 1  المستخدمون والصلاحيات
    admin_rbac_router,
    admin_address_lookups_router,
    admin_verification_router,

    orders_router, # <-- المجموعة 3 الطلبات والمخزون
    rfqs_router,
    quotes_router,
    shipments_router,

    pricing_router, # <-- المجموعة 4 التسعير الديناميكي

    unit_of_measure_admin_router, # <-- المجموعة 2 المنتجات واحجامها

    auctions_router, # <-- المجموعة 5  المزاد
    admin_auctions_router
)

from src.users.models.core_models import User 
from sqlalchemy.dialects.postgresql import UUID


# --- الراوتر الرئيسي المجمع لإدارة المنتجات ---
router = APIRouter()

# ================================================================
# --- القسم الفرعي 1: إدارة سمات المنتجات (Attributes) ---
# ================================================================

attributes_router = APIRouter(
    prefix="/attributes",
    tags=["Admin - Product Attributes"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_ATTRIBUTES"))] # حماية المجموعة كاملة
)

# ... داخل attributes_router ...

@attributes_router.post("/", response_model=attribute_schemas.AttributeRead, status_code=status.HTTP_201_CREATED)
def create_new_attribute(attribute_in: attribute_schemas.AttributeCreate, db: Session = Depends(get_db)):
    """إنشاء سمة جديدة (مثل: اللون، الحجم). يتطلب صلاحية ADMIN_MANAGE_ATTRIBUTES."""
    return attribute_service.create_new_attribute(db=db, attribute_in=attribute_in)

@attributes_router.get("/", response_model=List[attribute_schemas.AttributeRead])
def read_attributes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), include_inactive: bool = False):
    """عرض قائمة بجميع السمات المعرفة في النظام، مع خيار لتضمين السمات غير النشطة."""
    return attribute_service.get_all_attributes(db, skip=skip, limit=limit, include_inactive=include_inactive)

@attributes_router.get(
    "/{attribute_id}",
    response_model=attribute_schemas.AttributeRead,
    summary="جلب تفاصيل سمة واحدة"
)
def get_attribute_details(attribute_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل سمة واحدة بالـ ID الخاص بها."""
    return attribute_service.get_attribute_details(db, attribute_id=attribute_id)

@attributes_router.patch(
    "/{attribute_id}",
    response_model=attribute_schemas.AttributeRead,
    summary="تحديث سمة معينة"
)
def update_an_attribute(
    attribute_id: int,
    attribute_in: attribute_schemas.AttributeUpdate,
    db: Session = Depends(get_db)
):
    """تحديث سمة معينة (مثل اسمها أو حالة التفعيل)."""
    return attribute_service.update_attribute(db, attribute_id=attribute_id, attribute_in=attribute_in)

@attributes_router.delete(
    "/{attribute_id}",
    response_model=attribute_schemas.AttributeRead, # ترجع الكائن الذي تم حذفه ناعمًا
    summary="حذف ناعم لسمة معينة"
)
def soft_delete_an_attribute(attribute_id: int, db: Session = Depends(get_db)):
    """حذف ناعم لسمة (بتعيين is_active إلى False). لا يمكن حذفها إذا كانت مرتبطة بقيم أو أصناف."""
    return attribute_service.soft_delete_attribute(db, attribute_id=attribute_id)


# ... في نفس الملف product_admin_router.py ...

# --- نقاط وصول لإدارة قيم السمات (Attribute Values) ---
attribute_values_router = APIRouter(
    prefix="/values", # هذا الـ prefix سيكون مضافًا إلى /attributes
    tags=["Admin - Attribute Values"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_ATTRIBUTES"))] # يمكن تخصيص الصلاحية
)

@attribute_values_router.post("/", response_model=attribute_schemas.AttributeValueRead, status_code=status.HTTP_201_CREATED)
def create_new_attribute_value_endpoint(value_in: attribute_schemas.AttributeValueCreate, db: Session = Depends(get_db)):
    """إنشاء قيمة جديدة لسمة معينة (مثال: 'أحمر' لسمة 'اللون')."""
    return attribute_value_service.create_new_attribute_value(db=db, value_in=value_in)

@attribute_values_router.get("/", response_model=List[attribute_schemas.AttributeValueRead])
def read_attribute_values_endpoint(attribute_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """عرض قائمة بجميع قيم السمات، مع إمكانية التصفية حسب السمة الأم."""
    return attribute_value_service.get_all_attribute_values(db, attribute_id=attribute_id, skip=skip, limit=limit)

@attribute_values_router.get("/{attribute_value_id}", response_model=attribute_schemas.AttributeValueRead)
def get_attribute_value_details_endpoint(attribute_value_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل قيمة سمة واحدة بالـ ID الخاص بها."""
    return attribute_value_service.get_attribute_value_details(db, attribute_value_id=attribute_value_id)

@attribute_values_router.patch("/{attribute_value_id}", response_model=attribute_schemas.AttributeValueRead)
def update_attribute_value_endpoint(
    attribute_value_id: int,
    value_in: attribute_schemas.AttributeValueUpdate,
    db: Session = Depends(get_db)
):
    """تحديث قيمة سمة معينة. لا يمكن تغيير السمة الأم لها."""
    return attribute_value_service.update_attribute_value(db, attribute_value_id=attribute_value_id, value_in=value_in)

@attribute_values_router.delete(
    "/{attribute_value_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف قيمة سمة معينة"
)
def delete_attribute_value_endpoint(attribute_value_id: int, db: Session = Depends(get_db)):
    """حذف قيمة سمة معينة (حذف صارم). لا يمكن حذفها إذا كانت مرتبطة بأصناف منتجات."""
    attribute_value_service.delete_attribute_value(db, attribute_value_id=attribute_value_id)
    return

# --- نقاط وصول لإدارة ترجمات قيم السمات (Attribute Value Translations) ---

@attribute_values_router.post(
    "/{attribute_value_id}/translations",
    response_model=attribute_schemas.AttributeValueTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="إنشاء ترجمة جديدة لقيمة سمة أو تحديثها إذا كانت موجودة"
)
def create_attribute_value_translation_endpoint(attribute_value_id: int, trans_in: attribute_schemas.AttributeValueTranslationCreate, db: Session = Depends(get_db)):
    """
    إنشاء ترجمة جديدة لقيمة سمة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة بالفعل، سيتم رفض الطلب بتضارب.
    """
    return attribute_value_service.create_attribute_value_translation(db=db, attribute_value_id=attribute_value_id, trans_in=trans_in)

@attribute_values_router.get(
    "/{attribute_value_id}/translations/{language_code}",
    response_model=attribute_schemas.AttributeValueTranslationRead,
    summary="جلب ترجمة محددة لقيمة سمة"
)
def get_attribute_value_translation_endpoint(attribute_value_id: int, language_code: str, db: Session = Depends(get_db)):
    """جلب ترجمة قيمة سمة معينة بلغة محددة."""
    return attribute_value_service.get_attribute_value_translation_details(db, attribute_value_id=attribute_value_id, language_code=language_code)

@attribute_values_router.patch(
    "/{attribute_value_id}/translations/{language_code}",
    response_model=attribute_schemas.AttributeValueTranslationRead,
    summary="تحديث ترجمة قيمة سمة"
)
def update_attribute_value_translation_endpoint(
    attribute_value_id: int,
    language_code: str,
    trans_in: attribute_schemas.AttributeValueTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة قيمة سمة معينة بلغة محددة."""
    return attribute_value_service.update_attribute_value_translation(db, attribute_value_id=attribute_value_id, language_code=language_code, trans_in=trans_in)

@attribute_values_router.delete(
    "/{attribute_value_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف ترجمة قيمة سمة"
)
def delete_attribute_value_translation_endpoint(attribute_value_id: int, language_code: str, db: Session = Depends(get_db)):
    """حذف ترجمة قيمة سمة معينة بلغة محددة (حذف صارم)."""
    attribute_value_service.delete_attribute_value_translation(db, attribute_value_id=attribute_value_id, language_code=language_code)
    return

# ... (بعد تعريف attribute_values_router ونقاط وصوله) ...

# --- نقاط وصول لإدارة ترجمات السمات (Attribute Translations) ---

@attributes_router.post(
    "/{attribute_id}/translations",
    response_model=attribute_schemas.AttributeTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="إنشاء ترجمة جديدة لسمة أو تحديثها إذا كانت موجودة"
)
def create_attribute_translation_endpoint(attribute_id: int, trans_in: attribute_schemas.AttributeTranslationCreate, db: Session = Depends(get_db)):
    """
    إنشاء ترجمة جديدة لسمة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة بالفعل، سيتم رفض الطلب بتضارب.
    """
    return attribute_service.create_attribute_translation(db=db, attribute_id=attribute_id, trans_in=trans_in)

@attributes_router.get(
    "/{attribute_id}/translations/{language_code}",
    response_model=attribute_schemas.AttributeTranslationRead,
    summary="جلب ترجمة محددة لسمة"
)
def get_attribute_translation_endpoint(attribute_id: int, language_code: str, db: Session = Depends(get_db)):
    """جلب ترجمة سمة معينة بلغة محددة."""
    return attribute_service.get_attribute_translation_details(db, attribute_id=attribute_id, language_code=language_code)

@attributes_router.patch(
    "/{attribute_id}/translations/{language_code}",
    response_model=attribute_schemas.AttributeTranslationRead,
    summary="تحديث ترجمة سمة"
)
def update_attribute_translation_endpoint(
    attribute_id: int,
    language_code: str,
    trans_in: attribute_schemas.AttributeTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة سمة معينة بلغة محددة."""
    return attribute_service.update_attribute_translation(db, attribute_id=attribute_id, language_code=language_code, trans_in=trans_in)

@attributes_router.delete(
    "/{attribute_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف ترجمة سمة"
)
def delete_attribute_translation_endpoint(attribute_id: int, language_code: str, db: Session = Depends(get_db)):
    """حذف ترجمة سمة معينة بلغة محددة (حذف صارم)."""
    attribute_service.delete_attribute_translation(db, attribute_id=attribute_id, language_code=language_code)
    return

# --- نقاط وصول لإدارة روابط سمات أصناف المنتج (Product Variety Attributes) ---
product_variety_attributes_router = APIRouter(
    prefix="/product-variety-attributes",
    tags=["Admin - Product Variety Attributes"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_ATTRIBUTES"))] # يمكن تخصيص الصلاحية هنا
)

@product_variety_attributes_router.post("/", response_model=attribute_schemas.ProductVarietyAttributeRead, status_code=status.HTTP_201_CREATED)
def create_product_variety_attribute_endpoint(link_in: attribute_schemas.ProductVarietyAttributeCreate, db: Session = Depends(get_db)):
    """إنشاء ربط جديد بين صنف منتج وسمة وقيمتها."""
    return product_variety_attribute_service.create_product_variety_attribute(db=db, link_in=link_in)

@product_variety_attributes_router.get("/", response_model=List[attribute_schemas.ProductVarietyAttributeRead])
def get_all_product_variety_attributes_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """جلب جميع روابط سمات أصناف المنتجات."""
    return product_variety_attribute_service.get_all_product_variety_attributes(db, skip=skip, limit=limit)

@product_variety_attributes_router.get("/{product_variety_attribute_id}", response_model=attribute_schemas.ProductVarietyAttributeRead)
def get_product_variety_attribute_details_endpoint(product_variety_attribute_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل رابط سمة صنف منتج واحد بالـ ID الخاص به."""
    return product_variety_attribute_service.get_product_variety_attribute_details(db, product_variety_attribute_id=product_variety_attribute_id)

@product_variety_attributes_router.delete(
    "/{product_variety_attribute_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف رابط سمة صنف منتج"
)
def delete_product_variety_attribute_endpoint(product_variety_attribute_id: int, db: Session = Depends(get_db)):
    """حذف رابط سمة صنف منتج معين (حذف صارم)."""
    product_variety_attribute_service.delete_product_variety_attribute(db, product_variety_attribute_id=product_variety_attribute_id)
    return

@product_variety_attributes_router.get("/for-variety/{product_variety_id}", response_model=List[attribute_schemas.ProductVarietyAttributeRead])
def get_attributes_for_variety_endpoint(product_variety_id: int, db: Session = Depends(get_db)):
    """جلب جميع السمات المرتبطة بصنف منتج معين."""
    return product_variety_attribute_service.get_attributes_for_variety(db, product_variety_id=product_variety_id)


# ================================================================
# --- قسم إدارة المخزون والجداول المرجعية (Inventory) ---
# ================================================================

inventory_lookups_router = APIRouter(
    prefix="/lookups",
    tags=["Admin - Inventory (Lookups)"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_PRODUCT_LOOKUPS"))] # صلاحية مخصصة لإدارة جداول المخزون المرجعية
)

@inventory_lookups_router.post("/statuses/", response_model=inventory_schemas.InventoryItemStatusRead)
def create_inventory_status(status_in: inventory_schemas.InventoryItemStatusCreate, db: Session = Depends(get_db)):
    return inventory_service.create_new_inventory_status(db, status_in=status_in)

@inventory_lookups_router.get("/statuses/", response_model=List[inventory_schemas.InventoryItemStatusRead])
def get_inventory_statuses(db: Session = Depends(get_db)):
    return inventory_service.get_all_inventory_statuses(db)



# ================================================================
# --- نقاط الوصول لحالات عناصر المخزون (InventoryItemStatus) ---
# ================================================================

@inventory_lookups_router.post(
    "/inventory-item-statuses",
    response_model=inventory_schemas.InventoryItemStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة بند مخزون جديدة"
)
async def create_inventory_item_status_endpoint(
    status_in: inventory_schemas.InventoryItemStatusCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مرجعية جديدة لبند المخزون (مثل 'معروض للبيع', 'محجوز', 'تالف').
    تتطلب صلاحية 'ADMIN_MANAGE_PRODUCT_LOOKUPS'.
    """
    return inventory_service.create_new_inventory_item_status(db=db, status_in=status_in)

@inventory_lookups_router.get(
    "/inventory-item-statuses",
    response_model=List[inventory_schemas.InventoryItemStatusRead],
    summary="[Admin] جلب جميع حالات بنود المخزون"
)
async def get_all_inventory_item_statuses_endpoint(db: Session = Depends(get_db)):
    """
    جلب قائمة بجميع الحالات المرجعية لبنود المخزون في النظام.
    """
    return inventory_service.get_all_inventory_item_statuses(db=db)

@inventory_lookups_router.get(
    "/inventory-item-statuses/{status_id}",
    response_model=inventory_schemas.InventoryItemStatusRead,
    summary="[Admin] جلب تفاصيل حالة بند مخزون واحدة"
)
async def get_inventory_item_status_details_endpoint(status_id: int, db: Session = Depends(get_db)):
    """
    جلب تفاصيل حالة مرجعية لبند مخزون بالـ ID الخاص بها.
    """
    return inventory_service.get_inventory_item_status_by_id(db=db, status_id=status_id)

@inventory_lookups_router.patch(
    "/inventory-item-statuses/{status_id}",
    response_model=inventory_schemas.InventoryItemStatusRead,
    summary="[Admin] تحديث حالة بند مخزون"
)
async def update_inventory_item_status_endpoint(
    status_id: int,
    status_in: inventory_schemas.InventoryItemStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    تحديث حالة مرجعية لبند مخزون.
    """
    return inventory_service.update_inventory_item_status(db=db, status_id=status_id, status_in=status_in)

@inventory_lookups_router.delete(
    "/inventory-item-statuses/{status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف حالة بند مخزون"
)
async def delete_inventory_item_status_endpoint(status_id: int, db: Session = Depends(get_db)):
    """
    حذف حالة مرجعية لبند مخزون (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأي بنود مخزون موجودة.
    """
    inventory_service.delete_inventory_item_status(db=db, status_id=status_id)
    return

# ================================================================
# --- نقاط الوصول لترجمات حالات عناصر المخزون (InventoryItemStatusTranslation) ---
# ================================================================

@inventory_lookups_router.post(
    "/inventory-item-statuses/{status_id}/translations",
    response_model=inventory_schemas.InventoryItemStatusTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لحالة بند مخزون أو تحديثها"
)
async def create_inventory_item_status_translation_endpoint(
    status_id: int,
    trans_in: inventory_schemas.InventoryItemStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء ترجمة جديدة لحالة مرجعية لبند مخزون بلغة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب بتضارب.
    """
    return inventory_service.create_inventory_item_status_translation(db=db, status_id=status_id, trans_in=trans_in)

@inventory_lookups_router.get(
    "/inventory-item-statuses/{status_id}/translations/{language_code}",
    response_model=inventory_schemas.InventoryItemStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة بند مخزون"
)
async def get_inventory_item_status_translation_endpoint(
    status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة حالة مرجعية لبند مخزون بلغة محددة."""
    return inventory_service.get_inventory_item_status_translation_by_id_and_lang(db=db, status_id=status_id, language_code=language_code)

@inventory_lookups_router.patch(
    "/inventory-item-statuses/{status_id}/translations/{language_code}",
    response_model=inventory_schemas.InventoryItemStatusTranslationRead,
    summary="[Admin] تحديث ترجمة حالة بند مخزون"
)
async def update_inventory_item_status_translation_endpoint(
    status_id: int,
    language_code: str,
    trans_in: inventory_schemas.InventoryItemStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة حالة مرجعية لبند مخزون بلغة محددة."""
    return inventory_service.update_inventory_item_status_translation(db=db, status_id=status_id, language_code=language_code, trans_in=trans_in)

@inventory_lookups_router.delete(
    "/inventory-item-statuses/{status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة حالة بند مخزون"
)
async def delete_inventory_item_status_translation_endpoint(
    status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة حالة مرجعية لبند مخزون بلغة محددة (حذف صارم)."""
    inventory_service.delete_inventory_item_status_translation(db=db, status_id=status_id, language_code=language_code)
    return

# ================================================================
# --- نقاط الوصول لأنواع حركات المخزون (InventoryTransactionType) ---
# ================================================================

@inventory_lookups_router.post(
    "/inventory-transaction-types",
    response_model=inventory_schemas.InventoryTransactionTypeRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء نوع حركة مخزون جديد"
)
async def create_inventory_transaction_type_endpoint(
    type_in: inventory_schemas.InventoryTransactionTypeCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء نوع مرجعي جديد لحركة المخزون (مثل 'إضافة يدوية', 'خصم بيع', 'إرجاع').
    تتطلب صلاحية 'ADMIN_MANAGE_PRODUCT_LOOKUPS'.
    """
    return inventory_service.create_new_inventory_transaction_type(db=db, type_in=type_in)

@inventory_lookups_router.get(
    "/inventory-transaction-types",
    response_model=List[inventory_schemas.InventoryTransactionTypeRead],
    summary="[Admin] جلب جميع أنواع حركات المخزون"
)
async def get_all_inventory_transaction_types_endpoint(db: Session = Depends(get_db)):
    """
    جلب قائمة بجميع أنواع الحركات المرجعية للمخزون في النظام.
    """
    return inventory_service.get_all_inventory_transaction_types(db=db)

@inventory_lookups_router.get(
    "/inventory-transaction-types/{type_id}",
    response_model=inventory_schemas.InventoryTransactionTypeRead,
    summary="[Admin] جلب تفاصيل نوع حركة مخزون واحدة"
)
async def get_inventory_transaction_type_details_endpoint(type_id: int, db: Session = Depends(get_db)):
    """
    جلب تفاصيل نوع حركة مرجعية للمخزون بالـ ID الخاص بها.
    """
    return inventory_service.get_inventory_transaction_type_by_id(db=db, type_id=type_id)

@inventory_lookups_router.patch(
    "/inventory-transaction-types/{type_id}",
    response_model=inventory_schemas.InventoryTransactionTypeRead,
    summary="[Admin] تحديث نوع حركة مخزون"
)
async def update_inventory_transaction_type_endpoint(
    type_id: int,
    type_in: inventory_schemas.InventoryTransactionTypeUpdate,
    db: Session = Depends(get_db)
):
    """
    تحديث نوع حركة مرجعية للمخزون.
    """
    return inventory_service.update_inventory_transaction_type(db=db, type_id=type_id, type_in=type_in)

@inventory_lookups_router.delete(
    "/inventory-transaction-types/{type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف نوع حركة مخزون"
)
async def delete_inventory_transaction_type_endpoint(type_id: int, db: Session = Depends(get_db)):
    """
    حذف نوع حركة مرجعية للمخزون (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأي حركات مخزون مسجلة.
    """
    inventory_service.delete_inventory_transaction_type(db=db, type_id=type_id)
    return

# ================================================================
# --- نقاط الوصول لترجمات أنواع حركات المخزون (InventoryTransactionTypeTranslation) ---
# ================================================================

@inventory_lookups_router.post(
    "/inventory-transaction-types/{type_id}/translations",
    response_model=inventory_schemas.InventoryTransactionTypeTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لنوع حركة مخزون أو تحديثها"
)
async def create_inventory_transaction_type_translation_endpoint(
    type_id: int,
    trans_in: inventory_schemas.InventoryTransactionTypeTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء ترجمة جديدة لنوع حركة مرجعية للمخزون بلغة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب بتضارب.
    """
    return inventory_service.create_inventory_transaction_type_translation(db=db, type_id=type_id, trans_in=trans_in)

@inventory_lookups_router.get(
    "/inventory-transaction-types/{type_id}/translations/{language_code}",
    response_model=inventory_schemas.InventoryTransactionTypeTranslationRead,
    summary="[Admin] جلب ترجمة محددة لنوع حركة مخزون"
)
async def get_inventory_transaction_type_translation_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة نوع حركة مرجعية للمخزون بلغة محددة."""
    return inventory_service.get_inventory_transaction_type_translation_by_id_and_lang(db=db, type_id=type_id, language_code=language_code)

@inventory_lookups_router.patch(
    "/inventory-transaction-types/{type_id}/translations/{language_code}",
    response_model=inventory_schemas.InventoryTransactionTypeTranslationRead,
    summary="[Admin] تحديث ترجمة نوع حركة مخزون"
)
async def update_inventory_transaction_type_translation_endpoint(
    type_id: int,
    language_code: str,
    trans_in: inventory_schemas.InventoryTransactionTypeTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة نوع حركة مرجعية للمخزون بلغة محددة."""
    return inventory_service.update_inventory_transaction_type_translation(db=db, type_id=type_id, language_code=language_code, trans_in=trans_in)

@inventory_lookups_router.delete(
    "/inventory-transaction-types/{type_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة نوع حركة مخزون"
)
async def delete_inventory_transaction_type_translation_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة نوع حركة مرجعية للمخزون بلغة محددة (حذف صارم)."""
    inventory_service.delete_inventory_transaction_type_translation(db=db, type_id=type_id, language_code=language_code)
    return


# ================================================================
# --- القسم الجديد: إدارة عناصر المخزون الشاملة (Admin - All Inventory Items) ---
# ================================================================

inventory_management_router = APIRouter(
    prefix="/inventory-items", # مسار فرعي جديد لإدارة بنود المخزون مباشرة
    tags=["Admin - Inventory Management"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_PRODUCT_LOOKUPS"))] # يمكن تخصيص صلاحية أدق هنا مثل ADMIN_MANAGE_INVENTORY
)

@inventory_management_router.get(
    "/",
    response_model=List[inventory_schemas.InventoryItemRead],
    summary="[Admin] جلب جميع بنود المخزون في النظام"
)
async def get_all_inventory_items_for_admin_endpoint(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    يجلب قائمة بجميع بنود المخزون الموجودة في النظام، بغض النظر عن البائع.
    تتطلب صلاحية 'ADMIN_MANAGE_PRODUCT_LOOKUPS' أو صلاحية إدارة المخزون.
    """
    return inventory_service.get_all_inventory_items_for_admin(db=db, skip=skip, limit=limit)

@inventory_management_router.get(
    "/{inventory_item_id}",
    response_model=inventory_schemas.InventoryItemRead,
    summary="[Admin] جلب تفاصيل بند مخزون واحد (إداري)"
)
async def get_inventory_item_details_admin_endpoint(
    inventory_item_id: int,
    db: Session = Depends(get_db)
):
    """
    يجلب تفاصيل بند مخزون واحد بالـ ID الخاص به.
    هذه النقطة مخصصة للمسؤولين لعرض تفاصيل أي بند مخزون.
    """
    # Note: The service function 'get_inventory_item_by_id' has a user check.
    # For an admin endpoint, you might need a dedicated admin service function
    # or pass a dummy admin user, or ensure the permission check handles it.
    # For simplicity, if ADMIN_MANAGE_PRODUCT_LOOKUPS gives admin full view,
    # the existing service function will work.
    # As per our service, it needs a User object, so we'd typically pass the admin_user here.
    # Let's adjust to be consistent with admin endpoints always receiving admin_user.
    return inventory_service.get_inventory_item_by_id(db=db, inventory_item_id=inventory_item_id, current_user=User(user_id=UUID('00000000-0000-0000-0000-000000000000'), default_role=None)) # Dummy admin user for internal check logic if needed


@inventory_management_router.patch(
    "/{inventory_item_id}",
    response_model=inventory_schemas.InventoryItemRead,
    summary="[Admin] تحديث بند مخزون مباشرة"
)
async def update_inventory_item_admin_endpoint(
    inventory_item_id: int,
    item_in: inventory_schemas.InventoryItemUpdate,
    db: Session = Depends(get_db)
):
    """
    يسمح للمسؤول بتحديث أي حقل في بند المخزون مباشرة، بما في ذلك الكميات والحالة.
    تتطلب صلاحية 'ADMIN_MANAGE_PRODUCT_LOOKUPS' أو صلاحية إدارة المخزون الشاملة.
    """
    return inventory_service.update_inventory_item_by_admin(db=db, inventory_item_id=inventory_item_id, item_in=item_in)

# ================================================================
# --- نقاط الوصول لحالات الطلب (Order Statuses) ---
# ================================================================

@inventory_lookups_router.post(
    "/order-statuses",
    response_model=order_schemas.OrderStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة طلب جديدة"
)
async def create_order_status_endpoint(
    status_in: order_schemas.OrderStatusCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مرجعية جديدة للطلب (مثلاً: 'قيد المراجعة', 'تم الشحن').
    تتطلب صلاحية 'ADMIN_MANAGE_PRODUCT_LOOKUPS' أو صلاحية إدارة جداول Lookups الخاصة بعمليات السوق.
    """
    return orders_service.create_order_status_service(db=db, status_in=status_in)

@inventory_lookups_router.get(
    "/order-statuses",
    response_model=List[order_schemas.OrderStatusRead],
    summary="[Admin] جلب جميع حالات الطلب"
)
async def get_all_order_statuses_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع الحالات المرجعية للطلبات في النظام."""
    return orders_service.get_all_order_statuses_service(db=db)

@inventory_lookups_router.get(
    "/order-statuses/{order_status_id}",
    response_model=order_schemas.OrderStatusRead,
    summary="[Admin] جلب تفاصيل حالة طلب واحدة"
)
async def get_order_status_details_endpoint(order_status_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل حالة مرجعية لطلب بالـ ID الخاص بها."""
    return orders_service.get_order_status_details(db=db, order_status_id=order_status_id)

@inventory_lookups_router.patch(
    "/order-statuses/{order_status_id}",
    response_model=order_schemas.OrderStatusRead,
    summary="[Admin] تحديث حالة طلب"
)
async def update_order_status_endpoint(
    order_status_id: int,
    status_in: order_schemas.OrderStatusUpdate,
    db: Session = Depends(get_db)
):
    """تحديث حالة مرجعية لطلب."""
    return orders_service.update_order_status_service(db=db, order_status_id=order_status_id, status_in=status_in)

@inventory_lookups_router.delete(
    "/order-statuses/{order_status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف حالة طلب"
)
async def delete_order_status_endpoint(order_status_id: int, db: Session = Depends(get_db)):
    """
    حذف حالة مرجعية لطلب (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأي طلبات موجودة.
    """
    orders_service.delete_order_status_service(db=db, order_status_id=order_status_id)
    return

# ================================================================
# --- نقاط الوصول لترجمات حالات الطلب (Order Status Translations) ---
# ================================================================

@inventory_lookups_router.post(
    "/order-statuses/{order_status_id}/translations",
    response_model=order_schemas.OrderStatusTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لحالة طلب أو تحديثها"
)
async def create_order_status_translation_endpoint(
    order_status_id: int,
    trans_in: order_schemas.OrderStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء ترجمة جديدة لحالة مرجعية لطلب بلغة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب بتضارب.
    """
    return orders_service.create_order_status_translation_service(db=db, order_status_id=order_status_id, trans_in=trans_in)

@inventory_lookups_router.get(
    "/order-statuses/{order_status_id}/translations/{language_code}",
    response_model=order_schemas.OrderStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة طلب"
)
async def get_order_status_translation_details_endpoint(
    order_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة حالة مرجعية لطلب بلغة محددة."""
    return orders_service.get_order_status_translation_details(db=db, order_status_id=order_status_id, language_code=language_code)

@inventory_lookups_router.patch(
    "/order-statuses/{order_status_id}/translations/{language_code}",
    response_model=order_schemas.OrderStatusTranslationRead,
    summary="[Admin] تحديث ترجمة حالة طلب"
)
async def update_order_status_translation_endpoint(
    order_status_id: int,
    language_code: str,
    trans_in: order_schemas.OrderStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة حالة مرجعية لطلب بلغة محددة."""
    return orders_service.update_order_status_translation_service(db=db, order_status_id=order_status_id, language_code=language_code, trans_in=trans_in)

@inventory_lookups_router.delete(
    "/order-statuses/{order_status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة حالة طلب"
)
async def delete_order_status_translation_endpoint(
    order_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة حالة مرجعية لطلب بلغة محددة (حذف صارم)."""
    orders_service.delete_order_status_translation_service(db=db, order_status_id=order_status_id, language_code=language_code)
    return

# ================================================================
# --- نقاط الوصول لحالات الدفع (Payment Statuses) ---
# ================================================================

@inventory_lookups_router.post(
    "/payment-statuses",
    response_model=order_schemas.PaymentStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة دفع جديدة"
)
async def create_payment_status_endpoint(
    status_in: order_schemas.PaymentStatusCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مرجعية جديدة للدفع (مثلاً: 'بانتظار الدفع', 'تم الدفع', 'فشل الدفع').
    تتطلب صلاحية 'ADMIN_MANAGE_PRODUCT_LOOKUPS'.
    """
    return orders_service.create_payment_status_service(db=db, status_in=status_in)

@inventory_lookups_router.get(
    "/payment-statuses",
    response_model=List[order_schemas.PaymentStatusRead],
    summary="[Admin] جلب جميع حالات الدفع"
)
async def get_all_payment_statuses_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع الحالات المرجعية للدفع في النظام."""
    return orders_service.get_all_payment_statuses_service(db=db)

@inventory_lookups_router.get(
    "/payment-statuses/{payment_status_id}",
    response_model=order_schemas.PaymentStatusRead,
    summary="[Admin] جلب تفاصيل حالة دفع واحدة"
)
async def get_payment_status_details_endpoint(payment_status_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل حالة مرجعية للدفع بالـ ID الخاص بها."""
    return orders_service.get_payment_status_details(db=db, payment_status_id=payment_status_id)

@inventory_lookups_router.patch(
    "/payment-statuses/{payment_status_id}",
    response_model=order_schemas.PaymentStatusRead,
    summary="[Admin] تحديث حالة دفع"
)
async def update_payment_status_endpoint(
    payment_status_id: int,
    status_in: order_schemas.PaymentStatusUpdate,
    db: Session = Depends(get_db)
):
    """تحديث حالة مرجعية للدفع."""
    return orders_service.update_payment_status_service(db=db, payment_status_id=payment_status_id, status_in=status_in)

@inventory_lookups_router.delete(
    "/payment-statuses/{payment_status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف حالة دفع"
)
async def delete_payment_status_endpoint(payment_status_id: int, db: Session = Depends(get_db)):
    """
    حذف حالة مرجعية للدفع (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأي طلبات دفع موجودة.
    """
    orders_service.delete_payment_status_service(db=db, payment_status_id=payment_status_id)
    return

# ================================================================
# --- نقاط الوصول لترجمات حالات الدفع (Payment Status Translations) ---
# ================================================================

@inventory_lookups_router.post(
    "/payment-statuses/{payment_status_id}/translations",
    response_model=order_schemas.PaymentStatusTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لحالة دفع أو تحديثها"
)
async def create_payment_status_translation_endpoint(
    payment_status_id: int,
    trans_in: order_schemas.PaymentStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء ترجمة جديدة لحالة مرجعية للدفع بلغة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب بتضارب.
    """
    return orders_service.create_payment_status_translation_service(db=db, payment_status_id=payment_status_id, trans_in=trans_in)

@inventory_lookups_router.get(
    "/payment-statuses/{payment_status_id}/translations/{language_code}",
    response_model=order_schemas.PaymentStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة دفع"
)
async def get_payment_status_translation_details_endpoint(
    payment_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة حالة مرجعية للدفع بلغة محددة."""
    return orders_service.get_payment_status_translation_details(db=db, payment_status_id=payment_status_id, language_code=language_code)

@inventory_lookups_router.patch(
    "/payment-statuses/{payment_status_id}/translations/{language_code}",
    response_model=order_schemas.PaymentStatusTranslationRead,
    summary="[Admin] تحديث ترجمة حالة دفع"
)
async def update_payment_status_translation_endpoint(
    payment_status_id: int,
    language_code: str,
    trans_in: order_schemas.PaymentStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة حالة مرجعية للدفع بلغة محددة."""
    return orders_service.update_payment_status_translation_service(db=db, payment_status_id=payment_status_id, language_code=language_code, trans_in=trans_in)

@inventory_lookups_router.delete(
    "/payment-statuses/{payment_status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة حالة دفع"
)
async def delete_payment_status_translation_endpoint(
    payment_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة حالة مرجعية للدفع بلغة محددة (حذف صارم)."""
    orders_service.delete_payment_status_translation_service(db=db, payment_status_id=payment_status_id, language_code=language_code)
    return

# ================================================================
# --- نقاط الوصول لحالات بنود الطلب (Order Item Statuses) ---
# ================================================================

@inventory_lookups_router.post(
    "/order-item-statuses",
    response_model=order_schemas.OrderItemStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة بند طلب جديدة"
)
async def create_order_item_status_endpoint(
    status_in: order_schemas.OrderItemStatusCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مرجعية جديدة لبند الطلب (مثلاً: 'قيد التجهيز', 'تم الشحن جزئيًا').
    تتطلب صلاحية 'ADMIN_MANAGE_PRODUCT_LOOKUPS'.
    """
    return orders_service.create_order_item_status_service(db=db, status_in=status_in)

@inventory_lookups_router.get(
    "/order-item-statuses",
    response_model=List[order_schemas.OrderItemStatusRead],
    summary="[Admin] جلب جميع حالات بنود الطلب"
)
async def get_all_order_item_statuses_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع الحالات المرجعية لبنود الطلب في النظام."""
    return orders_service.get_all_order_item_statuses_service(db=db)

@inventory_lookups_router.get(
    "/order-item-statuses/{item_status_id}",
    response_model=order_schemas.OrderItemStatusRead,
    summary="[Admin] جلب تفاصيل حالة بند طلب واحدة"
)
async def get_order_item_status_details_endpoint(item_status_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل حالة مرجعية لبند طلب بالـ ID الخاص بها."""
    return orders_service.get_order_item_status_details(db=db, item_status_id=item_status_id)

@inventory_lookups_router.patch(
    "/order-item-statuses/{item_status_id}",
    response_model=order_schemas.OrderItemStatusRead,
    summary="[Admin] تحديث حالة بند طلب"
)
async def update_order_item_status_endpoint(
    item_status_id: int,
    status_in: order_schemas.OrderItemStatusUpdate,
    db: Session = Depends(get_db)
):
    """تحديث حالة مرجعية لبند طلب."""
    return orders_service.update_order_item_status_service(db=db, item_status_id=item_status_id, status_in=status_in)

@inventory_lookups_router.delete(
    "/order-item-statuses/{item_status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف حالة بند طلب"
)
async def delete_order_item_status_endpoint(item_status_id: int, db: Session = Depends(get_db)):
    """
    حذف حالة مرجعية لبند طلب (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأي بنود طلبات موجودة.
    """
    orders_service.delete_order_item_status_service(db=db, item_status_id=item_status_id)
    return

# ================================================================
# --- نقاط الوصول لترجمات حالات بنود الطلب (Order Item Status Translations) ---
# ================================================================

@inventory_lookups_router.post(
    "/order-item-statuses/{item_status_id}/translations",
    response_model=order_schemas.OrderItemStatusTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لحالة بند طلب أو تحديثها"
)
async def create_order_item_status_translation_endpoint(
    item_status_id: int,
    trans_in: order_schemas.OrderItemStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء ترجمة جديدة لحالة مرجعية لبند طلب بلغة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب بتضارب.
    """
    return orders_service.create_order_item_status_translation_service(db=db, item_status_id=item_status_id, trans_in=trans_in)

@inventory_lookups_router.get(
    "/order-item-statuses/{item_status_id}/translations/{language_code}",
    response_model=order_schemas.OrderItemStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة بند طلب"
)
async def get_order_item_status_translation_details_endpoint(
    item_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة حالة مرجعية لبند طلب بلغة محددة."""
    return orders_service.get_order_item_status_translation_details(db=db, item_status_id=item_status_id, language_code=language_code)

@inventory_lookups_router.patch(
    "/order-item-statuses/{item_status_id}/translations/{language_code}",
    response_model=order_schemas.OrderItemStatusTranslationRead,
    summary="[Admin] تحديث ترجمة حالة بند طلب"
)
async def update_order_item_status_translation_endpoint(
    item_status_id: int,
    language_code: str,
    trans_in: order_schemas.OrderItemStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة حالة مرجعية لبند طلب بلغة محددة."""
    return orders_service.update_order_item_status_translation_service(db=db, item_status_id=item_status_id, language_code=language_code, trans_in=trans_in)

@inventory_lookups_router.delete(
    "/order-item-statuses/{item_status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة حالة بند طلب"
)
async def delete_order_item_status_translation_endpoint(
    item_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة حالة مرجعية لبند طلب بلغة محددة (حذف صارم)."""
    orders_service.delete_order_item_status_translation_service(db=db, item_status_id=item_status_id, language_code=language_code)
    return

# backend\src\api\v1\routers\product_admin_router.py

# ... (الاستيرادات والراوترات السابقة، بما في ذلك inventory_lookups_router) ...

# ================================================================
# --- قسم إدارة عمليات السوق العامة (Admin - General Market Operations) ---
# ================================================================

market_management_router = APIRouter(
    prefix="/market-operations", # مسار فرعي جديد لإدارة جميع عمليات السوق
    tags=["Admin - Market Operations"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_ORDER_MANAGE_ANY"))] # صلاحية عامة لإدارة عمليات السوق
)

# --- نقاط الوصول لإدارة الطلبات (Orders) كمسؤول ---
@market_management_router.get(
    "/orders",
    response_model=List[order_schemas.OrderRead],
    summary="[Admin] جلب جميع الطلبات في النظام"
)
async def get_all_orders_for_admin_endpoint(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    يجلب قائمة بجميع الطلبات الموجودة في النظام (بما في ذلك التفاصيل).
    تتطلب صلاحية 'ADMIN_ORDER_MANAGE_ANY' أو 'ADMIN_ORDER_VIEW_ANY'.
    """
    return orders_service.get_all_orders_for_admin(db=db, skip=skip, limit=limit)

@market_management_router.get(
    "/orders/{order_id}",
    response_model=order_schemas.OrderRead,
    summary="[Admin] جلب تفاصيل طلب واحد (إداري)"
)
async def get_order_details_admin_endpoint(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_ORDER_MANAGE_ANY")) # صلاحية عامة للوصول
):
    """
    يجلب تفاصيل طلب واحد بالـ ID الخاص به.
    هذه النقطة مخصصة للمسؤولين لعرض تفاصيل أي طلب.
    """
    return orders_service.get_order_details(db=db, order_id=order_id, current_user=current_user)

@market_management_router.patch(
    "/orders/{order_id}/status",
    response_model=order_schemas.OrderRead,
    summary="[Admin] تحديث حالة طلب (إداري)"
)
async def update_order_status_admin_endpoint(
    order_id: UUID,
    status_update: order_schemas.OrderUpdate, # يجب أن يحتوي على order_status_id
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_ORDER_MANAGE_ANY"))
):
    """
    يسمح للمسؤول بتحديث حالة طلب محدد مباشرة.
    يتطلب صلاحية 'ADMIN_ORDER_MANAGE_ANY'.
    """
    if status_update.order_status_id is None:
        raise BadRequestException(detail="يجب توفير معرف الحالة الجديدة (order_status_id).")
    return orders_service.update_order_status(db=db, order_id=order_id, new_status_id=status_update.order_status_id, current_user=current_user)

@market_management_router.post(
    "/orders/{order_id}/cancel",
    response_model=order_schemas.OrderRead,
    summary="[Admin] إلغاء طلب (إداري)",
    description="""
    يسمح للمسؤول بإلغاء طلب معين (حذف ناعم).
    تتم عملية الإلغاء بغض النظر عن حالة الطلب أو منشئه.
    """,
)
async def cancel_order_admin_endpoint(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_ORDER_MANAGE_ANY")),
    reason: Optional[str] = None
):
    """نقطة وصول لإلغاء طلب محدد بواسطة المسؤول."""
    return orders_service.cancel_order(db=db, order_id=order_id, current_user=current_user, reason=reason)

# --- نقاط الوصول لإدارة طلبات عروض الأسعار (RFQs) كمسؤول ---
@market_management_router.get(
    "/rfqs",
    response_model=List[rfq_schemas.RfqRead],
    summary="[Admin] جلب جميع طلبات عروض الأسعار (RFQs) في النظام"
)
async def get_all_rfqs_for_admin_endpoint(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    يجلب قائمة بجميع طلبات عروض الأسعار (RFQs) الموجودة في النظام.
    تتطلب صلاحية 'ADMIN_RFQ_MANAGE_ANY' أو 'ADMIN_RFQ_VIEW_ANY'.
    """
    return rfqs_service.get_all_rfqs_for_admin(db=db, skip=skip, limit=limit)

@market_management_router.get(
    "/rfqs/{rfq_id}",
    response_model=rfq_schemas.RfqRead,
    summary="[Admin] جلب تفاصيل طلب RFQ واحد (إداري)"
)
async def get_rfq_details_admin_endpoint(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_RFQ_MANAGE_ANY"))
):
    """
    يجلب تفاصيل طلب عرض أسعار (RFQ) واحد بالـ ID الخاص به.
    مخصصة للمسؤولين لعرض تفاصيل أي RFQ.
    """
    return rfqs_service.get_rfq_details(db=db, rfq_id=rfq_id, current_user=current_user)

@market_management_router.patch(
    "/rfqs/{rfq_id}/status",
    response_model=rfq_schemas.RfqRead,
    summary="[Admin] تحديث حالة طلب RFQ (إداري)"
)
async def update_rfq_status_admin_endpoint(
    rfq_id: int,
    status_update: rfq_schemas.RfqUpdate, # يجب أن يحتوي على rfq_status_id
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_RFQ_MANAGE_ANY"))
):
    """
    يسمح للمسؤول بتحديث حالة طلب عرض أسعار (RFQ) محدد مباشرة.
    """
    if status_update.rfq_status_id is None:
        raise BadRequestException(detail="يجب توفير معرف الحالة الجديدة (rfq_status_id).")
    return rfqs_service.update_rfq_status(db=db, rfq_id=rfq_id, new_status_id=status_update.rfq_status_id, current_user=current_user)

@market_management_router.post(
    "/rfqs/{rfq_id}/cancel",
    response_model=rfq_schemas.RfqRead,
    summary="[Admin] إلغاء طلب RFQ (إداري)",
    description="""
    يسمح للمسؤول بإلغاء طلب RFQ معين (حذف ناعم).
    تتم عملية الإلغاء بغض النظر عن حالة الـ RFQ.
    """,
)
async def cancel_rfq_admin_endpoint(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_RFQ_MANAGE_ANY"))
):
    """نقطة وصول لإلغاء طلب RFQ محدد بواسطة المسؤول."""
    return rfqs_service.cancel_rfq(db=db, rfq_id=rfq_id, current_user=current_user)


# --- نقاط الوصول لإدارة عروض الأسعار (Quotes) كمسؤول ---
@market_management_router.get(
    "/quotes",
    response_model=List[quote_schemas.QuoteRead],
    summary="[Admin] جلب جميع عروض الأسعار في النظام"
)
async def get_all_quotes_for_admin_endpoint(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    يجلب قائمة بجميع عروض الأسعار الموجودة في النظام.
    تتطلب صلاحية 'ADMIN_QUOTE_MANAGE_ANY' أو 'ADMIN_QUOTE_VIEW_ANY'.
    """
    return quotes_service.get_all_quotes_for_admin(db=db, skip=skip, limit=limit)

@market_management_router.get(
    "/quotes/{quote_id}",
    response_model=quote_schemas.QuoteRead,
    summary="[Admin] جلب تفاصيل عرض سعر واحد (إداري)"
)
async def get_quote_details_admin_endpoint(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_QUOTE_MANAGE_ANY"))
):
    """
    يجلب تفاصيل عرض سعر واحد بالـ ID الخاص به.
    مخصصة للمسؤولين لعرض تفاصيل أي عرض سعر.
    """
    return quotes_service.get_quote_details(db=db, quote_id=quote_id, current_user=current_user)

@market_management_router.patch(
    "/quotes/{quote_id}/status",
    response_model=quote_schemas.QuoteRead,
    summary="[Admin] تحديث حالة عرض سعر (إداري)"
)
async def update_quote_status_admin_endpoint(
    quote_id: int,
    status_update: quote_schemas.QuoteUpdate, # يجب أن يحتوي على quote_status_id
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_QUOTE_MANAGE_ANY"))
):
    """
    يسمح للمسؤول بتحديث حالة عرض سعر محدد مباشرة.
    """
    if status_update.quote_status_id is None:
        raise BadRequestException(detail="يجب توفير معرف الحالة الجديدة (quote_status_id).")
    return quotes_service.update_quote_status(db=db, quote_id=quote_id, new_status_id=status_update.quote_status_id, current_user=current_user)

# --- نقاط الوصول لإدارة الشحنات (Shipments) كمسؤول ---
@market_management_router.get(
    "/shipments",
    response_model=List[shipment_schemas.ShipmentRead],
    summary="[Admin] جلب جميع الشحنات في النظام"
)
async def get_all_shipments_for_admin_endpoint(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    يجلب قائمة بجميع الشحنات الموجودة في النظام.
    تتطلب صلاحية 'ADMIN_ORDER_MANAGE_ANY' أو 'ADMIN_SHIPMENT_VIEW_ANY'.
    """
    return shipments_service.get_all_shipments_for_admin(db=db, skip=skip, limit=limit)

@market_management_router.get(
    "/shipments/{shipment_id}",
    response_model=shipment_schemas.ShipmentRead,
    summary="[Admin] جلب تفاصيل شحنة واحدة (إداري)"
)
async def get_shipment_details_admin_endpoint(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_ORDER_MANAGE_ANY")) # TODO: صلاحية ADMIN_SHIPMENT_VIEW_ANY
):
    """
    يجلب تفاصيل شحنة واحدة بالـ ID الخاص بها.
    مخصصة للمسؤولين لعرض تفاصيل أي شحنة.
    """
    return shipments_service.get_shipment_details(db=db, shipment_id=shipment_id, current_user=current_user)

@market_management_router.patch(
    "/shipments/{shipment_id}/status",
    response_model=shipment_schemas.ShipmentRead,
    summary="[Admin] تحديث حالة شحنة (إداري)"
)
async def update_shipment_status_admin_endpoint(
    shipment_id: int,
    status_update: shipment_schemas.ShipmentUpdate, # يجب أن يحتوي على shipment_status_id
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_ORDER_MANAGE_ANY")) # TODO: صلاحية ADMIN_SHIPMENT_UPDATE_ANY
):
    """
    يسمح للمسؤول بتحديث حالة شحنة محددة مباشرة.
    """
    if status_update.shipment_status_id is None:
        raise BadRequestException(detail="يجب توفير معرف الحالة الجديدة (shipment_status_id).")
    return shipments_service.update_shipment_status(db=db, shipment_id=shipment_id, new_status_id=status_update.shipment_status_id, current_user=current_user)

@market_management_router.post(
    "/shipments/{shipment_id}/cancel",
    response_model=shipment_schemas.ShipmentRead,
    summary="[Admin] إلغاء شحنة (إداري)",
    description="""
    يسمح للمسؤول بإلغاء شحنة معينة (حذف ناعم).
    تتم عملية الإلغاء بغض النظر عن حالة الشحنة.
    """,
)
async def cancel_shipment_admin_endpoint(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ADMIN_ORDER_MANAGE_ANY")) # TODO: صلاحية ADMIN_SHIPMENT_MANAGE_ANY
):
    """نقطة وصول لإلغاء شحنة محددة بواسطة المسؤول."""
    return shipments_service.cancel_shipment(db=db, shipment_id=shipment_id, current_user=current_user)




# ================================================================
# --- القسم الجديد: إدارة فئات المنتجات (Categories) ---
# ================================================================
category_router = APIRouter(
    prefix="/categories",
    tags=["Admin - Products (Categories)"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_CATEGORIES"))]
)

@category_router.post("/", response_model=category_schemas.ProductCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category_in: category_schemas.ProductCategoryCreate, db: Session = Depends(get_db)):
    """
    إنشاء فئة منتج جديدة (مثل: فواكه، خضروات ورقية).
    """
    return category_service.create_new_category(db, category_in=category_in)

@category_router.get("/", response_model=List[category_schemas.ProductCategoryRead])
def get_all_categories(db: Session = Depends(get_db)):
    """
    جلب قائمة بكل فئات المنتجات في النظام.
    """
    return category_service.get_all_categories(db)

@category_router.patch("/{category_id}", response_model=category_schemas.ProductCategoryRead)
def update_category(category_id: int, category_in: category_schemas.ProductCategoryUpdate, db: Session = Depends(get_db)):
    """
    تحديث بيانات فئة منتج معينة.
    """
    return category_service.update_existing_category(db, category_id=category_id, category_in=category_in)

@category_router.delete("/{category_id}", response_model=dict, summary="حذف ناعم لفئة منتج")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    حذف ناعم لفئة منتج.
    سيتم نقل المنتجات المرتبطة إلى فئة 'غير مصنف'.
    """
    return category_service.delete_category_by_id(db, category_id=category_id)

# --- Endpoints for Category Translations ---

@category_router.post("/{category_id}/translations", response_model=category_schemas.ProductCategoryRead)
def manage_category_translation(category_id: int, trans_in: category_schemas.ProductCategoryTranslationCreate, db: Session = Depends(get_db)):
    """
    إضافة أو تحديث ترجمة لفئة معينة.
    """
    return category_service.manage_category_translation(db, category_id=category_id, trans_in=trans_in)

@category_router.delete("/{category_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_translation(category_id: int, language_code: str, db: Session = Depends(get_db)):
    """
    حذف ترجمة فئة معينة بلغة محددة.
    """
    category_service.remove_category_translation(db, category_id=category_id, language_code=language_code)
    return


@category_router.get("/{category_id}", response_model=category_schemas.ProductCategoryRead, summary="جلب تفاصيل فئة واحدة")
def get_single_category(category_id: int, db: Session = Depends(get_db)):
    """
    جلب التفاصيل الكاملة لفئة منتج واحدة عن طريق الـ ID.
    """
    return category_service.get_category_by_id(db, category_id=category_id)

# ================================================================
# --- القسم الجديد: إدارة المنتجات (Products) ---
# ================================================================
products_management_router = APIRouter(
    prefix="/products",
    tags=["Admin - Products Management"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_PRODUCT_VIEW_ANY"))]
)

@products_management_router.get("/", response_model=List[product_schemas.ProductRead])
def get_all_products_as_admin(db: Session = Depends(get_db)):
    """[Admin] جلب كل المنتجات في النظام (بكل حالاتها)."""
    return product_service.get_all_products_for_admin(db)

@products_management_router.patch("/{product_id}/status", response_model=product_schemas.ProductRead)
def update_product_status_as_admin(
    product_id: UUID, 
    status_update: product_lookups_schemas.ProductStatusUpdate, # نفترض وجود هذا الـ schema
    db: Session = Depends(get_db),
    admin_user: User = Depends(dependencies.has_permission("ADMIN_PRODUCT_UPDATE_ANY"))
):
    """[Admin] تحديث حالة أي منتج (مثلاً: الموافقة عليه بنقله من DRAFT إلى ACTIVE)."""
    return product_service.update_product_status(db, product_id=product_id, new_status_id=status_update.product_status_id)

# ================================================================
# --- قسم إدارة المخزون والجداول المرجعية (Inventory) ---
#    (تأكد من أن هذا هو نفس inventory_lookups_router الذي أضفنا إليه نقاط وصول المخزون سابقًا)
# ================================================================

inventory_lookups_router = APIRouter(
    prefix="/lookups",
    tags=["Admin - Inventory (Lookups)"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_PRODUCT_LOOKUPS"))] # صلاحية مخصصة
)

# ... (نقاط الوصول الحالية في inventory_lookups_router، بما في ذلك حالات المخزون وأنواع حركاته) ...


# ================================================================
# --- نقاط الوصول لحالات المحاصيل المتوقعة (ExpectedCropStatus) ---
# ================================================================

@inventory_lookups_router.post(
    "/expected-crop-statuses",
    response_model=future_offerings_schemas.ExpectedCropStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة محصول متوقع جديدة"
)
async def create_expected_crop_status_endpoint(
    status_in: future_offerings_schemas.ExpectedCropStatusCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مرجعية جديدة للمحصول المتوقع (مثل 'متاح للحجز', 'تم الحجز', 'ملغى').
    تتطلب صلاحية 'ADMIN_MANAGE_PRODUCT_LOOKUPS'.
    """
    return future_offerings_service.create_new_expected_crop_status(db=db, status_in=status_in)

@inventory_lookups_router.get(
    "/expected-crop-statuses",
    response_model=List[future_offerings_schemas.ExpectedCropStatusRead],
    summary="[Admin] جلب جميع حالات المحاصيل المتوقعة"
)
async def get_all_expected_crop_statuses_endpoint(db: Session = Depends(get_db)):
    """
    جلب قائمة بجميع الحالات المرجعية للمحاصيل المتوقعة في النظام.
    """
    return future_offerings_service.get_all_expected_crop_statuses(db=db)

@inventory_lookups_router.get(
    "/expected-crop-statuses/{status_id}",
    response_model=future_offerings_schemas.ExpectedCropStatusRead,
    summary="[Admin] جلب تفاصيل حالة محصول متوقع واحدة"
)
async def get_expected_crop_status_details_endpoint(status_id: int, db: Session = Depends(get_db)):
    """
    جلب تفاصيل حالة مرجعية لمحصول متوقع بالـ ID الخاص بها.
    """
    return future_offerings_service.get_expected_crop_status_by_id(db=db, status_id=status_id)

@inventory_lookups_router.patch(
    "/expected-crop-statuses/{status_id}",
    response_model=future_offerings_schemas.ExpectedCropStatusRead,
    summary="[Admin] تحديث حالة محصول متوقع"
)
async def update_expected_crop_status_endpoint(
    status_id: int,
    status_in: future_offerings_schemas.ExpectedCropStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    تحديث حالة مرجعية لمحصول متوقع.
    """
    return future_offerings_service.update_expected_crop_status(db=db, status_id=status_id, status_in=status_in)

@inventory_lookups_router.delete(
    "/expected-crop-statuses/{status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف حالة محصول متوقع"
)
async def delete_expected_crop_status_endpoint(status_id: int, db: Session = Depends(get_db)):
    """
    حذف حالة مرجعية لمحصول متوقع (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأي عروض محاصيل متوقعة موجودة.
    """
    future_offerings_service.delete_expected_crop_status(db=db, status_id=status_id)
    return

# ================================================================
# --- نقاط الوصول لترجمات حالات المحاصيل المتوقعة (ExpectedCropStatusTranslation) ---
# ================================================================

@inventory_lookups_router.post(
    "/expected-crop-statuses/{status_id}/translations",
    response_model=future_offerings_schemas.ExpectedCropStatusTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لحالة محصول متوقع أو تحديثها"
)
async def create_expected_crop_status_translation_endpoint(
    status_id: int,
    trans_in: future_offerings_schemas.ExpectedCropStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء ترجمة جديدة لحالة مرجعية لمحصول متوقع بلغة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب بتضارب.
    """
    return future_offerings_service.create_expected_crop_status_translation(db=db, status_id=status_id, trans_in=trans_in)

@inventory_lookups_router.get(
    "/expected-crop-statuses/{status_id}/translations/{language_code}",
    response_model=future_offerings_schemas.ExpectedCropStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة محصول متوقع"
)
async def get_expected_crop_status_translation_endpoint(
    status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة حالة مرجعية لمحصول متوقع بلغة محددة."""
    return future_offerings_service.get_expected_crop_status_translation_details(db=db, status_id=status_id, language_code=language_code)

@inventory_lookups_router.patch(
    "/expected-crop-statuses/{status_id}/translations/{language_code}",
    response_model=future_offerings_schemas.ExpectedCropStatusTranslationRead,
    summary="[Admin] تحديث ترجمة حالة محصول متوقع"
)
async def update_expected_crop_status_translation_endpoint(
    status_id: int,
    language_code: str,
    trans_in: future_offerings_schemas.ExpectedCropStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة حالة مرجعية لمحصول متوقع بلغة محددة."""
    return future_offerings_service.update_expected_crop_status_translation(db=db, status_id=status_id, language_code=language_code, trans_in=trans_in)

@inventory_lookups_router.delete(
    "/expected-crop-statuses/{status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة حالة محصول متوقع"
)
async def delete_expected_crop_status_translation_endpoint(
    status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة حالة مرجعية لمحصول متوقع بلغة محددة (حذف صارم)."""
    future_offerings_service.delete_expected_crop_status_translation(db=db, status_id=status_id, language_code=language_code)
    return

# backend\src\api\v1\routers\product_admin_router.py

# ... (الاستيرادات والراوترات السابقة، بما في ذلك الأجزاء المضافة للمجموعة 4 والمجموعة 5.أ) ...

# ================================================================
# --- قسم إدارة المزادات العامة (Admin - General Auction Management) ---
# ================================================================

# راوتر لإدارة المزادات من جانب المسؤول (عرض شامل)
auction_general_admin_router = APIRouter(
    prefix="/auctions-management", # مسار فرعي جديد لإدارة المزادات بشكل عام
    tags=["Admin - General Auction Management"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_AUCTION_VIEW_ANY"))] # صلاحية عامة لعرض المزادات
)

# --- نقاط الوصول لجلب المزادات كمسؤول ---
@auction_general_admin_router.get(
    "/auctions",
    response_model=List[auction_schemas.AuctionRead],
    summary="[Admin] جلب جميع المزادات في النظام"
)
async def get_all_auctions_for_admin_endpoint(
    db: Session = Depends(get_db),
    status_name_key: Optional[str] = None,
    type_name_key: Optional[str] = None,
    seller_user_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    يجلب قائمة بجميع المزادات الموجودة في النظام (بما في ذلك التفاصيل).
    تتطلب صلاحية 'ADMIN_AUCTION_VIEW_ANY'.
    """
    return auctions_service.get_all_auctions(db=db, status_name_key=status_name_key, type_name_key=type_name_key, seller_user_id=seller_user_id, skip=skip, limit=limit)

# --- نقاط الوصول لجلب المزايدات كمسؤول ---
@auction_general_admin_router.get(
    "/bids",
    response_model=List[bidding_schemas.BidRead],
    summary="[Admin] جلب جميع المزايدات في النظام"
)
async def get_all_bids_for_admin_endpoint(
    db: Session = Depends(get_db),
    auction_id: Optional[UUID] = None,
    bidder_user_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    يجلب قائمة بجميع المزايدات الموجودة في النظام، مع خيارات تصفية.
    تتطلب صلاحية 'ADMIN_AUCTION_VIEW_ANY'.
    """
    return bidding_service.get_all_bids_for_admin(db=db, auction_id=auction_id, bidder_user_id=bidder_user_id, skip=skip, limit=limit)

# --- نقاط الوصول لجلب تسويات المزادات كمسؤول ---
@auction_general_admin_router.get(
    "/settlements",
    response_model=List[settlement_schemas.AuctionSettlementRead],
    summary="[Admin] جلب جميع تسويات المزادات في النظام"
)
async def get_all_auction_settlements_for_admin_endpoint(
    db: Session = Depends(get_db),
    auction_id: Optional[UUID] = None,
    winner_user_id: Optional[UUID] = None,
    seller_user_id: Optional[UUID] = None,
    settlement_status_name_key: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    يجلب قائمة بجميع تسويات المزادات الموجودة في النظام، مع خيارات تصفية.
    تتطلب صلاحية 'ADMIN_AUCTION_VIEW_ANY'.
    """
    return settlements_service.get_all_auction_settlements(db=db, auction_id=auction_id, winner_user_id=winner_user_id, seller_user_id=seller_user_id, settlement_status_name_key=settlement_status_name_key, skip=skip, limit=limit)



# ================================================================
# --- دمج الراوترات الفرعية في راوتر إدارة المنتجات الرئيسي ---
# ================================================================
router.include_router(admin_core_users_router.router) # <-- دمج راوتر إدارة المستخدمين الأساسية
router.include_router(admin_rbac_router.router)       # <-- دمج راوتر إدارة الأدوار والصلاحيات
router.include_router(admin_address_lookups_router.router) # <-- دمج راوتر إدارة جداول العناوين
router.include_router(admin_verification_router.router) # <-- دمج راوتر إدارة التراخيص والتحقق
attributes_router.include_router(attribute_values_router)
attributes_router.include_router(product_variety_attributes_router)
router.include_router(attributes_router)
router.include_router(inventory_lookups_router) # هذا الراوتر يحتوي الآن على نقاط وصول لحالات وأنواع المخزون
router.include_router(category_router)
router.include_router(products_management_router) 

router.include_router(inventory_management_router) # <-- راوتر إدارة بنود المخزون
router.include_router(pricing_router.router) # <--    لدمج راوتر الأسعار
router.include_router(market_management_router) # <--     راوتر إدارة عمليات السوق
router.include_router(auctions_router.router) # <-- دمج راوتر المزادات للمستخدمين

router.include_router(auction_general_admin_router) # <-- دمج راوتر إدارة المزادات العامة للمسؤول



# ================================================================
# --- دمج الراوترات الفرعية الإدارية المتخصصة ---
# ================================================================
# كل راوتر فرعي له prefix و tags خاص به معرف في ملفه.
# الترتيب هنا يحدد ترتيب ظهور الأقسام في Swagger UI ضمن لوحة التحكم الإدارية.

# 1. راوترات إدارة المستخدمين (المجموعة 1)
router.include_router(admin_core_users_router.router) # <-- دمج راوتر إدارة المستخدمين الأساسية
router.include_router(admin_rbac_router.router)       # <-- دمج راوتر إدارة الأدوار والصلاحيات
router.include_router(admin_address_lookups_router.router) # <-- دمج راوتر إدارة جداول العناوين
router.include_router(admin_verification_router.router) # <-- دمج راوتر إدارة التراخيص والتحقق

# 2. راوترات إدارة المزادات (المجموعة 5)
router.include_router(admin_auctions_router.router)

# 3. راوترات إدارة المنتجات والمخزون (المجموعة 2) - جداول Lookups
# هذا كان سابقاً جزءاً من product_admin_router.py، والآن يمكن أن يكون راوتراً مستقلاً
# إذا كان لديك راوترadmin_product_lookups_router أو inventory_lookups_router منفصل.
# إذا لم يكن كذلك، يمكنك الاحتفاظ بنقاط الوصول تلك في هذا الملف مباشرة إذا كانت قليلة.
# ولكن الأفضل هو جعلها راوترات منفصلة.
# بما أننا قمنا بدمج inventory_lookups_router في product_admin_router.py سابقاً،
# سنفترض أنه تم نقله إلى ملفه الخاص (admin_inventory_lookups_router.py) أو سيبقى هنا كـ TODO
# للتوضيح: إذا كنت قد أنشأت admin_inventory_lookups_router.py، فضعه هنا.
# router.include_router(admin_inventory_lookups_router.router) # مثال

router.include_router(unit_of_measure_admin_router.router) # هذا راوتر جاهز لوحدات القياس

# TODO: راوترات إدارية أخرى للمجموعات 2، 3، 4، 6، 7، 8، 9، 10، 11، 13، 14
#        يجب أن يتم استيرادها ودمجها هنا أيضاً بنفس النمط.
#        مثال:
#        from src.api.v1.routers import admin_product_management_router
#        from src.api.v1.routers import admin_market_management_router
#        from src.api.v1.routers import admin_pricing_management_router
#        router.include_router(admin_product_management_router.router)
#        router.include_router(admin_market_management_router.router)
#        router.include_router(admin_pricing_management_router.router)
