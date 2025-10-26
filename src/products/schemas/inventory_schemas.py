# backend\src\products\schemas\inventory_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

# Schema لطلب تعديل المخزون (صحيح كما هو) - يُستخدم لعمليات الإضافة/الخصم
class StockAdjustmentCreate(BaseModel):
    product_packaging_option_id: int
    change_in_quantity: float = Field(..., description="Positive for add, negative for subtract")
    reason_notes: Optional[str] = None

# ==========================================================
# --- Schemas لعناصر المخزون (InventoryItem) ---
# ==========================================================

# Schema لعرض حالة المخزون (لتكون جزءًا من InventoryItemRead)
class InventoryItemStatusNestedRead(BaseModel):
    status_name_key: str
    model_config = ConfigDict(from_attributes=True)

# Schema لعرض سجل حركة مخزون واحدة
class InventoryTransactionRead(BaseModel):
    transaction_id: int
    inventory_item_id: int
    transaction_type_id: int # يمكن هنا تضمين كائن TransactionTypeRead لاحقًا
    quantity_changed: float
    balance_after_transaction: float
    transaction_timestamp: datetime
    reason_notes: Optional[str] = None
    created_by_user_id: Optional[UUID] = None
    model_config = ConfigDict(from_attributes=True)

# Schema لعرض بيانات بند المخزون الأساسية
class InventoryItemRead(BaseModel):
    inventory_item_id: int
    product_packaging_option_id: int
    seller_user_id: UUID
    on_hand_quantity: float
    reserved_quantity: float
    available_quantity: float
    inventory_item_status_id: int # يمكن هنا تضمين كائن InventoryItemStatusNestedRead
    status: InventoryItemStatusNestedRead # لعرض الحالة المتداخلة
    last_restock_date: Optional[datetime] = None
    location_identifier: Optional[str] = Field(None, max_length=100)
    created_at: datetime
    updated_at: datetime
    transactions: List[InventoryTransactionRead] = [] # لعرض الحركات المرتبطة
    model_config = ConfigDict(from_attributes=True)

# Schema لتحديث InventoryItem مباشرة (خاصة للمسؤولين أو في عمليات داخلية معقدة)
class InventoryItemUpdate(BaseModel):
    available_quantity: Optional[float] = Field(None, ge=0)
    reserved_quantity: Optional[float] = Field(None, ge=0)
    on_hand_quantity: Optional[float] = Field(None, ge=0)
    inventory_item_status_id: Optional[int] = None
    last_restock_date: Optional[datetime] = None
    location_identifier: Optional[str] = Field(None, max_length=100)

# ==========================================================
# --- Schemas لحالات عناصر المخزون (InventoryItemStatus) ---
# ==========================================================

class InventoryItemStatusBase(BaseModel):
    status_name_key: str = Field(..., max_length=50)

class InventoryItemStatusCreate(InventoryItemStatusBase):
    translations: Optional[List["InventoryItemStatusTranslationCreate"]] = []

class InventoryItemStatusUpdate(InventoryItemStatusBase):
    pass # لا تزال فارغة لأن Base تحتوي على الحقل الوحيد القابل للتحديث

class InventoryItemStatusRead(InventoryItemStatusBase):
    inventory_item_status_id: int
    translations: List["InventoryItemStatusTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لترجمات حالات عناصر المخزون (InventoryItemStatusTranslation) ---
# ==========================================================

class InventoryItemStatusTranslationBase(BaseModel):
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)
    translated_status_description: Optional[str] = Field(None)

class InventoryItemStatusTranslationCreate(InventoryItemStatusTranslationBase):
    pass

class InventoryItemStatusTranslationUpdate(BaseModel):
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_status_description: Optional[str] = Field(None)

class InventoryItemStatusTranslationRead(InventoryItemStatusTranslationBase):
    inventory_item_status_id: int
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لأنواع حركات المخزون (InventoryTransactionType) ---
# ==========================================================

class InventoryTransactionTypeBase(BaseModel):
    transaction_type_name_key: str = Field(..., max_length=50)

class InventoryTransactionTypeCreate(InventoryTransactionTypeBase):
    translations: Optional[List["InventoryTransactionTypeTranslationCreate"]] = []

class InventoryTransactionTypeUpdate(InventoryTransactionTypeBase):
    pass # لا تزال فارغة لأن Base تحتوي على الحقل الوحيد القابل للتحديث

class InventoryTransactionTypeRead(InventoryTransactionTypeBase):
    transaction_type_id: int
    translations: List["InventoryTransactionTypeTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لترجمات أنواع حركات المخزون (InventoryTransactionTypeTranslation) ---
# ==========================================================

class InventoryTransactionTypeTranslationBase(BaseModel):
    language_code: str = Field(..., max_length=10)
    translated_transaction_type_name: str = Field(..., max_length=100)
    translated_transaction_description: Optional[str] = Field(None)

class InventoryTransactionTypeTranslationCreate(InventoryTransactionTypeTranslationBase):
    pass

class InventoryTransactionTypeTranslationUpdate(BaseModel):
    translated_transaction_type_name: Optional[str] = Field(None, max_length=100)
    translated_transaction_description: Optional[str] = Field(None)

class InventoryTransactionTypeTranslationRead(InventoryTransactionTypeTranslationBase):
    transaction_type_id: int
    model_config = ConfigDict(from_attributes=True)