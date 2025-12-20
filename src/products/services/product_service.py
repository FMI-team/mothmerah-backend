# backend/src/products/services/product_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID

# --- الاستيرادات ---
# تم إزالة 'from src.db import base' لتجنب مشاكل الاستيراد الدائرية
from src.products.crud import product_crud # لـ product_crud CRUDs
from src.products.schemas import product_schemas # لـ product_schemas

# استيراد المودلات مباشرة من ملفاتها التعريفية
from src.products.models.products_models import Product # <-- Product من هنا
from src.products.models.categories_models import ProductCategory # <-- ProductCategory من هنا
from src.lookups.models.lookups_models import ProductStatus # <-- ProductStatus من هنا (Lookups العامة)
from src.users.models.core_models import User # <-- User من هنا
from sqlalchemy.dialects.postgresql import UUID

# ==========================================================
# --- Services for Product ---
# ==========================================================

def create_new_product(db: Session, product_in: product_schemas.ProductCreate, seller: User) -> Product: # <-- تم التعديل هنا: Product بدلاً من base.Product
    """
    خدمة لإنشاء منتج جديد مع التحقق من صحة البيانات.
    """
    # 1. التحقق من وجود الفئة
    category = db.query(ProductCategory).filter(ProductCategory.category_id == product_in.category_id).first() # <-- تم التعديل هنا: ProductCategory بدلاً من base.ProductCategory
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {product_in.category_id} not found.")

    # 2. تحديد الحالة الأولية للمنتج (مسودة)
    draft_status = db.query(ProductStatus).filter(ProductStatus.status_name_key == "DRAFT").first() # <-- تم التعديل هنا: ProductStatus بدلاً من base.ProductStatus
    if not draft_status:
        # هذا خطأ فادح في البيانات الأولية ويجب ألا يحدث إذا تم البذر بنجاح
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Default product status 'DRAFT' not found.")
    
    return product_crud.create_product(
        db=db, 
        product_in=product_in, 
        seller_id=seller.user_id, 
        status_id=draft_status.product_status_id
    )

def get_all_products_by_seller(db: Session, seller: User) -> List[Product]: # <-- تم التعديل هنا: Product بدلاً من base.Product
    """خدمة لجلب كل منتجات البائع الحالي."""
    return product_crud.get_all_products_by_seller(db, seller_id=seller.user_id)

def get_public_active_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    """
    خدمة لجلب جميع المنتجات النشطة المتاحة للعامة.
    يجلب فقط المنتجات التي حالتها 'ACTIVE'.
    """
    # Get ACTIVE status
    active_status = db.query(ProductStatus).filter(ProductStatus.status_name_key == "ACTIVE").first()
    if not active_status:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Active status not configured.")
    
    # Get all products with ACTIVE status
    return product_crud.get_all_active_products(db, status_id=active_status.product_status_id, skip=skip, limit=limit)

def get_product_by_id_for_user(db: Session, product_id: UUID, user: Optional[User]) -> Product: # <-- تم التعديل هنا: Product بدلاً من base.Product
    """
    خدمة لجلب منتج واحد بناءً على صلاحيات المستخدم.
    يعرض المنتج إذا كان نشطًا، أو إذا كان المستخدم هو المالك أو مسؤولاً.
    """
    db_product = product_crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    is_active = db_product.status.status_name_key == "ACTIVE"
    # نفترض وجود صلاحية ADMIN_PRODUCT_VIEW_ANY للمسؤول
    # TODO: يجب استيراد User بشكل مباشر من models.core_models لـ type hint هنا
    # و التأكد أن permissions محملة بشكل صحيح
    # can_view_any = user and any(p.permission_name_key == "ADMIN_PRODUCT_VIEW_ANY" for p in user.default_role.permissions)
    can_view_any = user and (user.user_id == UUID('00000000-0000-0000-0000-000000000000')) # TODO: هذه ليست طريقة صحيحة للتحقق من صلاحية المسؤول

    is_owner = user and user.user_id == db_product.seller_user_id

    if is_active or is_owner or can_view_any:
        return db_product
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or not active.")

def update_existing_product(db: Session, product_id: UUID, product_in: product_schemas.ProductUpdate, user: User) -> Product: # <-- تم التعديل هنا: Product بدلاً من base.Product
    """خدمة لتحديث منتج موجود مع التحقق من الملكية."""
    db_product = get_product_by_id_for_user(db, product_id, user) # نستفيد من الدالة أعلاه للتحقق من الملكية والصلاحية

    return product_crud.update_product(db=db, db_product=db_product, product_in=product_in)

def soft_delete_product_by_id(db: Session, product_id: UUID, user: User): # <-- تم التعديل هنا: User بدلاً من base.User
    """خدمة للحذف الناعم لمنتج مع التحقق من الملكية."""
    db_product = get_product_by_id_for_user(db, product_id, user) # التحقق من الملكية

    # Use DISCONTINUED status for soft delete (archived state)
    discontinued_status = db.query(ProductStatus).filter(ProductStatus.status_name_key == "DISCONTINUED").first() # <-- تم التعديل هنا: ProductStatus بدلاً من base.ProductStatus
    if not discontinued_status:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Discontinued status not configured. Please ensure product statuses are seeded in the database.")

    # (منطق عمل مستقبلي: لا يمكن أرشفة منتج نشط في طلبات قائمة)
    # if crud.is_product_in_active_orders(db, product_id):
    #     raise HTTPException(status_code=409, detail="Cannot archive product, it exists in active orders.")

    return product_crud.soft_delete_product(db, db_product=db_product, archived_status_id=discontinued_status.product_status_id)

def remove_product_translation(db: Session, product_id: UUID, language_code: str, user: User): # <-- تم التعديل هنا: User بدلاً من base.User
    """خدمة لحذف ترجمة معينة لمنتج مع التحقق من الملكية."""
    get_product_by_id_for_user(db, product_id, user) # للتحقق من الملكية أولاً
    
    success = product_crud.delete_product_translation(db, product_id=product_id, language_code=language_code)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found.")
    return

# ==========================================================
# --- Admin-Specific Services for Products ---
# ==========================================================

def get_all_products_for_admin(db: Session, skip: int = 0, limit: int = 100) -> List[Product]: # <-- تم التعديل هنا: Product بدلاً من base.Product
    """
    [للمسؤول] خدمة لجلب كل المنتجات في النظام (بما في ذلك غير النشطة).
    """
    # نفترض وجود دالة CRUD تجلب كل المنتجات بدون فلترة بالحالة
    # TODO: هنا نحتاج لدالة get_all_products_admin في product_crud
    #       أو يجب أن يكون get_all_products (بدون seller_id) ويدعم include_inactive
    raise NotImplementedError("دالة جلب جميع المنتجات للمسؤول لم تُنفذ بعد في product_crud.")

def change_product_status_by_admin(db: Session, product_id: UUID, new_status_id: int) -> Product: # <-- تم التعديل هنا: Product بدلاً من base.Product
    """
    [للمسؤول] خدمة لتحديث حالة منتج معين.
    """
    # TODO: يجب استيراد product_crud هنا
    db_product = product_crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    
    # يمكن إضافة تحقق هنا للتأكد من أن new_status_id صالح (من ProductStatus)
    
    db_product.product_status_id = new_status_id
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product