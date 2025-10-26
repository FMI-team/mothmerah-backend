# backend\src\products\services\attribute_value_service.py

from sqlalchemy.orm import Session
from typing import List, Optional

# استيراد المودلز (للتعريفات والـ Type Hinting)
from src.products.models.attributes_models import AttributeValue, AttributeValueTranslation, ProductVarietyAttribute
# استيراد الـ Schemas
from src.products.schemas import attribute_schemas
# استيراد دوال الـ CRUD من الملف الخاص بها
from src.products.crud import attribute_value_crud
# استيراد الخدمات الأخرى للتحقق من الوجود (مثل خدمة السمة الأم)
from src.products.services.attribute_service import get_attribute_details
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)

# ==========================================================
# --- خدمات قيم السمات (Attribute Values) ---
# ==========================================================

def create_new_attribute_value(db: Session, value_in: attribute_schemas.AttributeValueCreate) -> AttributeValue:
    """
    خدمة لإنشاء قيمة سمة جديدة مع ترجماتها الاختيارية.
    تتضمن التحقق من وجود السمة الأم وعدم التكرار.
    """
    # منطق عمل: التحقق من وجود السمة الأم
    get_attribute_details(db, value_in.attribute_id) # هذه الدالة سترمي NotFoundException إذا لم تكن موجودة

    # منطق عمل: التحقق من عدم وجود قيمة سمة بنفس المفتاح لنفس السمة الأم
    existing_value_by_key = db.query(AttributeValue).filter(
        AttributeValue.attribute_id == value_in.attribute_id,
        AttributeValue.attribute_value_key == value_in.attribute_value_key
    ).first()
    if existing_value_by_key:
        raise ConflictException(detail=f"Attribute value with key '{value_in.attribute_value_key}' already exists for attribute ID {value_in.attribute_id}.")

    # استدعاء دالة CRUD للإنشاء
    return attribute_value_crud.create_attribute_value(db=db, value_in=value_in)

def get_all_attribute_values(db: Session, attribute_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[AttributeValue]:
    """
    خدمة لجلب جميع قيم السمات، مع إمكانية التصفية حسب السمة الأم.
    """
    return attribute_value_crud.get_all_attribute_values(db, attribute_id=attribute_id, skip=skip, limit=limit)

def get_attribute_value_details(db: Session, attribute_value_id: int) -> AttributeValue:
    """
    خدمة لجلب تفاصيل قيمة سمة واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    value = attribute_value_crud.get_attribute_value(db, attribute_value_id=attribute_value_id)
    if not value:
        raise NotFoundException(detail=f"Attribute value with ID {attribute_value_id} not found.")
    return value

def update_attribute_value(db: Session, attribute_value_id: int, value_in: attribute_schemas.AttributeValueUpdate) -> AttributeValue:
    """
    خدمة لتحديث قيمة سمة موجودة.
    """
    db_value = get_attribute_value_details(db, attribute_value_id) # استخدام دالة الخدمة للتحقق من الوجود

    # منطق عمل: إذا تم تحديث attribute_value_key، تحقق من عدم التكرار لنفس السمة الأم
    if value_in.attribute_value_key and value_in.attribute_value_key != db_value.attribute_value_key:
        existing_value_by_key = db.query(AttributeValue).filter(
            AttributeValue.attribute_id == db_value.attribute_id, # نفس السمة الأم
            AttributeValue.attribute_value_key == value_in.attribute_value_key
        ).first()
        if existing_value_by_key:
            raise ConflictException(detail=f"Attribute value with key '{value_in.attribute_value_key}' already exists for attribute ID {db_value.attribute_id}.")

    return attribute_value_crud.update_attribute_value(db=db, db_attribute_value=db_value, value_in=value_in)

def delete_attribute_value(db: Session, attribute_value_id: int):
    """
    خدمة لحذف قيمة سمة (حذف صارم).
    تتضمن التحقق من عدم وجود ارتباطات في ProductVarietyAttribute قبل الحذف.
    """
    db_value = get_attribute_value_details(db, attribute_value_id) # استخدام دالة الخدمة للتحقق من الوجود

    # منطق عمل: التحقق من وجود ارتباطات في جدول product_variety_attributes
    # إذا كانت هذه القيمة مستخدمة في أي صنف منتج، لا تسمح بالحذف
    if db.query(ProductVarietyAttribute).filter(ProductVarietyAttribute.attribute_value_id == attribute_value_id).count() > 0:
        raise ForbiddenException(detail=f"Cannot delete attribute value ID {attribute_value_id} because it is associated with existing product varieties. Please remove associations first.")

    attribute_value_crud.delete_attribute_value(db=db, db_attribute_value=db_value)
    return {"message": "Attribute value deleted successfully."}

# ==========================================================
# --- خدمات ترجمات قيم السمات (Attribute Value Translations) ---
# ==========================================================

def create_attribute_value_translation(db: Session, attribute_value_id: int, trans_in: attribute_schemas.AttributeValueTranslationCreate) -> AttributeValueTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لقيمة سمة معينة.
    تتضمن التحقق من وجود قيمة السمة الأم وعدم تكرار الترجمة.
    """
    # منطق عمل: التحقق من وجود قيمة السمة الأم
    get_attribute_value_details(db, attribute_value_id)

    # منطق عمل: التحقق من عدم وجود ترجمة بنفس اللغة لقيمة السمة
    existing_translation = attribute_value_crud.get_attribute_value_translation(db, attribute_value_id=attribute_value_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"Translation for attribute value ID {attribute_value_id} with language '{trans_in.language_code}' already exists.")

    return attribute_value_crud.create_attribute_value_translation(db=db, attribute_value_id=attribute_value_id, trans_in=trans_in)

def get_attribute_value_translation_details(db: Session, attribute_value_id: int, language_code: str) -> AttributeValueTranslation:
    """
    خدمة لجلب ترجمة محددة لقيمة سمة بلغة معينة، مع معالجة عدم الوجود.
    """
    translation = attribute_value_crud.get_attribute_value_translation(db, attribute_value_id=attribute_value_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"Translation for attribute value ID {attribute_value_id} in language '{language_code}' not found.")
    return translation

def update_attribute_value_translation(db: Session, attribute_value_id: int, language_code: str, trans_in: attribute_schemas.AttributeValueTranslationUpdate) -> AttributeValueTranslation:
    """
    خدمة لتحديث ترجمة قيمة سمة موجودة.
    """
    db_translation = get_attribute_value_translation_details(db, attribute_value_id, language_code) # استخدام دالة الخدمة للتحقق

    return attribute_value_crud.update_attribute_value_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_attribute_value_translation(db: Session, attribute_value_id: int, language_code: str):
    """
    خدمة لحذف ترجمة قيمة سمة معينة (حذف صارم).
    """
    db_translation = get_attribute_value_translation_details(db, attribute_value_id, language_code) # استخدام دالة الخدمة للتحقق
    attribute_value_crud.delete_attribute_value_translation(db=db, db_translation=db_translation)
    return {"message": "Attribute value translation deleted successfully."}