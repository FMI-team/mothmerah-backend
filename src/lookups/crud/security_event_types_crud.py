# backend\src\lookups\crud\security_event_types_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # SecurityEventType, SecurityEventTypeTranslation
# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # SecurityEventType, SecurityEventTypeTranslation
# TODO: استيراد مودل SecurityEventLog (من المجموعة 13) للتحقق من الارتباطات
# from src.audit.models.audit_models import SecurityEventLog


# ==========================================================
# --- CRUD Functions for SecurityEventType (أنواع أحداث الأمان) ---
# ==========================================================

def create_security_event_type(db: Session, type_in: schemas.SecurityEventTypeCreate) -> models.SecurityEventType:
    """
    ينشئ نوع حدث أمان جديد في قاعدة البيانات، مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas.SecurityEventTypeCreate): بيانات النوع للإنشاء.

    Returns:
        models.SecurityEventType: كائن النوع الذي تم إنشاؤه.
    """
    db_type = models.SecurityEventType(
        event_name_key=type_in.event_name_key,
        description_key=type_in.description_key,
        severity_level=type_in.severity_level
    )
    db.add(db_type)
    db.flush() # للحصول على security_event_type_id قبل إضافة الترجمات

    if type_in.translations:
        for trans_in in type_in.translations:
            db_translation = models.SecurityEventTypeTranslation(
                security_event_type_id=db_type.security_event_type_id,
                language_code=trans_in.language_code,
                translated_event_name=trans_in.translated_event_name,
                translated_event_description=trans_in.translated_event_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_type)
    return db_type

def get_security_event_type(db: Session, type_id: int) -> Optional[models.SecurityEventType]:
    """
    يجلب نوع حدث أمان واحد بالـ ID الخاص به، مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع المطلوب.

    Returns:
        Optional[models.SecurityEventType]: كائن النوع أو None.
    """
    return db.query(models.SecurityEventType).options(
        joinedload(models.SecurityEventType.translations)
    ).filter(models.SecurityEventType.security_event_type_id == type_id).first()

def get_security_event_type_by_key(db: Session, key: str) -> Optional[models.SecurityEventType]:
    """جلب نوع حدث أمان عن طريق المفتاح النصي."""
    return db.query(models.SecurityEventType).filter(models.SecurityEventType.event_name_key == key).first()

def get_all_security_event_types(db: Session) -> List[models.SecurityEventType]:
    """
    يجلب قائمة بجميع أنواع أحداث الأمان.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[models.SecurityEventType]: قائمة بكائنات الأنواع.
    """
    return db.query(models.SecurityEventType).options(
        joinedload(models.SecurityEventType.translations)
    ).order_by(models.SecurityEventType.security_event_type_id).all()

def update_security_event_type(db: Session, db_type: models.SecurityEventType, type_in: schemas.SecurityEventTypeUpdate) -> models.SecurityEventType:
    """
    يحدث بيانات نوع حدث أمان موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_type (models.SecurityEventType): كائن النوع من قاعدة البيانات.
        type_in (schemas.SecurityEventTypeUpdate): البيانات المراد تحديثها.

    Returns:
        models.SecurityEventType: كائن النوع المحدث.
    """
    update_data = type_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_type, key, value)
    db_type.updated_at = datetime.now(timezone.utc)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

# TODO: أضف دالة count_security_event_logs_for_type (عند بناء Module 13)
# def count_security_event_logs_for_type(db: Session, event_type_id: int) -> int:
#     """يحسب عدد سجلات أحداث الأمان المرتبطة بنوع حدث أمان معين."""
#     return db.query(SecurityEventLog).filter(SecurityEventLog.event_type_id == event_type_id).count()

def delete_security_event_type(db: Session, db_type: models.SecurityEventType):
    """
    يحذف نوع حدث أمان معين (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_type (models.SecurityEventType): كائن النوع من قاعدة البيانات.
    """
    db.delete(db_type)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for SecurityEventTypeTranslation (ترجمات أنواع أحداث الأمان) ---
# ==========================================================

def create_security_event_type_translation(db: Session, security_event_type_id: int, trans_in: schemas.SecurityEventTypeTranslationCreate) -> models.SecurityEventTypeTranslation:
    """
    ينشئ ترجمة جديدة لنوع حدث أمان معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        security_event_type_id (int): معرف النوع الأم.
        trans_in (schemas.SecurityEventTypeTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.SecurityEventTypeTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models.SecurityEventTypeTranslation(
        security_event_type_id=security_event_type_id,
        language_code=trans_in.language_code,
        translated_event_name=trans_in.translated_event_name,
        translated_event_description=trans_in.translated_event_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_security_event_type_translation(db: Session, security_event_type_id: int, language_code: str) -> Optional[models.SecurityEventTypeTranslation]:
    """
    يجلب ترجمة نوع حدث أمان محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        security_event_type_id (int): معرف النوع.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models.SecurityEventTypeTranslation]: كائن الترجمة أو None.
    """
    return db.query(models.SecurityEventTypeTranslation).filter(
        and_(
            models.SecurityEventTypeTranslation.security_event_type_id == security_event_type_id,
            models.SecurityEventTypeTranslation.language_code == language_code
        )
    ).first()

def update_security_event_type_translation(db: Session, db_translation: models.SecurityEventTypeTranslation, trans_in: schemas.SecurityEventTypeTranslationUpdate) -> models.SecurityEventTypeTranslation:
    """
    يحدث ترجمة نوع حدث أمان موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.SecurityEventTypeTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.SecurityEventTypeTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.SecurityEventTypeTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_security_event_type_translation(db: Session, db_translation: models.SecurityEventTypeTranslation):
    """
    يحذف ترجمة نوع حدث أمان معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.SecurityEventTypeTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return