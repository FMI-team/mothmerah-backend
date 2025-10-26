# backend/src/products/crud/variety_crud.py

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from src.products.models import products_models as models
from src.products.schemas import variety_schemas as schemas

# ==========================================================
# --- CRUD Functions for ProductVariety ---
# ==========================================================

def get_all_varieties_for_product(db: Session, product_id: UUID) -> List[models.ProductVariety]:
    """جلب كل أصناف منتج معين مع ترجماتها."""
    return db.query(models.ProductVariety).filter(
        models.ProductVariety.product_id == product_id
    ).options(joinedload(models.ProductVariety.translations)).all()

def get_variety(db: Session, variety_id: int) -> Optional[models.ProductVariety]:
    """جلب صنف منتج واحد عن طريق الـ ID الخاص به."""
    return db.query(models.ProductVariety).filter(models.ProductVariety.variety_id == variety_id).first()

def create_variety(db: Session, variety_in: schemas.ProductVarietyCreate) -> models.ProductVariety:
    """إنشاء صنف منتج جديد مع ترجماته الأولية."""
    db_variety = models.ProductVariety(
        **variety_in.model_dump(exclude={"translations"})
    )
    if variety_in.translations:
        for trans in variety_in.translations:
            db_variety.translations.append(
                models.ProductVarietyTranslation(**trans.model_dump())
            )
    db.add(db_variety)
    db.commit()
    db.refresh(db_variety)
    return db_variety

def update_variety(db: Session, db_variety: models.ProductVariety, variety_in: schemas.ProductVarietyUpdate) -> models.ProductVariety:
    """تحديث بيانات صنف منتج موجود."""
    update_data = variety_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_variety, key, value)
    db.add(db_variety)
    db.commit()
    db.refresh(db_variety)
    return db_variety

def soft_delete_variety(db: Session, db_variety: models.ProductVariety) -> models.ProductVariety:
    """
    يقوم بالحذف الناعم لصنف المنتج عن طريق تحديث حالته إلى غير نشط.
    """
    db_variety.is_active = False
    db.add(db_variety)
    db.commit()
    db.refresh(db_variety)
    return db_variety

# ==========================================================
# --- CRUD Functions for ProductVarietyTranslation ---
# ==========================================================

def add_or_update_variety_translation(db: Session, variety_id: int, trans_in: schemas.ProductVarietyTranslationCreate) -> Optional[models.ProductVariety]:
    """إضافة أو تحديث ترجمة لصنف منتج."""
    db_variety = db.query(models.ProductVariety).options(joinedload(models.ProductVariety.translations)).filter(models.ProductVariety.variety_id == variety_id).first()
    if not db_variety:
        return None

    existing_trans = next((t for t in db_variety.translations if t.language_code == trans_in.language_code), None)
    if existing_trans:
        existing_trans.translated_variety_name = trans_in.translated_variety_name
        existing_trans.translated_variety_description = trans_in.translated_variety_description
    else:
        new_trans = models.ProductVarietyTranslation(variety_id=variety_id, **trans_in.model_dump())
        db.add(new_trans)
    
    db.commit()
    db.refresh(db_variety)
    return db_variety

def delete_variety_translation(db: Session, variety_id: int, language_code: str) -> bool:
    """حذف ترجمة صنف منتج معينة."""
    translation = db.query(models.ProductVarietyTranslation).filter_by(variety_id=variety_id, language_code=language_code).first()
    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False