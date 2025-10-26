# backend\src\users\services\verification_service.py

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, date, timezone

# استيراد المودلز
from src.users.models import verification_models as models # LicenseType, IssuingAuthority, License, UserVerificationStatus, LicenseVerificationStatus, UserVerificationHistory, ManualVerificationLog
from src.users.models.core_models import User # لـ User في العلاقات (changed_by_user, reviewer_user, user_id)

# استيراد الـ CRUD
from src.users.crud import license_crud # لـ License CRUDs
from src.users.crud import user_lookups_crud # لـ UserVerificationStatus CRUDs (كانت هنا سابقا)
from src.users.crud import verification_history_log_crud # لـ UserVerificationHistory, ManualVerificationLog CRUDs
# TODO: استيراد CRUDs لـ LicenseType, IssuingAuthority, LicenseVerificationStatus
#      لأنها الآن في verification_lookups_crud.py (أو user_lookups_crud.py)
#       سنستخدم user_lookups_crud لـ UserVerificationStatus
#       وسنستخدم license_crud لتوابع LicenseType, IssuingAuthority, LicenseVerificationStatus (بافتراض أنها تتبع هذا النمط)
#       أو يجب إنشاء verification_lookups_crud.py جديد لها.
#       بناءً على التخطيط السابق، تم نقلها إلى user_lookups_crud.py.
#       لا، الخطة الأخيرة كانت وضعها في verification_lookups_schemas.py و CRUDs في user_lookups_crud.py أو management_crud.py.
#       للتوضيح:
#       - UserVerificationStatus CRUDs هي في user_lookups_crud.py.
#       - LicenseType, IssuingAuthority, LicenseVerificationStatus CRUDs هي في management_crud.py سابقا.
#       - بما أن management_crud.py حُذف، سنضعهم في ملف CRUD جديد اسمه verification_lookups_crud.py
#       - سأقوم بتضمين هذا الاستيراد هنا:
from src.users.crud import user_lookups_crud # for UserVerificationStatus CRUDs
# TODO: يجب استيراد هذه الدوال من ملفات CRUD المناسبة بعد إنشائها.
#       لتسهيل الأمر سأفترض وجودها في user_lookups_crud مؤقتًا لحين تنظيم CRUD بشكل أفضل.


# استيراد Schemas
from src.users.schemas import license_schemas as schemas # License Schemas
from src.users.schemas import verification_lookups_schemas as schemas_lookups # LicenseType, IssuingAuthority, UserVerificationStatus, LicenseVerificationStatus Schemas

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود
from src.users.services.core_service import get_user_profile # للتحقق من وجود المستخدم (get_user_profile(db, user_id))
from src.users.services.address_lookups_service import get_country_by_code_service # لـ country_code في IssuingAuthority
# TODO: خدمة تخزين الملفات السحابية (مثلاً من Module 2.ج - image_service)
# TODO: خدمة الإشعارات (notifications_service) من Module 11 لإرسال التنبيهات.
# TODO: خدمة التكامل مع APIs الجهات الحكومية (مثلاً من Module 14 أو Integration Service).



# TODO: يجب إضافة CRUDs لـ LicenseType, IssuingAuthority, LicenseVerificationStatus من ملفات CRUD المناسبة بعد إنشائها.
#       بما أن user_lookups_crud.py يحتوي على UserVerificationStatus CRUDs، سننشئ ملفاً جديداً لـ LicenseType و IssuingAuthority و LicenseVerificationStatus.
#       لنقم بتضمينها هنا مؤقتاً بالاعتماد على وجودها في ملفات CRUD منفصلة.
#       سأفترض أنك قمت بإنشاء verification_lookups_crud.py ووضعت فيه CRUDs لـ LicenseType, IssuingAuthority, LicenseVerificationStatus
#       لذلك سأقوم بالاستيراد منه:
from src.users.crud import verification_lookups_crud # لـ LicenseType, IssuingAuthority, LicenseVerificationStatus CRUDs





# ==========================================================
# --- Services for LicenseType Management (إدارة أنواع التراخيص) ---
# ==========================================================

def create_new_license_type(db: Session, type_in: schemas_lookups.LicenseTypeCreate) -> models.LicenseType:
    """
    خدمة لإنشاء نوع ترخيص جديد مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas_lookups.LicenseTypeCreate): بيانات النوع للإنشاء.

    Returns:
        models.LicenseType: كائن النوع الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان نوع الترخيص بمفتاح معين موجوداً بالفعل.
    """
    # 1. التحقق من عدم وجود نوع ترخيص بنفس المفتاح
    # TODO: يجب استخدام دالة CRUD من user_lookups_crud أو crud مخصص لأنواع التراخيص
    existing_type = db.query(models.LicenseType).filter(models.LicenseType.license_type_name_key == type_in.license_type_name_key).first()
    if existing_type:
        raise ConflictException(detail=f"نوع الترخيص بمفتاح '{type_in.license_type_name_key}' موجود بالفعل.")
    
    # 2. استدعاء CRUD لإنشاء النوع
    # TODO: يجب استدعاء دالة CRUD create_license_type من user_lookups_crud أو crud مخصص.
    # حالياً، لا توجد هذه الدوال في user_lookups_crud.py، يجب إضافتها هناك.
    db_type = models.LicenseType(**type_in.model_dump(exclude={"translations"}))
    if type_in.translations:
        for trans in type_in.translations:
            db_type.translations.append(models.LicenseTypeTranslation(**trans.model_dump()))
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type


def get_all_license_types_service(db: Session) -> List[models.LicenseType]:
    """خدمة لجلب جميع أنواع التراخيص."""
    # TODO: يجب استدعاء دالة CRUD get_all_license_types من user_lookups_crud أو crud مخصص.
    return db.query(models.LicenseType).options(joinedload(models.LicenseType.translations)).all()

def get_license_type_by_id_service(db: Session, type_id: int) -> models.LicenseType:
    """
    خدمة لجلب نوع ترخيص واحد بالـ ID، مع معالجة عدم الوجود.
    """
    # TODO: يجب استدعاء دالة CRUD get_license_type من user_lookups_crud أو crud مخصص.
    db_type = db.query(models.LicenseType).options(joinedload(models.LicenseType.translations)).filter(models.LicenseType.license_type_id == type_id).first()
    if not db_type:
        raise NotFoundException(detail=f"نوع الترخيص بمعرف {type_id} غير موجود.")
    return db_type

def update_license_type(db: Session, type_id: int, type_in: schemas_lookups.LicenseTypeUpdate) -> models.LicenseType:
    """
    خدمة لتحديث نوع ترخيص موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.
    """
    db_type = get_license_type_by_id_service(db, type_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث license_type_name_key
    if type_in.license_type_name_key and type_in.license_type_name_key != db_type.license_type_name_key:
        # TODO: يجب استخدام دالة CRUD get_license_type_by_key من user_lookups_crud أو crud مخصص.
        existing_type_by_key = db.query(models.LicenseType).filter(models.LicenseType.license_type_name_key == type_in.license_type_name_key).first()
        if existing_type_by_key and existing_type_by_key.license_type_id != type_id:
            raise ConflictException(detail=f"نوع الترخيص بمفتاح '{type_in.license_type_name_key}' موجود بالفعل.")

    # TODO: يجب استدعاء دالة CRUD update_license_type من user_lookups_crud أو crud مخصص.
    update_data = type_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_type, key, value)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def delete_license_type_by_id(db: Session, type_id: int):
    """
    خدمة لحذف نوع ترخيص بشكل آمن (حذف صارم).
    تتضمن التحقق من عدم وجود تراخيص فعلية تستخدم هذا النوع.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع المراد حذفه.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
        ConflictException: إذا كانت هناك تراخيص مرتبطة.
    """
    db_type_to_delete = get_license_type_by_id_service(db, type_id) # استخدام دالة الخدمة للتحقق

    # التحقق من عدم وجود تراخيص فعلية تستخدم هذا النوع
    # TODO: يجب استدعاء دالة CRUD count_licenses_for_license_type من license_crud
    license_count = db.query(models.License).filter(models.License.license_type_id == type_id).count() # مؤقتاً
    if license_count > 0:
        raise ConflictException(detail=f"لا يمكن حذف نوع الترخيص بمعرف {type_id} لأنه مرتبط بـ {license_count} ترخيص(تراخيص) فعال(ة).")

    # TODO: يجب استدعاء دالة CRUD delete_license_type من user_lookups_crud أو crud مخصص.
    db.delete(db_type_to_delete)
    db.commit()
    return {"message": f"تم حذف نوع الترخيص '{db_type_to_delete.license_type_name_key}' بنجاح."}

# --- خدمات إدارة الترجمات لنوع الترخيص ---

def create_license_type_translation(db: Session, type_id: int, trans_in: schemas_lookups.LicenseTypeTranslationCreate) -> models.LicenseType:
    """خدمة لإنشاء ترجمة جديدة لنوع ترخيص."""
    db_type = get_license_type_by_id_service(db, type_id) # التحقق من وجود النوع الأم

    # التحقق من عدم وجود ترجمة بنفس اللغة
    # TODO: يجب استدعاء دالة CRUD get_license_type_translation من user_lookups_crud أو crud مخصص.
    existing_translation = db.query(models.LicenseTypeTranslation).filter(
        models.LicenseTypeTranslation.license_type_id == type_id,
        models.LicenseTypeTranslation.language_code == trans_in.language_code
    ).first()
    if existing_translation:
        raise ConflictException(detail=f"الترجمة لنوع الترخيص بمعرف {type_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    # TODO: يجب استدعاء دالة CRUD add_or_update_license_type_translation من user_lookups_crud أو crud مخصص.
    db_translation = models.LicenseTypeTranslation(**trans_in.model_dump(), license_type_id=type_id)
    db.add(db_translation)
    db.commit()
    db.refresh(db_type) # تحديث النوع الأم لتحميل الترجمات الجديدة
    return db_type

def get_license_type_translation_details(db: Session, type_id: int, language_code: str) -> models.LicenseTypeTranslation:
    """خدمة لجلب ترجمة نوع ترخيص محددة."""
    # TODO: يجب استدعاء دالة CRUD get_license_type_translation من user_lookups_crud أو crud مخصص.
    translation = db.query(models.LicenseTypeTranslation).filter(
        models.LicenseTypeTranslation.license_type_id == type_id,
        models.LicenseTypeTranslation.language_code == language_code
    ).first()
    if not translation:
        raise NotFoundException(detail=f"الترجمة لنوع الترخيص بمعرف {type_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_license_type_translation(db: Session, type_id: int, language_code: str, trans_in: schemas_lookups.LicenseTypeTranslationUpdate) -> models.LicenseType:
    """خدمة لتحديث ترجمة نوع ترخيص موجودة."""
    db_translation = get_license_type_translation_details(db, type_id, language_code) # التحقق من وجود الترجمة
    # TODO: يجب استدعاء دالة CRUD add_or_update_license_type_translation أو update_license_type_translation.
    db_translation.translated_license_type_name = trans_in.translated_license_type_name
    db_translation.translated_description = trans_in.translated_description
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation.license_type) # تحديث النوع الأم لتحميل الترجمات الجديدة
    return db_translation.license_type

def remove_license_type_translation(db: Session, type_id: int, language_code: str):
    """خدمة لحذف ترجمة معينة لنوع ترخيص."""
    db_translation = get_license_type_translation_details(db, type_id, language_code) # التحقق من وجود الترجمة
    # TODO: يجب استدعاء دالة CRUD delete_license_type_translation من user_lookups_crud أو crud مخصص.
    db.delete(db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة نوع الترخيص بنجاح."}


# ==========================================================
# --- Services for IssuingAuthority Management (إدارة الجهات المصدرة للتراخيص) ---
# ==========================================================

def create_new_issuing_authority(db: Session, authority_in: schemas_lookups.IssuingAuthorityCreate) -> models.IssuingAuthority:
    """
    خدمة لإنشاء جهة إصدار جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        authority_in (schemas_lookups.IssuingAuthorityCreate): بيانات الجهة للإنشاء.

    Returns:
        models.IssuingAuthority: كائن الجهة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت الجهة بنفس المفتاح موجودة بالفعل.
        NotFoundException: إذا كانت الدولة المرتبطة غير موجودة.
    """
    # 1. التحقق من عدم وجود الجهة بنفس المفتاح
    # TODO: يجب استخدام دالة CRUD get_issuing_authority_by_key
    existing_authority = db.query(models.IssuingAuthority).filter(models.IssuingAuthority.authority_name_key == authority_in.authority_name_key).first()
    if existing_authority:
        raise ConflictException(detail=f"الجهة المصدرة بمفتاح '{authority_in.authority_name_key}' موجودة بالفعل.")
    
    # 2. التحقق من وجود الدولة المرتبطة
    # TODO: يجب استيراد get_country_by_code_service من address_lookups_service
    # from src.users.services.address_lookups_service import get_country_by_code_service
    get_country_by_code_service(db, authority_in.country_code)

    # 3. استدعاء CRUD لإنشاء الجهة
    # TODO: يجب استدعاء دالة CRUD create_issuing_authority
    db_authority = models.IssuingAuthority(**authority_in.model_dump(exclude={"translations"}))
    if authority_in.translations:
        for trans in authority_in.translations:
            db_authority.translations.append(models.IssuingAuthorityTranslation(**trans.model_dump()))
    db.add(db_authority)
    db.commit()
    db.refresh(db_authority)
    return db_authority

def get_all_issuing_authorities_service(db: Session) -> List[models.IssuingAuthority]:
    """خدمة لجلب جميع الجهات المصدرة للتراخيص."""
    # TODO: يجب استدعاء دالة CRUD get_all_issuing_authorities
    return db.query(models.IssuingAuthority).options(joinedload(models.IssuingAuthority.translations)).all()

def get_issuing_authority_details(db: Session, authority_id: int) -> models.IssuingAuthority:
    """
    خدمة لجلب جهة إصدار واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    # TODO: يجب استدعاء دالة CRUD get_issuing_authority
    db_authority = db.query(models.IssuingAuthority).options(joinedload(models.IssuingAuthority.translations)).filter(models.IssuingAuthority.authority_id == authority_id).first()
    if not db_authority:
        raise NotFoundException(detail=f"الجهة المصدرة بمعرف {authority_id} غير موجودة.")
    return db_authority

def update_issuing_authority(db: Session, authority_id: int, authority_in: schemas_lookups.IssuingAuthorityUpdate) -> models.IssuingAuthority:
    """
    خدمة لتحديث جهة إصدار موجودة.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره، والتحقق من وجود الدولة الجديدة إن وجدت.
    """
    db_authority = get_issuing_authority_details(db, authority_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث authority_name_key
    if authority_in.authority_name_key and authority_in.authority_name_key != db_authority.authority_name_key:
        # TODO: يجب استخدام دالة CRUD get_issuing_authority_by_key
        existing_authority_by_key = db.query(models.IssuingAuthority).filter(models.IssuingAuthority.authority_name_key == authority_in.authority_name_key).first()
        if existing_authority_by_key and existing_authority_by_key.authority_id != authority_id:
            raise ConflictException(detail=f"الجهة المصدرة بمفتاح '{authority_in.authority_name_key}' موجودة بالفعل.")
    
    # التحقق من وجود الدولة الجديدة إذا تم تغيير country_code
    if authority_in.country_code and authority_in.country_code != db_authority.country_code:
        get_country_by_code_service(db, authority_in.country_code)

    # TODO: يجب استدعاء دالة CRUD update_issuing_authority
    update_data = authority_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_authority, key, value)
    db.add(db_authority)
    db.commit()
    db.refresh(db_authority)
    return db_authority

def delete_issuing_authority_by_id(db: Session, authority_id: int):
    """
    خدمة للحذف الآمن لجهة إصدار.
    تتضمن التحقق من عدم وجود تراخيص فعلية تستخدم هذه الجهة.
    """
    db_authority = get_issuing_authority_details(db, authority_id) # استخدام دالة الخدمة للتحقق

    # التحقق من عدم وجود تراخيص فعلية تستخدم هذه الجهة
    # TODO: يجب استدعاء دالة CRUD count_licenses_for_issuing_authority من license_crud
    license_count = db.query(models.License).filter(models.License.issuing_authority_id == authority_id).count() # مؤقتاً
    if license_count > 0:
        raise ConflictException(detail=f"لا يمكن حذف الجهة المصدرة بمعرف {authority_id} لأنها مرتبطة بـ {license_count} ترخيص(تراخيص) فعال(ة).")

    # TODO: يجب استدعاء دالة CRUD delete_issuing_authority
    db.delete(db_authority)
    db.commit()
    return {"message": f"تم حذف الجهة المصدرة '{db_authority.authority_name_key}' بنجاح."}

# --- خدمات إدارة الترجمات للجهة المصدرة ---

def create_issuing_authority_translation(db: Session, authority_id: int, trans_in: schemas_lookups.IssuingAuthorityTranslationCreate) -> models.IssuingAuthority:
    """خدمة لإنشاء ترجمة جديدة لجهة إصدار."""
    db_authority = get_issuing_authority_details(db, authority_id) # التحقق من وجود الجهة الأم

    # التحقق من عدم وجود ترجمة بنفس اللغة
    # TODO: يجب استدعاء دالة CRUD get_issuing_authority_translation
    existing_translation = db.query(models.IssuingAuthorityTranslation).filter(
        models.IssuingAuthorityTranslation.authority_id == authority_id,
        models.IssuingAuthorityTranslation.language_code == trans_in.language_code
    ).first()
    if existing_translation:
        raise ConflictException(detail=f"الترجمة للجهة المصدرة بمعرف {authority_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    # TODO: يجب استدعاء دالة CRUD add_or_update_issuing_authority_translation
    db_translation = models.IssuingAuthorityTranslation(**trans_in.model_dump(), authority_id=authority_id)
    db.add(db_translation)
    db.commit()
    db.refresh(db_authority)
    return db_authority

def get_issuing_authority_translation_details(db: Session, authority_id: int, language_code: str) -> models.IssuingAuthorityTranslation:
    """خدمة لجلب ترجمة جهة إصدار محددة."""
    # TODO: يجب استدعاء دالة CRUD get_issuing_authority_translation
    translation = db.query(models.IssuingAuthorityTranslation).filter(
        models.IssuingAuthorityTranslation.authority_id == authority_id,
        models.IssuingAuthorityTranslation.language_code == language_code
    ).first()
    if not translation:
        raise NotFoundException(detail=f"الترجمة للجهة المصدرة بمعرف {authority_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_issuing_authority_translation(db: Session, authority_id: int, language_code: str, trans_in: schemas_lookups.IssuingAuthorityTranslationUpdate) -> models.IssuingAuthority:
    """خدمة لتحديث ترجمة جهة إصدار موجودة."""
    db_translation = get_issuing_authority_translation_details(db, authority_id, language_code) # التحقق من وجود الترجمة
    # TODO: يجب استدعاء دالة CRUD add_or_update_issuing_authority_translation أو update_issuing_authority_translation.
    db_translation.translated_authority_name = trans_in.translated_authority_name
    db_translation.translated_description = trans_in.translated_description
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation.issuing_authority)
    return db_translation.issuing_authority

def remove_issuing_authority_translation(db: Session, authority_id: int, language_code: str):
    """خدمة لحذف ترجمة جهة إصدار معينة."""
    db_translation = get_issuing_authority_translation_details(db, authority_id, language_code) # التحقق من وجود الترجمة
    # TODO: يجب استدعاء دالة CRUD delete_issuing_authority_translation
    db.delete(db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة الجهة المصدرة بنجاح."}


# ================================================================
# --- Services for UserVerificationStatus Management (إدارة حالات التحقق من المستخدم) ---
# ================================================================

def create_new_user_verification_status(db: Session, status_in: schemas_lookups.UserVerificationStatusCreate) -> models.UserVerificationStatus:
    """
    خدمة لإنشاء حالة تحقق مستخدم جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas_lookups.UserVerificationStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        models.UserVerificationStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    # 1. التحقق من عدم وجود حالة تحقق بنفس المفتاح
    existing_status = user_lookups_crud.get_user_verification_status_by_key(db, key=status_in.status_name_key)
    if existing_status:
        raise ConflictException(detail=f"حالة التحقق من المستخدم بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")

    # 2. استدعاء CRUD لإنشاء الحالة
    return user_lookups_crud.create_user_verification_status(db, status_in=status_in)

def get_all_user_verification_statuses_service(db: Session) -> List[models.UserVerificationStatus]:
    """خدمة لجلب كل حالات التحقق من المستخدم مع ترجماتهم."""
    return user_lookups_crud.get_all_user_verification_statuses(db)

def get_user_verification_status_details_service(db: Session, user_verification_status_id: int) -> models.UserVerificationStatus:
    """
    خدمة لجلب حالة تحقق مستخدم واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    db_status = user_lookups_crud.get_user_verification_status(db, user_verification_status_id=user_verification_status_id)
    if not db_status:
        raise NotFoundException(detail=f"حالة التحقق من المستخدم بمعرف {user_verification_status_id} غير موجودة.")
    return db_status

def update_user_verification_status(db: Session, user_verification_status_id: int, status_in: schemas_lookups.UserVerificationStatusUpdate) -> models.UserVerificationStatus:
    """
    خدمة لتحديث حالة تحقق مستخدم موجودة.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_verification_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas_lookups.UserVerificationStatusUpdate): البيانات المراد تحديثها.

    Returns:
        models.UserVerificationStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_user_verification_status_details_service(db, user_verification_status_id=user_verification_status_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث status_name_key
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        existing_status_by_key = user_lookups_crud.get_user_verification_status_by_key(db, key=status_in.status_name_key)
        if existing_status_by_key and existing_status_by_key.user_verification_status_id != user_verification_status_id:
            raise ConflictException(detail=f"حالة التحقق من المستخدم بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")

    return user_lookups_crud.update_user_verification_status(db, db_status=db_status, status_in=status_in)

def delete_user_verification_status(db: Session, user_verification_status_id: int):
    """
    خدمة لحذف حالة تحقق من المستخدم (حذف صارم).
    تتضمن التحقق من عدم وجود مستخدمين مرتبطين بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_verification_status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك مستخدمين مرتبطين.
    """
    db_status_to_delete = get_user_verification_status_details_service(db, user_verification_status_id) # استخدام دالة الخدمة للتحقق

    # التحقق من عدم وجود مستخدمين مرتبطين
    users_count_with_status = user_lookups_crud.count_users_with_verification_status(db, status_id=user_verification_status_id)
    if users_count_with_status > 0:
        raise ConflictException(detail=f"لا يمكن حذف حالة التحقق من المستخدم بمعرف {user_verification_status_id} لأنها مرتبطة بـ {users_count_with_status} مستخدم(ين).")
    
    user_lookups_crud.delete_user_verification_status(db, db_status=db_status_to_delete)
    db.commit()
    return {"message": f"تم حذف حالة التحقق من المستخدم '{db_status_to_delete.status_name_key}' بنجاح."}


# --- خدمات إدارة الترجمات لحالة التحقق من المستخدم ---

def create_user_verification_status_translation(db: Session, user_verification_status_id: int, trans_in: schemas_lookups.UserVerificationStatusTranslationCreate) -> models.UserVerificationStatus:
    """خدمة لإنشاء ترجمة جديدة لحالة تحقق مستخدم."""
    db_status = get_user_verification_status_details_service(db, user_verification_status_id) # التحقق من وجود الحالة الأم

    # التحقق من عدم وجود ترجمة بنفس اللغة
    existing_translation = user_lookups_crud.get_user_verification_status_translation(db, status_id=user_verification_status_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة لحالة التحقق بمعرف {user_verification_status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    updated_status = user_lookups_crud.create_user_verification_status_translation(db, status_id=user_verification_status_id, trans_in=trans_in)
    db.commit() # commit داخل الدالة crud
    return updated_status.user_verification_status # ترجع النوع الأم بعد تحديث ترجمته

def get_user_verification_status_translation_details(db: Session, user_verification_status_id: int, language_code: str) -> models.UserVerificationStatusTranslation:
    """خدمة لجلب ترجمة حالة تحقق مستخدم محددة."""
    translation = user_lookups_crud.get_user_verification_status_translation(db, status_id=user_verification_status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة التحقق بمعرف {user_verification_status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_user_verification_status_translation(db: Session, user_verification_status_id: int, language_code: str, trans_in: schemas_lookups.UserVerificationStatusTranslationUpdate) -> models.UserVerificationStatus:
    """خدمة لتحديث ترجمة حالة تحقق مستخدم موجودة."""
    db_translation = get_user_verification_status_translation_details(db, user_verification_status_id, language_code) # التحقق من وجود الترجمة
    updated_status = user_lookups_crud.update_user_verification_status_translation(db, db_translation=db_translation, trans_in=trans_in)
    db.commit() # commit داخل الدالة crud
    return updated_status.user_verification_status # ترجع النوع الأم بعد تحديث ترجمته

def remove_user_verification_status_translation(db: Session, user_verification_status_id: int, language_code: str):
    """خدمة لحذف ترجمة حالة تحقق مستخدم معينة."""
    db_translation = get_user_verification_status_translation_details(db, user_verification_status_id, language_code) # التحقق من وجود الترجمة
    user_lookups_crud.delete_user_verification_status_translation(db, db_translation=db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة حالة التحقق من المستخدم بنجاح."}