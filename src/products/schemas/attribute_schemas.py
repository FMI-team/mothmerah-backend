# backend\src\products\schemas\attribute_schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

# ==========================================================
# --- Schemas للسمات العامة (Attributes) ---
# ==========================================================
class AttributeBase(BaseModel):
    attribute_name_key: str = Field(..., max_length=50)
    attribute_description_key: Optional[str] = Field(None, max_length=255)
    is_filterable: bool = False
    is_variant_defining: bool = False

class AttributeCreate(AttributeBase):
    translations: Optional[List["AttributeTranslationCreate"]] = [] # لإضافة ترجمات عند الإنشاء

class AttributeUpdate(BaseModel):
    # جميع الحقول اختيارية للتحديث
    attribute_name_key: Optional[str] = Field(None, max_length=50)
    attribute_description_key: Optional[str] = Field(None, max_length=255)
    is_filterable: Optional[bool] = None
    is_variant_defining: Optional[bool] = None
    is_active: Optional[bool] = None # لإدارة الحذف الناعم/التفعيل

class AttributeRead(AttributeBase):
    attribute_id: int
    translations: List["AttributeTranslationRead"] = [] # لإظهار الترجمات عند القراءة
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لترجمات السمات العامة (Attribute Translations) ---
# ==========================================================
class AttributeTranslationBase(BaseModel):
    language_code: str = Field(..., max_length=10)
    translated_attribute_name: str = Field(..., max_length=100)
    translated_attribute_description: Optional[str] = Field(None, max_length=150)

class AttributeTranslationCreate(AttributeTranslationBase):
    pass

class AttributeTranslationUpdate(BaseModel):
    translated_attribute_name: Optional[str] = Field(None, max_length=100)
    translated_attribute_description: Optional[str] = Field(None, max_length=150)

class AttributeTranslationRead(AttributeTranslationBase):
    attribute_id: int # مفتاح أجنبي للسمة
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لقيم السمات (Attribute Values) ---
# ==========================================================
class AttributeValueBase(BaseModel):
    attribute_value_key: str = Field(..., max_length=100)
    sort_order: Optional[int] = None

class AttributeValueCreate(AttributeValueBase):
    attribute_id: int # لتحديد السمة الأم
    translations: Optional[List["AttributeValueTranslationCreate"]] = [] # لإضافة ترجمات عند الإنشاء

class AttributeValueUpdate(BaseModel):
    # جميع الحقول اختيارية للتحديث
    attribute_value_key: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = None
    # لا يوجد is_active هنا لأن المودل لا يدعمه

class AttributeValueRead(AttributeValueBase):
    attribute_value_id: int
    attribute_id: int
    translations: List["AttributeValueTranslationRead"] = [] # لإظهار الترجمات عند القراءة
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لترجمات قيم السمات (Attribute Value Translations) ---
# ==========================================================
class AttributeValueTranslationBase(BaseModel):
    language_code: str = Field(..., max_length=10)
    translated_value_name: str = Field(..., max_length=100)
    # ملاحظة: حقل 'translated_variety_description' في المودل قد يكون خطأ إملائي أو مقصود لوصف القيمة
    # سأفترض أنه غير مطلوب هنا في الـ Schema إذا لم يكن في تعريف الجدول الأصلي
    # وإذا كان المقصود هو وصف القيمة، يرجى توضيح ذلك لاحقاً
    translated_value_description: Optional[str] = Field(None, max_length=255) # إضافة حقل وصف للقيمة إذا كان مطلوبًا

class AttributeValueTranslationCreate(AttributeValueTranslationBase):
    pass

class AttributeValueTranslationUpdate(BaseModel):
    translated_value_name: Optional[str] = Field(None, max_length=100)
    translated_value_description: Optional[str] = Field(None, max_length=255)

class AttributeValueTranslationRead(AttributeValueTranslationBase):
    attribute_value_id: int # مفتاح أجنبي لقيمة السمة
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لربط الأصناف بالسمات وقيمها (Product Variety Attributes) ---
# ==========================================================
class ProductVarietyAttributeBase(BaseModel):
    product_variety_id: int
    attribute_id: int
    attribute_value_id: int

class ProductVarietyAttributeCreate(ProductVarietyAttributeBase):
    pass

class ProductVarietyAttributeRead(ProductVarietyAttributeBase):
    product_variety_attribute_id: int
    model_config = ConfigDict(from_attributes=True)

# لتسهيل الحذف لـ ProductVarietyAttribute، لا نحتاج Update Schema لها