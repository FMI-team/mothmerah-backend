# backend\src\users\crud\address_crud.py

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

# استيراد المودلز من Users
from src.users.models import addresses_models as models # Address
from src.users.schemas import address_schemas as schemas


# ==========================================================
# --- CRUD Functions for Address (العناوين) ---
# ==========================================================

def create_address(db: Session, address_in: schemas.AddressCreate, user_id: UUID) -> models.Address:
    """
    ينشئ سجل عنوان جديد لمستخدم معين في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        address_in (schemas.AddressCreate): بيانات العنوان للإنشاء.
        user_id (UUID): معرف المستخدم الذي ينتمي إليه العنوان.

    Returns:
        models.Address: كائن العنوان الذي تم إنشاؤه.
    """
    db_address = models.Address(**address_in.model_dump(), user_id=user_id)
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

def get_address_by_id(db: Session, address_id: int) -> Optional[models.Address]:
    """
    يجلب عنوان واحد عن طريق الـ ID الخاص به.
    يتم تحميل بعض العلاقات الأساسية بشكل فوري لتحسين الأداء.

    Args:
        db (Session): جلسة قاعدة البيانات.
        address_id (int): معرف العنوان المطلوب.

    Returns:
        Optional[models.Address]: كائن العنوان أو None.
    """
    return db.query(models.Address).options(
        joinedload(models.Address.user), # المستخدم المالك
        joinedload(models.Address.address_type), # نوع العنوان
        joinedload(models.Address.country), # الدولة
        joinedload(models.Address.governorate), # المحافظة
        joinedload(models.Address.city), # المدينة
        joinedload(models.Address.district) # الحي
    ).filter(models.Address.address_id == address_id).first()

def get_addresses_for_user(db: Session, user_id: UUID) -> List[models.Address]:
    """
    جلب قائمة بجميع العناوين لمستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.

    Returns:
        List[models.Address]: قائمة بكائنات العناوين.
    """
    return db.query(models.Address).filter(models.Address.user_id == user_id).all()

def update_address(db: Session, db_address: models.Address, address_in: schemas.AddressUpdate) -> models.Address:
    """
    يحدث بيانات عنوان موجود في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_address (models.Address): كائن العنوان من قاعدة البيانات.
        address_in (schemas.AddressUpdate): البيانات المراد تحديثها.

    Returns:
        models.Address: كائن العنوان المحدث.
    """
    update_data = address_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_address, key, value)
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

def delete_address(db: Session, db_address: models.Address):
    """
    يحذف عنوانًا من قاعدة البيانات (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_address (models.Address): كائن العنوان من قاعدة البيانات.
    """
    db.delete(db_address)
    db.commit()
    return