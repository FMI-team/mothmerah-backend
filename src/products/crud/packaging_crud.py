# backend\src\products\crud\packaging_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID

from src.products.models import units_models as models # استيراد المودلز (ProductPackagingOption و ProductPackagingOptionTranslation موجودة هنا)
from src.products.schemas import packaging_schemas as schemas # استيراد الـ Schemas

# ==========================================================
# --- CRUD Functions for ProductPackagingOption ---
# ==========================================================

def create_packaging_option(db: Session, option_in: schemas.PackagingOptionCreate, product_id: UUID) -> models.ProductPackagingOption:
    """
    ينشئ خيار تعبئة جديد في قاعدة البيانات، مع ترجماته المضمنة.
    """
    db_option = models.ProductPackagingOption(
        product_id=product_id,
        packaging_option_name_key=option_in.packaging_option_name_key,
        custom_packaging_description=option_in.custom_packaging_description,
        quantity_in_packaging=option_in.quantity_in_packaging,
        unit_of_measure_id_for_quantity=option_in.unit_of_measure_id_for_quantity,
        base_price=option_in.base_price,
        sku=option_in.sku,
        barcode=option_in.barcode,
        is_default_option=option_in.is_default_option,
        is_active=option_in.is_active,
        sort_order=option_in.sort_order
    )
    db.add(db_option)
    db.flush() # للحصول على packaging_option_id قبل حفظ الترجمات

    if option_in.translations:
        for trans_in in option_in.translations:
            db_translation = models.ProductPackagingOptionTranslation(
                packaging_option_id=db_option.packaging_option_id,
                language_code=trans_in.language_code,
                translated_packaging_option_name=trans_in.translated_packaging_option_name,
                translated_custom_description=trans_in.translated_custom_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_option)
    return db_option

def get_packaging_option(db: Session, packaging_option_id: int) -> Optional[models.ProductPackagingOption]:
    """
    يجلب خيار تعبئة واحد بالـ ID الخاص به، مع ترجماته ووحدة القياس.
    """
    return db.query(models.ProductPackagingOption).options(
        joinedload(models.ProductPackagingOption.translations),
        joinedload(models.ProductPackagingOption.unit_of_measure) # تحميل وحدة القياس المرتبطة
    ).filter(models.ProductPackagingOption.packaging_option_id == packaging_option_id).first()

def get_all_packaging_options_for_product(db: Session, product_id: UUID, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[models.ProductPackagingOption]:
    """
    يجلب قائمة بخيارات التعبئة لمنتج معين، مع خيار لتضمين غير النشطة.
    """
    query = db.query(models.ProductPackagingOption).options(
        joinedload(models.ProductPackagingOption.translations),
        joinedload(models.ProductPackagingOption.unit_of_measure) # تحميل وحدة القياس المرتبطة
    ).filter(models.ProductPackagingOption.product_id == product_id)

    if not include_inactive:
        query = query.filter(models.ProductPackagingOption.is_active == True)
    
    return query.offset(skip).limit(limit).all()

def update_packaging_option(db: Session, db_option: models.ProductPackagingOption, option_in: schemas.PackagingOptionUpdate) -> models.ProductPackagingOption:
    """
    يحدث بيانات خيار تعبئة موجود.
    """
    update_data = option_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_option, key, value)
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    return db_option

def soft_delete_packaging_option(db: Session, db_option: models.ProductPackagingOption) -> models.ProductPackagingOption:
    """
    يقوم بالحذف الناعم لخيار تعبئة عن طريق تعيين 'is_active' إلى False.
    """
    db_option.is_active = False
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    return db_option

# ==========================================================
# --- CRUD Functions for ProductPackagingOptionTranslation ---
# ==========================================================

def create_packaging_option_translation(db: Session, packaging_option_id: int, trans_in: schemas.ProductPackagingOptionTranslationCreate) -> models.ProductPackagingOptionTranslation:
    """
    ينشئ ترجمة جديدة لخيار تعبئة معين.
    """
    db_translation = models.ProductPackagingOptionTranslation(
        packaging_option_id=packaging_option_id,
        language_code=trans_in.language_code,
        translated_packaging_option_name=trans_in.translated_packaging_option_name,
        translated_custom_description=trans_in.translated_custom_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_packaging_option_translation(db: Session, packaging_option_id: int, language_code: str) -> Optional[models.ProductPackagingOptionTranslation]:
    """
    يجلب ترجمة خيار تعبئة محددة بالـ ID الخاص بالخيار ورمز اللغة.
    """
    return db.query(models.ProductPackagingOptionTranslation).filter(
        and_(
            models.ProductPackagingOptionTranslation.packaging_option_id == packaging_option_id,
            models.ProductPackagingOptionTranslation.language_code == language_code
        )
    ).first()

def update_packaging_option_translation(db: Session, db_translation: models.ProductPackagingOptionTranslation, trans_in: schemas.ProductPackagingOptionTranslationUpdate) -> models.ProductPackagingOptionTranslation:
    """
    يحدث ترجمة خيار تعبئة موجودة.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_packaging_option_translation(db: Session, db_translation: models.ProductPackagingOptionTranslation):
    """
    يحذف ترجمة خيار تعبئة معينة (حذف صارم).
    """
    db.delete(db_translation)
    db.commit()
    return