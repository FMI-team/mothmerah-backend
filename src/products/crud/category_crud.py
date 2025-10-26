# backend/src/products/crud/category_crud.py

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from src.products.models import categories_models as models
from src.products.models import products_models
from src.products.schemas import category_schemas as schemas

# ==========================================================
# --- CRUD Functions for ProductCategory ---
# ==========================================================

def get_all_product_categories(db: Session) -> List[models.ProductCategory]:
    """جلب كل فئات المنتجات مع ترجماتها."""
    return db.query(models.ProductCategory).options(
        joinedload(models.ProductCategory.translations)
    ).order_by(models.ProductCategory.sort_order, models.ProductCategory.category_name_key).all()

def get_category(db: Session, category_id: int) -> Optional[models.ProductCategory]:
    """جلب فئة منتج واحدة عن طريق الـ ID الخاص بها."""
    return db.query(models.ProductCategory).filter(models.ProductCategory.category_id == category_id).first()

def get_category_by_key(db: Session, key: str) -> Optional[models.ProductCategory]:
    """جلب فئة منتج عن طريق مفتاحها النصي."""
    return db.query(models.ProductCategory).filter(models.ProductCategory.category_name_key == key).first()

def create_category(db: Session, category_in: schemas.ProductCategoryCreate) -> models.ProductCategory:
    """إنشاء فئة منتج جديدة مع ترجماتها الأولية."""
    db_category = models.ProductCategory(
        **category_in.model_dump(exclude={"translations"})
    )
    if category_in.translations:
        for trans in category_in.translations:
            db_category.translations.append(
                models.ProductCategoryTranslation(**trans.model_dump())
            )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, db_category: models.ProductCategory, category_in: schemas.ProductCategoryUpdate) -> models.ProductCategory:
    """تحديث بيانات فئة منتج موجودة."""
    update_data = category_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def count_products_in_category(db: Session, category_id: int) -> int:
    """يحسب عدد المنتجات المرتبطة بفئة معينة."""
    return db.query(products_models.Product).filter(products_models.Product.category_id == category_id).count()

def delete_category(db: Session, db_category: models.ProductCategory) -> None:
    """حذف فئة منتج من قاعدة البيانات."""
    db.delete(db_category)
    # الـ Commit سيتم من طبقة الخدمات لضمان سلامة العملية
    return

# ==========================================================
# --- CRUD Functions for ProductCategoryTranslation ---
# ==========================================================

def add_or_update_category_translation(db: Session, category_id: int, trans_in: schemas.ProductCategoryTranslationCreate) -> Optional[models.ProductCategory]:
    """إضافة أو تحديث ترجمة لفئة منتج."""
    db_category = db.query(models.ProductCategory).options(joinedload(models.ProductCategory.translations)).filter(models.ProductCategory.category_id == category_id).first()
    if not db_category:
        return None

    existing_trans = next((t for t in db_category.translations if t.language_code == trans_in.language_code), None)
    if existing_trans:
        existing_trans.translated_category_name = trans_in.translated_category_name
        existing_trans.translated_category_description = trans_in.translated_category_description
    else:
        new_trans = models.ProductCategoryTranslation(category_id=category_id, **trans_in.model_dump())
        db.add(new_trans)
    
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category_translation(db: Session, category_id: int, language_code: str) -> bool:
    """حذف ترجمة فئة منتج معينة."""
    translation = db.query(models.ProductCategoryTranslation).filter_by(category_id=category_id, language_code=language_code).first()
    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False


# ... (دوال CRUD الحالية) ...

def reassign_products_to_default_category(db: Session, old_category_id: int, default_category_id: int):
    """يقوم بتحديث كل المنتجات من فئة معينة ونقلهم إلى الفئة الافتراضية."""
    db.query(models.Product).filter(
        models.Product.category_id == old_category_id
    ).update({models.Product.category_id: default_category_id})
    return

def soft_delete_category(db: Session, db_category: models.ProductCategory) -> models.ProductCategory:
    """
    يقوم بالحذف الناعم للفئة عن طريق تحديث حالتها إلى غير نشطة.
    """
    db_category.is_active = False
    db.add(db_category)
    # الـ Commit سيتم من طبقة الخدمات
    return db_category

def delete_category_translation(db: Session, category_id: int, language_code: str) -> bool:
    """
    [دالة موجودة للتأكيد]
    يحذف ترجمة فئة منتج معينة.
    """
    translation = db.query(models.ProductCategoryTranslation).filter_by(category_id=category_id, language_code=language_code).first()
    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False

def get_category(db: Session, category_id: int) -> Optional[models.ProductCategory]:
    """جلب فئة منتج واحدة عن طريق الـ ID الخاص بها مع ترجماتها."""
    return db.query(models.ProductCategory).options(
        joinedload(models.ProductCategory.translations)
    ).filter(models.ProductCategory.category_id == category_id).first()
