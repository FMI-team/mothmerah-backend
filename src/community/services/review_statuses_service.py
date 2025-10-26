# backend\src\community\services\review_statuses_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # ReviewStatus, ReviewStatusTranslation
# استيراد الـ CRUD
from src.lookups.crud import review_statuses_crud as crud
from src.lookups.crud import languages_crud # للتحقق من وجود اللغة (Language)
# TODO: استيراد CRUDs لـ Review للتحقق من الارتباطات (عند بناءه)
# from src.community.crud import reviews_crud


# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # ReviewStatus, ReviewStatusTranslation

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for ReviewStatus (حالات المراجعة) ---
# ==========================================================

def create_new_review_status(db: Session, status_in: schemas.ReviewStatusCreate) -> models.ReviewStatus:
    """
    خدمة لإنشاء حالة مراجعة جديدة مع ترجماتها الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas.ReviewStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        models.ReviewStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت الحالة بنفس المفتاح موجودة بالفعل.
        NotFoundException: إذا كانت اللغة المحددة للترجمة غير موجودة.
    """
    # 1. التحقق من عدم وجود حالة بنفس المفتاح
    existing_status = crud.get_review_status_by_key(db, key=status_in.status_name_key)
    if existing_status:
        raise ConflictException(detail=f"حالة المراجعة بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    
    # 2. التحقق من وجود اللغات المستخدمة في الترجمات
    if status_in.translations:
        for trans_in in status_in.translations:
            language_obj = languages_crud.get_language(db, language_code=trans_in.language_code)
            if not language_obj:
                raise NotFoundException(detail=f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    return crud.create_review_status(db=db, status_in=status_in)

def get_all_review_statuses_service(db: Session) -> List[models.ReviewStatus]:
    """خدمة لجلب قائمة بجميع حالات المراجعة."""
    return crud.get_all_review_statuses(db)

def get_review_status_details(db: Session, status_id: int) -> models.ReviewStatus:
    """
    خدمة لجلب حالة مراجعة واحد بالـ ID الخاص بها.
    """
    db_status = crud.get_review_status(db, status_id=status_id)
    if not db_status:
        raise NotFoundException(detail=f"حالة المراجعة بمعرف {status_id} غير موجودة.")
    return db_status

def update_review_status_service(db: Session, status_id: int, status_in: schemas.ReviewStatusUpdate) -> models.ReviewStatus:
    """
    خدمة لتحديث حالة مراجعة موجودة.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas.ReviewStatusUpdate): البيانات المراد تحديثها.

    Returns:
        models.ReviewStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_review_status_details(db, status_id) # استخدام دالة الخدمة للتحقق

    # 1. التحقق من تفرد المفتاح إذا تم تحديث status_name_key
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        existing_status_by_key = crud.get_review_status_by_key(db, key=status_in.status_name_key)
        if existing_status_by_key and existing_status_by_key.status_id != status_id:
            raise ConflictException(detail=f"حالة المراجعة بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")

    return crud.update_review_status(db, db_status=db_status, status_in=status_in)

def delete_review_status_service(db: Session, status_id: int):
    """
    خدمة لحذف حالة مراجعة (حذف صارم).
    تتضمن التحقق من عدم وجود مراجعات مرتبطة بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ForbiddenException: إذا كانت الحالة مستخدمة حالياً بواسطة مراجعات.
    """
    db_status = get_review_status_details(db, status_id) # استخدام دالة الخدمة للتحقق

    # TODO: التحقق من عدم وجود Review تستخدم status_id هذا
    #       هذا يتطلب CRUD لدالة count_reviews_for_status
    # reviews_count = reviews_crud.count_reviews_for_status(db, status_id)
    # if reviews_count > 0:
    #     raise ForbiddenException(detail=f"لا يمكن حذف حالة المراجعة بمعرف {status_id} لأنها تستخدم من قبل {reviews_count} مراجعة(مراجعات).")

    crud.delete_review_status(db=db, db_status=db_status)
    return {"message": f"تم حذف حالة المراجعة '{db_status.status_name_key}' بنجاح."}


# ==========================================================
# --- Services for ReviewStatusTranslation ---
# ==========================================================

def create_review_status_translation_service(db: Session, status_id: int, trans_in: schemas.ReviewStatusTranslationCreate) -> models.ReviewStatusTranslation:
    """خدمة لإنشاء ترجمة جديدة لحالة مراجعة."""
    # 1. التحقق من وجود الحالة الأم
    get_review_status_details(db, status_id)

    # 2. التحقق من وجود اللغة
    languages_crud.get_language(db, language_code=trans_in.language_code)

    # 3. التحقق من عدم وجود ترجمة بنفس اللغة
    existing_translation = crud.get_review_status_translation(db, status_id=status_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة لحالة المراجعة بمعرف {status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return crud.create_review_status_translation(db=db, status_id=status_id, trans_in=trans_in)

def get_review_status_translation_details_service(db: Session, status_id: int, language_code: str) -> models.ReviewStatusTranslation:
    """خدمة لجلب ترجمة حالة مراجعة محددة."""
    translation = crud.get_review_status_translation(db, status_id=status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة المراجعة بمعرف {status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_review_status_translation_service(db: Session, status_id: int, language_code: str, trans_in: schemas.ReviewStatusTranslationUpdate) -> models.ReviewStatusTranslation:
    """خدمة لتحديث ترجمة حالة مراجعة موجودة."""
    db_translation = get_review_status_translation_details_service(db, status_id, language_code) # التحقق من وجود الترجمة
    return crud.update_review_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def remove_review_status_translation_service(db: Session, status_id: int, language_code: str):
    """خدمة لحذف ترجمة حالة مراجعة معينة."""
    db_translation = get_review_status_translation_details_service(db, status_id, language_code) # التحقق من وجود الترجمة
    crud.delete_review_status_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة حالة المراجعة بنجاح."}