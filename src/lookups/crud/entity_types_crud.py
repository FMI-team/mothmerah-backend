# backend\src\lookups\crud\entity_types_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # EntityTypeForReviewOrImage, EntityTypeTranslation
# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # EntityTypeForReviewOrImage, EntityTypeTranslation
# TODO: استيراد مودلات Reviews و Images للتحقق من الارتباطات (من المجموعة 6 و 2)
# from src.reviews.models.reviews_models import Review
# from src.products.models.products_models import Image


# ==========================================================
# --- CRUD Functions for EntityTypeForReviewOrImage (أنواع الكيانات للمراجعة أو الصورة) ---
# ==========================================================

def create_entity_type(db: Session, type_in: schemas.EntityTypeForReviewOrImageCreate) -> models.EntityTypeForReviewOrImage:
    """
    ينشئ نوع كيان جديد في قاعدة البيانات، مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas.EntityTypeForReviewOrImageCreate): بيانات النوع للإنشاء.

    Returns:
        models.EntityTypeForReviewOrImage: كائن النوع الذي تم إنشاؤه.
    """
    db_type = models.EntityTypeForReviewOrImage(
        entity_type_code=type_in.entity_type_code,
        entity_type_name_key=type_in.entity_type_name_key,
        description_key=type_in.description_key
    )
    db.add(db_type)
    db.flush() # للحصول على entity_type_code قبل إضافة الترجمات

    if type_in.translations:
        for trans_in in type_in.translations:
            db_translation = models.EntityTypeTranslation(
                entity_type_code=db_type.entity_type_code,
                language_code=trans_in.language_code,
                translated_entity_type_name=trans_in.translated_entity_type_name,
                translated_entity_description=trans_in.translated_entity_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_type)
    return db_type

def get_entity_type(db: Session, entity_type_code: str) -> Optional[models.EntityTypeForReviewOrImage]:
    """
    يجلب نوع كيان واحد بالرمز الخاص به، مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        entity_type_code (str): رمز الكيان المطلوب.

    Returns:
        Optional[models.EntityTypeForReviewOrImage]: كائن النوع أو None.
    """
    return db.query(models.EntityTypeForReviewOrImage).options(
        joinedload(models.EntityTypeForReviewOrImage.translations)
    ).filter(models.EntityTypeForReviewOrImage.entity_type_code == entity_type_code).first()

def get_entity_type_by_key(db: Session, key: str) -> Optional[models.EntityTypeForReviewOrImage]:
    """جلب نوع كيان عن طريق المفتاح النصي."""
    return db.query(models.EntityTypeForReviewOrImage).filter(models.EntityTypeForReviewOrImage.entity_type_name_key == key).first()


def get_all_entity_types(db: Session) -> List[models.EntityTypeForReviewOrImage]:
    """
    يجلب قائمة بجميع أنواع الكيانات للمراجعة أو الصورة.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[models.EntityTypeForReviewOrImage]: قائمة بكائنات الأنواع.
    """
    return db.query(models.EntityTypeForReviewOrImage).options(
        joinedload(models.EntityTypeForReviewOrImage.translations)
    ).order_by(models.EntityTypeForReviewOrImage.entity_type_code).all()

def update_entity_type(db: Session, db_type: models.EntityTypeForReviewOrImage, type_in: schemas.EntityTypeForReviewOrImageUpdate) -> models.EntityTypeForReviewOrImage:
    """
    يحدث بيانات نوع كيان موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_type (models.EntityTypeForReviewOrImage): كائن النوع من قاعدة البيانات.
        type_in (schemas.EntityTypeForReviewOrImageUpdate): البيانات المراد تحديثها.

    Returns:
        models.EntityTypeForReviewOrImage: كائن النوع المحدث.
    """
    update_data = type_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_type, key, value)
    db_type.updated_at = datetime.now(timezone.utc)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

# TODO: أضف دوال count_reviews_for_entity_type و count_images_for_entity_type
# def count_reviews_for_entity_type(db: Session, entity_type_code: str) -> int:
#     """يحسب عدد المراجعات المرتبطة بنوع كيان معين."""
#     return db.query(Review).filter(Review.entity_type_code == entity_type_code).count()

# def count_images_for_entity_type(db: Session, entity_type_code: str) -> int:
#     """يحسب عدد الصور المرتبطة بنوع كيان معين."""
#     return db.query(Image).filter(Image.entity_type_code == entity_type_code).count()

def delete_entity_type(db: Session, db_type: models.EntityTypeForReviewOrImage):
    """
    يحذف نوع كيان معين (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_type (models.EntityTypeForReviewOrImage): كائن النوع من قاعدة البيانات.
    """
    db.delete(db_type)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for EntityTypeTranslation (ترجمات أنواع الكيانات) ---
# ==========================================================

def create_entity_type_translation(db: Session, entity_type_code: str, trans_in: schemas.EntityTypeTranslationCreate) -> models.EntityTypeTranslation:
    """
    ينشئ ترجمة جديدة لنوع كيان معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        entity_type_code (str): رمز الكيان الأم.
        trans_in (schemas.EntityTypeTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.EntityTypeTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models.EntityTypeTranslation(
        entity_type_code=entity_type_code,
        language_code=trans_in.language_code,
        translated_entity_type_name=trans_in.translated_entity_type_name,
        translated_entity_description=trans_in.translated_entity_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_entity_type_translation(db: Session, entity_type_code: str, language_code: str) -> Optional[models.EntityTypeTranslation]:
    """
    يجلب ترجمة نوع كيان محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        entity_type_code (str): رمز الكيان.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models.EntityTypeTranslation]: كائن الترجمة أو None.
    """
    return db.query(models.EntityTypeTranslation).filter(
        and_(
            models.EntityTypeTranslation.entity_type_code == entity_type_code,
            models.EntityTypeTranslation.language_code == language_code
        )
    ).first()

def update_entity_type_translation(db: Session, db_translation: models.EntityTypeTranslation, trans_in: schemas.EntityTypeTranslationUpdate) -> models.EntityTypeTranslation:
    """
    يحدث ترجمة نوع كيان موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.EntityTypeTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.EntityTypeTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.EntityTypeTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_entity_type_translation(db: Session, db_translation: models.EntityTypeTranslation):
    """
    يحذف ترجمة نوع كيان معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.EntityTypeTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return