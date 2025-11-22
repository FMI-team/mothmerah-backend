# backend/src/products/schemas/product_schemas.py


# استيراد الـ Schemas التي سنحتاجها من الحزمة الرئيسية
# هذا يتطلب أن يكون ملف __init__.py في نفس المجلد يقوم باستيرادها
# from src.products import schemas

# from src.products.schemas.category_schemas import ProductCategoryRead
# from src.products.schemas.packaging_schemas import PackagingOptionRead, PackagingOptionCreate
# from src.products.schemas.product_lookups_schemas import  ProductStatusRead

# backend/src/products/schemas/product_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# from src.products.schemas import ProductCategoryRead,PackagingOptionRead, PackagingOptionCreate,ProductStatusRead
from src.products.schemas.category_schemas import ProductCategoryRead
from src.products.schemas.packaging_schemas import PackagingOptionRead, PackagingOptionCreate,UnitOfMeasureNestedRead
from src.products.schemas.product_lookups_schemas import ProductStatusRead
# from src.products.schemas.units_schemas import UnitOfMeasureRead

# ==========================================================
# --- Schemas for Product Translations ---
# ==========================================================
class ProductTranslationBase(BaseModel):
    language_code: str = Field(..., max_length=10)
    translated_product_name: str = Field(..., max_length=255)
    translated_description: Optional[str] = None
    translated_short_description: Optional[str] = Field(None, max_length=500)

class ProductTranslationCreate(ProductTranslationBase):
    pass

class ProductTranslationUpdate(BaseModel):
    # عند التحديث، يمكن تغيير الاسم أو الوصف أو كلاهما
    translated_product_name: Optional[str] = Field(None, max_length=255)
    translated_description: Optional[str] = None
    translated_short_description: Optional[str] = Field(None, max_length=500)

class ProductTranslationRead(ProductTranslationBase):
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas for Product Management ---
# ==========================================================
class ProductBase(BaseModel):
    category_id: int
    base_price_per_unit: float = Field(..., gt=0, description="السعر الأساسي لكل وحدة قبل أي تسعير ديناميكي")
    unit_of_measure_id: int = Field(..., description="معرف وحدة القياس")
    country_of_origin_code: Optional[str] = Field(None, max_length=2)
    is_organic: bool = False
    is_local_saudi_product: bool = False
    main_image_url: Optional[str] = Field(None, max_length=512)
    sku: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = []

class ProductCreate(ProductBase):
    # عند إنشاء منتج، نرسل الترجمات وخيارات التعبئة مباشرةً
    translations: List[ProductTranslationCreate]
    packaging_options: List[PackagingOptionCreate] 

class ProductUpdate(BaseModel):
    # كل الحقول اختيارية في عملية التحديث
    category_id: Optional[int] = None
    country_of_origin_code: Optional[str] = Field(None, max_length=2)
    is_organic: Optional[bool] = None
    is_local_saudi_product: Optional[bool] = None
    main_image_url: Optional[str] = Field(None, max_length=512)
    sku: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    product_status_id: Optional[int] = None

class ProductRead(ProductBase):
    """
    الـ Schema الكاملة لعرض بيانات المنتج عند قراءته.
    """
    product_id: UUID
    seller_user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # عرض الكائنات المرتبطة بشكل كامل
    category: ProductCategoryRead
    status: ProductStatusRead 
    unit_of_measure: UnitOfMeasureNestedRead 
    translations: List[ProductTranslationRead] = []
    packaging_options: List[PackagingOptionRead] = []

    model_config = ConfigDict(from_attributes=True)