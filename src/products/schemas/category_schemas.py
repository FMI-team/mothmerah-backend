# backend/src/products/schemas/category_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# ==========================================================
# --- Schemas for ProductCategory Translations ---
# ==========================================================
class ProductCategoryTranslationBase(BaseModel):
    language_code: str = Field(..., max_length=10)
    translated_category_name: str = Field(..., max_length=150)
    translated_category_description: Optional[str] = None

class ProductCategoryTranslationCreate(ProductCategoryTranslationBase):
    pass

class ProductCategoryTranslationUpdate(BaseModel):
    translated_category_name: Optional[str] = Field(None, max_length=150)
    translated_category_description: Optional[str] = None

class ProductCategoryTranslationRead(ProductCategoryTranslationBase):
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas for ProductCategory Management ---
# ==========================================================
class ProductCategoryBase(BaseModel):
    category_name_key: str = Field(..., max_length=100)
    parent_category_id: Optional[int] = None
    category_image_url: Optional[str] = Field(None, max_length=512)
    sort_order: Optional[int] = 0
    is_active: bool = True

class ProductCategoryCreate(ProductCategoryBase):
    translations: Optional[List[ProductCategoryTranslationCreate]] = []

class ProductCategoryUpdate(BaseModel):
    category_name_key: Optional[str] = Field(None, max_length=100)
    parent_category_id: Optional[int] = None
    category_image_url: Optional[str] = Field(None, max_length=512)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class ProductCategoryRead(ProductCategoryBase):
    category_id: int
    translations: List[ProductCategoryTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)