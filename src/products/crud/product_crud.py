# backend/src/products/crud/product_crud.py

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

# --- الاستيراد المباشر من ملفات النماذج ---
from src.products.models import products_models as models
from src.products.models.units_models import ProductPackagingOption
from src.products.schemas import product_schemas as schemas

# ==========================================================
# --- CRUD Functions for Product ---
# ==========================================================

def get_product(db: Session, product_id: UUID) -> Optional[models.Product]:
    """جلب منتج واحد مع كل علاقاته."""
    from src.products.models.units_models import ProductPackagingOption
    from src.lookups.models.lookups_models import ProductStatus
    
    return db.query(models.Product).options(
        joinedload(models.Product.translations),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.unit_of_measure),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.translations),
        joinedload(models.Product.category),
        joinedload(models.Product.status),
        joinedload(models.Product.unit_of_measure)
    ).join(ProductStatus, models.Product.product_status_id == ProductStatus.product_status_id).filter(
        models.Product.product_id == product_id
    ).first()

def get_all_products_by_seller(db: Session, seller_id: UUID) -> List[models.Product]:
    """جلب كل منتجات بائع معين مع جميع علاقاته."""
    from src.products.models.units_models import ProductPackagingOption
    from src.lookups.models.lookups_models import ProductStatus
    
    products = db.query(models.Product).options(
        joinedload(models.Product.category),
        joinedload(models.Product.status),
        joinedload(models.Product.unit_of_measure),
        joinedload(models.Product.translations),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.unit_of_measure),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.translations)
    ).join(ProductStatus, models.Product.product_status_id == ProductStatus.product_status_id).filter(
        models.Product.seller_user_id == seller_id
    ).all()
    
    # Filter out any products with None status (data integrity issue)
    return [p for p in products if p.status is not None]

def get_all_active_products(db: Session, status_id: int, skip: int = 0, limit: int = 100) -> List[models.Product]:
    """جلب جميع المنتجات النشطة مع جميع علاقاته."""
    from src.products.models.units_models import ProductPackagingOption
    from src.lookups.models.lookups_models import ProductStatus
    
    products = db.query(models.Product).options(
        joinedload(models.Product.category),
        joinedload(models.Product.status),
        joinedload(models.Product.unit_of_measure),
        joinedload(models.Product.translations),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.unit_of_measure),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.translations)
    ).join(ProductStatus, models.Product.product_status_id == ProductStatus.product_status_id).filter(
        models.Product.product_status_id == status_id
    ).offset(skip).limit(limit).all()
    
    # Filter out any products with None status (data integrity issue)
    return [p for p in products if p.status is not None]

def create_product(db: Session, product_in: schemas.ProductCreate, seller_id: UUID, status_id: int) -> models.Product:
    """إنشاء منتج جديد مع ترجماته وخيارات التعبئة."""
    from src.products.models.units_models import ProductPackagingOptionTranslation
    
    product_data = product_in.model_dump(exclude={"translations", "packaging_options"})
    db_product = models.Product(**product_data, seller_user_id=seller_id, product_status_id=status_id)

    # إضافة الترجمات للمنتج
    for trans_in in product_in.translations:
        db_product.translations.append(models.ProductTranslation(**trans_in.model_dump()))

    # إضافة خيارات التعبئة مع ترجماتها
    for pkg_in in product_in.packaging_options:
        packaging_data = pkg_in.model_dump(exclude={"translations"})
        db_packaging_option = ProductPackagingOption(**packaging_data)
        
        # إضافة ترجمات خيار التعبئة
        if pkg_in.translations:
            for trans_in in pkg_in.translations:
                db_translation = ProductPackagingOptionTranslation(
                    language_code=trans_in.language_code,
                    translated_packaging_option_name=trans_in.translated_packaging_option_name,
                    translated_custom_description=trans_in.translated_custom_description
                )
                db_packaging_option.translations.append(db_translation)
        
        db_product.packaging_options.append(db_packaging_option)

    db.add(db_product)
    db.commit()
    
    # Eagerly load all relationships after creation (same pattern as get_product)
    product_id = db_product.product_id
    created_product = db.query(models.Product).options(
        joinedload(models.Product.translations),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.unit_of_measure),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.translations),
        joinedload(models.Product.category),
        joinedload(models.Product.status),
        joinedload(models.Product.unit_of_measure)
    ).filter(models.Product.product_id == product_id).first()
    
    if not created_product:
        raise ValueError(f"Product with id {product_id} not found after creation")
    
    # Verify required relationships are loaded
    if created_product.status is None:
        raise ValueError(f"Product status could not be loaded for product {product_id}")
    if created_product.category is None:
        raise ValueError(f"Product category could not be loaded for product {product_id}")
    
    return created_product

def update_product(db: Session, db_product: models.Product, product_in: schemas.ProductUpdate) -> models.Product:
    """تحديث بيانات منتج."""
    from src.products.models.units_models import ProductPackagingOption
    from src.lookups.models.lookups_models import ProductStatus
    from src.products.models.categories_models import ProductCategory
    
    # Validate category exists if category_id is being updated
    update_data = product_in.model_dump(exclude_unset=True)
    if 'category_id' in update_data:
        category = db.query(ProductCategory).filter(ProductCategory.category_id == update_data['category_id']).first()
        if not category:
            raise ValueError(f"Category with id {update_data['category_id']} does not exist")
    
    # Store product_id before update
    product_id = db_product.product_id
    
    # Update the product
    for key, value in update_data.items():
        setattr(db_product, key, value)
    db.add(db_product)
    db.commit()
    
    # Eagerly load all relationships after update - use the same pattern as get_product
    # Don't use INNER JOINs here as they can exclude the product if relationships fail
    updated_product = db.query(models.Product).options(
        joinedload(models.Product.category),
        joinedload(models.Product.status),
        joinedload(models.Product.unit_of_measure),
        joinedload(models.Product.translations),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.unit_of_measure),
        joinedload(models.Product.packaging_options).joinedload(ProductPackagingOption.translations)
    ).filter(models.Product.product_id == product_id).first()
    
    if not updated_product:
        # This should never happen, but if it does, the product still exists in DB
        # Just reload it without joins to verify it exists
        product_exists = db.query(models.Product).filter(models.Product.product_id == product_id).first()
        if product_exists:
            # Product exists but relationships failed to load - reload with basic query
            db.refresh(product_exists)
            return product_exists
        else:
            raise ValueError(f"Product with id {product_id} was deleted during update")
    
    # Verify status is loaded (required field)
    if updated_product.status is None:
        # Force reload status
        db.refresh(updated_product, ['status'])
        if updated_product.status is None:
            raise ValueError(f"Product status could not be loaded for product {product_id}")
    
    return updated_product

def soft_delete_product(db: Session, db_product: models.Product, archived_status_id: int) -> dict:
    """الحذف الناعم للمنتج بتغيير حالته إلى 'مؤرشف'."""
    db_product.product_status_id = archived_status_id
    db.add(db_product)
    db.commit()
    return {"message": "Product has been discontinued (soft deleted)", "product_id": str(db_product.product_id)}

def delete_product_translation(db: Session, product_id: UUID, language_code: str) -> bool:
    """حذف ترجمة منتج معينة."""
    translation = db.query(models.ProductTranslation).filter_by(product_id=product_id, language_code=language_code).first()
    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False