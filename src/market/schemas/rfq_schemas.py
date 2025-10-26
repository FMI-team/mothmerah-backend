from sqlalchemy import JSON
# backend\src\market\schemas\rfq_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List,TYPE_CHECKING
from datetime import datetime, date
from uuid import UUID # لمعرفات المستخدمين والمنتجات

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas الأخرى
# RfqStatusRead تستورد الآن من src.lookups.schemas
from src.lookups.schemas import RfqStatusRead # <-- تم التعديل هنا

# TODO: تأكد من أن UserRead, ProductRead, UnitOfMeasureRead, AddressRead, QuoteRead موجودة ومستوردة
from src.users.schemas.core_schemas import UserRead # UserRead
from src.products.schemas.product_schemas import ProductRead # ProductRead
from src.products.schemas.units_schemas import UnitOfMeasureRead # UnitOfMeasureRead
from src.users.schemas.address_schemas import AddressRead # AddressRead

# TODO: تأكد من أن QuoteRead موجودة ومستوردة
# from src.market.schemas.quote_schemas import QuoteRead # لإظهار عروض الأسعار المرتبطة

# استيراد QuoteRead فقط لأغراض فحص الأنواع (TYPE_CHECKING)
if TYPE_CHECKING: # <-- هذا الاستيراد يتم فقط لفحص الأنواع، لا يتم تنفيذه في وقت التشغيل
    from src.market.schemas.quote_schemas import QuoteRead # <-- استيراد QuoteRead هنا



# ==========================================================
# --- Schemas لحالات طلب عرض السعر (Rfq Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)
# ... (تم إزالة الأقسام الكاملة لـ RfqStatus و RfqStatusTranslation) ...

# ==========================================================
# --- Schemas لبنود طلب عرض السعر (Rfq Items) ---
#    (المودلات من backend\src\market\models\rfqs_models.py)
# ==========================================================
class RfqItemBase(BaseModel):
    """النموذج الأساسي لبند طلب عرض السعر: يصف المنتج المطلوب وكميته ومواصفاته."""
    product_id: Optional[UUID] = Field(None, description="معرف المنتج الموجود في الكتالوج إذا كان الطلب لمنتج محدد.")
    custom_product_description: Optional[str] = Field(None, description="وصف مخصص للمنتج إذا كان غير موجود في الكتالوج أو بمواصفات خاصة.")
    quantity_requested: float = Field(..., gt=0, description="الكمية المطلوبة من هذا البند.")
    unit_of_measure_id: int = Field(..., description="معرف وحدة القياس للكمية المطلوبة.")
    required_specifications: Optional[dict] = Field(None, description="مواصفات فنية أو جودة مفصلة بصيغة JSON.")
    target_price_per_unit: Optional[float] = Field(None, gt=0, description="السعر المستهدف للوحدة من قبل المشتري، إن وجد.")
    notes: Optional[str] = Field(None, description="ملاحظات إضافية من المشتري حول هذا البند.")

class RfqItemCreate(RfqItemBase):
    """نموذج لإنشاء بند طلب عرض سعر جديد. يُستخدم كجزء من RfqCreate."""
    # rfq_id سيتم تعيينه في طبقة الخدمة/الـ CRUD.
    pass

class RfqItemUpdate(BaseModel):
    """نموذج لتحديث بند طلب عرض سعر موجود."""
    # لا يمكن تغيير rfq_id أو product_id أو الكميات بعد الإنشاء عادةً.
    custom_product_description: Optional[str] = Field(None)
    quantity_requested: Optional[float] = Field(None, gt=0)
    unit_of_measure_id: Optional[int] = Field(None)
    required_specifications: Optional[dict] = Field(None)
    target_price_per_unit: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = Field(None)

class RfqItemRead(RfqItemBase):
    """نموذج لقراءة وعرض تفاصيل بند طلب عرض السعر."""
    rfq_item_id: int
    rfq_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات المنتج (ProductRead) ووحدة القياس (UnitOfMeasureRead) بشكل متداخل.
    product: ProductRead
    unit_of_measure: UnitOfMeasureRead


# ==========================================================
# --- Schemas لطلبات عروض الأسعار (RFQs) ---
#    (المودلات من backend\src\market\models\rfqs_models.py)
# ==========================================================
class RfqBase(BaseModel):
    """النموذج الأساسي لطلب عرض الأسعار: يصف الخصائص الرئيسية للطلب."""
    # buyer_user_id يُحدد من المستخدم الحالي في طبقة الخدمة.
    rfq_reference_number: Optional[str] = Field(None, max_length=50, description="رقم مرجعي فريد لطلب عرض الأسعار، يُنشأ بواسطة النظام.")
    title: str = Field(..., max_length=255, description="عنوان موجز لطلب عرض الأسعار (مثلاً: 'خضروات متنوعة للفنادق').")
    description: Optional[str] = Field(None, description="وصف تفصيلي للمتطلبات العامة للـ RFQ.")
    submission_deadline: datetime = Field(..., description="الموعد النهائي لتقديم عروض الأسعار من الموردين.")
    delivery_deadline: Optional[date] = Field(None, description="الموعد النهائي المطلوب للتسليم (تاريخ فقط).")
    delivery_address_id: Optional[int] = Field(None, description="معرف عنوان التسليم المفضل للمشتري.")
    payment_terms_preference: Optional[str] = Field(None, description="شروط الدفع المفضلة للمشتري.")
    rfq_status_id: Optional[int] = Field(None, description="حالة طلب عرض الأسعار (يُعين عادة تلقائيًا عند الإنشاء).")

class RfqCreate(RfqBase):
    """نموذج لإنشاء طلب عرض أسعار جديد. يتطلب قائمة ببنوده."""
    items: List[RfqItemCreate] = Field(..., description="قائمة ببنود طلب عرض الأسعار المطلوبة.")

class RfqUpdate(BaseModel):
    """نموذج لتحديث طلب عرض أسعار موجود (يمكن للمشتري/المسؤول تحديث بعض الحقول)."""
    # لا يمكن تغيير rfq_id أو buyer_user_id أو rfq_reference_number بعد الإنشاء.
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None)
    submission_deadline: Optional[datetime] = Field(None)
    delivery_deadline: Optional[date] = Field(None)
    delivery_address_id: Optional[int] = Field(None)
    payment_terms_preference: Optional[str] = Field(None)
    rfq_status_id: Optional[int] = Field(None, description="تحديث حالة طلب عرض الأسعار.")

class RfqRead(RfqBase):
    """نموذج لقراءة وعرض تفاصيل طلب عرض الأسعار بشكل كامل."""
    rfq_id: int
    buyer_user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    items: List[RfqItemRead] = [] # بنود طلب عرض الأسعار المرتبطة
    # TODO: يمكن تضمين معلومات المشتري (UserRead) وعنوان التسليم (AddressRead) وحالة الـ RFQ (RfqStatusRead) بشكل متداخل.
    buyer: UserRead
    delivery_address: AddressRead
    rfq_status: RfqStatusRead # حالة الـ RFQ

    # TODO: يمكن تضمين قائمة بعروض الأسعار المرتبطة (QuotesRead)
    # يمكن تضمين قائمة بعروض الأسعار المرتبطة (QuotesRead)
    quotes_ids: List[int] = Field([], description="قائمة بمعرفات عروض الأسعار المرتبطة بهذا الـ RFQ.") # <-- تم التعديل هنا: وضع اسم الـ Schema كسلسلة نصية
    # quotes: List["QuoteRead"] = Field([], description="قائمة بعروض الأسعار المرتبطة.") # تبقى كسلسلة نصية (Forward Reference)
    
    model_config = ConfigDict(from_attributes=True)

# إضافة استدعاء update_forward_refs() في نهاية الملف
# from src.market.schemas.quote_schemas import QuoteRead
# RfqRead.update_forward_refs() # <-- أضف هذا السطر في نهاية الملف بعد تعريف جميع الكلاسات
