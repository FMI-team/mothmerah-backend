# backend\src\products\crud\product_variety_attribute_crud.py

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID # قد تحتاج UUID لـ product_variety_id إذا كان UUID في المودل

from src.products.models import attributes_models as models # استيراد المودلز
from src.products.schemas import attribute_schemas as schemas # استيراد الـ Schemas

# ==========================================================
# --- CRUD Functions for ProductVarietyAttribute ---
# ==========================================================

def create_product_variety_attribute(db: Session, link_in: schemas.ProductVarietyAttributeCreate) -> models.ProductVarietyAttribute:
    """
    ينشئ ربطًا جديدًا بين صنف منتج وسمة وقيمتها في قاعدة البيانات.
    """
    db_link = models.ProductVarietyAttribute(
        product_variety_id=link_in.product_variety_id,
        attribute_id=link_in.attribute_id,
        attribute_value_id=link_in.attribute_value_id
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def get_product_variety_attribute(db: Session, product_variety_attribute_id: int) -> Optional[models.ProductVarietyAttribute]:
    """
    يجلب ربط سمة صنف منتج واحد بالـ ID الخاص به.
    """
    return db.query(models.ProductVarietyAttribute).filter(
        models.ProductVarietyAttribute.product_variety_attribute_id == product_variety_attribute_id
    ).first()

def get_product_variety_attributes_for_variety(db: Session, product_variety_id: int) -> List[models.ProductVarietyAttribute]:
    """
    يجلب جميع ارتباطات السمات لصنف منتج معين.
    """
    query = db.query(models.ProductVarietyAttribute).filter(
        models.ProductVarietyAttribute.product_variety_id == product_variety_id
    )
    # يمكن هنا إضافة joinedload لجلب تفاصيل السمة وقيمتها إذا كانت العلاقات معرفة في المودل
    # مثال: .options(joinedload(models.ProductVarietyAttribute.attribute), joinedload(models.ProductVarietyAttribute.attribute_value))
    return query.all()

def delete_product_variety_attribute(db: Session, db_link: models.ProductVarietyAttribute):
    """
    يحذف ربط سمة صنف منتج معين (حذف صارم).
    """
    db.delete(db_link)
    db.commit()
    return