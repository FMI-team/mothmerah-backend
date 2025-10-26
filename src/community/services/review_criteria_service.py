# backend\src\community\services\review_criteria_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID # إذا تم استخدام user_id
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # ReviewCriterion, ReviewCriterionTranslation
# استيراد الـ CRUD
from src.lookups.crud import review_criteria_crud # لـ ReviewCriterion, ReviewCriterionTranslation CRUDs
from src.lookups.crud import languages_crud # للتحقق من وجود اللغة (Language)
from src.lookups.crud import entity_types_crud # للتحقق من وجود نوع الكيان (EntityTypeForReviewOrImage)
# TODO: استيراد CRUDs لـ ReviewRatingsByCriterion للتحقق من الارتباطات (عند بناءه)
# from src.community.crud import review_ratings_by_criteria_crud


# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # ReviewCriterion, ReviewCriterionTranslation

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for ReviewCriterion (معايير التقييم) ---
# ==========================================================

def create_new_review_criterion(db: Session, criterion_in: schemas.ReviewCriterionCreate) -> models.ReviewCriterion:
    """
    خدمة لإنشاء معيار تقييم جديد مع ترجماته الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        criterion_in (schemas.ReviewCriterionCreate): بيانات المعيار للإنشاء.

    Returns:
        models.ReviewCriterion: كائن المعيار الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان المعيار بنفس المفتاح موجوداً بالفعل.
        NotFoundException: إذا كانت اللغة المحددة للترجمة أو نوع الكيان غير موجود.
    """
    # 1. التحقق من عدم وجود معيار بنفس المفتاح
    existing_criterion = crud.get_review_criterion_by_key(db, key=criterion_in.criteria_name_key)
    if existing_criterion:
        raise ConflictException(detail=f"معيار التقييم بمفتاح '{criterion_in.criteria_name_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود نوع الكيان المرتبط (إذا كان موجوداً)
    if criterion_in.applicable_entity_type_code:
        entity_type_obj = entity_types_crud.get_entity_type(db, entity_type_code=criterion_in.applicable_entity_type_code)
        if not entity_type_obj:
            raise NotFoundException(detail=f"نوع الكيان '{criterion_in.applicable_entity_type_code}' غير موجود لنوع المعيار.")
    
    # 3. التحقق من وجود اللغات المستخدمة في الترجمات
    if criterion_in.translations:
        for trans_in in criterion_in.translations:
            language_obj = languages_crud.get_language(db, language_code=trans_in.language_code)
            if not language_obj:
                raise NotFoundException(detail=f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    return crud.create_review_criterion(db=db, criterion_in=criterion_in)

def get_all_review_criteria_service(db: Session, is_active: Optional[bool] = None, applicable_entity_type_code: Optional[str] = None) -> List[models.ReviewCriterion]:
    """خدمة لجلب قائمة بجميع معايير التقييم."""
    return crud.get_all_review_criteria(db, is_active=is_active, applicable_entity_type_code=applicable_entity_type_code)

def get_review_criterion_details(db: Session, criteria_id: int) -> models.ReviewCriterion:
    """
    خدمة لجلب معيار تقييم واحد بالـ ID الخاص به.
    """
    db_criterion = crud.get_review_criterion(db, criteria_id=criteria_id)
    if not db_criterion:
        raise NotFoundException(detail=f"معيار التقييم بمعرف {criteria_id} غير موجود.")
    return db_criterion

def update_review_criterion_service(db: Session, criteria_id: int, criterion_in: schemas.ReviewCriterionUpdate) -> models.ReviewCriterion:
    """
    خدمة لتحديث معيار تقييم موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره، ووجود نوع الكيان الجديد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        criteria_id (int): معرف المعيار المراد تحديثه.
        criterion_in (schemas.ReviewCriterionUpdate): البيانات المراد تحديثها.

    Returns:
        models.ReviewCriterion: كائن المعيار المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على المعيار أو نوع الكيان الجديد.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_criterion = get_review_criterion_details(db, criteria_id) # استخدام دالة الخدمة للتحقق

    # 1. التحقق من تفرد المفتاح إذا تم تحديث criteria_name_key
    if criterion_in.criteria_name_key and criterion_in.criteria_name_key != db_criterion.criteria_name_key:
        existing_criterion_by_key = crud.get_review_criterion_by_key(db, key=criterion_in.criteria_name_key)
        if existing_criterion_by_key and existing_criterion_by_key.criteria_id != criteria_id:
            raise ConflictException(detail=f"معيار التقييم بمفتاح '{criterion_in.criteria_name_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود نوع الكيان الجديد (إذا تم تحديثه)
    if criterion_in.applicable_entity_type_code and criterion_in.applicable_entity_type_code != db_criterion.applicable_entity_type_code:
        entity_type_obj = entity_types_crud.get_entity_type(db, entity_type_code=criterion_in.applicable_entity_type_code)
        if not entity_type_obj:
            raise NotFoundException(detail=f"نوع الكيان '{criterion_in.applicable_entity_type_code}' غير موجود لنوع المعيار.")

    return crud.update_review_criterion(db, db_criterion=db_criterion, criterion_in=criterion_in)

def delete_review_criterion_service(db: Session, criteria_id: int):
    """
    خدمة لحذف معيار تقييم (حذف صارم).
    تتضمن التحقق من عدم وجود تقييمات مرتبطة بهذا المعيار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        criteria_id (int): معرف المعيار المراد حذفه.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على المعيار.
        ForbiddenException: إذا كان المعيار مستخدماً حالياً بواسطة تقييمات.
    """
    db_criterion = get_review_criterion_details(db, criteria_id) # استخدام دالة الخدمة للتحقق

    # TODO: التحقق من عدم وجود ReviewRatingByCriterion تستخدم criteria_id هذا
    #       هذا يتطلب CRUD لدالة count_ratings_for_criterion
    # ratings_count = review_ratings_by_criteria_crud.count_ratings_for_criterion(db, criteria_id)
    # if ratings_count > 0:
    #     raise ForbiddenException(detail=f"لا يمكن حذف معيار التقييم بمعرف {criteria_id} لأنه يستخدم من قبل {ratings_count} تقييم(تقييمات).")

    crud.delete_review_criterion(db=db, db_criterion=db_criterion)
    return {"message": f"تم حذف معيار التقييم '{db_criterion.criteria_name_key}' بنجاح."}


# ==========================================================
# --- Services for ReviewCriterionTranslation ---
# ==========================================================

def create_review_criterion_translation_service(db: Session, criteria_id: int, trans_in: schemas.ReviewCriterionTranslationCreate) -> models.ReviewCriterionTranslation:
    """خدمة لإنشاء ترجمة جديدة لمعيار تقييم."""
    # 1. التحقق من وجود المعيار الأم
    get_review_criterion_details(db, criteria_id)

    # 2. التحقق من وجود اللغة
    languages_crud.get_language(db, language_code=trans_in.language_code)

    # 3. التحقق من عدم وجود ترجمة بنفس اللغة
    existing_translation = crud.get_review_criterion_translation(db, criteria_id=criteria_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة لمعيار التقييم بمعرف {criteria_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return crud.create_review_criterion_translation(db=db, criteria_id=criteria_id, trans_in=trans_in)

def get_review_criterion_translation_details_service(db: Session, criteria_id: int, language_code: str) -> models.ReviewCriterionTranslation:
    """خدمة لجلب ترجمة معيار تقييم محددة."""
    translation = crud.get_review_criterion_translation(db, criteria_id=criteria_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لمعيار التقييم بمعرف {criteria_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_review_criterion_translation_service(db: Session, criteria_id: int, language_code: str, trans_in: schemas.ReviewCriterionTranslationUpdate) -> models.ReviewCriterionTranslation:
    """خدمة لتحديث ترجمة معيار تقييم موجودة."""
    db_translation = get_review_criterion_translation_details_service(db, criteria_id, language_code) # التحقق من وجود الترجمة
    return crud.update_review_criterion_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def remove_review_criterion_translation_service(db: Session, criteria_id: int, language_code: str):
    """خدمة لحذف ترجمة معيار تقييم معينة."""
    db_translation = get_review_criterion_translation_details_service(db, criteria_id, language_code) # التحقق من وجود الترجمة
    crud.delete_review_criterion_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة معيار التقييم بنجاح."}