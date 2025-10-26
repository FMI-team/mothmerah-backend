# backend\src\auctions\schemas\auction_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID # لمعرفات المستخدمين والمنتجات

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas أخرى
# AuctionStatusRead, AuctionTypeRead تستورد الآن من src.lookups.schemas
from src.lookups.schemas import ( 
    AuctionStatusRead,
    AuctionTypeRead
)

# TODO: تأكد من أن UserRead, ProductRead, UnitOfMeasureRead موجودة ومستوردة
from src.users.schemas.core_schemas import UserRead
from src.products.schemas.product_schemas import ProductRead
from src.products.schemas.units_schemas import UnitOfMeasureRead
from src.products.schemas.packaging_schemas import PackagingOptionRead

# ==========================================================
# --- Schemas لحالات المزاد (Auction Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)


# ==========================================================
# --- Schemas لأنواع المزادات (Auction Types) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)


# ==========================================================
# --- Schemas لصور اللوت (Lot Images) ---
# ==========================================================
class LotImageBase(BaseModel):
    """النموذج الأساسي لصور اللوت: يصف صورة مرتبطة بلوت مزاد."""
    image_id: int = Field(..., description="معرف الصورة من جدول الصور العام (Module 2.ج).")
    sort_order: int = Field(0, description="ترتيب عرض الصورة ضمن اللوت.")

class LotImageCreate(LotImageBase):
    """نموذج لإنشاء صورة لوت جديدة. يتطلب lot_id عند الإنشاء."""
    lot_id: UUID = Field(..., description="معرف اللوت الذي تنتمي إليه هذه الصورة.")
    pass

class LotImageUpdate(BaseModel):
    """نموذج لتحديث صورة لوت موجودة."""
    sort_order: Optional[int] = Field(None)

class LotImageRead(LotImageBase):
    """نموذج لقراءة وعرض تفاصيل صورة اللوت."""
    lot_image_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين بيانات الصورة الكاملة (ImageRead) بشكل متداخل.
    # image: "ImageRead" # تتطلب استيراد من schemas/image_schemas.py


# ==========================================================
# --- Schemas لمنتجات اللوت (Lot Products) ---
# ==========================================================
class LotProductBase(BaseModel):
    """النموذج الأساسي لمنتجات اللوت: يصف منتجًا معينًا ضمن لوت مجمع."""
    packaging_option_id: int = Field(..., description="معرف خيار التعبئة والتغليف للمنتج (من المجموعة 2.ج).")
    quantity_in_lot: float = Field(..., gt=0, description="الكمية من هذا المنتج في اللوت.")

class LotProductCreate(LotProductBase):
    """نموذج لإنشاء منتج لوت جديد. يتطلب lot_id عند الإنشاء."""
    lot_id: UUID = Field(..., description="معرف اللوت الذي ينتمي إليه هذا المنتج.")
    pass

class LotProductUpdate(BaseModel):
    """نموذج لتحديث منتج لوت موجود. لا يمكن تغيير المعرفات أو الكميات بعد الإنشاء عادةً."""
    quantity_in_lot: Optional[float] = Field(None, gt=0)

class LotProductRead(LotProductBase):
    """نموذج لقراءة وعرض تفاصيل منتج اللوت."""
    lot_product_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات خيار التعبئة (PackagingOptionRead) بشكل متداخل.
    packaging_option: PackagingOptionRead # تتطلب استيراد من schemas/packaging_schemas.py


# ==========================================================
# --- Schemas للوطات/دفعات المزاد (Auction Lots) ---
# ==========================================================
class AuctionLotBase(BaseModel):
    """النموذج الأساسي للوت المزاد: يصف دفعة فردية ضمن المزاد."""
    auction_id: UUID = Field(..., description="معرف المزاد الأم الذي ينتمي إليه هذا اللوت.")
    lot_title_key: Optional[str] = Field(None, max_length=255, description="مفتاح لعنوان اللوت للترجمة (إذا كان معياريًا).")
    custom_lot_title: Optional[str] = Field(None, description="عنوان مخصص للوت بلغة الإدخال.")
    lot_description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف اللوت للترجمة (إذا كان معياريًا).")
    custom_lot_description: Optional[str] = Field(None, description="وصف مخصص للوت بلغة الإدخال.")
    quantity_in_lot: Optional[float] = Field(None, gt=0, description="الكمية الإجمالية في اللوت (إذا كان يمثل جزءًا من كمية المزاد الكلية).")
    lot_starting_price: Optional[float] = Field(None, gt=0, description="سعر البدء للوت (إذا كان لكل لوت سعر بدء خاص).")
    lot_status_id: Optional[int] = Field(None, description="حالة اللوت (يمكن استخدام AuctionStatus أو حالة خاصة باللوت).")
    # TODO: منطق عمل: التحقق من أن quantity_in_lot لا يتجاوز الكمية المعروضة في المزاد الأب.

class AuctionLotCreate(AuctionLotBase):
    """نموذج لإنشاء لوت مزاد جديد. يتضمن ترجماته ومنتجاته وصوره."""
    translations: Optional[List["AuctionLotTranslationCreate"]] = Field([], description="الترجمات الأولية لعنوان اللوت ووصفه.")
    products_in_lot: Optional[List[LotProductCreate]] = Field([], description="المنتجات المحددة في هذا اللوت المجمع.")
    images: Optional[List[LotImageBase]] = Field([], description="صور خاصة بهذا اللوت.")

class AuctionLotUpdate(BaseModel):
    """نموذج لتحديث لوت مزاد موجود. جميع الحقول اختيارية."""
    lot_title_key: Optional[str] = Field(None, max_length=255)
    custom_lot_title: Optional[str] = Field(None)
    lot_description_key: Optional[str] = Field(None, max_length=255)
    custom_lot_description: Optional[str] = Field(None)
    quantity_in_lot: Optional[float] = Field(None, gt=0)
    lot_starting_price: Optional[float] = Field(None, gt=0)
    lot_status_id: Optional[int] = Field(None)

class AuctionLotRead(AuctionLotBase):
    """نموذج لقراءة وعرض تفاصيل لوت مزاد."""
    lot_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    translations: List["AuctionLotTranslationRead"] = []
    products_in_lot: List[LotProductRead] = []
    images: List[LotImageRead] = []
    # TODO: يمكن تضمين AuctionStatusRead لـ lot_status.
    # lot_status: AuctionStatusRead
    # TODO: يمكن تضمين معلومات المزاد الأب (AuctionRead).
    auction: "AuctionRead" # <-- استخدام سلسلة نصية (Forward Reference)

# ==========================================================
# --- Schemas لترجمات لوطات المزاد (Auction Lot Translations) ---
# ==========================================================
class AuctionLotTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة لوت المزاد."""
    language_code: str = Field(..., max_length=10)
    translated_lot_title: Optional[str] = Field(None, max_length=255)
    translated_lot_description: Optional[str] = Field(None)

class AuctionLotTranslationCreate(AuctionLotTranslationBase):
    """نموذج لإنشاء ترجمة جديدة للوت مزاد."""
    pass

class AuctionLotTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة لوت مزاد موجودة."""
    translated_lot_title: Optional[str] = Field(None, max_length=255)
    translated_lot_description: Optional[str] = Field(None)

class AuctionLotTranslationRead(AuctionLotTranslationBase):
    """نموذج لقراءة وعرض ترجمة لوت مزاد."""
    lot_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas للمزادات (Auctions) ---
# ==========================================================
class AuctionBase(BaseModel):
    """النموذج الأساسي للمزاد: يصف الخصائص الرئيسية للمزاد."""
    seller_user_id: UUID = Field(..., description="معرف البائع الذي ينشئ المزاد.")
    product_id: UUID = Field(..., description="معرف المنتج من الكتالوج الذي يتم المزاد عليه.")
    auction_type_id: int = Field(..., description="معرف نوع المزاد (مثلاً: 'مزاد عادي', 'مزاد ما قبل الوصول').")
    auction_status_id: Optional[int] = Field(None, description="حالة المزاد (يُعين تلقائيًا عند الإنشاء).") # يُعين تلقائياً لـ SCHEDULED
    auction_title_key: Optional[str] = Field(None, max_length=255, description="مفتاح لعنوان المزاد للترجمة (إذا كان معياريًا).")
    custom_auction_title: Optional[str] = Field(None, description="عنوان مخصص للمزاد بلغة الإدخال.")
    auction_description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف المزاد للترجمة.")
    custom_auction_description: Optional[str] = Field(None, description="وصف مخصص للمزاد بلغة الإدخال.")
    start_timestamp: datetime = Field(..., description="تاريخ ووقت بدء المزاد.")
    end_timestamp: datetime = Field(..., description="تاريخ ووقت انتهاء المزاد.")
    starting_price_per_unit: float = Field(..., gt=0, description="السعر الافتتاحي لكل وحدة من المنتج.")
    minimum_bid_increment: float = Field(..., gt=0, description="الحد الأدنى لزيادة المزايدة في كل مرة.")
    reserve_price_per_unit: Optional[float] = Field(None, ge=0, description="السعر الاحتياطي لكل وحدة (إذا لم تصل المزايدات إليه، لا يتم البيع).")
    quantity_offered: float = Field(..., gt=0, description="الكمية المعروضة للمزاد.")
    unit_of_measure_id_for_quantity: int = Field(..., description="معرف وحدة القياس للكمية المعروضة.")
    is_private_auction: Optional[bool] = Field(False, description="هل المزاد خاص لمجموعة محددة من المشترين؟")
    pre_arrival_shipping_info: Optional[str] = Field(None, description="معلومات عن الشحنة القادمة (لمزادات ما قبل الوصول).")
    cancellation_reason: Optional[str] = Field(None, description="سبب إلغاء المزاد (إذا تم إلغاؤه).")
    
    # حقول تُحدث ديناميكيًا بواسطة النظام
    current_highest_bid_amount_per_unit: Optional[float] = Field(None, ge=0)
    current_highest_bidder_user_id: Optional[UUID] = None
    total_bids_count: Optional[int] = Field(0, ge=0)
    # TODO: منطق عمل: التأكد من أن start_timestamp قبل end_timestamp.
    # TODO: منطق عمل: التحقق من أن reserve_price_per_unit أكبر من أو يساوي starting_price_per_unit إن وجد.

class AuctionCreate(AuctionBase):
    """نموذج لإنشاء مزاد جديد. يتضمن قائمة بلوطاته."""
    lots: Optional[List["AuctionLotCreate"]] = Field([], description="قائمة باللوطات (دفعات) التي يتكون منها المزاد.")
    # TODO: يمكن إضافة قائمة بالمشاركين المستهدفين إذا كان المزاد خاصًا.

class AuctionUpdate(BaseModel):
    """نموذج لتحديث مزاد موجود. جميع الحقول اختيارية."""
    # لا يمكن تغيير seller_user_id, product_id, auction_type_id بعد الإنشاء عادةً.
    auction_status_id: Optional[int] = Field(None, description="تحديث حالة المزاد.")
    auction_title_key: Optional[str] = Field(None, max_length=255)
    custom_auction_title: Optional[str] = Field(None)
    auction_description_key: Optional[str] = Field(None, max_length=255)
    custom_auction_description: Optional[str] = Field(None)
    start_timestamp: Optional[datetime] = Field(None)
    end_timestamp: Optional[datetime] = Field(None) # يمكن تحديثه كسترنج لتفسير من الواجهة الأمامية
    starting_price_per_unit: Optional[float] = Field(None, gt=0)
    minimum_bid_increment: Optional[float] = Field(None, gt=0)
    reserve_price_per_unit: Optional[float] = Field(None, ge=0)
    quantity_offered: Optional[float] = Field(None, gt=0)
    unit_of_measure_id_for_quantity: Optional[int] = Field(None)
    is_private_auction: Optional[bool] = Field(None)
    pre_arrival_shipping_info: Optional[str] = Field(None)
    cancellation_reason: Optional[str] = Field(None)
    
    # حقول تُحدث ديناميكيًا بواسطة النظام
    current_highest_bid_amount_per_unit: Optional[float] = Field(None, ge=0)
    current_highest_bidder_user_id: Optional[UUID] = None
    total_bids_count: Optional[int] = Field(0, ge=0)
    # TODO: يمكن السماح بتعديل بعض الحقول فقط قبل بدء المزاد.

class AuctionRead(AuctionBase):
    """نموذج لقراءة وعرض تفاصيل المزاد بشكل كامل."""
    auction_id: UUID
    created_at: datetime
    updated_at: datetime
    
    lots: List["AuctionLotRead"] = Field([]) # لوطات المزاد المرتبطة
    
    # الكائنات المرتبطة بشكل متداخل (Nested Relationships)
    # TODO: يمكن تضمين معلومات البائع (UserRead), المنتج (ProductRead), نوع المزاد (AuctionTypeRead), حالة المزاد (AuctionStatusRead), أعلى مزايد (UserRead) بشكل متداخل.
    seller: UserRead
    product: ProductRead
    auction_type: AuctionTypeRead
    auction_status: AuctionStatusRead
    current_highest_bidder: Optional[UserRead] = None # قد لا يكون هناك مزايد بعد

    model_config = ConfigDict(from_attributes=True)
