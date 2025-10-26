# backend\src\community\services\review_report_reasons_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # ReviewReportReason, ReviewReportReasonTranslation, Language
# استيراد الـ CRUD
from src.lookups.crud import review_report_reasons_crud as crud
from src.lookups.crud import languages_crud # للتحقق من وجود اللغة (Language)
# TODO: استيراد CRUDs لـ ReviewReport للتحقق من الارتباطات (عند بناءه)
# from src.community.crud import review_reports_crud


# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # ReviewReportReason, ReviewReportReasonTranslation

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for ReviewReportReason (أسباب الإبلاغ عن المراجعات) ---
# ==========================================================

def create_new_review_report_reason(db: Session, reason_in: schemas.ReviewReportReasonCreate) -> models.ReviewReportReason:
    """
    خدمة لإنشاء سبب إبلاغ جديد عن مراجعة مع ترجماته الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        reason_in (schemas.ReviewReportReasonCreate): بيانات السبب للإنشاء.

    Returns:
        models.ReviewReportReason: كائن السبب الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان السبب بنفس المفتاح موجوداً بالفعل.
        NotFoundException: إذا كانت اللغة المحددة للترجمة غير موجودة.
    """
    # 1. التحقق من عدم وجود سبب بنفس المفتاح
    existing_reason = crud.get_review_report_reason_by_key(db, key=reason_in.reason_key)
    if existing_reason:
        raise ConflictException(detail=f"سبب الإبلاغ بمفتاح '{reason_in.reason_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود اللغات المستخدمة في الترجمات
    if reason_in.translations:
        for trans_in in reason_in.translations:
            language_obj = languages_crud.get_language(db, language_code=trans_in.language_code)
            if not language_obj:
                raise NotFoundException(detail=f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    return crud.create_review_report_reason(db=db, reason_in=reason_in)

def get_all_review_report_reasons_service(db: Session) -> List[models.ReviewReportReason]:
    """خدمة لجلب قائمة بجميع أسباب الإبلاغ عن المراجعات."""
    return crud.get_all_review_report_reasons(db)

def get_review_report_reason_details(db: Session, reason_id: int) -> models.ReviewReportReason:
    """
    خدمة لجلب سبب إبلاغ عن مراجعة واحد بالـ ID الخاص به.
    """
    db_reason = crud.get_review_report_reason(db, reason_id=reason_id)
    if not db_reason:
        raise NotFoundException(detail=f"سبب الإبلاغ بمعرف {reason_id} غير موجود.")
    return db_reason

def update_review_report_reason_service(db: Session, reason_id: int, reason_in: schemas.ReviewReportReasonUpdate) -> models.ReviewReportReason:
    """
    خدمة لتحديث سبب إبلاغ عن مراجعة موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        reason_id (int): معرف السبب المراد تحديثه.
        reason_in (schemas.ReviewReportReasonUpdate): البيانات المراد تحديثها.

    Returns:
        models.ReviewReportReason: كائن السبب المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على السبب.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_reason = get_review_report_reason_details(db, reason_id) # استخدام دالة الخدمة للتحقق

    # 1. التحقق من تفرد المفتاح إذا تم تحديث reason_key
    if reason_in.reason_key and reason_in.reason_key != db_reason.reason_key:
        existing_reason_by_key = crud.get_review_report_reason_by_key(db, key=reason_in.reason_key)
        if existing_reason_by_key and existing_reason_by_key.reason_id != reason_id:
            raise ConflictException(detail=f"سبب الإبلاغ بمفتاح '{reason_in.reason_key}' موجود بالفعل.")

    return crud.update_review_report_reason(db, db_reason=db_reason, reason_in=reason_in)

def delete_review_report_reason_service(db: Session, reason_id: int):
    """
    خدمة لحذف سبب إبلاغ عن مراجعة (حذف صارم).
    تتضمن التحقق من عدم وجود بلاغات مرتبطة بهذا السبب.

    Args:
        db (Session): جلسة قاعدة البيانات.
        reason_id (int): معرف السبب المراد حذفه.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على السبب.
        ForbiddenException: إذا كان السبب مستخدماً حالياً بواسطة بلاغات.
    """
    db_reason = get_review_report_reason_details(db, reason_id) # استخدام دالة الخدمة للتحقق

    # TODO: التحقق من عدم وجود ReviewReport تستخدم reason_id هذا
    #       هذا يتطلب CRUD لدالة count_reports_for_reason
    # reports_count = review_reports_crud.count_reports_for_reason(db, reason_id)
    # if reports_count > 0:
    #     raise ForbiddenException(detail=f"لا يمكن حذف سبب الإبلاغ بمعرف {reason_id} لأنه يستخدم من قبل {reports_count} بلاغ(بلاغات).")

    crud.delete_review_report_reason(db=db, db_reason=db_reason)
    return {"message": f"تم حذف سبب الإبلاغ '{db_reason.reason_key}' بنجاح."}


# ==========================================================
# --- Services for ReviewReportReasonTranslation ---
# ==========================================================

def create_review_report_reason_translation_service(db: Session, reason_id: int, trans_in: schemas.ReviewReportReasonTranslationCreate) -> models.ReviewReportReasonTranslation:
    """خدمة لإنشاء ترجمة جديدة لسبب إبلاغ عن مراجعة."""
    # 1. التحقق من وجود السبب الأم
    get_review_report_reason_details(db, reason_id)

    # 2. التحقق من وجود اللغة
    languages_crud.get_language(db, language_code=trans_in.language_code)

    # 3. التحقق من عدم وجود ترجمة بنفس اللغة
    existing_translation = crud.get_review_report_reason_translation(db, reason_id=reason_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة لسبب الإبلاغ بمعرف {reason_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return crud.create_review_report_reason_translation(db=db, reason_id=reason_id, trans_in=trans_in)

def get_review_report_reason_translation_details_service(db: Session, reason_id: int, language_code: str) -> models.ReviewReportReasonTranslation:
    """خدمة لجلب ترجمة سبب إبلاغ عن مراجعة محددة."""
    translation = crud.get_review_report_reason_translation(db, reason_id=reason_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لسبب الإبلاغ بمعرف {reason_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_review_report_reason_translation_service(db: Session, reason_id: int, language_code: str, trans_in: schemas.ReviewReportReasonTranslationUpdate) -> models.ReviewReportReasonTranslation:
    """خدمة لتحديث ترجمة سبب إبلاغ عن مراجعة موجودة."""
    db_translation = get_review_report_reason_translation_details_service(db, reason_id, language_code) # التحقق من وجود الترجمة
    return crud.update_review_report_reason_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def remove_review_report_reason_translation_service(db: Session, reason_id: int, language_code: str):
    """خدمة لحذف ترجمة سبب إبلاغ عن مراجعة معينة."""
    db_translation = get_review_report_reason_translation_details_service(db, reason_id, language_code) # التحقق من وجود الترجمة
    crud.delete_review_report_reason_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة سبب الإبلاغ بنجاح."}