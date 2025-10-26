# backend/src/products/services/variety_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from uuid import UUID

from src.products.crud import variety_crud, product_crud
from src.products.schemas import variety_schemas as schemas
from src.users.models.core_models import User
from src.products.models import products_models as models

def get_all_varieties_for_a_product(db: Session, product_id: UUID, user: User) -> List[models.ProductVariety]:
    """خدمة لجلب كل أصناف منتج معين مع التحقق من ملكية المنتج."""
    # أولاً، نتأكد أن المستخدم يملك المنتج
    db_product = product_crud.get_product(db, product_id)
    if not db_product or db_product.seller_user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or you do not have permission to view its varieties.")
    
    return variety_crud.get_all_varieties_for_product(db, product_id=product_id)

def create_new_variety(db: Session, variety_in: schemas.ProductVarietyCreate, user: User) -> models.ProductVariety:
    """خدمة لإنشاء صنف جديد مع التحقق من ملكية المنتج."""
    # نتأكد أن المستخدم يملك المنتج الذي يحاول إضافة صنف له
    db_product = product_crud.get_product(db, variety_in.product_id)
    if not db_product or db_product.seller_user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only add varieties to your own products.")
        
    return variety_crud.create_variety(db, variety_in=variety_in)

def update_existing_variety(db: Session, variety_id: int, variety_in: schemas.ProductVarietyUpdate, user: User) -> models.ProductVariety:
    """خدمة لتحديث صنف موجود مع التحقق من الملكية."""
    db_variety = variety_crud.get_variety(db, variety_id)
    if not db_variety:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variety not found.")

    # نتأكد أن المستخدم يملك المنتج المرتبط بهذا الصنف
    db_product = product_crud.get_product(db, db_variety.product_id)
    if not db_product or db_product.seller_user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update varieties of your own products.")

    return variety_crud.update_variety(db, db_variety=db_variety, variety_in=variety_in)

def soft_delete_variety_by_id(db: Session, variety_id: int, user: User):
    """خدمة للحذف الناعم لصنف منتج مع التحقق من الملكية."""
    db_variety = variety_crud.get_variety(db, variety_id)
    if not db_variety:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variety not found.")

    # نتأكد أن المستخدم يملك المنتج المرتبط بهذا الصنف
    db_product = product_crud.get_product(db, db_variety.product_id)
    if not db_product or db_product.seller_user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete varieties of your own products.")
    
    # منطق حماية إضافي: هل هذا الصنف مستخدم في أي خيار تعبئة؟
    # if crud.is_variety_in_use(db, variety_id):
    #     raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete variety, it is currently in use in packaging options.")
        
    variety_crud.soft_delete_variety(db, db_variety=db_variety)
    return {"message": "Variety has been deactivated (soft deleted)."}

# --- خدمات إدارة الترجمات للصنف ---

def manage_variety_translation(db: Session, variety_id: int, trans_in: schemas.ProductVarietyTranslationCreate, user: User) -> models.ProductVariety:
    """خدمة لإضافة أو تحديث ترجمة لصنف مع التحقق من الملكية."""
    db_variety = variety_crud.get_variety(db, variety_id)
    if not db_variety:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variety not found.")

    db_product = product_crud.get_product(db, db_variety.product_id)
    if not db_product or db_product.seller_user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    return variety_crud.add_or_update_variety_translation(db, variety_id=variety_id, trans_in=trans_in)

def remove_variety_translation(db: Session, variety_id: int, language_code: str, user: User):
    """خدمة لحذف ترجمة معينة لصنف مع التحقق من الملكية."""
    db_variety = variety_crud.get_variety(db, variety_id)
    if not db_variety:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variety not found.")

    db_product = product_crud.get_product(db, db_variety.product_id)
    if not db_product or db_product.seller_user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    success = variety_crud.delete_variety_translation(db, variety_id=variety_id, language_code=language_code)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found.")
    return {"message": "Translation deleted successfully"}