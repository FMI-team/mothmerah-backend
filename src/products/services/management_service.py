# backend/src/users/services/management_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from src.users.crud import management_crud as crud
from src.users.schemas import management_schemas as schemas
from src.users.models.core_models import AccountStatus

def create_new_account_status(db: Session, status_in: schemas.AccountStatusCreate) -> AccountStatus:
    """
    خدمة لإنشاء حالة حساب جديدة مع التحقق من عدم وجودها مسبقًا.
    """
    # التحقق مما إذا كان المفتاح النصي للحالة موجودًا بالفعل
    existing_status = crud.get_account_status_by_key(db, key=status_in.status_name_key)
    if existing_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account status with key '{status_in.status_name_key}' already exists."
        )
    
    return crud.create_account_status(db, status_in=status_in)

def get_all_statuses(db: Session) -> List[AccountStatus]:
    """
    خدمة لجلب جميع حالات الحساب.
    """
    return crud.get_all_account_statuses(db)

def get_status_by_id(db: Session, status_id: int) -> AccountStatus:
    """
    خدمة لجلب حالة حساب واحدة عن طريق الـ ID.
    """
    db_status = crud.get_account_status(db, status_id=status_id)
    if not db_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account status not found.")
    return db_status

def update_existing_account_status(db: Session, status_id: int, status_in: schemas.AccountStatusUpdate) -> AccountStatus:
    """
    خدمة لتحديث حالة حساب موجودة.
    """
    db_status = get_status_by_id(db, status_id) # استخدام الدالة أعلاه للتحقق من الوجود أولاً
    
    # إذا كان التحديث يتضمن تغيير المفتاح، تأكد من أنه غير مكرر
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        existing_status = crud.get_account_status_by_key(db, key=status_in.status_name_key)
        if existing_status:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Account status with key '{status_in.status_name_key}' already exists."
            )
            
    return crud.update_account_status(db=db, db_status=db_status, status_in=status_in)

def manage_status_translation(db: Session, status_id: int, trans_in: schemas.AccountStatusTranslationCreate) -> AccountStatus:
    """
    خدمة لإضافة أو تحديث ترجمة لحالة حساب.
    """
    updated_status = crud.add_or_update_translation(db, status_id=status_id, trans_in=trans_in)
    if not updated_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account status not found.")
    return updated_status
