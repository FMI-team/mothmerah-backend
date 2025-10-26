# backend\src\products\crud\image_crud.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID # قد تحتاج UUID لـ uploaded_by_user_id و entity_id إذا كان UUID

from src.products.models import units_models as models # استيراد المودلز (تفترض أن Image موجود هنا)
from src.products.schemas import image_schemas as schemas # استيراد الـ Schemas
from src.products.models.products_models import Product # لاستخدام Product في joinedload إذا لزم الأمر
from src.products.models.units_models import ProductPackagingOption # لاستخدام ProductPackagingOption في joinedload إذا لزم الأمر

# ==========================================================
# --- CRUD Functions for Image ---
# ==========================================================

def create_image(db: Session, image_in: schemas.ImageCreate, uploaded_by_user_id: Optional[UUID] = None) -> models.Image:
    """
    ينشئ سجل صورة جديد في قاعدة البيانات.
    """
    db_image = models.Image(
        entity_id=image_in.entity_id,
        entity_type=image_in.entity_type,
        image_url=image_in.image_url,
        alt_text_key=image_in.alt_text_key,
        is_primary_image=image_in.is_primary_image,
        sort_order=image_in.sort_order,
        uploaded_by_user_id=uploaded_by_user_id
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def get_image(db: Session, image_id: int) -> Optional[models.Image]:
    """
    يجلب سجل صورة واحد بالـ ID الخاص به.
    """
    return db.query(models.Image).filter(models.Image.image_id == image_id).first()

def get_images_for_entity(db: Session, entity_id: str, entity_type: str) -> List[models.Image]:
    """
    يجلب جميع الصور المرتبطة بكيان معين (مثل منتج أو خيار تعبئة).
    """
    query = db.query(models.Image).filter(
        models.Image.entity_id == entity_id,
        models.Image.entity_type == entity_type
    ).order_by(models.Image.sort_order)
    return query.all()

def update_image(db: Session, db_image: models.Image, image_in: schemas.ImageUpdate) -> models.Image:
    """
    يحدث بيانات سجل صورة موجود.
    """
    update_data = image_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_image, key, value)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def delete_image(db: Session, db_image: models.Image):
    """
    يحذف سجل صورة معين (حذف صارم).
    """
    db.delete(db_image)
    db.commit()
    return