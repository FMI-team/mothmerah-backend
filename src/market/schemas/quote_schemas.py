# backend\src\market\schemas\quote_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List,TYPE_CHECKING
from datetime import datetime, date # لـ Date/Timestamp
from uuid import UUID # لمعرفات المستخدمين والمنتجات

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas أخرى
# QuoteStatusRead تستورد الآن من src.lookups.schemas
from src.lookups.schemas import QuoteStatusRead 

# تأكد من أن UserRead, RfqRead, ProductPackagingOptionRead, UnitOfMeasureRead, AddressRead موجودة ومستوردة
from src.users.schemas.core_schemas import UserRead

# استيراد RfqRead فقط لأغراض فحص الأنواع (TYPE_CHECKING)
if TYPE_CHECKING: # <-- هذا الاستيراد يتم فقط لفحص الأنواع، لا يتم تنفيذه في وقت التشغيل
    from src.market.schemas.rfq_schemas import RfqRead # <-- استيراد RfqRead هنا
    from src.market.schemas.rfq_schemas import RfqItemRead # لاستخدامه في QuoteItemRead

# TODO: ProductPackagingOptionRead, UnitOfMeasureRead, AddressRead تحتاج استيراد
# from src.products.schemas.packaging_schemas import ProductPackagingOptionRead
# from src.products.schemas.units_schemas import UnitOfMeasureRead
# from src.users.schemas.address_schemas import AddressRead

# ==========================================================
# --- Schemas لحالات عرض السعر (Quote Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)


# ==========================================================
# --- Schemas لبنود عرض السعر (Quote Items) ---
#    (المودلات من backend\src\market\models\quotes_models.py)
# ==========================================================
class QuoteItemBase(BaseModel):
    """النموذج الأساسي لبند عرض السعر: يصف تفاصيل المنتج المعروض داخل عرض سعر."""
    rfq_item_id: int = Field(..., description="معرف بند طلب عرض الأسعار (RFQ Item) الذي يرتبط به هذا العرض.")
    offered_product_description: Optional[str] = Field(None, description="وصف مخصص للمنتج المعروض إذا كان يختلف عن وصف RFQ.")
    offered_quantity: float = Field(..., gt=0, description="الكمية المعروضة من هذا البند.")
    unit_price_offered: float = Field(..., gt=0, description="السعر للوحدة المعروض من قبل البائع.")
    total_item_price: float = Field(..., gt=0, description="إجمالي سعر هذا البند (الكمية المعروضة × سعر الوحدة المعروض).")
    item_notes: Optional[str] = Field(None, description="ملاحظات خاصة بهذا البند من العرض.")

class QuoteItemCreate(QuoteItemBase):
    """نموذج لإنشاء بند عرض سعر جديد. يُستخدم كجزء من QuoteCreate."""
    # quote_id سيتم تعيينه في طبقة الخدمة/الـ CRUD.
    pass

class QuoteItemUpdate(BaseModel):
    """نموذج لتحديث بند عرض سعر موجود. لا يمكن تغيير المعرفات أو الكميات بعد الإنشاء عادةً."""
    offered_product_description: Optional[str] = Field(None)
    offered_quantity: Optional[float] = Field(None, gt=0)
    unit_price_offered: Optional[float] = Field(None, gt=0)
    total_item_price: Optional[float] = Field(None, gt=0)
    item_notes: Optional[str] = Field(None)

class QuoteItemRead(QuoteItemBase):
    """نموذج لقراءة وعرض تفاصيل بند عرض السعر."""
    quote_item_id: int
    quote_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات بند طلب RFQ المرتبط (RfqItemRead) بشكل متداخل.
    # rfq_item: "RfqItemRead" # تتطلب استيراد من schemas/rfq_schemas.py


# ==========================================================
# --- Schemas لعروض الأسعار (Quotes) ---
#    (المودلات من backend\src\market\models\quotes_models.py)
# ==========================================================
class QuoteBase(BaseModel):
    """النموذج الأساسي لعرض السعر: يصف الخصائص الرئيسية لعرض سعر مقدم استجابة لـ RFQ."""
    rfq_id: int = Field(..., description="معرف طلب عرض الأسعار (RFQ) الذي تم تقديم هذا العرض استجابة له.")
    seller_user_id: UUID = Field(..., description="معرف البائع الذي يقدم عرض السعر.")
    submission_timestamp: datetime = Field(None, description="تاريخ ووقت تقديم عرض السعر.") # سيتم تعيينه تلقائياً في المودل
    total_quote_amount: float = Field(..., gt=0, description="المبلغ الإجمالي لعرض السعر.")
    payment_terms_key: Optional[str] = Field(None, max_length=255, description="مفتاح لشروط الدفع المعروضة.")
    delivery_terms_key: Optional[str] = Field(None, max_length=255, description="مفتاح لشروط التسليم المعروضة.")
    validity_period_days: Optional[int] = Field(None, gt=0, description="عدد أيام صلاحية العرض.")
    expiry_timestamp: Optional[datetime] = Field(None, description="تاريخ ووقت انتهاء صلاحية العرض (يُحسب أو يُدخل).")
    quote_status_id: Optional[int] = Field(None, description="حالة عرض السعر (مثلاً: 'مقدم', 'مقبول').")
    seller_notes: Optional[str] = Field(None, description="ملاحظات إضافية من البائع على العرض.")

class QuoteCreate(QuoteBase):
    """نموذج لإنشاء عرض سعر جديد. يتطلب قائمة ببنود العرض."""
    items: List[QuoteItemCreate] = Field(..., description="قائمة ببنود عرض السعر.")

class QuoteUpdate(BaseModel):
    """نموذج لتحديث عرض سعر موجود (يمكن للبائع/المشتري/المسؤول تحديث حالته أو شروطه)."""
    # لا يمكن تغيير rfq_id أو seller_user_id بعد الإنشاء.
    total_quote_amount: Optional[float] = Field(None, gt=0)
    payment_terms_key: Optional[str] = Field(None, max_length=255)
    delivery_terms_key: Optional[str] = Field(None, max_length=255)
    validity_period_days: Optional[int] = Field(None, gt=0)
    expiry_timestamp: Optional[datetime] = Field(None)
    quote_status_id: Optional[int] = Field(None)
    seller_notes: Optional[str] = Field(None)

class QuoteRead(QuoteBase):
    """نموذج لقراءة وعرض تفاصيل عرض السعر بشكل كامل."""
    quote_id: int
    created_at: datetime
    updated_at: datetime
    
    items: List[QuoteItemRead] = [] # بنود عرض السعر المرتبطة
    
    # الكائنات المرتبطة بشكل متداخل (Nested Relationships)
    # TODO: يمكن تضمين معلومات طلب RFQ (RfqRead) والبائع (UserRead) وحالة العرض (QuoteStatusRead) بشكل متداخل.
    seller_user: UserRead
    # rfq: "RfqRead" # تبقى كسلسلة نصية (Forward Reference)
    quote_status: QuoteStatusRead

    model_config = ConfigDict(from_attributes=True)

# إضافة استدعاء update_forward_refs() في نهاية الملف
# from src.market.schemas.rfq_schemas import RfqRead
# QuoteRead.update_forward_refs() # <-- أضف هذا السطر في نهاية الملف بعد تعريف جميع الكلاسات

