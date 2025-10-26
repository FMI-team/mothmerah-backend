# backend\src\api\v1\routers\unit_of_measure_admin_router.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

# استيرادات عامة
from src.db.session import get_db
from src.api.v1 import dependencies
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

# استيراد Schemas وخدمات وحدات القياس
from src.products.schemas import units_schemas
from src.products.services import unit_of_measure_service

# --- الراوتر الرئيسي لإدارة وحدات القياس (للإدارة فقط) ---
router = APIRouter(
    prefix="/units-of-measure",
    tags=["Admin - Units of Measure"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_UNITS"))] # صلاحية مخصصة لإدارة وحدات القياس
)

# ================================================================
# --- نقاط الوصول لوحدات القياس (UnitOfMeasure) ---
# ================================================================

@router.post("/", response_model=units_schemas.UnitOfMeasureRead, status_code=status.HTTP_201_CREATED)
def create_new_unit_of_measure_endpoint(unit_in: units_schemas.UnitOfMeasureCreate, db: Session = Depends(get_db)):
    """إنشاء وحدة قياس جديدة مع ترجماتها."""
    return unit_of_measure_service.create_new_unit_of_measure(db=db, unit_in=unit_in)

@router.get("/", response_model=List[units_schemas.UnitOfMeasureRead])
def read_units_of_measure_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), include_inactive: bool = False):
    """عرض قائمة بجميع وحدات القياس المعرفة في النظام، مع خيار لتضمين غير النشطة."""
    return unit_of_measure_service.get_all_units_of_measure(db, skip=skip, limit=limit, include_inactive=include_inactive)

@router.get("/{unit_id}", response_model=units_schemas.UnitOfMeasureRead)
def get_unit_of_measure_details_endpoint(unit_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل وحدة قياس واحدة بالـ ID الخاص بها."""
    return unit_of_measure_service.get_unit_of_measure_details(db, unit_id=unit_id)

@router.patch("/{unit_id}", response_model=units_schemas.UnitOfMeasureRead)
def update_unit_of_measure_endpoint(unit_id: int, unit_in: units_schemas.UnitOfMeasureUpdate, db: Session = Depends(get_db)):
    """تحديث وحدة قياس معينة (مثل اسمها أو حالة التفعيل)."""
    return unit_of_measure_service.update_unit_of_measure(db, unit_id=unit_id, unit_in=unit_in)

@router.delete("/{unit_id}", response_model=units_schemas.UnitOfMeasureRead)
def soft_delete_unit_of_measure_endpoint(unit_id: int, db: Session = Depends(get_db)):
    """حذف ناعم لوحدة قياس (بتعيين is_active إلى False). لا يمكن حذفها إذا كانت مرتبطة بمنتجات أو خيارات تعبئة."""
    return unit_of_measure_service.soft_delete_unit_of_measure(db, unit_id=unit_id)

# ================================================================
# --- نقاط الوصول لترجمات وحدات القياس (UnitOfMeasureTranslation) ---
# ================================================================

@router.post(
    "/{unit_id}/translations",
    response_model=units_schemas.UnitOfMeasureTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="إنشاء ترجمة جديدة لوحدة قياس أو تحديثها إذا كانت موجودة"
)
def create_unit_of_measure_translation_endpoint(unit_id: int, trans_in: units_schemas.UnitOfMeasureTranslationCreate, db: Session = Depends(get_db)):
    """
    إنشاء ترجمة جديدة لوحدة قياس معينة.
    إذا كانت الترجمة بنفس اللغة موجودة بالفعل، سيتم رفض الطلب بتضارب.
    """
    return unit_of_measure_service.create_unit_of_measure_translation(db=db, unit_id=unit_id, trans_in=trans_in)

@router.get(
    "/{unit_id}/translations/{language_code}",
    response_model=units_schemas.UnitOfMeasureTranslationRead,
    summary="جلب ترجمة محددة لوحدة قياس"
)
def get_unit_of_measure_translation_endpoint(unit_id: int, language_code: str, db: Session = Depends(get_db)):
    """جلب ترجمة وحدة قياس معينة بلغة محددة."""
    return unit_of_measure_service.get_unit_of_measure_translation_details(db, unit_id=unit_id, language_code=language_code)

@router.patch(
    "/{unit_id}/translations/{language_code}",
    response_model=units_schemas.UnitOfMeasureTranslationRead,
    summary="تحديث ترجمة وحدة قياس"
)
def update_unit_of_measure_translation_endpoint(
    unit_id: int,
    language_code: str,
    trans_in: units_schemas.UnitOfMeasureTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة وحدة قياس معينة بلغة محددة."""
    return unit_of_measure_service.update_unit_of_measure_translation(db, unit_id=unit_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/{unit_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف ترجمة وحدة قياس"
)
def delete_unit_of_measure_translation_endpoint(unit_id: int, language_code: str, db: Session = Depends(get_db)):
    """حذف ترجمة وحدة قياس معينة بلغة محددة (حذف صارم)."""
    unit_of_measure_service.delete_unit_of_measure_translation(db, unit_id=unit_id, language_code=language_code)
    return