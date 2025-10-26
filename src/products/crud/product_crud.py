# backend/src/products/crud/product_crud.py

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

# --- الاستيراد المباشر من ملفات النماذج ---
from src.products.models import products_models as models
from src.products.schemas import product_schemas as schemas

# ==========================================================
# --- CRUD Functions for Product ---
# ==========================================================

def get_product(db: Session, product_id: UUID) -> Optional[models.Product]:
    """جلب منتج واحد مع كل علاقاته."""
    return db.query(models.Product).options(
        joinedload(models.Product.translations),
        joinedload(models.Product.packaging_options),
        joinedload(models.Product.category)
    ).filter(models.Product.product_id == product_id).first()

def get_all_products_by_seller(db: Session, seller_id: UUID) -> List[models.Product]:
    """جلب كل منتجات بائع معين."""
    return db.query(models.Product).filter(models.Product.seller_user_id == seller_id).all()

def create_product(db: Session, product_in: schemas.ProductCreate, seller_id: UUID, status_id: int) -> models.Product:
    """إنشاء منتج جديد مع ترجماته وخيارات التعبئة."""
    product_data = product_in.model_dump(exclude={"translations", "packaging_options"})
    db_product = models.Product(**product_data, seller_user_id=seller_id, product_status_id=status_id)

    for trans_in in product_in.translations:
        db_product.translations.append(models.ProductTranslation(**trans_in.model_dump()))

    for pkg_in in product_in.packaging_options:
        db_product.packaging_options.append(models.ProductPackagingOption(**pkg_in.model_dump()))

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, db_product: models.Product, product_in: schemas.ProductUpdate) -> models.Product:
    """تحديث بيانات منتج."""
    update_data = product_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def soft_delete_product(db: Session, db_product: models.Product, archived_status_id: int) -> models.Product:
    """الحذف الناعم للمنتج بتغيير حالته إلى 'مؤرشف'."""
    db_product.product_status_id = archived_status_id
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product_translation(db: Session, product_id: UUID, language_code: str) -> bool:
    """حذف ترجمة منتج معينة."""
    translation = db.query(models.ProductTranslation).filter_by(product_id=product_id, language_code=language_code).first()
    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False