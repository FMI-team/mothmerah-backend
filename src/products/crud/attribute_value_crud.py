# backend\src\products\crud\attribute_value_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional

from src.products.models import attributes_models as models # استيراد المودلز
from src.products.schemas import attribute_schemas as schemas # استيراد الـ Schemas

# ==========================================================
# --- CRUD Functions for AttributeValue ---
# ==========================================================

def create_attribute_value(db: Session, value_in: schemas.AttributeValueCreate) -> models.AttributeValue:
    """
    ينشئ قيمة سمة جديدة في قاعدة البيانات، مع ترجماتها المضمنة.
    """
    db_value = models.AttributeValue(
        attribute_id=value_in.attribute_id,
        attribute_value_key=value_in.attribute_value_key,
        sort_order=value_in.sort_order
    )
    db.add(db_value)
    db.flush() # للحصول على attribute_value_id قبل حفظ الترجمات

    if value_in.translations:
        for trans_in in value_in.translations:
            db_translation = models.AttributeValueTranslation(
                attribute_value_id=db_value.attribute_value_id,
                language_code=trans_in.language_code,
                translated_value_name=trans_in.translated_value_name,
                translated_value_description=trans_in.translated_value_description # تأكد من أن هذا الحقل موجود في المودل
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_value)
    return db_value

def get_attribute_value(db: Session, attribute_value_id: int) -> Optional[models.AttributeValue]:
    """
    يجلب قيمة سمة واحدة بالـ ID الخاص بها، مع ترجماتها.
    """
    return db.query(models.AttributeValue).options(
        joinedload(models.AttributeValue.translations)
    ).filter(models.AttributeValue.attribute_value_id == attribute_value_id).first()

def get_all_attribute_values(db: Session, attribute_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models.AttributeValue]:
    """
    يجلب قائمة بجميع قيم السمات، مع خيار التصفية حسب السمة الأم.
    """
    query = db.query(models.AttributeValue).options(
        joinedload(models.AttributeValue.translations)
    )
    if attribute_id:
        query = query.filter(models.AttributeValue.attribute_id == attribute_id)
    return query.offset(skip).limit(limit).all()

def update_attribute_value(db: Session, db_attribute_value: models.AttributeValue, value_in: schemas.AttributeValueUpdate) -> models.AttributeValue:
    """
    يحدث بيانات قيمة سمة موجودة.
    """
    update_data = value_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_attribute_value, key, value)
    db.add(db_attribute_value)
    db.commit()
    db.refresh(db_attribute_value)
    return db_attribute_value

def delete_attribute_value(db: Session, db_attribute_value: models.AttributeValue):
    """
    يحذف قيمة سمة معينة (حذف صارم).
    """
    db.delete(db_attribute_value)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for AttributeValueTranslation ---
# ==========================================================

def create_attribute_value_translation(db: Session, attribute_value_id: int, trans_in: schemas.AttributeValueTranslationCreate) -> models.AttributeValueTranslation:
    """
    ينشئ ترجمة جديدة لقيمة سمة معينة.
    """
    db_translation = models.AttributeValueTranslation(
        attribute_value_id=attribute_value_id,
        language_code=trans_in.language_code,
        translated_value_name=trans_in.translated_value_name,
        translated_value_description=trans_in.translated_value_description # تأكد من أن هذا الحقل موجود في المودل
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_attribute_value_translation(db: Session, attribute_value_id: int, language_code: str) -> Optional[models.AttributeValueTranslation]:
    """
    يجلب ترجمة قيمة سمة محددة بالـ ID الخاص بالقيمة ورمز اللغة.
    """
    return db.query(models.AttributeValueTranslation).filter(
        and_(
            models.AttributeValueTranslation.attribute_value_id == attribute_value_id,
            models.AttributeValueTranslation.language_code == language_code
        )
    ).first()

def update_attribute_value_translation(db: Session, db_translation: models.AttributeValueTranslation, trans_in: schemas.AttributeValueTranslationUpdate) -> models.AttributeValueTranslation:
    """
    يحدث ترجمة قيمة سمة موجودة.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_attribute_value_translation(db: Session, db_translation: models.AttributeValueTranslation):
    """
    يحذف ترجمة قيمة سمة معينة (حذف صارم).
    """
    db.delete(db_translation)
    db.commit()
    return