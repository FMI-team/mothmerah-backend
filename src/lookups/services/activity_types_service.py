# backend\src\lookups\services\activity_types_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # ActivityType, ActivityTypeTranslation, Language
# استيراد الـ CRUD
from src.lookups.crud import activity_types_crud # لـ ActivityType, ActivityTypeTranslation CRUDs
from src.lookups.crud import languages_crud # للتحقق من وجود اللغة (Language)
# TODO: استيراد CRUDs لـ UserActivityLog (من المجموعة 13) للتحقق من الارتباطات
# from src.audit.crud import user_activity_logs_crud # للتحقق من UserActivityLog


# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # ActivityType, ActivityTypeTranslation

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for ActivityType (أنواع الأنشطة) ---
# ==========================================================

def create_new_activity_type(db: Session, type_in: schemas.ActivityTypeCreate) -> models.ActivityType:
    """
    خدمة لإنشاء نوع نشاط جديد مع ترجماته الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas.ActivityTypeCreate): بيانات النوع للإنشاء.

    Returns:
        models.ActivityType: كائن النوع الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان نوع النشاط بمفتاح معين موجوداً بالفعل.
        NotFoundException: إذا كانت اللغة المحددة للترجمة غير موجودة.
    """
    # 1. التحقق من عدم وجود نوع نشاط بنفس المفتاح
    existing_type = activity_types_crud.get_activity_type_by_key(db, key=type_in.activity_name_key)
    if existing_type:
        raise ConflictException(detail=f"نوع النشاط بمفتاح '{type_in.activity_name_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود اللغات المستخدمة في الترجمات
    if type_in.translations:
        for trans_in in type_in.translations:
            language_obj = languages_crud.get_language(db, language_code=trans_in.language_code)
            if not language_obj:
                raise NotFoundException(detail=f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    return activity_types_crud.create_activity_type(db=db, type_in=type_in)

def get_all_activity_types_service(db: Session) -> List[models.ActivityType]:
    """خدمة لجلب قائمة بجميع أنواع الأنشطة."""
    return activity_types_crud.get_all_activity_types(db)

def get_activity_type_details(db: Session, type_id: int) -> models.ActivityType:
    """
    خدمة لجلب نوع نشاط واحد بالـ ID الخاص به، مع معالجة عدم الوجود.
    """
    db_type = activity_types_crud.get_activity_type(db, type_id=type_id)
    if not db_type:
        raise NotFoundException(detail=f"نوع النشاط بمعرف {type_id} غير موجود.")
    return db_type

def update_activity_type(db: Session, type_id: int, type_in: schemas.ActivityTypeUpdate) -> models.ActivityType:
    """
    خدمة لتحديث نوع نشاط موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع المراد تحديثه.
        type_in (schemas.ActivityTypeUpdate): البيانات المراد تحديثها.

    Returns:
        models.ActivityType: كائن النوع المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_type = get_activity_type_details(db, type_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث activity_name_key
    if type_in.activity_name_key and type_in.activity_name_key != db_type.activity_name_key:
        existing_type_by_key = activity_types_crud.get_activity_type_by_key(db, key=type_in.activity_name_key)
        if existing_type_by_key and existing_type_by_key.activity_type_id != type_id:
            raise ConflictException(detail=f"نوع النشاط بمفتاح '{type_in.activity_name_key}' موجود بالفعل.")

    return activity_types_crud.update_activity_type(db, db_type=db_type, type_in=type_in)

def delete_activity_type_by_id(db: Session, type_id: int):
    """
    خدمة لحذف نوع نشاط بشكل صارم.
    تتضمن التحقق من عدم وجود سجلات أنشطة مستخدم مرتبطة به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع المراد حذفه.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
        ConflictException: إذا كانت هناك سجلات أنشطة مرتبطة.
    """
    db_type_to_delete = get_activity_type_details(db, type_id) # استخدام دالة الخدمة للتحقق

    # التحقق من عدم وجود سجلات أنشطة مستخدم مرتبطة بهذا النوع (من المجموعة 13)
    # TODO: يجب إضافة دالة count_user_activity_logs_for_type في user_activity_logs_crud
    # user_activity_logs_count = user_activity_logs_crud.count_user_activity_logs_for_type(db, type_id)
    # if user_activity_logs_count > 0:
    #     raise ConflictException(detail=f"لا يمكن حذف نوع النشاط بمعرف {type_id} لأنه مرتبط بـ {user_activity_logs_count} سجل(سجلات) أنشطة مستخدم.")

    activity_types_crud.delete_activity_type(db, db_type=db_type_to_delete)
    db.commit()
    return {"message": f"تم حذف نوع النشاط '{db_type_to_delete.activity_name_key}' بنجاح."}


# ==========================================================
# --- Services for ActivityTypeTranslation (ترجمات أنواع الأنشطة) ---
# ==========================================================

def create_activity_type_translation(db: Session, activity_type_id: int, trans_in: schemas.ActivityTypeTranslationCreate) -> models.ActivityTypeTranslation:
    """خدمة لإنشاء ترجمة جديدة لنوع نشاط."""
    # 1. التحقق من وجود النوع الأم
    get_activity_type_details(db, activity_type_id)

    # 2. التحقق من وجود اللغة
    languages_crud.get_language(db, language_code=trans_in.language_code)

    # 3. التحقق من عدم وجود ترجمة بنفس اللغة
    existing_translation = activity_types_crud.get_activity_type_translation(db, activity_type_id=activity_type_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة لنوع النشاط بمعرف {activity_type_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return activity_types_crud.create_activity_type_translation(db=db, activity_type_id=activity_type_id, trans_in=trans_in)

def get_activity_type_translation_details(db: Session, activity_type_id: int, language_code: str) -> models.ActivityTypeTranslation:
    """خدمة لجلب ترجمة نوع نشاط محددة."""
    translation = activity_types_crud.get_activity_type_translation(db, activity_type_id=activity_type_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لنوع النشاط بمعرف {activity_type_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_activity_type_translation(db: Session, activity_type_id: int, language_code: str, trans_in: schemas.ActivityTypeTranslationUpdate) -> models.ActivityTypeTranslation:
    """خدمة لتحديث ترجمة نوع نشاط موجودة."""
    db_translation = get_activity_type_translation_details(db, activity_type_id, language_code) # التحقق من وجود الترجمة
    return activity_types_crud.update_activity_type_translation(db, db_translation=db_translation, trans_in=trans_in)

def remove_activity_type_translation(db: Session, activity_type_id: int, language_code: str):
    """خدمة لحذف ترجمة نوع نشاط معينة."""
    db_translation = get_activity_type_translation_details(db, activity_type_id, language_code) # التحقق من وجود الترجمة
    activity_types_crud.delete_activity_type_translation(db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة نوع النشاط بنجاح."}