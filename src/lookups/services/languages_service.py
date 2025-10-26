# backend\src\lookups\services\languages_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # Language
# استيراد الـ CRUD
from src.lookups.crud import languages_crud # لـ Language CRUDs

# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # Language

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for Language (اللغات) ---
# ==========================================================

def create_new_language(db: Session, language_in: schemas.LanguageCreate) -> models.Language:
    """
    خدمة لإنشاء لغة جديدة.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        language_in (schemas.LanguageCreate): بيانات اللغة للإنشاء.

    Returns:
        models.Language: كائن اللغة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت اللغة بنفس الرمز أو الاسم موجودة بالفعل.
    """
    # 1. التحقق من عدم وجود لغة بنفس الرمز أو الاسم
    existing_language_by_code = languages_crud.get_language(db, language_code=language_in.language_code)
    if existing_language_by_code:
        raise ConflictException(detail=f"اللغة بالرمز '{language_in.language_code}' موجودة بالفعل.")
    
    # لا يوجد حقل name_key لـ Language، ولكن يمكن التحقق من uniqueness لـ language_name_native أو language_name_en إذا لزم الأمر.
    existing_language_by_native_name = db.query(models.Language).filter(models.Language.language_name_native == language_in.language_name_native).first()
    if existing_language_by_native_name:
        raise ConflictException(detail=f"اللغة بالاسم الأصلي '{language_in.language_name_native}' موجودة بالفعل.")

    return languages_crud.create_language(db=db, language_in=language_in)

def get_all_languages_service(db: Session, include_inactive: bool = False) -> List[models.Language]:
    """خدمة لجلب قائمة بجميع اللغات."""
    return languages_crud.get_all_languages(db, include_inactive=include_inactive)

def get_language_by_code_service(db: Session, language_code: str) -> models.Language:
    """
    خدمة لجلب لغة واحدة بالرمز الخاص بها، مع معالجة عدم الوجود.
    """
    db_language = languages_crud.get_language(db, language_code=language_code)
    if not db_language:
        raise NotFoundException(detail=f"اللغة بالرمز '{language_code}' غير موجودة.")
    return db_language

def update_language(db: Session, language_code: str, language_in: schemas.LanguageUpdate) -> models.Language:
    """
    خدمة لتحديث لغة موجودة.
    تتضمن التحقق من تفرد الأسماء إذا تم تغييرها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        language_code (str): رمز اللغة المراد تحديثها.
        language_in (schemas.LanguageUpdate): البيانات المراد تحديثها.

    Returns:
        models.Language: كائن اللغة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على اللغة.
        ConflictException: إذا كانت هناك محاولة لتغيير الاسم إلى اسم موجود بالفعل.
    """
    db_language = get_language_by_code_service(db, language_code=language_code) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد الأسماء إذا تم تحديثها
    if language_in.language_name_native and language_in.language_name_native != db_language.language_name_native:
        existing_by_native_name = db.query(models.Language).filter(models.Language.language_name_native == language_in.language_name_native).first()
        if existing_by_native_name and existing_by_native_name.language_code != language_code:
            raise ConflictException(detail=f"اللغة بالاسم الأصلي '{language_in.language_name_native}' موجودة بالفعل.")
    
    if language_in.language_name_en and language_in.language_name_en != db_language.language_name_en:
        existing_by_en_name = db.query(models.Language).filter(models.Language.language_name_en == language_in.language_name_en).first()
        if existing_by_en_name and existing_by_en_name.language_code != language_code:
            raise ConflictException(detail=f"اللغة بالاسم الإنجليزي '{language_in.language_name_en}' موجودة بالفعل.")

    return languages_crud.update_language(db, db_language=db_language, language_in=language_in)

def soft_delete_language_by_code(db: Session, language_code: str):
    """
    خدمة للحذف الناعم للغة (بتعيين is_active_for_interface إلى False).
    تتضمن التحقق من عدم وجود ارتباطات حيوية (مثل ترجمات، تفضيلات مستخدمين).

    Args:
        db (Session): جلسة قاعدة البيانات.
        language_code (str): رمز اللغة المراد حذفها ناعماً.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على اللغة.
        BadRequestException: إذا كانت اللغة غير نشطة بالفعل.
        ConflictException: إذا كانت هناك ارتباطات تمنع التعطيل.
    """
    db_language = get_language_by_code_service(db, language_code=language_code) # استخدام دالة الخدمة للتحقق

    if not db_language.is_active_for_interface:
        raise BadRequestException(detail=f"اللغة بالرمز '{language_code}' غير نشطة بالفعل.")

    # TODO: التحقق من عدم وجود ارتباطات حيوية في جداول الترجمة المختلفة (جميع جداول Translation.language_code)
    #       هذا يتطلب دوال count في CRUD الخاص بتلك المودلات الترجمة.
    #       مثلاً: currencies_crud.count_translations_for_language(db, language_code)
    #       وجميع جداول الترجمة الأخرى في النظام.
    #       إذا كانت اللغة تستخدم كـ preferred_language_code في جدول users:
    #       users_count = core_crud.count_users_with_preferred_language(db, language_code)
    #       if users_count > 0: ...

    db_language.is_active_for_interface = False # تعيين is_active_for_interface إلى False
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return {"message": f"تم تعطيل اللغة '{db_language.language_name_native}' بنجاح."}