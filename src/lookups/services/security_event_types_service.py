# backend\src\lookups\services\security_event_types_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # SecurityEventType, SecurityEventTypeTranslation, Language
# استيراد الـ CRUD
from src.lookups.crud import security_event_types_crud # لـ SecurityEventType, SecurityEventTypeTranslation CRUDs
from src.lookups.crud import languages_crud # للتحقق من وجود اللغة (Language)
# TODO: استيراد CRUDs لـ SecurityEventLog (من المجموعة 13) للتحقق من الارتباطات
# from src.audit.crud import security_event_logs_crud # للتحقق من SecurityEventLog


# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # SecurityEventType, SecurityEventTypeTranslation

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for SecurityEventType (أنواع أحداث الأمان) ---
# ==========================================================

def create_new_security_event_type(db: Session, type_in: schemas.SecurityEventTypeCreate) -> models.SecurityEventType:
    """
    خدمة لإنشاء نوع حدث أمان جديد مع ترجماته الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas.SecurityEventTypeCreate): بيانات النوع للإنشاء.

    Returns:
        models.SecurityEventType: كائن النوع الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان نوع حدث الأمان بمفتاح معين موجوداً بالفعل.
        NotFoundException: إذا كانت اللغة المحددة للترجمة غير موجودة.
    """
    # 1. التحقق من عدم وجود نوع حدث أمان بنفس المفتاح
    existing_type = security_event_types_crud.get_security_event_type_by_key(db, key=type_in.event_name_key)
    if existing_type:
        raise ConflictException(detail=f"نوع حدث الأمان بمفتاح '{type_in.event_name_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود اللغات المستخدمة في الترجمات
    if type_in.translations:
        for trans_in in type_in.translations:
            language_obj = languages_crud.get_language(db, language_code=trans_in.language_code)
            if not language_obj:
                raise NotFoundException(detail=f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    return security_event_types_crud.create_security_event_type(db=db, type_in=type_in)

def get_all_security_event_types_service(db: Session) -> List[models.SecurityEventType]:
    """خدمة لجلب قائمة بجميع أنواع أحداث الأمان."""
    return security_event_types_crud.get_all_security_event_types(db)

def get_security_event_type_details(db: Session, type_id: int) -> models.SecurityEventType:
    """
    خدمة لجلب نوع حدث أمان واحد بالـ ID الخاص به، مع معالجة عدم الوجود.
    """
    db_type = security_event_types_crud.get_security_event_type(db, type_id=type_id)
    if not db_type:
        raise NotFoundException(detail=f"نوع حدث الأمان بمعرف {type_id} غير موجود.")
    return db_type

def update_security_event_type(db: Session, type_id: int, type_in: schemas.SecurityEventTypeUpdate) -> models.SecurityEventType:
    """
    خدمة لتحديث نوع حدث أمان موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع المراد تحديثه.
        type_in (schemas.SecurityEventTypeUpdate): البيانات المراد تحديثها.

    Returns:
        models.SecurityEventType: كائن النوع المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_type = get_security_event_type_details(db, type_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث event_name_key
    if type_in.event_name_key and type_in.event_name_key != db_type.event_name_key:
        existing_type_by_key = security_event_types_crud.get_security_event_type_by_key(db, key=type_in.event_name_key)
        if existing_type_by_key and existing_type_by_key.security_event_type_id != type_id:
            raise ConflictException(detail=f"نوع حدث الأمان بمفتاح '{type_in.event_name_key}' موجود بالفعل.")

    return security_event_types_crud.update_security_event_type(db, db_type=db_type, type_in=type_in)

def delete_security_event_type_by_id(db: Session, type_id: int):
    """
    خدمة لحذف نوع حدث أمان بشكل صارم.
    تتضمن التحقق من عدم وجود سجلات أحداث أمان مرتبطة به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع المراد حذفه.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
        ConflictException: إذا كانت هناك سجلات أحداث أمان مرتبطة.
    """
    db_type_to_delete = get_security_event_type_details(db, type_id) # استخدام دالة الخدمة للتحقق

    # التحقق من عدم وجود سجلات أحداث أمان مرتبطة بهذا النوع (من المجموعة 13)
    # TODO: يجب إضافة دالة count_security_event_logs_for_type في security_event_logs_crud
    # security_event_logs_count = security_event_logs_crud.count_security_event_logs_for_type(db, type_id)
    # if security_event_logs_count > 0:
    #     raise ConflictException(detail=f"لا يمكن حذف نوع حدث الأمان بمعرف {type_id} لأنه مرتبط بـ {security_event_logs_count} سجل(سجلات) أحداث أمان.")

    security_event_types_crud.delete_security_event_type(db, db_type=db_type_to_delete)
    db.commit()
    return {"message": f"تم حذف نوع حدث الأمان '{db_type_to_delete.event_name_key}' بنجاح."}


# ==========================================================
# --- Services for SecurityEventTypeTranslation (ترجمات أنواع أحداث الأمان) ---
# ==========================================================

def create_security_event_type_translation(db: Session, security_event_type_id: int, trans_in: schemas.SecurityEventTypeTranslationCreate) -> models.SecurityEventTypeTranslation:
    """خدمة لإنشاء ترجمة جديدة لنوع حدث أمان."""
    # 1. التحقق من وجود النوع الأم
    get_security_event_type_details(db, security_event_type_id)

    # 2. التحقق من وجود اللغة
    languages_crud.get_language(db, language_code=trans_in.language_code)

    # 3. التحقق من عدم وجود ترجمة بنفس اللغة
    existing_translation = security_event_types_crud.get_security_event_type_translation(db, security_event_type_id=security_event_type_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة لنوع حدث الأمان بمعرف {security_event_type_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return security_event_types_crud.create_security_event_type_translation(db=db, security_event_type_id=security_event_type_id, trans_in=trans_in)

def get_security_event_type_translation_details(db: Session, security_event_type_id: int, language_code: str) -> models.SecurityEventTypeTranslation:
    """خدمة لجلب ترجمة نوع حدث أمان محددة."""
    translation = security_event_types_crud.get_security_event_type_translation(db, security_event_type_id=security_event_type_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لنوع حدث الأمان بمعرف {security_event_type_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_security_event_type_translation(db: Session, security_event_type_id: int, language_code: str, trans_in: schemas.SecurityEventTypeTranslationUpdate) -> models.SecurityEventTypeTranslation:
    """خدمة لتحديث ترجمة نوع حدث أمان موجودة."""
    db_translation = get_security_event_type_translation_details(db, security_event_type_id, language_code) # التحقق من وجود الترجمة
    return security_event_types_crud.update_security_event_type_translation(db, db_translation=db_translation, trans_in=trans_in)

def remove_security_event_type_translation(db: Session, security_event_type_id: int, language_code: str):
    """خدمة لحذف ترجمة نوع حدث أمان معينة."""
    db_translation = get_security_event_type_translation_details(db, security_event_type_id, language_code) # التحقق من وجود الترجمة
    security_event_types_crud.delete_security_event_type_translation(db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة نوع حدث الأمان بنجاح."}