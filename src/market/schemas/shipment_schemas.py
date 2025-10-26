# backend\src\market\schemas\shipment_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID # لمعرفات المستخدمين والطلبات

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas الأخرى
# ShipmentStatusRead تستورد الآن من src.lookups.schemas
from src.lookups.schemas import ShipmentStatusRead 
from src.lookups.schemas import CurrencyRead # لاستخدامها في ShipmentBase

# TODO: تأكد من أن OrderRead, UserRead, AddressRead موجودة ومستوردة
from src.market.schemas.order_schemas import OrderRead, OrderItemRead
from src.users.schemas.core_schemas import UserRead
from src.users.schemas.address_schemas import AddressRead

# ==========================================================
# --- Schemas لحالات الشحن (Shipment Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)

# ==========================================================
# --- Schemas لبنود الشحنة (Shipment Items) ---
#    (المودلات من backend\src\market\models\shipments_models.py)
# ==========================================================
class ShipmentItemBase(BaseModel):
    """النموذج الأساسي لبند الشحنة: يصف جزءًا من بند طلب يتم شحنه."""
    order_item_id: int = Field(..., description="معرف بند الطلب (Order Item) الذي يرتبط به هذا البند في الشحنة.")
    shipped_quantity: float = Field(..., gt=0, description="الكمية المشحونة من هذا البند.")
    item_notes: Optional[str] = Field(None, description="ملاحظات خاصة بهذا البند في الشحنة.")

class ShipmentItemCreate(ShipmentItemBase):
    """نموذج لإنشاء بند شحنة جديد. يُستخدم كجزء من ShipmentCreate."""
    # shipment_id سيتم تعيينه في طبقة الخدمة/الـ CRUD.
    pass

class ShipmentItemUpdate(BaseModel):
    """نموذج لتحديث بند شحنة موجود. لا يمكن تغيير المعرفات أو الكميات بعد الإنشاء عادةً."""
    shipped_quantity: Optional[float] = Field(None, gt=0)
    item_notes: Optional[str] = Field(None)

class ShipmentItemRead(ShipmentItemBase):
    """نموذج لقراءة وعرض تفاصيل بند الشحنة."""
    shipment_item_id: int
    shipment_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات بند الطلب المرتبط (OrderItemRead) بشكل متداخل.
    order_item: OrderItemRead # تتطلب استيراد من schemas/order_schemas.py


# ==========================================================
# --- Schemas للشحنات (Shipments) ---
#    (المودلات من backend\src\market\models\shipments_models.py)
# ==========================================================
class ShipmentBase(BaseModel):
    """النموذج الأساسي للشحنة: يصف تفاصيل عملية شحن واحدة."""
    order_id: UUID = Field(..., description="معرف الطلب (Order) الذي تنتمي إليه هذه الشحنة.")
    shipment_reference_number: Optional[str] = Field(None, max_length=50, description="رقم مرجعي فريد للشحنة، يُنشأ بواسطة النظام.")
    shipping_date: Optional[date] = Field(None, description="تاريخ الشحن الفعلي.")
    estimated_delivery_date: Optional[date] = Field(None, description="تاريخ التسليم المقدر.")
    actual_delivery_date: Optional[date] = Field(None, description="تاريخ التسليم الفعلي.")
    shipment_status_id: Optional[int] = Field(None, description="حالة الشحنة (مثلاً: 'قيد التجهيز', 'تم التسليم').")
    shipping_carrier: Optional[str] = Field(None, max_length=100, description="اسم شركة الشحن.")
    tracking_number: Optional[str] = Field(None, max_length=100, description="رقم تتبع الشحنة.")
    shipping_cost: Optional[float] = Field(None, ge=0, description="تكلفة الشحن.")
    currency_code: str = Field(..., max_length=3, description="رمز العملة لتكلفة الشحن (مثلاً 'SAR').")
    shipping_address_id: Optional[int] = Field(None, description="معرف عنوان الشحن الفعلي لهذه الشحنة.")
    shipped_by_user_id: Optional[UUID] = Field(None, description="معرف المستخدم الذي قام بإنشاء/تأكيد الشحن.")
    notes: Optional[str] = Field(None, description="ملاحظات إضافية حول الشحنة.")

class ShipmentCreate(ShipmentBase):
    """نموذج لإنشاء شحنة جديدة. يتطلب قائمة ببنود الشحنة."""
    items: List[ShipmentItemCreate] = Field(..., description="قائمة ببنود الشحنة.")

class ShipmentUpdate(BaseModel):
    """نموذج لتحديث شحنة موجودة (يمكن للبائع/المسؤول تحديث حالتها أو تفاصيلها)."""
    shipping_date: Optional[date] = Field(None)
    estimated_delivery_date: Optional[date] = Field(None)
    actual_delivery_date: Optional[date] = Field(None)
    shipment_status_id: Optional[int] = Field(None)
    shipping_carrier: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    shipping_cost: Optional[float] = Field(None, ge=0)
    currency_code: Optional[str] = Field(None, max_length=3)
    shipping_address_id: Optional[int] = Field(None)
    shipped_by_user_id: Optional[UUID] = Field(None)
    notes: Optional[str] = Field(None)

class ShipmentRead(ShipmentBase):
    """نموذج لقراءة وعرض تفاصيل الشحنة بشكل كامل."""
    shipment_id: int
    created_at: datetime
    updated_at: datetime
    
    items: List[ShipmentItemRead] = [] # بنود الشحنة المرتبطة
    # TODO: يمكن تضمين معلومات الطلب (OrderRead) وحالة الشحنة (ShipmentStatusRead) وعنوان الشحن (AddressRead) والمستخدم (UserRead) بشكل متداخل.
    order: OrderRead # تتطلب استيراد من schemas/order_schemas.py
    shipment_status: ShipmentStatusRead # حالة الشحنة
    shipping_address: AddressRead
    shipped_by_user: UserRead
    currency: CurrencyRead # العملة

    model_config = ConfigDict(from_attributes=True)
    