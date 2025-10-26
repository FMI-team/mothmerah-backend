# backend/src/products/schemas/variety_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID

# ==========================================================
# --- Schemas for ProductVariety Translations ---
# ==========================================================
class ProductVarietyTranslationBase(BaseModel):
    language_code: str = Field(..., max_length=10)
    translated_variety_name: str = Field(..., max_length=150)
    translated_variety_description: Optional[str] = None

class ProductVarietyTranslationCreate(ProductVarietyTranslationBase):
    pass

class ProductVarietyTranslationUpdate(BaseModel):
    translated_variety_name: Optional[str] = Field(None, max_length=150)
    translated_variety_description: Optional[str] = None

class ProductVarietyTranslationRead(ProductVarietyTranslationBase):
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas for ProductVariety Management ---
# ==========================================================
class ProductVarietyBase(BaseModel):
    variety_name_key: str = Field(..., max_length=100)
    sku_variant: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class ProductVarietyCreate(ProductVarietyBase):
    product_id: UUID
    translations: Optional[List[ProductVarietyTranslationCreate]] = []

class ProductVarietyUpdate(BaseModel):
    variety_name_key: Optional[str] = Field(None, max_length=100)
    sku_variant: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class ProductVarietyRead(ProductVarietyBase):
    variety_id: int
    product_id: UUID
    translations: List[ProductVarietyTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)