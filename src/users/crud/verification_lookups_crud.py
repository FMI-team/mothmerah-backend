# backend\src\users\crud\verification_lookups_crud.py

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.users.models import verification_models as models
from src.lookups.models import lookups_models # لـ Language

# استيراد Schemas
from src.users.schemas import verification_lookups_schemas as schemas
from src.lookups.schemas.lookups_schemas import LanguageCreate # لإنشاء ترجمات اللغة (إذا لزم الأمر)


# ==========================================================
# --- CRUD for LicenseType (أنواع التراخيص) ---
# ==========================================================

def create_license_type(db: Session, type_in: schemas.LicenseTypeCreate) -> models.LicenseType:
    """إنشاء نوع ترخيص جديد مع ترجماته."""
    db_type = models.LicenseType(
        license_type_name_key=type_in.license_type_name_key,
        is_mandatory_for_role=type_in.is_mandatory_for_role
    )
    db.add(db_type)
    db.flush() # للحصول على license_type_id قبل إضافة الترجمات

    if type_in.translations:
        for trans_in in type_in.translations:
            # التحقق من وجود اللغة أولاً
            language = db.query(lookups_models.Language).filter(lookups_models.Language.language_code == trans_in.language_code).first()
            if not language:
                # إذا لم تكن اللغة موجودة، يمكن إما رفع خطأ أو إنشائها تلقائياً.
                # هنا نرفع خطأ، يفضل أن تكون اللغات موجودة مسبقاً في جدول Lookups.
                raise ValueError(f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

            db_translation = models.LicenseTypeTranslation(
                license_type_id=db_type.license_type_id,
                language_code=trans_in.language_code,
                translated_license_type_name=trans_in.translated_license_type_name,
                translated_description=trans_in.translated_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_type)
    return db_type

def get_license_type(db: Session, type_id: int) -> Optional[models.LicenseType]:
    """جلب نوع ترخيص بواسطة المعرف."""
    return db.query(models.LicenseType).filter(models.LicenseType.license_type_id == type_id).first()

def get_license_type_by_key(db: Session, key: str) -> Optional[models.LicenseType]:
    """جلب نوع ترخيص بواسطة المفتاح الفريد."""
    return db.query(models.LicenseType).filter(models.LicenseType.license_type_name_key == key).first()

def get_all_license_types(db: Session) -> List[models.LicenseType]:
    """جلب جميع أنواع التراخيص."""
    return db.query(models.LicenseType).all()

def update_license_type(db: Session, db_type: models.LicenseType, type_in: schemas.LicenseTypeUpdate) -> models.LicenseType:
    """تحديث نوع ترخيص موجود."""
    update_data = type_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_type, key, value)
    db_type.updated_at = datetime.now(timezone.utc)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def delete_license_type(db: Session, db_type: models.LicenseType):
    """حذف نوع ترخيص."""
    db.delete(db_type)
    db.commit()

# --- CRUD for LicenseTypeTranslation ---

def create_license_type_translation(db: Session, type_id: int, trans_in: schemas.LicenseTypeTranslationCreate) -> models.LicenseTypeTranslation:
    """إنشاء ترجمة جديدة لنوع ترخيص."""
    # التحقق من وجود اللغة أولاً
    language = db.query(lookups_models.Language).filter(lookups_models.Language.language_code == trans_in.language_code).first()
    if not language:
        raise ValueError(f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    db_translation = models.LicenseTypeTranslation(
        license_type_id=type_id,
        language_code=trans_in.language_code,
        translated_license_type_name=trans_in.translated_license_type_name,
        translated_description=trans_in.translated_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_license_type_translation(db: Session, type_id: int, language_code: str) -> Optional[models.LicenseTypeTranslation]:
    """جلب ترجمة نوع ترخيص محددة."""
    return db.query(models.LicenseTypeTranslation).filter(
        models.LicenseTypeTranslation.license_type_id == type_id,
        models.LicenseTypeTranslation.language_code == language_code
    ).first()

def update_license_type_translation(db: Session, db_translation: models.LicenseTypeTranslation, trans_in: schemas.LicenseTypeTranslationUpdate) -> models.LicenseTypeTranslation:
    """تحديث ترجمة نوع ترخيص موجودة."""
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_license_type_translation(db: Session, db_translation: models.LicenseTypeTranslation):
    """حذف ترجمة نوع ترخيص."""
    db.delete(db_translation)
    db.commit()


# ==========================================================
# --- CRUD for IssuingAuthority (الجهات المصدرة للتراخيص) ---
# ==========================================================

def create_issuing_authority(db: Session, authority_in: schemas.IssuingAuthorityCreate) -> models.IssuingAuthority:
    """إنشاء جهة إصدار جديدة مع ترجماتها."""
    db_authority = models.IssuingAuthority(
        authority_name_key=authority_in.authority_name_key,
        country_code=authority_in.country_code
    )
    db.add(db_authority)
    db.flush() # للحصول على authority_id قبل إضافة الترجمات

    if authority_in.translations:
        for trans_in in authority_in.translations:
            # التحقق من وجود اللغة أولاً
            language = db.query(lookups_models.Language).filter(lookups_models.Language.language_code == trans_in.language_code).first()
            if not language:
                raise ValueError(f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")
                
            db_translation = models.IssuingAuthorityTranslation(
                authority_id=db_authority.authority_id,
                language_code=trans_in.language_code,
                translated_authority_name=trans_in.translated_authority_name,
                translated_description=trans_in.translated_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_authority)
    return db_authority

def get_issuing_authority(db: Session, authority_id: int) -> Optional[models.IssuingAuthority]:
    """جلب جهة إصدار بواسطة المعرف."""
    return db.query(models.IssuingAuthority).filter(models.IssuingAuthority.authority_id == authority_id).first()

def get_issuing_authority_by_key(db: Session, key: str) -> Optional[models.IssuingAuthority]:
    """جلب جهة إصدار بواسطة المفتاح الفريد."""
    return db.query(models.IssuingAuthority).filter(models.IssuingAuthority.authority_name_key == key).first()

def get_all_issuing_authorities(db: Session) -> List[models.IssuingAuthority]:
    """جلب جميع الجهات المصدرة للتراخيص."""
    return db.query(models.IssuingAuthority).all()

def update_issuing_authority(db: Session, db_authority: models.IssuingAuthority, authority_in: schemas.IssuingAuthorityUpdate) -> models.IssuingAuthority:
    """تحديث جهة إصدار موجودة."""
    update_data = authority_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_authority, key, value)
    db_authority.updated_at = datetime.now(timezone.utc)
    db.add(db_authority)
    db.commit()
    db.refresh(db_authority)
    return db_authority

def delete_issuing_authority(db: Session, db_authority: models.IssuingAuthority):
    """حذف جهة إصدار."""
    db.delete(db_authority)
    db.commit()

# --- CRUD for IssuingAuthorityTranslation ---

def create_issuing_authority_translation(db: Session, authority_id: int, trans_in: schemas.IssuingAuthorityTranslationCreate) -> models.IssuingAuthorityTranslation:
    """إنشاء ترجمة جديدة لجهة إصدار."""
    # التحقق من وجود اللغة أولاً
    language = db.query(lookups_models.Language).filter(lookups_models.Language.language_code == trans_in.language_code).first()
    if not language:
        raise ValueError(f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    db_translation = models.IssuingAuthorityTranslation(
        authority_id=authority_id,
        language_code=trans_in.language_code,
        translated_authority_name=trans_in.translated_authority_name,
        translated_description=trans_in.translated_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_issuing_authority_translation(db: Session, authority_id: int, language_code: str) -> Optional[models.IssuingAuthorityTranslation]:
    """جلب ترجمة جهة إصدار محددة."""
    return db.query(models.IssuingAuthorityTranslation).filter(
        models.IssuingAuthorityTranslation.authority_id == authority_id,
        models.IssuingAuthorityTranslation.language_code == language_code
    ).first()

def update_issuing_authority_translation(db: Session, db_translation: models.IssuingAuthorityTranslation, trans_in: schemas.IssuingAuthorityTranslationUpdate) -> models.IssuingAuthorityTranslation:
    """تحديث ترجمة جهة إصدار موجودة."""
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_issuing_authority_translation(db: Session, db_translation: models.IssuingAuthorityTranslation):
    """حذف ترجمة جهة إصدار."""
    db.delete(db_translation)
    db.commit()


# ====================================================================
# --- CRUD for LicenseVerificationStatus (حالات التحقق من التراخيص) ---
# ====================================================================

def create_license_verification_status(db: Session, status_in: schemas.LicenseVerificationStatusCreate) -> models.LicenseVerificationStatus:
    """إنشاء حالة تحقق ترخيص جديدة مع ترجماتها."""
    db_status = models.LicenseVerificationStatus(
        status_name_key=status_in.status_name_key,
        description_key=status_in.description_key
    )
    db.add(db_status)
    db.flush() # للحصول على license_verification_status_id قبل إضافة الترجمات

    if status_in.translations:
        for trans_in in status_in.translations:
            # التحقق من وجود اللغة أولاً
            language = db.query(lookups_models.Language).filter(lookups_models.Language.language_code == trans_in.language_code).first()
            if not language:
                raise ValueError(f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

            db_translation = models.LicenseVerificationStatusTranslation(
                license_verification_status_id=db_status.license_verification_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name,
                translated_description=trans_in.translated_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_license_verification_status(db: Session, status_id: int) -> Optional[models.LicenseVerificationStatus]:
    """جلب حالة تحقق ترخيص بواسطة المعرف."""
    return db.query(models.LicenseVerificationStatus).filter(models.LicenseVerificationStatus.license_verification_status_id == status_id).first()

def get_license_verification_status_by_key(db: Session, key: str) -> Optional[models.LicenseVerificationStatus]:
    """جلب حالة تحقق ترخيص بواسطة المفتاح الفريد."""
    return db.query(models.LicenseVerificationStatus).filter(models.LicenseVerificationStatus.status_name_key == key).first()

def get_all_license_verification_statuses(db: Session) -> List[models.LicenseVerificationStatus]:
    """جلب جميع حالات التحقق من التراخيص."""
    return db.query(models.LicenseVerificationStatus).all()

def update_license_verification_status(db: Session, db_status: models.LicenseVerificationStatus, status_in: schemas.LicenseVerificationStatusUpdate) -> models.LicenseVerificationStatus:
    """تحديث حالة تحقق ترخيص موجودة."""
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db_status.updated_at = datetime.now(timezone.utc)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_license_verification_status(db: Session, db_status: models.LicenseVerificationStatus):
    """حذف حالة تحقق ترخيص."""
    db.delete(db_status)
    db.commit()

# --- CRUD for LicenseVerificationStatusTranslation ---

def create_license_verification_status_translation(db: Session, status_id: int, trans_in: schemas.LicenseVerificationStatusTranslationCreate) -> models.LicenseVerificationStatusTranslation:
    """إنشاء ترجمة جديدة لحالة تحقق ترخيص."""
    # التحقق من وجود اللغة أولاً
    language = db.query(lookups_models.Language).filter(lookups_models.Language.language_code == trans_in.language_code).first()
    if not language:
        raise ValueError(f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    db_translation = models.LicenseVerificationStatusTranslation(
        license_verification_status_id=status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_description=trans_in.translated_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_license_verification_status_translation(db: Session, status_id: int, language_code: str) -> Optional[models.LicenseVerificationStatusTranslation]:
    """جلب ترجمة حالة تحقق ترخيص محددة."""
    return db.query(models.LicenseVerificationStatusTranslation).filter(
        models.LicenseVerificationStatusTranslation.license_verification_status_id == status_id,
        models.LicenseVerificationStatusTranslation.language_code == language_code
    ).first()

def update_license_verification_status_translation(db: Session, db_translation: models.LicenseVerificationStatusTranslation, trans_in: schemas.LicenseVerificationStatusTranslationUpdate) -> models.LicenseVerificationStatusTranslation:
    """تحديث ترجمة حالة تحقق ترخيص موجودة."""
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_license_verification_status_translation(db: Session, db_translation: models.LicenseVerificationStatusTranslation):
    """حذف ترجمة حالة تحقق ترخيص."""
    db.delete(db_translation)
    db.commit()