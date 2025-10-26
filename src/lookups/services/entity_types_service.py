# backend\src\lookups\services\entity_types_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # EntityTypeForReviewOrImage, EntityTypeTranslation, Language
# استيراد الـ CRUD
from src.lookups.crud import entity_types_crud # لـ EntityTypeForReviewOrImage, EntityTypeTranslation CRUDs
from src.lookups.crud import languages_crud # للتحقق من وجود اللغة (Language)
# TODO: استيراد CRUDs لـ Reviews و Images (من المجموعة 6 و 2) للتحقق من الارتباطات
# from src.reviews.crud import reviews_crud # للتحقق من Review
# from src.products.crud import image_crud # للتحقق من Image


# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # EntityTypeForReviewOrImage, EntityTypeTranslation

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for EntityTypeForReviewOrImage (أنواع الكيانات للمراجعة أو الصورة) ---
# ==========================================================

def create_new_entity_type(db: Session, type_in: schemas.EntityTypeForReviewOrImageCreate) -> models.EntityTypeForReviewOrImage:
    """
    خدمة لإنشاء نوع كيان جديد للمراجعة أو الصورة، مع ترجماته الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas.EntityTypeForReviewOrImageCreate): بيانات النوع للإنشاء.

    Returns:
        models.EntityTypeForReviewOrImage: كائن النوع الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان نوع الكيان بنفس الرمز أو المفتاح موجوداً بالفعل.
        NotFoundException: إذا كانت اللغة المحددة للترجمة غير موجودة.
    """
    # 1. التحقق من عدم وجود نوع كيان بنفس الرمز أو المفتاح
    existing_type_by_code = entity_types_crud.get_entity_type(db, entity_type_code=type_in.entity_type_code)
    if existing_type_by_code:
        raise ConflictException(detail=f"نوع الكيان بالرمز '{type_in.entity_type_code}' موجود بالفعل.")
    
    existing_type_by_key = entity_types_crud.get_entity_type_by_key(db, key=type_in.entity_type_name_key)
    if existing_type_by_key:
        raise ConflictException(detail=f"نوع الكيان بمفتاح الاسم '{type_in.entity_type_name_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود اللغات المستخدمة في الترجمات
    if type_in.translations:
        for trans_in in type_in.translations:
            language_obj = languages_crud.get_language(db, language_code=trans_in.language_code)
            if not language_obj:
                raise NotFoundException(detail=f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    return entity_types_crud.create_entity_type(db=db, type_in=type_in)

def get_all_entity_types_service(db: Session) -> List[models.EntityTypeForReviewOrImage]:
    """خدمة لجلب قائمة بجميع أنواع الكيانات للمراجعة أو الصورة."""
    return entity_types_crud.get_all_entity_types(db)

def get_entity_type_details(db: Session, entity_type_code: str) -> models.EntityTypeForReviewOrImage:
    """
    خدمة لجلب نوع كيان واحد بالرمز الخاص به، مع معالجة عدم الوجود.
    """
    db_type = entity_types_crud.get_entity_type(db, entity_type_code=entity_type_code)
    if not db_type:
        raise NotFoundException(detail=f"نوع الكيان بالرمز '{entity_type_code}' غير موجود.")
    return db_type

def update_entity_type(db: Session, entity_type_code: str, type_in: schemas.EntityTypeForReviewOrImageUpdate) -> models.EntityTypeForReviewOrImage:
    """
    خدمة لتحديث نوع كيان موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        entity_type_code (str): رمز الكيان المراد تحديثه.
        type_in (schemas.EntityTypeForReviewOrImageUpdate): البيانات المراد تحديثها.

    Returns:
        models.EntityTypeForReviewOrImage: كائن النوع المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على نوع الكيان.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_type = get_entity_type_details(db, entity_type_code=entity_type_code) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث entity_type_name_key
    if type_in.entity_type_name_key and type_in.entity_type_name_key != db_type.entity_type_name_key:
        existing_type_by_key = entity_types_crud.get_entity_type_by_key(db, key=type_in.entity_type_name_key)
        if existing_type_by_key and existing_type_by_key.entity_type_code != entity_type_code:
            raise ConflictException(detail=f"نوع الكيان بمفتاح الاسم '{type_in.entity_type_name_key}' موجود بالفعل.")

    return entity_types_crud.update_entity_type(db, db_type=db_type, type_in=type_in)

def delete_entity_type_by_code(db: Session, entity_type_code: str):
    """
    خدمة لحذف نوع كيان للمراجعة أو الصورة بشكل صارم.
    تتضمن التحقق من عدم وجود مراجعات أو صور مرتبطة به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        entity_type_code (str): رمز الكيان المراد حذفه.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على نوع الكيان.
        ConflictException: إذا كانت هناك مراجعات أو صور مرتبطة.
    """
    db_type_to_delete = get_entity_type_details(db, entity_type_code=entity_type_code) # استخدام دالة الخدمة للتحقق

    # التحقق من عدم وجود مراجعات أو صور مرتبطة بهذا النوع
    # TODO: يجب إضافة دوال count_reviews_for_entity_type و count_images_for_entity_type في CRUDs الخاصة بها (Module 6 و 2).
    # reviews_count = reviews_crud.count_reviews_for_entity_type(db, entity_type_code)
    # if reviews_count > 0:
    #     raise ConflictException(detail=f"لا يمكن حذف نوع الكيان '{entity_type_code}' لأنه مرتبط بـ {reviews_count} مراجعة(مراجعات).")
    # images_count = image_crud.count_images_for_entity_type(db, entity_type_code)
    # if images_count > 0:
    #     raise ConflictException(detail=f"لا يمكن حذف نوع الكيان '{entity_type_code}' لأنه مرتبط بـ {images_count} صورة(صور).")

    entity_types_crud.delete_entity_type(db, db_type=db_type_to_delete)
    db.commit()
    return {"message": f"تم حذف نوع الكيان '{db_type_to_delete.entity_type_name_key}' بنجاح."}


# ==========================================================
# --- Services for EntityTypeTranslation (ترجمات أنواع الكيانات) ---
# ==========================================================

def create_entity_type_translation(db: Session, entity_type_code: str, trans_in: schemas.EntityTypeTranslationCreate) -> models.EntityTypeTranslation:
    """خدمة لإنشاء ترجمة جديدة لنوع كيان."""
    # 1. التحقق من وجود النوع الأم
    get_entity_type_details(db, entity_type_code)

    # 2. التحقق من وجود اللغة
    languages_crud.get_language(db, language_code=trans_in.language_code)

    # 3. التحقق من عدم وجود ترجمة بنفس اللغة
    existing_translation = entity_types_crud.get_entity_type_translation(db, entity_type_code=entity_type_code, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة لنوع الكيان بالرمز '{entity_type_code}' باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return entity_types_crud.create_entity_type_translation(db=db, entity_type_code=entity_type_code, trans_in=trans_in)

def get_entity_type_translation_details(db: Session, entity_type_code: str, language_code: str) -> models.EntityTypeTranslation:
    """خدمة لجلب ترجمة نوع كيان محددة."""
    translation = entity_types_crud.get_entity_type_translation(db, entity_type_code=entity_type_code, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لنوع الكيان بالرمز '{entity_type_code}' باللغة '{language_code}' غير موجودة.")
    return translation

def update_entity_type_translation(db: Session, entity_type_code: str, language_code: str, trans_in: schemas.EntityTypeTranslationUpdate) -> models.EntityTypeTranslation:
    """خدمة لتحديث ترجمة نوع كيان موجودة."""
    db_translation = get_entity_type_translation_details(db, entity_type_code, language_code) # التحقق من وجود الترجمة
    return entity_types_crud.update_entity_type_translation(db, db_translation=db_translation, trans_in=trans_in)

def remove_entity_type_translation(db: Session, entity_type_code: str, language_code: str):
    """خدمة لحذف ترجمة نوع كيان معينة."""
    db_translation = get_entity_type_translation_details(db, entity_type_code, language_code) # التحقق من وجود الترجمة
    entity_types_crud.delete_entity_type_translation(db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة نوع الكيان بنجاح."}