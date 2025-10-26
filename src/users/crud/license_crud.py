# backend\src\users\crud\license_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

# استيراد المودلز من Users
from src.users.models import verification_models as models # License
from src.users.schemas import license_schemas as schemas


# ==========================================================
# --- CRUD Functions for License (التراخيص) ---
# ==========================================================

def create_license(db: Session, license_in: schemas.LicenseCreate, user_id: UUID, file_storage_key: str, verification_status_id: int) -> models.License:
    """
    ينشئ سجل ترخيص جديد في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        license_in (schemas.LicenseCreate): بيانات الترخيص للإنشاء.
        user_id (UUID): معرف المستخدم صاحب الترخيص.
        file_storage_key (str): مفتاح الملف المخزن في الخدمة السحابية.
        verification_status_id (int): معرف حالة التحقق الأولية للترخيص.

    Returns:
        models.License: كائن الترخيص الذي تم إنشاؤه.
    """
    db_license = models.License(
        user_id=user_id,
        license_type_id=license_in.license_type_id,
        issuing_authority_id=license_in.issuing_authority_id,
        file_storage_key=file_storage_key,
        license_number=license_in.license_number,
        issue_date=license_in.issue_date,
        expiry_date=license_in.expiry_date,
        verification_status_id=verification_status_id
    )
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license

def get_license_by_id(db: Session, license_id: int) -> Optional[models.License]:
    """
    جلب سجل ترخيص واحد عن طريق الـ ID الخاص به.
    يتم تحميل بعض العلاقات الأساسية بشكل فوري لتحسين الأداء.

    Args:
        db (Session): جلسة قاعدة البيانات.
        license_id (int): معرف الترخيص المطلوب.

    Returns:
        Optional[models.License]: كائن الترخيص أو None.
    """
    return db.query(models.License).options(
        joinedload(models.License.user), # المستخدم المالك
        joinedload(models.License.license_type), # نوع الترخيص
        joinedload(models.License.issuing_authority), # الجهة المصدرة
        joinedload(models.License.verification_status) # حالة التحقق
    ).filter(models.License.license_id == license_id).first()

def get_licenses_for_user(db: Session, user_id: UUID) -> List[models.License]:
    """
    جلب قائمة بجميع التراخيص لمستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.

    Returns:
        List[models.License]: قائمة بكائنات التراخيص.
    """
    return db.query(models.License).filter(models.License.user_id == user_id).all()

def get_all_licenses(db: Session, skip: int = 0, limit: int = 100) -> List[models.License]:
    """
    [للمسؤول] جلب قائمة بكل التراخيص في النظام مع إمكانية التصفح.

    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.License]: قائمة بكائنات التراخيص.
    """
    return db.query(models.License).offset(skip).limit(limit).all()

def update_license(db: Session, db_license: models.License, license_in: schemas.LicenseUpdate) -> models.License:
    """
    تحديث بيانات ترخيص موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_license (models.License): كائن الترخيص من قاعدة البيانات.
        license_in (schemas.LicenseUpdate): البيانات المراد تحديثها.

    Returns:
        models.License: كائن الترخيص المحدث.
    """
    update_data = license_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_license, key, value)
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license

def update_license_verification_status(db: Session, db_license: models.License, new_verification_status_id: int) -> models.License:
    """
    يحدث حالة التحقق لترخيص معين.
    هذه الدالة تُستخدم بواسطة المسؤولين أو النظام.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_license (models.License): كائن الترخيص من قاعدة البيانات.
        new_verification_status_id (int): معرف الحالة الجديدة.

    Returns:
        models.License: كائن الترخيص المحدث.
    """
    db_license.verification_status_id = new_verification_status_id
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license


def delete_license(db: Session, db_license: models.License) -> None:
    """
    يحذف سجل ترخيص من قاعدة البيانات (حذف صارم).
    TODO: التحقق من عدم وجود ارتباطات حيوية سيتم في طبقة الخدمة.
    """
    db.delete(db_license)
    db.commit()
    return