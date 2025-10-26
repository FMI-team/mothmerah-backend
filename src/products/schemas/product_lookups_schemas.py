# backend\src\products\schemas\product_lookups_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملف lookups_schemas.py
from src.lookups.schemas import ( # <-- تم التعديل هنا
    ProductStatusRead,
    InventoryItemStatusRead,
    InventoryTransactionTypeRead,
    ExpectedCropStatusRead
)


# ==========================================================
# --- Schemas لحالات المنتج (Product Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)
#    تمت إزالة الأقسام الكاملة لـ ProductStatus و ProductStatusTranslation من هنا.


# ==========================================================
# --- Schemas لحالات عنصر المخزون (Inventory Item Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)
#    تمت إزالة الأقسام الكاملة لـ InventoryItemStatus و InventoryItemStatusTranslation من هنا.


# ==========================================================
# --- Schemas لأنواع حركات المخزون (Inventory Transaction Types) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)
#    تمت إزالة الأقسام الكاملة لـ InventoryTransactionType و InventoryTransactionTypeTranslation من هنا.


# ==========================================================
# --- Schemas لحالات المحاصيل المتوقعة (Expected Crop Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)
#    تمت إزالة الأقسام الكاملة لـ ExpectedCropStatus و ExpectedCropStatusTranslation من هنا.


# ==========================================================
# --- Schema لتحديث حالة المنتج (Update Product Status) ---
#    (هذا الـ Schema يستخدم في Product Admin Router)
# ==========================================================
class ProductStatusUpdate(BaseModel):
    """Schema لتحديث حالة منتج. يستخدم في Product Admin Router."""
    product_status_id: int = Field(..., description="معرف حالة المنتج الجديدة.")

    