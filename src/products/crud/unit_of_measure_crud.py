# backend\src\products\crud\unit_of_measure_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional

from src.products.models import units_models as models # استيراد المودلز (تفترض أنها موجودة هنا)
from src.products.schemas import units_schemas as schemas # استيراد الـ Schemas

# ==========================================================
# --- CRUD Functions for UnitOfMeasure ---
# ==========================================================

def create_unit_of_measure(db: Session, unit_in: schemas.UnitOfMeasureCreate) -> models.UnitOfMeasure:
    """
    ينشئ وحدة قياس جديدة في قاعدة البيانات، مع ترجماتها المضمنة.
    """
    db_unit = models.UnitOfMeasure(
        unit_name_key=unit_in.unit_name_key,
        unit_abbreviation_key=unit_in.unit_abbreviation_key,
        is_base_unit_for_type=unit_in.is_base_unit_for_type,
        conversion_factor_to_base=unit_in.conversion_factor_to_base,
        is_active=unit_in.is_active
    )
    db.add(db_unit)
    db.flush() # للحصول على unit_id قبل حفظ الترجمات

    if unit_in.translations:
        for trans_in in unit_in.translations:
            db_translation = models.UnitOfMeasureTranslation(
                unit_id=db_unit.unit_id,
                language_code=trans_in.language_code,
                translated_unit_name=trans_in.translated_unit_name,
                translated_unit_abbreviation=trans_in.translated_unit_abbreviation
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_unit)
    return db_unit

def get_unit_of_measure(db: Session, unit_id: int) -> Optional[models.UnitOfMeasure]:
    """
    يجلب وحدة قياس واحدة بالـ ID الخاص بها، مع ترجماتها.
    """
    return db.query(models.UnitOfMeasure).options(
        joinedload(models.UnitOfMeasure.translations)
    ).filter(models.UnitOfMeasure.unit_id == unit_id).first()

def get_all_units_of_measure(db: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[models.UnitOfMeasure]:
    """
    يجلب قائمة بجميع وحدات القياس، مع خيار لتضمين غير النشطة.
    """
    query = db.query(models.UnitOfMeasure).options(
        joinedload(models.UnitOfMeasure.translations)
    )
    if not include_inactive:
        query = query.filter(models.UnitOfMeasure.is_active == True)
    return query.offset(skip).limit(limit).all()

def update_unit_of_measure(db: Session, db_unit: models.UnitOfMeasure, unit_in: schemas.UnitOfMeasureUpdate) -> models.UnitOfMeasure:
    """
    يحدث بيانات وحدة قياس موجودة.
    """
    update_data = unit_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_unit, key, value)
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit

def soft_delete_unit_of_measure(db: Session, db_unit: models.UnitOfMeasure) -> models.UnitOfMeasure:
    """
    يقوم بالحذف الناعم لوحدة قياس عن طريق تعيين 'is_active' إلى False.
    """
    db_unit.is_active = False
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit

# ==========================================================
# --- CRUD Functions for UnitOfMeasureTranslation ---
# ==========================================================

def create_unit_of_measure_translation(db: Session, unit_id: int, trans_in: schemas.UnitOfMeasureTranslationCreate) -> models.UnitOfMeasureTranslation:
    """
    ينشئ ترجمة جديدة لوحدة قياس معينة.
    """
    db_translation = models.UnitOfMeasureTranslation(
        unit_id=unit_id,
        language_code=trans_in.language_code,
        translated_unit_name=trans_in.translated_unit_name,
        translated_unit_abbreviation=trans_in.translated_unit_abbreviation
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_unit_of_measure_translation(db: Session, unit_id: int, language_code: str) -> Optional[models.UnitOfMeasureTranslation]:
    """
    يجلب ترجمة وحدة قياس محددة بالـ ID الخاص بالوحدة ورمز اللغة.
    """
    return db.query(models.UnitOfMeasureTranslation).filter(
        and_(
            models.UnitOfMeasureTranslation.unit_id == unit_id,
            models.UnitOfMeasureTranslation.language_code == language_code
        )
    ).first()

def update_unit_of_measure_translation(db: Session, db_translation: models.UnitOfMeasureTranslation, trans_in: schemas.UnitOfMeasureTranslationUpdate) -> models.UnitOfMeasureTranslation:
    """
    يحدث ترجمة وحدة قياس موجودة.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_unit_of_measure_translation(db: Session, db_translation: models.UnitOfMeasureTranslation):
    """
    يحذف ترجمة وحدة قياس معينة (حذف صارم).
    """
    db.delete(db_translation)
    db.commit()
    return