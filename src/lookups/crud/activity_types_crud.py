# backend\src\lookups\crud\activity_types_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # ActivityType, ActivityTypeTranslation
# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # ActivityType, ActivityTypeTranslation
# TODO: استيراد مودل UserActivityLog (من المجموعة 13) للتحقق من الارتباطات
# from src.audit.models.audit_models import UserActivityLog


# ==========================================================
# --- CRUD Functions for ActivityType (أنواع الأنشطة) ---
# ==========================================================

def create_activity_type(db: Session, type_in: schemas.ActivityTypeCreate) -> models.ActivityType:
    """
    ينشئ نوع نشاط جديد في قاعدة البيانات، مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas.ActivityTypeCreate): بيانات النوع للإنشاء.

    Returns:
        models.ActivityType: كائن النوع الذي تم إنشاؤه.
    """
    db_type = models.ActivityType(
        activity_name_key=type_in.activity_name_key,
        description_key=type_in.description_key
    )
    db.add(db_type)
    db.flush() # للحصول على activity_type_id قبل إضافة الترجمات

    if type_in.translations:
        for trans_in in type_in.translations:
            db_translation = models.ActivityTypeTranslation(
                activity_type_id=db_type.activity_type_id,
                language_code=trans_in.language_code,
                translated_activity_name=trans_in.translated_activity_name,
                translated_activity_description=trans_in.translated_activity_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_type)
    return db_type

def get_activity_type(db: Session, type_id: int) -> Optional[models.ActivityType]:
    """
    يجلب نوع نشاط واحد بالـ ID الخاص به، مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع المطلوب.

    Returns:
        Optional[models.ActivityType]: كائن النوع أو None.
    """
    return db.query(models.ActivityType).options(
        joinedload(models.ActivityType.translations)
    ).filter(models.ActivityType.activity_type_id == type_id).first()

def get_activity_type_by_key(db: Session, key: str) -> Optional[models.ActivityType]:
    """جلب نوع نشاط عن طريق المفتاح النصي."""
    return db.query(models.ActivityType).filter(models.ActivityType.activity_name_key == key).first()

def get_all_activity_types(db: Session) -> List[models.ActivityType]:
    """
    يجلب قائمة بجميع أنواع الأنشطة.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[models.ActivityType]: قائمة بكائنات الأنواع.
    """
    return db.query(models.ActivityType).options(
        joinedload(models.ActivityType.translations)
    ).order_by(models.ActivityType.activity_type_id).all()

def update_activity_type(db: Session, db_type: models.ActivityType, type_in: schemas.ActivityTypeUpdate) -> models.ActivityType:
    """
    يحدث بيانات نوع نشاط موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_type (models.ActivityType): كائن النوع من قاعدة البيانات.
        type_in (schemas.ActivityTypeUpdate): البيانات المراد تحديثها.

    Returns:
        models.ActivityType: كائن النوع المحدث.
    """
    update_data = type_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_type, key, value)
    db_type.updated_at = datetime.now(timezone.utc)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

# TODO: أضف دالة count_user_activity_logs_for_type (عند بناء Module 13)
# def count_user_activity_logs_for_type(db: Session, activity_type_id: int) -> int:
#     """يحسب عدد سجلات أنشطة المستخدم المرتبطة بنوع نشاط معين."""
#     return db.query(UserActivityLog).filter(UserActivityLog.activity_type_id == activity_type_id).count()

def delete_activity_type(db: Session, db_type: models.ActivityType):
    """
    يحذف نوع نشاط معين (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_type (models.ActivityType): كائن النوع من قاعدة البيانات.
    """
    db.delete(db_type)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for ActivityTypeTranslation (ترجمات أنواع الأنشطة) ---
# ==========================================================

def create_activity_type_translation(db: Session, activity_type_id: int, trans_in: schemas.ActivityTypeTranslationCreate) -> models.ActivityTypeTranslation:
    """
    ينشئ ترجمة جديدة لنوع نشاط معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        activity_type_id (int): معرف النوع الأم.
        trans_in (schemas.ActivityTypeTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.ActivityTypeTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models.ActivityTypeTranslation(
        activity_type_id=activity_type_id,
        language_code=trans_in.language_code,
        translated_activity_name=trans_in.translated_activity_name,
        translated_activity_description=trans_in.translated_activity_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_activity_type_translation(db: Session, activity_type_id: int, language_code: str) -> Optional[models.ActivityTypeTranslation]:
    """
    يجلب ترجمة نوع نشاط محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        activity_type_id (int): معرف النوع.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models.ActivityTypeTranslation]: كائن الترجمة أو None.
    """
    return db.query(models.ActivityTypeTranslation).filter(
        and_(
            models.ActivityTypeTranslation.activity_type_id == activity_type_id,
            models.ActivityTypeTranslation.language_code == language_code
        )
    ).first()

def update_activity_type_translation(db: Session, db_translation: models.ActivityTypeTranslation, trans_in: schemas.ActivityTypeTranslationUpdate) -> models.ActivityTypeTranslation:
    """
    يحدث ترجمة نوع نشاط موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.ActivityTypeTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.ActivityTypeTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.ActivityTypeTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_activity_type_translation(db: Session, db_translation: models.ActivityTypeTranslation):
    """
    يحذف ترجمة نوع نشاط معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.ActivityTypeTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return