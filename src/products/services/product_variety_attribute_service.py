# backend\src\products\services\product_variety_attribute_service.py

from sqlalchemy.orm import Session
from typing import List, Optional

# استيراد المودلز (للتعريفات والـ Type Hinting)
from src.products.models.attributes_models import ProductVarietyAttribute
# استيراد الـ Schemas
from src.products.schemas import attribute_schemas
# استيراد دوال الـ CRUD من الملف الخاص بها
from src.products.crud import product_variety_attribute_crud
# استيراد الخدمات الأخرى للتحقق من وجود الكيانات المرتبطة
from src.products.services.attribute_service import get_attribute_details
from src.products.services.attribute_value_service import get_attribute_value_details
# من المفترض أن يكون لديك خدمة لجلب تفاصيل صنف المنتج (ProductVariety) من المجموعة 2.أ
# سأفترض وجودها حاليًا أو يمكنك استبدالها بدالة CRUD مباشرة إذا لم يكن هناك خدمة
# مثال افتراضي:
# from src.products.services.variety_service import get_variety_details # يجب أن تقوم بإنشاء هذه الخدمة لاحقًا
from src.products.crud.variety_crud import get_variety as crud_get_variety # استخدام CRUD مؤقتًا لـ ProductVariety

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)

# ==========================================================
# --- خدمات ربط الأصناف بالسمات وقيمها (Product Variety Attributes) ---
# ==========================================================

def create_product_variety_attribute(db: Session, link_in: attribute_schemas.ProductVarietyAttributeCreate) -> ProductVarietyAttribute:
    """
    خدمة لإنشاء ربط جديد بين صنف منتج وسمة وقيمتها.
    تتضمن التحقق من وجود الكيانات المرتبطة وعدم تكرار الربط.
    """
    # منطق عمل: التحقق من وجود صنف المنتج (ProductVariety)
    # ملاحظة: سأستخدم get_variety من variety_crud مؤقتاً، ولكن يفضل استخدام دالة خدمة هنا
    db_variety = crud_get_variety(db, link_in.product_variety_id)
    if not db_variety:
        raise NotFoundException(detail=f"Product Variety with ID {link_in.product_variety_id} not found.")

    # منطق عمل: التحقق من وجود السمة (Attribute)
    get_attribute_details(db, link_in.attribute_id) # هذه الدالة سترمي NotFoundException إذا لم تكن موجودة

    # منطق عمل: التحقق من وجود قيمة السمة (AttributeValue)
    get_attribute_value_details(db, link_in.attribute_value_id) # هذه الدالة سترمي NotFoundException إذا لم تكن موجودة

    # منطق عمل: التحقق من أن قيمة السمة (attribute_value_id) تنتمي بالفعل إلى السمة (attribute_id) المحددة
    # هذا يمنع ربط قيمة 'أحمر' (من سمة اللون) بسمة 'الحجم' مثلاً.
    db_attribute_value = get_attribute_value_details(db, link_in.attribute_value_id)
    if db_attribute_value.attribute_id != link_in.attribute_id:
        raise BadRequestException(detail=f"Attribute Value ID {link_in.attribute_value_id} does not belong to Attribute ID {link_in.attribute_id}.")

    # منطق عمل: التحقق من عدم وجود نفس الربط مسبقًا
    existing_link = db.query(ProductVarietyAttribute).filter(
        ProductVarietyAttribute.product_variety_id == link_in.product_variety_id,
        ProductVarietyAttribute.attribute_id == link_in.attribute_id,
        ProductVarietyAttribute.attribute_value_id == link_in.attribute_value_id
    ).first()
    if existing_link:
        raise ConflictException(detail="This product variety attribute link already exists.")

    # استدعاء دالة CRUD للإنشاء
    return product_variety_attribute_crud.create_product_variety_attribute(db=db, link_in=link_in)

def get_all_product_variety_attributes(db: Session, skip: int = 0, limit: int = 100) -> List[ProductVarietyAttribute]:
    """
    خدمة لجلب جميع ارتباطات سمات أصناف المنتجات.
    """
    return product_variety_attribute_crud.get_all_product_variety_attributes(db, skip=skip, limit=limit)

def get_product_variety_attribute_details(db: Session, product_variety_attribute_id: int) -> ProductVarietyAttribute:
    """
    خدمة لجلب ربط سمة صنف منتج واحد بالـ ID، مع معالجة عدم الوجود.
    """
    link = product_variety_attribute_crud.get_product_variety_attribute(db, product_variety_attribute_id=product_variety_attribute_id)
    if not link:
        raise NotFoundException(detail=f"Product variety attribute link with ID {product_variety_attribute_id} not found.")
    return link

def delete_product_variety_attribute(db: Session, product_variety_attribute_id: int):
    """
    خدمة لحذف ربط سمة صنف منتج معين (حذف صارم).
    """
    db_link = get_product_variety_attribute_details(db, product_variety_attribute_id) # استخدام دالة الخدمة للتحقق
    product_variety_attribute_crud.delete_product_variety_attribute(db=db, db_link=db_link)
    return {"message": "Product variety attribute link deleted successfully."}

def get_attributes_for_variety(db: Session, product_variety_id: int) -> List[ProductVarietyAttribute]:
    """
    خدمة لجلب جميع السمات المرتبطة بصنف منتج معين.
    """
    # يمكن إضافة تحقق من وجود Product Variety هنا إذا لزم الأمر
    return product_variety_attribute_crud.get_product_variety_attributes_for_variety(db, product_variety_id=product_variety_id)