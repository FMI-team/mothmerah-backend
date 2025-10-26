# backend/src/products/services/category_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from src.products.crud import category_crud as crud
from src.products.schemas import category_schemas as schemas
from src.products import models

def get_all_categories(db: Session) -> List[models.ProductCategory]:
    """خدمة لجلب كل فئات المنتجات."""
    return crud.get_all_product_categories(db)

def get_category_by_id(db: Session, category_id: int) -> models.ProductCategory:
    """خدمة لجلب فئة واحدة والتأكد من وجودها."""
    db_category = crud.get_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return db_category

def create_new_category(db: Session, category_in: schemas.ProductCategoryCreate) -> models.ProductCategory:
    """خدمة لإنشاء فئة جديدة مع التحقق من البيانات."""
    # التحقق من أن المفتاح غير مكرر
    existing_category = crud.get_category_by_key(db, key=category_in.category_name_key)
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with key '{category_in.category_name_key}' already exists."
        )
    
    # التحقق من وجود الفئة الأم إذا تم تحديدها
    if category_in.parent_category_id:
        parent_category = crud.get_category(db, category_id=category_in.parent_category_id)
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with id {category_in.parent_category_id} not found."
            )
            
    return crud.create_category(db, category_in=category_in)

def update_existing_category(db: Session, category_id: int, category_in: schemas.ProductCategoryUpdate) -> models.ProductCategory:
    """خدمة لتحديث فئة موجودة."""
    db_category = get_category_by_id(db, category_id) # نستفيد من الدالة أعلاه للتحقق

    # منطق عمل: منع الفئة من أن تكون أباً لنفسها
    if category_in.parent_category_id and category_in.parent_category_id == category_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A category cannot be its own parent.")

    return crud.update_category(db, db_category=db_category, category_in=category_in)

def delete_category_by_id(db: Session, category_id: int):
    """خدمة للحذف الآمن لفئة منتج."""
    # منطق الحماية: لا يمكن حذف فئة إذا كانت مرتبطة بمنتجات
    product_count = crud.count_products_in_category(db, category_id=category_id)
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete category. It is associated with {product_count} product(s)."
        )
    
    db_category = get_category_by_id(db, category_id)
        
    crud.delete_category(db, db_category=db_category)
    return {"message": "Category permanently deleted."}

# --- خدمات إدارة الترجمات للفئة ---

def manage_category_translation(db: Session, category_id: int, trans_in: schemas.ProductCategoryTranslationCreate) -> models.ProductCategory:
    """خدمة لإضافة أو تحديث ترجمة لفئة."""
    updated_category = crud.add_or_update_category_translation(db, category_id=category_id, trans_in=trans_in)
    if not updated_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return updated_category

def remove_category_translation(db: Session, category_id: int, language_code: str):
    """خدمة لحذف ترجمة معينة لفئة."""
    success = crud.delete_category_translation(db, category_id=category_id, language_code=language_code)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found.")
    return {"message": "Translation deleted successfully"}




def delete_category_by_id(db: Session, category_id: int):
    """
    خدمة للحذف الناعم لفئة منتج، مع إعادة إسناد المنتجات المرتبطة.
    """
    db_category_to_delete = crud.get_category(db, category_id)
    if not db_category_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    # جلب الفئة الافتراضية "غير مصنف"
    DEFAULT_CATEGORY_KEY = "UNCATEGORIZED" 
    default_category = crud.get_category_by_key(db, key=DEFAULT_CATEGORY_KEY)
    if not default_category:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Default category '{DEFAULT_CATEGORY_KEY}' not configured.")
    if default_category.category_id == category_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Default category cannot be deleted.")

    # إعادة إسناد المنتجات
    crud.reassign_products_to_default_category(db, old_category_id=category_id, default_category_id=default_category.category_id)

    # الحذف الناعم للفئة
    crud.soft_delete_category(db, db_category=db_category_to_delete)

    db.commit()
    return {"message": "Category deactivated and associated products have been moved to 'Uncategorized'."}

def remove_category_translation(db: Session, category_id: int, language_code: str):
    """
    [دالة موجودة للتأكيد]
    خدمة لحذف ترجمة معينة لفئة.
    """
    success = crud.delete_category_translation(db, category_id=category_id, language_code=language_code)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found.")
    return # لا نعيد شيئًا عند الحذف الناجح


def get_category_by_id(db: Session, category_id: int) -> models.ProductCategory:
    """خدمة لجلب فئة واحدة والتأكد من وجودها."""
    db_category = crud.get_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found."
        )
    return db_category