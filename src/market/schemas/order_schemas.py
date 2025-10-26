# backend\src\market\schemas\order_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas الأخرى
# CurrencyRead, PaymentStatusRead, OrderItemStatusRead تستورد الآن من src.lookups.schemas
from src.lookups.schemas import ( 
    CurrencyRead,
    PaymentStatusRead,
    OrderItemStatusRead,
    OrderStatusRead # OrderStatusRead أيضاً من lookups
)

# TODO: تأكد من أن UserRead, ProductPackagingOptionRead, AddressRead موجودة ومستوردة
from src.users.schemas.core_schemas import UserRead
from src.products.schemas.packaging_schemas import PackagingOptionRead
from src.users.schemas.address_schemas import AddressRead


# ==========================================================
# --- Schemas لحالة الطلب (Order Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)
# --- Schemas لحالة الدفع (Payment Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)


# ==========================================================
# --- Schemas لبنود الطلب (Order Items) ---
#    (المودلات من backend\src\market\models\orders_models.py)
# ==========================================================
class OrderItemBase(BaseModel):
    """النموذج الأساسي لبند الطلب: يصف المنتج، الكمية، والسعر داخل طلب."""
    product_packaging_option_id: int = Field(..., description="معرف خيار التعبئة والتغليف للمنتج الذي تم طلبه.")
    seller_user_id: UUID = Field(..., description="معرف البائع لهذا البند تحديدًا (مفيد في الطلبات متعددة البائعين).")
    quantity_ordered: float = Field(..., gt=0, description="الكمية المطلوبة من هذا البند.")
    unit_price_at_purchase: float = Field(..., gt=0, description="السعر الفعال للوحدة وقت الشراء بعد تطبيق أي خصومات كمية.")
    total_price_for_item: float = Field(..., gt=0, description="إجمالي السعر لهذا البند (الكمية × سعر الوحدة).")
    item_status_id: Optional[int] = Field(None, description="حالة هذا البند ضمن الطلب (مثلاً: 'قيد التجهيز', 'تم الشحن جزئيًا').")
    notes: Optional[str] = Field(None, description="ملاحظات إضافية على البند.")

class OrderItemCreate(OrderItemBase):
    """نموذج لإنشاء بند طلب جديد. يُستخدم كجزء من OrderCreate."""
    # order_id سيتم تعيينه في طبقة الخدمة/الـ CRUD عندما يتم إنشاء الطلب الأب.
    pass

class OrderItemUpdate(BaseModel):
    """نموذج لتحديث بند طلب موجود (يمكن للبائع تعديل الحالة أو الملاحظات).
    عادة لا يمكن تغيير المنتج أو الكميات بعد إنشاء الطلب.
    """
    item_status_id: Optional[int] = Field(None, description="تحديث حالة البند ضمن الطلب.")
    notes: Optional[str] = Field(None, description="تحديث الملاحظات على البند.")

class OrderItemRead(OrderItemBase):
    """نموذج لقراءة وعرض تفاصيل بند الطلب، يتضمن معرفه ومعلومات أخرى."""
    order_item_id: int
    order_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات المنتج (ProductPackagingOptionRead) والبائع (UserRead) وحالة البند (OrderItemStatusRead) بشكل متداخل.
    packaging_option: PackagingOptionRead
    seller: UserRead
    item_status: OrderItemStatusRead # حالة البند

# ==========================================================
# --- Schemas للطلبات (Orders) ---
#    (المودلات من backend\src\market\models\orders_models.py)
# ==========================================================
class OrderBase(BaseModel):
    """النموذج الأساسي للطلب: يصف الخصائص الرئيسية للطلب."""
    # buyer_user_id يُحدد من المستخدم الحالي في طبقة الخدمة.
    seller_user_id: Optional[UUID] = Field(None, description="معرف البائع إذا كان الطلب موجهًا لبائع واحد فقط.")
    # order_reference_number يُنشأ بواسطة النظام في طبقة الخدمة ليكون فريدًا.
    shipping_address_id: Optional[int] = Field(None, description="معرف عنوان الشحن للطلب.")
    billing_address_id: Optional[int] = Field(None, description="معرف عنوان الفوترة للطلب.")
    # TODO: payment_method_id: يجب أن يشير إلى FK لجدول طرق الدفع (payment_methods) عند إضافتها.
    payment_status_id: Optional[int] = Field(None, description="معرف حالة الدفع للطلب.")
    source_of_order: Optional[str] = Field(None, max_length=50, description="مصدر الطلب (مثلاً: 'شراء مباشر', 'من عرض سعر', 'من مزاد').")
    related_quote_id: Optional[int] = Field(None, description="معرف عرض السعر المرتبط إذا كان الطلب ناتجًا عن قبول عرض سعر.")
    related_auction_settlement_id: Optional[int] = Field(None, description="معرف تسوية المزاد المرتبطة إذا كان الطلب ناتجًا عن مزاد.")
    notes_from_buyer: Optional[str] = Field(None, description="ملاحظات إضافية من المشتري حول الطلب.")
    notes_from_seller: Optional[str] = Field(None, description="ملاحظات إضافية من البائع حول الطلب.")

    # حقول الأسعار يتم حسابها في طبقة الخدمة بناءً على بنود الطلب
    total_amount_before_discount: float = Field(0.0, ge=0, description="إجمالي المبلغ قبل الخصم.")
    discount_amount: float = Field(0.0, ge=0, description="قيمة الخصم المطبق على الطلب الكلي.")
    total_amount_after_discount: float = Field(0.0, ge=0, description="إجمالي المبلغ بعد الخصم (قبل الضريبة).")
    vat_amount: float = Field(0.0, ge=0, description="مبلغ ضريبة القيمة المضافة.")
    final_total_amount: float = Field(0.0, ge=0, description="الإجمالي النهائي للطلب شامل الضريبة بعد الخصم.")
    currency_code: str = Field(..., max_length=3, description="رمز العملة (مثلاً 'SAR').")

class OrderCreate(OrderBase):
    """نموذج لإنشاء طلب جديد. يتطلب قائمة ببنود الطلب."""
    items: List[OrderItemCreate] = Field(..., description="قائمة ببنود الطلب التي يطلبها المشتري.")
    # TODO: يمكن إضافة اختيار طرق الدفع هنا (payment_method_id) إذا كان يتم اختياره في هذه المرحلة من الـ API.

class OrderUpdate(BaseModel):
    """نموذج لتحديث طلب موجود (يمكن للبائع/المسؤول تحديث حالته أو ملاحظاته).
    لا يمكن تغيير بنود الطلب أو المبالغ المالية الرئيسية مباشرة هنا.
    """
    order_status_id: Optional[int] = Field(None, description="تحديث حالة الطلب (مثلاً: 'قيد التجهيز', 'تم الشحن').")
    shipping_address_id: Optional[int] = Field(None, description="تحديث عنوان الشحن للطلب.")
    billing_address_id: Optional[int] = Field(None, description="تحديث عنوان الفوترة للطلب.")
    payment_method_id: Optional[int] = Field(None, description="تحديث طريقة الدفع للطلب.")
    payment_status_id: Optional[int] = Field(None, description="تحديث حالة الدفع للطلب.")
    notes_from_buyer: Optional[str] = Field(None, description="تحديث ملاحظات المشتري.")
    notes_from_seller: Optional[str] = Field(None, description="تحديث ملاحظات البائع.")
    # TODO: قد يُسمح بتحديث بعض حقول الأسعار من قبل المسؤول فقط في حالات استثنائية.


class OrderRead(OrderBase):
    """نموذج لقراءة وعرض تفاصيل الطلب بشكل كامل، بما في ذلك معرفاته والطوابع الزمنية."""
    order_id: UUID
    buyer_user_id: UUID
    seller_user_id: Optional[UUID] = None
    order_reference_number: str
    order_date: datetime
    order_status_id: int # يمكن تضمين كائن OrderStatusRead لاحقاً
    created_at: datetime
    updated_at: datetime
    
    # TODO: يمكن تضمين معلومات الكيانات المرتبطة بشكل متداخل (Nested Relationships) لتحسين العرض.
    buyer: UserRead
    seller: Optional[UserRead] = None # البائع (قد يكون None إذا كان من أكثر من بائع)
    order_status: OrderStatusRead # حالة الطلب
    payment_status: PaymentStatusRead # حالة الدفع
    currency: CurrencyRead # العملة
    shipping_address: Optional[AddressRead] = None # عنوان الشحن
    billing_address: Optional[AddressRead] = None # عنوان الفوترة
    # related_quote: QuoteRead
    # related_auction_settlement: AuctionSettlementRead

    # items: List[OrderItemRead] = [] # قائمة ببنود الطلب المرتبطة
    # TODO: يمكن تضمين سجل تاريخ الحالة لعرض التغييرات التاريخية للطلب.
    ## history: List["OrderStatusHistoryRead"] = [] # تتطلب تعريف OrderStatusHistoryRead هنا
    
    model_config = ConfigDict(from_attributes=True)
class OrderRead(OrderBase):
    """نموذج لقراءة وعرض تفاصيل الطلب بشكل كامل، بما في ذلك معرفاته والطوابع الزمنية."""
    order_id: UUID
    buyer_user_id: UUID
    seller_user_id: Optional[UUID] = None
    order_reference_number: str
    order_date: datetime
    order_status_id: int # يمكن تضمين كائن OrderStatusRead لاحقاً
    created_at: datetime
    updated_at: datetime
    
    items: List[OrderItemRead] = [] # بنود الطلب المرتبطة
    
    # الكائنات المرتبطة بشكل متداخل (Nested Relationships)
    # TODO: يمكن تضمين UserRead, AddressRead, PaymentMethodRead, QuoteRead, AuctionSettlementRead
    buyer: UserRead
    seller: Optional[UserRead] = None # البائع (قد يكون None إذا كان من أكثر من بائع)
    order_status: OrderStatusRead # حالة الطلب
    payment_status: PaymentStatusRead # حالة الدفع
    currency: CurrencyRead # العملة
    shipping_address: Optional[AddressRead] = None # عنوان الشحن
    billing_address: Optional[AddressRead] = None # عنوان الفوترة
    # related_quote: QuoteRead
    # related_auction_settlement: AuctionSettlementRead

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لسجل تغييرات حالة الطلب (Order Status History) ---
#    (المودلات من backend\src\market\models\orders_models.py)
#    هذا الجدول يُنشأ تلقائياً ولا يُعدّل أو يُحذف مباشرةً عبر API.
# ==========================================================
# class OrderStatusHistoryRead(BaseModel):
#     """نموذج لقراءة وعرض تفاصيل سجل تغييرات حالة الطلب.
#     يُستخدم لتتبع مسار التغييرات التي طرأت على حالة الطلب بمرور الوقت.
#     """
#     order_status_history_id: int
#     order_id: UUID
#     old_status_id: Optional[int] = Field(None, description="معرف الحالة القديمة للطلب.")
#     new_status_id: int = Field(..., description="معرف الحالة الجديدة للطلب.")
#     change_timestamp: datetime = Field(..., description="تاريخ ووقت تغيير الحالة.")
#     changed_by_user_id: Optional[UUID] = Field(None, description="معرف المستخدم الذي أجرى التغيير (إذا لم يكن النظام).")
#     notes: Optional[str] = Field(None, description="ملاحظات إضافية حول سبب التغيير.")
#     created_at: datetime # هذا الحقل سيكون مطابقًا لـ change_timestamp في هذا السياق
#     model_config = ConfigDict(from_attributes=True)
#     # TODO: يمكن تضمين OrderStatusRead لـ old_status و new_status
#     # old_status: "OrderStatusRead"
#     # new_status: "OrderStatusRead"
#     # TODO: يمكن تضمين UserRead لـ changed_by_user


class OrderStatusHistoryRead(BaseModel):
    """نموذج لقراءة وعرض تفاصيل سجل تغييرات حالة الطلب.
    يُستخدم لتتبع مسار التغييرات التي طرأت على حالة الطلب بمرور الوقت.
    """
    order_status_history_id: int
    order_id: UUID
    old_status_id: Optional[int] = Field(None, description="معرف الحالة القديمة للطلب.")
    new_status_id: int = Field(..., description="معرف الحالة الجديدة للطلب.")
    change_timestamp: datetime = Field(..., description="تاريخ ووقت تغيير الحالة.")
    changed_by_user_id: Optional[UUID] = Field(None, description="معرف المستخدم الذي أجرى التغيير (إذا لم يكن النظام).")
    notes: Optional[str] = Field(None, description="ملاحظات إضافية حول سبب التغيير.")
    created_at: datetime # هذا الحقل سيكون مطابقًا لـ change_timestamp في هذا السياق
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين OrderStatusRead لـ old_status و new_status
    old_status: OrderStatusRead
    new_status: OrderStatusRead
    # TODO: يمكن تضمين UserRead لـ changed_by_user
    # changed_by_user: UserRead
