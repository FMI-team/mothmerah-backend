# backend\src\users\crud\user_lookups_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID # لـ User (في التحقق من عدد المستخدمين)

# استيراد المودلز
from src.users.models.core_models import AccountStatus, AccountStatusTranslation, UserType, UserTypeTranslation, User # User لـ count_users_with_status/type
from src.users.models.verification_models import UserVerificationStatus, UserVerificationStatusTranslation
# استيراد Schemas (فقط لـ Type Hinting إذا لزم الأمر)
from src.users.schemas import core_schemas as schemas_core # لـ UserType schemas, AccountStatus schemas
from src.users.schemas import verification_lookups_schemas as schemas_management # لـ UserVerificationStatus schemas


# ==========================================================
# --- CRUD Functions for UserType (أنواع المستخدمين) ---
# ==========================================================

def get_user_type(db: Session, type_id: int) -> Optional[UserType]:
    """جلب نوع مستخدم واحد مع ترجماته."""
    return db.query(UserType).options(
        joinedload(UserType.translations)
    ).filter(UserType.user_type_id == type_id).first()

def get_user_type_by_key(db: Session, key: str) -> Optional[UserType]:
    """جلب نوع مستخدم عن طريق مفتاحه النصي."""
    return db.query(UserType).filter(UserType.user_type_name_key == key).first()

def get_all_user_types(db: Session) -> List[UserType]:
    """جلب كل أنواع المستخدمين مع ترجماتهم."""
    return db.query(UserType).options(
        joinedload(UserType.translations)
    ).order_by(UserType.user_type_id).all()

def create_user_type(db: Session, type_in: schemas_core.UserTypeCreate) -> UserType:
    """إنشاء نوع مستخدم جديد مع ترجماته الأولية."""
    type_data = type_in.model_dump(exclude={"translations"})
    db_type = UserType(**type_data)

    if type_in.translations:
        for trans in type_in.translations:
            db_type.translations.append(UserTypeTranslation(**trans.model_dump()))

    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def update_user_type(db: Session, db_type: UserType, type_in: schemas_core.UserTypeUpdate) -> UserType:
    """تحديث بيانات نوع مستخدم."""
    update_data = type_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_type, key, value)

    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def count_users_with_type(db: Session, type_id: int) -> int:
    """يحسب عدد المستخدمين الذين يستخدمون نوع مستخدم معين."""
    return db.query(User).filter(User.user_type_id == type_id).count()

def reassign_users_to_default_type(db: Session, old_type_id: int, default_type_id: int) -> int:
    """
    يقوم بتحديث كل المستخدمين من نوع معين ونقلهم إلى النوع الافتراضي.
    :return: عدد الصفوف (المستخدمين) التي تم تحديثها.
    """
    updated_rows = db.query(User).filter(
        User.user_type_id == old_type_id
    ).update(
        {User.user_type_id: default_type_id},
        synchronize_session=False  # ضروري للأداء في التحديث المجمع
    )
    # لا نقم بعمل db.commit() هنا، ليتم التحكم بالـ transaction من طبقة الخدمات
    return updated_rows

def delete_user_type(db: Session, db_type: UserType) -> None:
    """حذف نوع مستخدم من قاعدة البيانات."""
    db.delete(db_type)
    # الـ Commit سيتم من الخدمة
    return


# ==========================================================
# --- CRUD Functions for AccountStatus (حالات الحساب) ---
# ==========================================================

def get_account_status(db: Session, status_id: int) -> Optional[AccountStatus]:
    """جلب حالة حساب واحدة مع ترجماتها."""
    return db.query(AccountStatus).options(
        joinedload(AccountStatus.translations)
    ).filter(AccountStatus.account_status_id == status_id).first()

def get_account_status_by_key(db: Session, key: str) -> Optional[AccountStatus]:
    """جلب حالة حساب عن طريق مفتاحها النصي."""
    return db.query(AccountStatus).filter(AccountStatus.status_name_key == key).first()

def get_all_account_statuses(db: Session) -> List[AccountStatus]:
    """جلب كل حالات الحساب مع ترجماتها."""
    return db.query(AccountStatus).options(
        joinedload(AccountStatus.translations)
    ).order_by(AccountStatus.account_status_id).all()

def create_account_status(db: Session, status_in: schemas_core.AccountStatusCreate) -> AccountStatus:
    """إنشاء حالة حساب جديدة مع ترجماتها الأولية."""
    status_data = status_in.model_dump(exclude={"translations"})
    db_status = AccountStatus(**status_data)
    
    if status_in.translations:
        for trans in status_in.translations:
            db_status.translations.append(AccountStatusTranslation(**trans.model_dump()))

    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def update_account_status(db: Session, db_status: AccountStatus, status_in: schemas_core.AccountStatusUpdate) -> AccountStatus:
    """تحديث بيانات حالة حساب موجودة."""
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def count_users_with_account_status(db: Session, status_id: int) -> int:
    """يحسب عدد المستخدمين الذين يستخدمون حالة حساب معينة."""
    return db.query(User).filter(User.account_status_id == status_id).count()

def reassign_users_to_default_account_status(db: Session, old_status_id: int, default_status_id: int) -> int:
    """
    يقوم بتحديث كل المستخدمين من حالة حساب معينة ونقلهم إلى الحالة الافتراضية.
    :return: عدد الصفوف (المستخدمين) التي تم تحديثها.
    """
    updated_rows = db.query(User).filter(
        User.account_status_id == old_status_id
    ).update(
        {User.account_status_id: default_status_id},
        synchronize_session=False
    )
    # لا نقم بعمل db.commit() هنا، ليتم التحكم بالـ transaction من طبقة الخدمات
    return updated_rows

def delete_account_status(db: Session, db_status: AccountStatus) -> None:
    """حذف حالة حساب من قاعدة البيانات."""
    db.delete(db_status)
    # الـ Commit سيتم من الخدمة
    return

# ==========================================================
# --- CRUD Functions for AccountStatusTranslation (ترجمات حالات الحساب) ---
# ==========================================================

def get_account_status_translation(db: Session, status_id: int, language_code: str) -> Optional[AccountStatusTranslation]:
    """جلب ترجمة معينة لحالة حساب."""
    return db.query(AccountStatusTranslation).filter(
        and_(
            AccountStatusTranslation.account_status_id == status_id,
            AccountStatusTranslation.language_code == language_code
        )
    ).first()

def add_or_update_account_status_translation(db: Session, status_id: int, trans_in: schemas_core.AccountStatusTranslationCreate) -> AccountStatus:
    """إضافة أو تحديث ترجمة لحالة حساب معينة."""
    db_status = db.query(AccountStatus).options(joinedload(AccountStatus.translations)).filter(AccountStatus.account_status_id == status_id).first()
    if not db_status:
        return None # يُفترض أن التحقق من وجود الحالة الأم يتم في طبقة الخدمة

    existing_trans = next((t for t in db_status.translations if t.language_code == trans_in.language_code), None)

    if existing_trans:
        existing_trans.translated_status_name = trans_in.translated_status_name
        existing_trans.translated_status_description = trans_in.translated_status_description
    else:
        db_status.translations.append(AccountStatusTranslation(**trans_in.model_dump()))
    
    # لا نقم بالـ commit هنا، بل يتم التحكم به في طبقة الخدمات
    return db_status

def delete_account_status_translation(db: Session, db_translation: AccountStatusTranslation) -> None:
    """حذف ترجمة حالة حساب."""
    db.delete(db_translation)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for UserVerificationStatus (حالات التحقق من المستخدم) ---
# ==========================================================

def get_user_verification_status(db: Session, status_id: int) -> Optional[UserVerificationStatus]:
    """جلب حالة تحقق مستخدم واحدة مع ترجماتها."""
    return db.query(UserVerificationStatus).options(
        joinedload(UserVerificationStatus.translations)
    ).filter(UserVerificationStatus.user_verification_status_id == status_id).first()

def get_user_verification_status_by_key(db: Session, key: str) -> Optional[UserVerificationStatus]:
    """جلب حالة تحقق مستخدم عن طريق مفتاحها النصي."""
    return db.query(UserVerificationStatus).filter(UserVerificationStatus.status_name_key == key).first()

def get_all_user_verification_statuses(db: Session) -> List[UserVerificationStatus]:
    """جلب كل حالات التحقق من المستخدم مع ترجماتهم."""
    return db.query(UserVerificationStatus).options(
        joinedload(UserVerificationStatus.translations)
    ).order_by(UserVerificationStatus.user_verification_status_id).all()

def create_user_verification_status(db: Session, status_in: schemas_management.UserVerificationStatusCreate) -> UserVerificationStatus:
    """إنشاء حالة تحقق مستخدم جديدة مع ترجماتها الأولية."""
    status_data = status_in.model_dump(exclude={"translations"})
    db_status = UserVerificationStatus(**status_data)

    if status_in.translations:
        for trans in status_in.translations:
            db_status.translations.append(UserVerificationStatusTranslation(**trans.model_dump()))

    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def update_user_verification_status(db: Session, db_status: UserVerificationStatus, status_in: schemas_management.UserVerificationStatusUpdate) -> UserVerificationStatus:
    """تحديث بيانات حالة تحقق مستخدم."""
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def count_users_with_verification_status(db: Session, status_id: int) -> int:
    """يحسب عدد المستخدمين الذين يستخدمون حالة تحقق معينة."""
    return db.query(User).filter(User.user_verification_status_id == status_id).count()

def reassign_users_to_default_verification_status(db: Session, old_status_id: int, default_status_id: int) -> int:
    """
    يقوم بتحديث كل المستخدمين من حالة تحقق معينة ونقلهم إلى الحالة الافتراضية.
    :return: عدد الصفوف (المستخدمين) التي تم تحديثها.
    """
    updated_rows = db.query(User).filter(
        User.user_verification_status_id == old_status_id
    ).update(
        {User.user_verification_status_id: default_status_id},
        synchronize_session=False
    )
    # لا نقم بعمل db.commit() هنا، ليتم التحكم بالـ transaction من طبقة الخدمات
    return updated_rows

def delete_user_verification_status(db: Session, db_status: UserVerificationStatus) -> None:
    """حذف حالة تحقق من المستخدم."""
    db.delete(db_status)
    # الـ Commit سيتم من الخدمة
    return

# ==========================================================
# --- CRUD Functions for UserVerificationStatusTranslation (ترجمات حالات التحقق من المستخدم) ---
# ==========================================================

def get_user_verification_status_translation(db: Session, status_id: int, language_code: str) -> Optional[UserVerificationStatusTranslation]:
    """جلب ترجمة معينة لحالة تحقق مستخدم."""
    return db.query(UserVerificationStatusTranslation).filter(
        and_(
            UserVerificationStatusTranslation.user_verification_status_id == status_id,
            UserVerificationStatusTranslation.language_code == language_code
        )
    ).first()

def create_user_verification_status_translation(db: Session, status_id: int, trans_in: schemas_management.UserVerificationStatusTranslationCreate) -> UserVerificationStatusTranslation:
    """إنشاء ترجمة جديدة لحالة تحقق مستخدم معينة."""
    db_translation = UserVerificationStatusTranslation(
        user_verification_status_id=status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_description=trans_in.translated_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def update_user_verification_status_translation(db: Session, db_translation: UserVerificationStatusTranslation, trans_in: schemas_management.UserVerificationStatusTranslationUpdate) -> UserVerificationStatusTranslation:
    """تحديث بيانات ترجمة حالة تحقق مستخدم موجودة."""
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_user_verification_status_translation(db: Session, db_translation: UserVerificationStatusTranslation) -> None:
    """حذف ترجمة حالة تحقق مستخدم."""
    db.delete(db_translation)
    db.commit()
    return