# backend\src\products\schemas\image_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# ==========================================================
# --- Schemas للصور (Images) ---
# ==========================================================
class ImageBase(BaseModel):
    entity_id: str = Field(..., description="ID of the entity this image belongs to (e.g., product_id, packaging_option_id)")
    entity_type: str = Field(..., max_length=50, description="Type of the entity (e.g., 'PRODUCT', 'PACKAGING_OPTION')")
    image_url: str = Field(..., max_length=512)
    alt_text_key: Optional[str] = Field(None, max_length=255, description="Key for alt text for localization/accessibility")
    is_primary_image: bool = False
    sort_order: int = 0

class ImageCreate(ImageBase):
    # عند الإنشاء، قد لا يكون entity_id معروفًا بعد، ولكن هنا نفترضه معروفًا.
    # يمكن تعديل هذا ليكون ImageUpload(BaseModel) إذا كان يتم تحميل الصورة أولًا ثم ربطها.
    # ولكن بناءً على الجدول، entity_id و entity_type ضروريان عند الإنشاء.
    pass

class ImageUpdate(BaseModel):
    # عند التحديث، كل الحقول اختيارية
    image_url: Optional[str] = Field(None, max_length=512)
    alt_text_key: Optional[str] = Field(None, max_length=255)
    is_primary_image: Optional[bool] = None
    sort_order: Optional[int] = None

class ImageRead(ImageBase):
    image_id: int
    uploaded_by_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)