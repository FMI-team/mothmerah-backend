# backend\src\products\services\attribute_service.py
from sqlalchemy.orm import Session
from typing import List, Optional

# استيراد المودلز (للتعريفات والـ Type Hinting)
from src.products.models.attributes_models import Attribute, AttributeTranslation, AttributeValue, ProductVarietyAttribute
# استيراد الـ Schemas
from src.products.schemas import attribute_schemas
# استيراد دوال الـ CRUD من الملف الجديد
from src.products.crud import attribute_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)

# ==========================================================
# --- خدمات السمات العامة (Attributes) ---
# ==========================================================

def create_new_attribute(db: Session, attribute_in: attribute_schemas.AttributeCreate) -> Attribute:
    """
    خدمة لإنشاء سمة جديدة مع ترجماتها الاختيارية.
    تتضمن التحقق من عدم التكرار.
    """
    # منطق عمل: التحقق من عدم وجود سمة بنفس المفتاح قبل محاولة الإنشاء في CRUD
    existing_attribute_by_key = db.query(Attribute).filter(Attribute.attribute_name_key == attribute_in.attribute_name_key).first()
    if existing_attribute_by_key:
        raise ConflictException(detail=f"Attribute with name key '{attribute_in.attribute_name_key}' already exists.")

    # استدعاء دالة CRUD للإنشاء
    return attribute_crud.create_attribute(db=db, attribute_in=attribute_in)

def get_all_attributes(db: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[Attribute]:
    """
    خدمة لجلب جميع السمات، مع خيار لتضمين السمات غير النشطة.
    """
    return attribute_crud.get_all_attributes(db, skip=skip, limit=limit, include_inactive=include_inactive)

def get_attribute_details(db: Session, attribute_id: int) -> Attribute:
    """
    خدمة لجلب تفاصيل سمة واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    attribute = attribute_crud.get_attribute(db, attribute_id=attribute_id)
    if not attribute:
        raise NotFoundException(detail=f"Attribute with ID {attribute_id} not found.")
    return attribute

def update_attribute(db: Session, attribute_id: int, attribute_in: attribute_schemas.AttributeUpdate) -> Attribute:
    """
    خدمة لتحديث سمة موجودة.
    """
    db_attribute = get_attribute_details(db, attribute_id) # استخدام دالة الخدمة للتحقق من الوجود

    # منطق عمل: إذا تم تحديث attribute_name_key، تحقق من عدم التكرار
    if attribute_in.attribute_name_key and attribute_in.attribute_name_key != db_attribute.attribute_name_key:
        existing_attribute_by_key = db.query(Attribute).filter(Attribute.attribute_name_key == attribute_in.attribute_name_key).first()
        if existing_attribute_by_key:
            raise ConflictException(detail=f"Attribute with name key '{attribute_in.attribute_name_key}' already exists.")

    return attribute_crud.update_attribute(db=db, db_attribute=db_attribute, attribute_in=attribute_in)

def soft_delete_attribute(db: Session, attribute_id: int) -> Attribute:
    """
    خدمة للحذف الناعم لسمة بتعيين is_active إلى False.
    تتضمن التحقق من عدم استخدام السمة.
    """
    db_attribute = get_attribute_details(db, attribute_id)
    if not db_attribute.is_active:
        raise BadRequestException(detail=f"Attribute with ID {attribute_id} is already inactive.")

    # منطق عمل: التحقق من عدم ارتباط السمة بأي قيم نشطة أو أصناف منتجات نشطة
    # هذا يتطلب استعلامًا لـ AttributeValue و ProductVarietyAttribute
    # التحقق من وجود قيم للسمة (AttributeValue)
    if db.query(AttributeValue).filter(AttributeValue.attribute_id == attribute_id).count() > 0:
         raise ForbiddenException(
             detail=f"Cannot soft-delete attribute ID {attribute_id} because it has associated attribute values. Please delete/deactivate values first."
         )
    # التحقق من ارتباط السمة بأي ProductVarietyAttribute مباشرة (إذا لم يتم التصفية حسب قيمة السمة)
    if db.query(ProductVarietyAttribute).filter(ProductVarietyAttribute.attribute_id == attribute_id).count() > 0:
        raise ForbiddenException(
            detail=f"Cannot soft-delete attribute ID {attribute_id} because it is directly linked to product varieties. Please remove these links first."
        )

    return attribute_crud.soft_delete_attribute(db=db, db_attribute=db_attribute)

# ==========================================================
# --- خدمات ترجمات السمات العامة (Attribute Translations) ---
# ==========================================================

def create_attribute_translation(db: Session, attribute_id: int, trans_in: attribute_schemas.AttributeTranslationCreate) -> AttributeTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لسمة معينة.
    تتضمن التحقق من وجود السمة الأم وعدم تكرار الترجمة.
    """
    # منطق عمل: التحقق من وجود السمة الأم
    get_attribute_details(db, attribute_id)

    # منطق عمل: التحقق من عدم وجود ترجمة بنفس اللغة للسمة
    existing_translation = attribute_crud.get_attribute_translation(db, attribute_id=attribute_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"Translation for attribute ID {attribute_id} with language '{trans_in.language_code}' already exists.")

    return attribute_crud.create_attribute_translation(db=db, attribute_id=attribute_id, trans_in=trans_in)

def get_attribute_translation_details(db: Session, attribute_id: int, language_code: str) -> AttributeTranslation:
    """
    خدمة لجلب ترجمة سمة محددة بلغة معينة، مع معالجة عدم الوجود.
    """
    translation = attribute_crud.get_attribute_translation(db, attribute_id=attribute_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"Translation for attribute ID {attribute_id} in language '{language_code}' not found.")
    return translation

def update_attribute_translation(db: Session, attribute_id: int, language_code: str, trans_in: attribute_schemas.AttributeTranslationUpdate) -> AttributeTranslation:
    """
    خدمة لتحديث ترجمة سمة موجودة.
    """
    db_translation = get_attribute_translation_details(db, attribute_id, language_code) # استخدام دالة الخدمة للتحقق

    return attribute_crud.update_attribute_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_attribute_translation(db: Session, attribute_id: int, language_code: str):
    """
    خدمة لحذف ترجمة سمة معينة (حذف صارم).
    """
    db_translation = get_attribute_translation_details(db, attribute_id, language_code) # استخدام دالة الخدمة للتحقق
    attribute_crud.delete_attribute_translation(db=db, db_translation=db_translation)
    return {"message": "Attribute translation deleted successfully."}