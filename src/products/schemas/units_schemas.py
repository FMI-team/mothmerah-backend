# backend\src\products\schemas\units_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# ==========================================================
# --- Schemas لوحدات القياس (Units of Measure) ---
# ==========================================================
class UnitOfMeasureBase(BaseModel):
    unit_name_key: str = Field(..., max_length=50)
    unit_abbreviation_key: str = Field(..., max_length=10)
    is_base_unit_for_type: Optional[bool] = None
    conversion_factor_to_base: Optional[float] = None
    is_active: bool = True # للحذف الناعم

class UnitOfMeasureCreate(UnitOfMeasureBase):
    translations: Optional[List["UnitOfMeasureTranslationCreate"]] = []

class UnitOfMeasureUpdate(BaseModel):
    unit_name_key: Optional[str] = Field(None, max_length=50)
    unit_abbreviation_key: Optional[str] = Field(None, max_length=10)
    is_base_unit_for_type: Optional[bool] = None
    conversion_factor_to_base: Optional[float] = None
    is_active: Optional[bool] = None

class UnitOfMeasureRead(UnitOfMeasureBase):
    unit_id: int
    translations: List["UnitOfMeasureTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لترجمات وحدات القياس (Unit of Measure Translations) ---
# ==========================================================
class UnitOfMeasureTranslationBase(BaseModel):
    language_code: str = Field(..., max_length=10)
    translated_unit_name: str = Field(..., max_length=50)
    translated_unit_abbreviation: str = Field(..., max_length=20)

class UnitOfMeasureTranslationCreate(UnitOfMeasureTranslationBase):
    pass

class UnitOfMeasureTranslationUpdate(BaseModel):
    translated_unit_name: Optional[str] = Field(None, max_length=50)
    translated_unit_abbreviation: Optional[str] = Field(None, max_length=20)

class UnitOfMeasureTranslationRead(UnitOfMeasureTranslationBase):
    unit_id: int
    model_config = ConfigDict(from_attributes=True)