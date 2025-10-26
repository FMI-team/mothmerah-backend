# backend\src\products\services\unit_of_measure_service.py

from sqlalchemy.orm import Session
from typing import List, Optional

# استيراد المودلز (للتعريفات والـ Type Hinting)
from src.products.models.units_models import UnitOfMeasure, UnitOfMeasureTranslation
# استيراد الـ Schemas
from src.products.schemas import units_schemas
# استيراد دوال الـ CRUD من الملف الخاص بها
from src.products.crud import unit_of_measure_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)

# ==========================================================
# --- خدمات وحدات القياس (UnitOfMeasure) ---
# ==========================================================

def create_new_unit_of_measure(db: Session, unit_in: units_schemas.UnitOfMeasureCreate) -> UnitOfMeasure:
    """
    خدمة لإنشاء وحدة قياس جديدة مع ترجماتها الاختيارية.
    تتضمن التحقق من عدم التكرار لمفتاحي الاسم والاختصار.
    """
    # منطق عمل: التحقق من عدم وجود وحدة قياس بنفس مفتاح الاسم
    existing_unit_by_name = db.query(UnitOfMeasure).filter(UnitOfMeasure.unit_name_key == unit_in.unit_name_key).first()
    if existing_unit_by_name:
        raise ConflictException(detail=f"Unit of measure with name key '{unit_in.unit_name_key}' already exists.")

    # منطق عمل: التحقق من عدم وجود وحدة قياس بنفس مفتاح الاختصار
    existing_unit_by_abbreviation = db.query(UnitOfMeasure).filter(UnitOfMeasure.unit_abbreviation_key == unit_in.unit_abbreviation_key).first()
    if existing_unit_by_abbreviation:
        raise ConflictException(detail=f"Unit of measure with abbreviation key '{unit_in.unit_abbreviation_key}' already exists.")

    # استدعاء دالة CRUD للإنشاء
    return unit_of_measure_crud.create_unit_of_measure(db=db, unit_in=unit_in)

def get_all_units_of_measure(db: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[UnitOfMeasure]:
    """
    خدمة لجلب جميع وحدات القياس، مع خيار لتضمين الوحدات غير النشطة.
    """
    return unit_of_measure_crud.get_all_units_of_measure(db, skip=skip, limit=limit, include_inactive=include_inactive)

def get_unit_of_measure_details(db: Session, unit_id: int) -> UnitOfMeasure:
    """
    خدمة لجلب تفاصيل وحدة قياس واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    unit = unit_of_measure_crud.get_unit_of_measure(db, unit_id=unit_id)
    if not unit:
        raise NotFoundException(detail=f"Unit of measure with ID {unit_id} not found.")
    return unit

def update_unit_of_measure(db: Session, unit_id: int, unit_in: units_schemas.UnitOfMeasureUpdate) -> UnitOfMeasure:
    """
    خدمة لتحديث وحدة قياس موجودة.
    """
    db_unit = get_unit_of_measure_details(db, unit_id) # استخدام دالة الخدمة للتحقق من الوجود

    # منطق عمل: إذا تم تحديث مفتاح الاسم، تحقق من عدم التكرار
    if unit_in.unit_name_key and unit_in.unit_name_key != db_unit.unit_name_key:
        existing_unit_by_name = db.query(UnitOfMeasure).filter(UnitOfMeasure.unit_name_key == unit_in.unit_name_key).first()
        if existing_unit_by_name and existing_unit_by_name.unit_id != unit_id:
            raise ConflictException(detail=f"Unit of measure with name key '{unit_in.unit_name_key}' already exists.")

    # منطق عمل: إذا تم تحديث مفتاح الاختصار، تحقق من عدم التكرار
    if unit_in.unit_abbreviation_key and unit_in.unit_abbreviation_key != db_unit.unit_abbreviation_key:
        existing_unit_by_abbreviation = db.query(UnitOfMeasure).filter(UnitOfMeasure.unit_abbreviation_key == unit_in.unit_abbreviation_key).first()
        if existing_unit_by_abbreviation and existing_unit_by_abbreviation.unit_id != unit_id:
            raise ConflictException(detail=f"Unit of measure with abbreviation key '{unit_in.unit_abbreviation_key}' already exists.")

    return unit_of_measure_crud.update_unit_of_measure(db=db, db_unit=db_unit, unit_in=unit_in)

def soft_delete_unit_of_measure(db: Session, unit_id: int) -> UnitOfMeasure:
    """
    خدمة للحذف الناعم لوحدة قياس بتعيين is_active إلى False.
    تتضمن التحقق من عدم استخدام الوحدة في أي منتجات أو خيارات تعبئة.
    """
    db_unit = get_unit_of_measure_details(db, unit_id)
    if not db_unit.is_active:
        raise BadRequestException(detail=f"Unit of measure with ID {unit_id} is already inactive.")

    # منطق عمل: التحقق من عدم استخدام هذه الوحدة في أي Product (base_price_per_unit)
    from src.products.models.products_models import Product # استيراد هنا لتجنب التبعية الدائرية
    if db.query(Product).filter(Product.unit_of_measure_id == unit_id).count() > 0:
        raise ForbiddenException(detail=f"Cannot soft-delete unit of measure ID {unit_id} because it is used by existing products.")

    # منطق عمل: التحقق من عدم استخدام هذه الوحدة في أي ProductPackagingOption (unit_of_measure_id_for_quantity)
    from src.products.models.units_models import ProductPackagingOption # استيراد هنا لتجنب التبعية الدائرية
    if db.query(ProductPackagingOption).filter(ProductPackagingOption.unit_of_measure_id_for_quantity == unit_id).count() > 0:
        raise ForbiddenException(detail=f"Cannot soft-delete unit of measure ID {unit_id} because it is used by existing product packaging options.")

    return unit_of_measure_crud.soft_delete_unit_of_measure(db=db, db_unit=db_unit)

# ==========================================================
# --- خدمات ترجمات وحدات القياس (UnitOfMeasure Translation) ---
# ==========================================================

def create_unit_of_measure_translation(db: Session, unit_id: int, trans_in: units_schemas.UnitOfMeasureTranslationCreate) -> UnitOfMeasureTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لوحدة قياس معينة.
    تتضمن التحقق من وجود الوحدة الأم وعدم تكرار الترجمة.
    """
    # منطق عمل: التحقق من وجود الوحدة الأم
    get_unit_of_measure_details(db, unit_id)

    # منطق عمل: التحقق من عدم وجود ترجمة بنفس اللغة للوحدة
    existing_translation = unit_of_measure_crud.get_unit_of_measure_translation(db, unit_id=unit_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"Translation for unit of measure ID {unit_id} with language '{trans_in.language_code}' already exists.")

    return unit_of_measure_crud.create_unit_of_measure_translation(db=db, unit_id=unit_id, trans_in=trans_in)

def get_unit_of_measure_translation_details(db: Session, unit_id: int, language_code: str) -> UnitOfMeasureTranslation:
    """
    خدمة لجلب ترجمة محددة لوحدة قياس بلغة معينة، مع معالجة عدم الوجود.
    """
    translation = unit_of_measure_crud.get_unit_of_measure_translation(db, unit_id=unit_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"Translation for unit of measure ID {unit_id} in language '{language_code}' not found.")
    return translation

def update_unit_of_measure_translation(db: Session, unit_id: int, language_code: str, trans_in: units_schemas.UnitOfMeasureTranslationUpdate) -> UnitOfMeasureTranslation:
    """
    خدمة لتحديث ترجمة وحدة قياس موجودة.
    """
    db_translation = get_unit_of_measure_translation_details(db, unit_id, language_code) # استخدام دالة الخدمة للتحقق

    return unit_of_measure_crud.update_unit_of_measure_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_unit_of_measure_translation(db: Session, unit_id: int, language_code: str):
    """
    خدمة لحذف ترجمة وحدة قياس معينة (حذف صارم).
    """
    db_translation = get_unit_of_measure_translation_details(db, unit_id, language_code) # استخدام دالة الخدمة للتحقق
    unit_of_measure_crud.delete_unit_of_measure_translation(db=db, db_translation=db_translation)
    return {"message": "Unit of measure translation deleted successfully."}
