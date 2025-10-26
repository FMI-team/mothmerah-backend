# backend\src\products\crud\attribute_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional

from src.products.models import attributes_models as models # استيراد المودلز
from src.products.schemas import attribute_schemas as schemas # استيراد الـ Schemas

# ==========================================================
# --- CRUD Functions for Attribute ---
# ==========================================================

def create_attribute(db: Session, attribute_in: schemas.AttributeCreate) -> models.Attribute:
    """
    ينشئ سمة جديدة في قاعدة البيانات، مع ترجماتها المضمنة.
    """
    db_attribute = models.Attribute(
        attribute_name_key=attribute_in.attribute_name_key,
        attribute_description_key=attribute_in.attribute_description_key,
        is_filterable=attribute_in.is_filterable,
        is_variant_defining=attribute_in.is_variant_defining
    )
    db.add(db_attribute)
    db.flush() # للحصول على attribute_id قبل حفظ الترجمات

    if attribute_in.translations:
        for trans_in in attribute_in.translations:
            db_translation = models.AttributeTranslation(
                attribute_id=db_attribute.attribute_id,
                language_code=trans_in.language_code,
                translated_attribute_name=trans_in.translated_attribute_name,
                translated_attribute_description=trans_in.translated_attribute_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_attribute)
    return db_attribute

def get_attribute(db: Session, attribute_id: int) -> Optional[models.Attribute]:
    """
    يجلب سمة واحدة بالـ ID الخاص بها، مع ترجماتها.
    """
    return db.query(models.Attribute).options(
        joinedload(models.Attribute.translations)
    ).filter(models.Attribute.attribute_id == attribute_id).first()

def get_all_attributes(db: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[models.Attribute]:
    """
    يجلب قائمة بجميع السمات، مع خيار لتضمين غير النشطة.
    """
    query = db.query(models.Attribute).options(
        joinedload(models.Attribute.translations)
    )
    if not include_inactive:
        query = query.filter(models.Attribute.is_active == True)
    return query.offset(skip).limit(limit).all()

def update_attribute(db: Session, db_attribute: models.Attribute, attribute_in: schemas.AttributeUpdate) -> models.Attribute:
    """
    يحدث بيانات سمة موجودة.
    """
    update_data = attribute_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_attribute, key, value)
    db.add(db_attribute)
    db.commit()
    db.refresh(db_attribute)
    return db_attribute

def soft_delete_attribute(db: Session, db_attribute: models.Attribute) -> models.Attribute:
    """
    يقوم بالحذف الناعم لسمة عن طريق تعيين 'is_active' إلى False.
    """
    db_attribute.is_active = False
    db.add(db_attribute)
    db.commit()
    db.refresh(db_attribute)
    return db_attribute

# ==========================================================
# --- CRUD Functions for AttributeTranslation ---
# ==========================================================

def create_attribute_translation(db: Session, attribute_id: int, trans_in: schemas.AttributeTranslationCreate) -> models.AttributeTranslation:
    """
    ينشئ ترجمة جديدة لسمة معينة.
    """
    db_translation = models.AttributeTranslation(
        attribute_id=attribute_id,
        language_code=trans_in.language_code,
        translated_attribute_name=trans_in.translated_attribute_name,
        translated_attribute_description=trans_in.translated_attribute_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_attribute_translation(db: Session, attribute_id: int, language_code: str) -> Optional[models.AttributeTranslation]:
    """
    يجلب ترجمة سمة محددة بالـ ID الخاص بالسمة ورمز اللغة.
    """
    return db.query(models.AttributeTranslation).filter(
        and_(
            models.AttributeTranslation.attribute_id == attribute_id,
            models.AttributeTranslation.language_code == language_code
        )
    ).first()

def update_attribute_translation(db: Session, db_translation: models.AttributeTranslation, trans_in: schemas.AttributeTranslationUpdate) -> models.AttributeTranslation:
    """
    يحدث ترجمة سمة موجودة.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_attribute_translation(db: Session, db_translation: models.AttributeTranslation):
    """
    يحذف ترجمة سمة معينة (حذف صارم).
    """
    db.delete(db_translation)
    db.commit()
    return