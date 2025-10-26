# backend\src\lookups\crud\languages_crud.py

from sqlalchemy.orm import Session
from sqlalchemy import exists, and_
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # Language

# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # Language


# ==========================================================
# --- CRUD Functions for Language (اللغات) ---
# ==========================================================

def create_language(db: Session, language_in: schemas.LanguageCreate) -> models.Language:
    """
    ينشئ لغة جديدة في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        language_in (schemas.LanguageCreate): بيانات اللغة للإنشاء.

    Returns:
        models.Language: كائن اللغة الذي تم إنشاؤه.
    """
    db_language = models.Language(
        language_code=language_in.language_code,
        language_name_native=language_in.language_name_native,
        language_name_en=language_in.language_name_en,
        text_direction=language_in.text_direction,
        is_active_for_interface=language_in.is_active_for_interface,
        sort_order=language_in.sort_order
    )
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return db_language

def get_language(db: Session, language_code: str) -> Optional[models.Language]:
    """
    يجلب لغة واحدة بالرمز الخاص بها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        language_code (str): رمز اللغة المطلوب.

    Returns:
        Optional[models.Language]: كائن اللغة أو None.
    """
    return db.query(models.Language).filter(models.Language.language_code == language_code).first()

def get_all_languages(db: Session, include_inactive: bool = False) -> List[models.Language]:
    """
    يجلب قائمة بجميع اللغات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        include_inactive (bool): هل يجب تضمين اللغات غير النشطة؟

    Returns:
        List[models.Language]: قائمة بكائنات اللغات.
    """
    query = db.query(models.Language)
    if not include_inactive:
        query = query.filter(models.Language.is_active_for_interface == True)
    return query.order_by(models.Language.sort_order, models.Language.language_name_en).all()

def update_language(db: Session, db_language: models.Language, language_in: schemas.LanguageUpdate) -> models.Language:
    """
    يحدث بيانات لغة موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_language (models.Language): كائن اللغة من قاعدة البيانات.
        language_in (schemas.LanguageUpdate): البيانات المراد تحديثها.

    Returns:
        models.Language: كائن اللغة المحدث.
    """
    update_data = language_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_language, key, value)
    db_language.updated_at = datetime.now(timezone.utc)
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return db_language

# لا يوجد delete_language مباشر، بل يتم إدارة الحالة عبر is_active_for_interface.