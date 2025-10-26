# backend/src/products/schemas/packaging_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Schema لعرض بيانات وحدة القياس بشكل متداخل
class UnitOfMeasureNestedRead(BaseModel):
    unit_id: int # أضف ID ليكون مرجعًا
    unit_name_key: str
    unit_abbreviation_key: str
    is_active: bool # لتعكس حالة الوحدة (نشطة/غير نشطة)
    
    model_config = ConfigDict(from_attributes=True) 

# Schema لعرض ترجمة خيار التغليف
class PackagingOptionTranslationRead(BaseModel):
    language_code: str
    translated_packaging_option_name: str
    translated_custom_description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# Schema أساسي يحتوي على الحقول المشتركة التي يرسلها المستخدم
class PackagingOptionBase(BaseModel):
    packaging_option_name_key: Optional[str] = None
    custom_packaging_description: Optional[str] = None
    quantity_in_packaging: float = Field(..., gt=0)
    unit_of_measure_id_for_quantity: int
    base_price: float = Field(..., gt=0)
    sku: Optional[str] = None
    barcode: Optional[str] = None
    is_default_option: bool = False
    is_active: bool = True
    sort_order: Optional[int] = 0

# Schema لإنشاء خيار تعبئة جديد
class PackagingOptionCreate(PackagingOptionBase):
    pass

# Schema لتحديث خيار تعبئة موجود (كل الحقول اختيارية)
class PackagingOptionUpdate(BaseModel):
    packaging_option_name_key: Optional[str] = None
    custom_packaging_description: Optional[str] = None
    quantity_in_packaging: Optional[float] = Field(None, gt=0)
    unit_of_measure_id_for_quantity: Optional[int] = None
    base_price: Optional[float] = Field(None, gt=0)
    sku: Optional[str] = None
    barcode: Optional[str] = None
    is_default_option: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

# Schema لعرض خيار التغليف مع كل تفاصيله المترابطة
class PackagingOptionRead(PackagingOptionBase):
    packaging_option_id: int
    product_id: UUID
    unit_of_measure: UnitOfMeasureNestedRead # <-- عرض كائن وحدة القياس
    translations: List[PackagingOptionTranslationRead] = [] # <-- عرض قائمة الترجمات

    model_config = ConfigDict(from_attributes=True)

# ... (المحتوى الحالي لـ packaging_schemas.py) ...

# ==========================================================
# --- Schemas لترجمات خيارات التعبئة والبيع (Product Packaging Option Translations) ---
# ==========================================================
class ProductPackagingOptionTranslationBase(BaseModel):
    language_code: str = Field(..., max_length=10)
    translated_packaging_option_name: str = Field(..., max_length=150)
    translated_custom_description: Optional[str] = Field(None)

class ProductPackagingOptionTranslationCreate(ProductPackagingOptionTranslationBase):
    pass

class ProductPackagingOptionTranslationUpdate(BaseModel):
    translated_packaging_option_name: Optional[str] = Field(None, max_length=150)
    translated_custom_description: Optional[str] = Field(None)

class ProductPackagingOptionTranslationRead(ProductPackagingOptionTranslationBase):
    packaging_option_id: int
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- تحديث Schemas لخيارات التعبئة والبيع (Product Packaging Options) ---
# ==========================================================
# قم بتعديل ProductPackagingOptionCreate و ProductPackagingOptionRead
# لكي تتضمن حقول الترجمات، وحقل unit_of_measure كاملاً في Read

# Schema أساسي يحتوي على الحقول المشتركة التي يرسلها المستخدم
class PackagingOptionBase(BaseModel):
    packaging_option_name_key: Optional[str] = Field(None, max_length=100)
    custom_packaging_description: Optional[str] = Field(None)
    quantity_in_packaging: float = Field(..., gt=0)
    unit_of_measure_id_for_quantity: int
    base_price: float = Field(..., gt=0)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    is_default_option: bool = False
    is_active: bool = True
    sort_order: Optional[int] = 0

# Schema لإنشاء خيار تعبئة جديد
class PackagingOptionCreate(PackagingOptionBase):
    translations: Optional[List[ProductPackagingOptionTranslationCreate]] = [] # أضف هذا

# Schema لتحديث خيار تعبئة موجود (كل الحقول اختيارية)
class PackagingOptionUpdate(BaseModel): # حافظ على هذا كما هو
    packaging_option_name_key: Optional[str] = Field(None, max_length=100)
    custom_packaging_description: Optional[str] = Field(None)
    quantity_in_packaging: Optional[float] = Field(None, gt=0)
    unit_of_measure_id_for_quantity: Optional[int] = None
    base_price: Optional[float] = Field(None, gt=0)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    is_default_option: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

# Schema لعرض خيار التغليف مع كل تفاصيله المترابطة
class PackagingOptionRead(PackagingOptionBase):
    packaging_option_id: int
    product_id: UUID
    unit_of_measure: UnitOfMeasureNestedRead # <-- عرض كائن وحدة القياس
    translations: List[ProductPackagingOptionTranslationRead] = [] # <-- عرض قائمة الترجمات
    model_config = ConfigDict(from_attributes=True) # تأكد من وجود هذا