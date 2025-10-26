# backend\src\api\v1\routers\admin_address_lookups_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional, Dict # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User as UserModel # مودل المستخدم، لضمان User type hint

# استيراد Schemas (هياكل البيانات)
from src.users.schemas import address_lookups_schemas as schemas # لجميع Schemas Lookups

# استيراد الخدمات (منطق العمل)
from src.users.services import address_lookups_service # لجميع خدمات Lookups الجغرافية


# تعريف الراوتر لإدارة جداول العناوين والمواقع الجغرافية من جانب المسؤولين.
router = APIRouter(
    prefix="/address-lookups", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /admin/address-lookups)
    tags=["Admin - Address Lookups Management"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_ADDRESS_LOOKUPS"))] # صلاحية عامة لإدارة جداول المواقع
)

# ================================================================
# --- نقاط الوصول لأنواع العناوين (Address Types) ---
# ================================================================

@router.post(
    "/address-types",
    response_model=schemas.AddressTypeRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء نوع عنوان جديد"
)
async def create_address_type_endpoint(
    type_in: schemas.AddressTypeCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء نوع مرجعي جديد للعنوان (مثلاً: 'عنوان شحن', 'عنوان فوترة').
    """
    return address_lookups_service.create_new_address_type(db=db, type_in=type_in)

@router.get(
    "/address-types",
    response_model=List[schemas.AddressTypeRead],
    summary="[Admin] جلب جميع أنواع العناوين"
)
async def get_all_address_types_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع أنواع العناوين المرجعية في النظام."""
    return address_lookups_service.get_all_address_types_service(db=db)

@router.get(
    "/address-types/{type_id}",
    response_model=schemas.AddressTypeRead,
    summary="[Admin] جلب تفاصيل نوع عنوان واحد"
)
async def get_address_type_details_endpoint(type_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل نوع مرجعي لعنوان بالـ ID الخاص بها."""
    return address_lookups_service.get_address_type_by_id_service(db=db, type_id=type_id)

@router.patch(
    "/address-types/{type_id}",
    response_model=schemas.AddressTypeRead,
    summary="[Admin] تحديث نوع عنوان"
)
async def update_address_type_endpoint(
    type_id: int,
    type_in: schemas.AddressTypeUpdate,
    db: Session = Depends(get_db)
):
    """تحديث نوع مرجعي لعنوان."""
    return address_lookups_service.update_address_type(db=db, type_id=type_id, type_in=type_in)

@router.delete(
    "/address-types/{type_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف نوع عنوان",
    description="""
    حذف نوع مرجعي لعنوان (حذف صارم).
    سيتم إعادة إسناد العناوين المرتبطة إلى النوع الافتراضي 'SHIPPING'.
    """,
)
async def delete_address_type_endpoint(type_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف نوع عنوان."""
    return address_lookups_service.delete_address_type_by_id(db=db, type_id=type_id)

# --- ترجمات أنواع العناوين ---
@router.post(
    "/address-types/{type_id}/translations",
    response_model=schemas.AddressTypeRead, # ترجع النوع كاملاً مع ترجماته المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لنوع عنوان",
    description="""
    إنشاء ترجمة جديدة لنوع مرجعي لعنوان بلغة معينة أو تحديث ترجمة موجودة.
    """,
)
async def create_address_type_translation_endpoint(
    type_id: int,
    trans_in: schemas.AddressTypeTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لنوع عنوان."""
    return address_lookups_service.create_address_type_translation(db=db, type_id=type_id, trans_in=trans_in)

@router.get(
    "/address-types/{type_id}/translations/{language_code}",
    response_model=schemas.AddressTypeTranslationRead,
    summary="[Admin] جلب ترجمة محددة لنوع عنوان",
    description="""
    جلب ترجمة نوع مرجعية لعنوان بلغة محددة.
    """,
)
async def get_address_type_translation_details_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة نوع عنوان محددة."""
    return address_lookups_service.get_address_type_translation_details(db=db, type_id=type_id, language_code=language_code)

@router.patch(
    "/address-types/{type_id}/translations/{language_code}",
    response_model=schemas.AddressTypeRead, # ترجع النوع كاملاً مع ترجماته المحدثة
    summary="[Admin] تحديث ترجمة نوع عنوان",
    description="""
    تحديث ترجمة نوع مرجعية لعنوان بلغة محددة.
    """,
)
async def update_address_type_translation_endpoint(
    type_id: int,
    language_code: str,
    trans_in: schemas.AddressTypeTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة نوع عنوان."""
    return address_lookups_service.update_address_type_translation(db=db, type_id=type_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/address-types/{type_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة نوع عنوان",
    description="""
    حذف ترجمة نوع مرجعية لعنوان بلغة محددة (حذف صارم).
    """,
)
async def remove_address_type_translation_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة نوع عنوان."""
    address_lookups_service.remove_address_type_translation(db=db, type_id=type_id, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول للدول (Countries) ---
# ================================================================

@router.post(
    "/countries",
    response_model=schemas.CountryRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء دولة جديدة"
)
async def create_country_endpoint(
    country_in: schemas.CountryCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء دولة مرجعية جديدة.
    """
    return address_lookups_service.create_new_country(db=db, country_in=country_in)

@router.get(
    "/countries",
    response_model=List[schemas.CountryRead],
    summary="[Admin] جلب جميع الدول"
)
async def get_all_countries_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع الدول المرجعية في النظام."""
    return address_lookups_service.get_all_countries_service(db=db)

@router.get(
    "/countries/{country_code}",
    response_model=schemas.CountryRead,
    summary="[Admin] جلب تفاصيل دولة واحدة"
)
async def get_country_details_endpoint(country_code: str, db: Session = Depends(get_db)):
    """جلب تفاصيل دولة مرجعية بالرمز الخاص بها."""
    return address_lookups_service.get_country_by_code_service(db=db, country_code=country_code)

@router.patch(
    "/countries/{country_code}",
    response_model=schemas.CountryRead,
    summary="[Admin] تحديث دولة",
    description="""
    تحديث دولة مرجعية (حذف ناعم إذا كانت 'is_active' تُحدث).
    """,
)
async def update_country_endpoint(
    country_code: str,
    country_in: schemas.CountryUpdate,
    db: Session = Depends(get_db)
):
    """تحديث دولة."""
    return address_lookups_service.update_country(db=db, country_code=country_code, country_in=country_in)

@router.delete(
    "/countries/{country_code}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف دولة (حذف ناعم)",
    description="""
    حذف دولة مرجعية (حذف ناعم بتعيين 'is_active' إلى False).
    لا يمكن حذفها إذا كانت مرتبطة بمحافظات أو عناوين نشطة.
    """,
)
async def soft_delete_country_endpoint(country_code: str, db: Session = Depends(get_db)):
    """نقطة وصول لحذف دولة (حذف ناعم)."""
    return address_lookups_service.soft_delete_country_by_code(db=db, country_code=country_code)

# --- ترجمات الدول ---
@router.post(
    "/countries/{country_code}/translations",
    response_model=schemas.CountryRead, # ترجع الدولة كاملاً مع ترجماتها المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لدولة",
    description="""
    إنشاء ترجمة جديدة لدولة بلغة معينة أو تحديث ترجمة موجودة.
    """,
)
async def create_country_translation_endpoint(
    country_code: str,
    trans_in: schemas.CountryTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لدولة."""
    return address_lookups_service.create_country_translation(db=db, country_code=country_code, trans_in=trans_in)

@router.get(
    "/countries/{country_code}/translations/{language_code}",
    response_model=schemas.CountryTranslationRead,
    summary="[Admin] جلب ترجمة محددة لدولة",
    description="""
    جلب ترجمة دولة مرجعية بلغة محددة.
    """,
)
async def get_country_translation_details_endpoint(
    country_code: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة دولة محددة."""
    return address_lookups_service.get_country_translation_details(db=db, country_code=country_code, language_code=language_code)

@router.patch(
    "/countries/{country_code}/translations/{language_code}",
    response_model=schemas.CountryRead, # ترجع الدولة كاملاً مع ترجماتها المحدثة
    summary="[Admin] تحديث ترجمة دولة",
    description="""
    تحديث ترجمة دولة مرجعية بلغة محددة.
    """,
)
async def update_country_translation_endpoint(
    country_code: str,
    language_code: str,
    trans_in: schemas.CountryTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة دولة."""
    return address_lookups_service.update_country_translation(db=db, country_code=country_code, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/countries/{country_code}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة دولة",
    description="""
    حذف ترجمة دولة مرجعية بلغة محددة (حذف صارم).
    """,
)
async def remove_country_translation_endpoint(
    country_code: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة دولة."""
    address_lookups_service.remove_country_translation(db=db, country_code=country_code, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول للمحافظات (Governorates) ---
# ================================================================

@router.post(
    "/governorates",
    response_model=schemas.GovernorateRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء محافظة جديدة"
)
async def create_governorate_endpoint(
    governorate_in: schemas.GovernorateCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء محافظة مرجعية جديدة.
    """
    return address_lookups_service.create_new_governorate(db=db, governorate_in=governorate_in)

@router.get(
    "/governorates",
    response_model=List[schemas.GovernorateRead],
    summary="[Admin] جلب جميع المحافظات"
)
async def get_all_governorates_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع المحافظات المرجعية في النظام."""
    return address_lookups_service.get_all_governorates_service(db=db)

@router.get(
    "/governorates/{governorate_id}",
    response_model=schemas.GovernorateRead,
    summary="[Admin] جلب تفاصيل محافظة واحدة"
)
async def get_governorate_details_endpoint(governorate_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل محافظة مرجعية بالـ ID الخاص بها."""
    return address_lookups_service.get_governorate_by_id_service(db=db, governorate_id=governorate_id)

@router.patch(
    "/governorates/{governorate_id}",
    response_model=schemas.GovernorateRead,
    summary="[Admin] تحديث محافظة",
    description="""
    تحديث محافظة مرجعية (حذف ناعم إذا كانت 'is_active' تُحدث).
    """,
)
async def update_governorate_endpoint(
    governorate_id: int,
    governorate_in: schemas.GovernorateUpdate,
    db: Session = Depends(get_db)
):
    """تحديث محافظة."""
    return address_lookups_service.update_governorate(db=db, governorate_id=governorate_id, governorate_in=governorate_in)

@router.delete(
    "/governorates/{governorate_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف محافظة (حذف ناعم)",
    description="""
    حذف محافظة مرجعية (حذف ناعم بتعيين 'is_active' إلى False).
    لا يمكن حذفها إذا كانت مرتبطة بمدن نشطة.
    """,
)
async def soft_delete_governorate_endpoint(governorate_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف محافظة (حذف ناعم)."""
    return address_lookups_service.soft_delete_governorate_by_id(db=db, governorate_id=governorate_id)

# --- ترجمات المحافظات ---
@router.post(
    "/governorates/{governorate_id}/translations",
    response_model=schemas.GovernorateRead, # ترجع المحافظة كاملاً مع ترجماتها المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لمحافظة",
    description="""
    إنشاء ترجمة جديدة لمحافظة بلغة معينة أو تحديث ترجمة موجودة.
    """,
)
async def create_governorate_translation_endpoint(
    governorate_id: int,
    trans_in: schemas.GovernorateTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لمحافظة."""
    return address_lookups_service.create_governorate_translation(db=db, governorate_id=governorate_id, trans_in=trans_in)

@router.get(
    "/governorates/{governorate_id}/translations/{language_code}",
    response_model=schemas.GovernorateTranslationRead,
    summary="[Admin] جلب ترجمة محددة لمحافظة",
    description="""
    جلب ترجمة محافظة مرجعية بلغة محددة.
    """,
)
async def get_governorate_translation_details_endpoint(
    governorate_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة محافظة محددة."""
    return address_lookups_service.get_governorate_translation_details(db=db, governorate_id=governorate_id, language_code=language_code)

@router.patch(
    "/governorates/{governorate_id}/translations/{language_code}",
    response_model=schemas.GovernorateRead, # ترجع المحافظة كاملاً مع ترجماتها المحدثة
    summary="[Admin] تحديث ترجمة محافظة",
    description="""
    تحديث ترجمة محافظة مرجعية بلغة محددة.
    """,
)
async def update_governorate_translation_endpoint(
    governorate_id: int,
    language_code: str,
    trans_in: schemas.GovernorateTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة محافظة."""
    return address_lookups_service.update_governorate_translation(db=db, governorate_id=governorate_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/governorates/{governorate_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة محافظة",
    description="""
    حذف ترجمة محافظة مرجعية بلغة محددة (حذف صارم).
    """,
)
async def remove_governorate_translation_endpoint(
    governorate_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة محافظة."""
    address_lookups_service.remove_governorate_translation(db=db, governorate_id=governorate_id, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول للمدن (Cities) ---
# ================================================================

@router.post(
    "/cities",
    response_model=schemas.CityRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء مدينة جديدة"
)
async def create_city_endpoint(
    city_in: schemas.CityCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء مدينة مرجعية جديدة.
    """
    return address_lookups_service.create_new_city(db=db, city_in=city_in)

@router.get(
    "/cities",
    response_model=List[schemas.CityRead],
    summary="[Admin] جلب جميع المدن"
)
async def get_all_cities_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع المدن المرجعية في النظام."""
    return address_lookups_service.get_all_cities_service(db=db)

@router.get(
    "/cities/{city_id}",
    response_model=schemas.CityRead,
    summary="[Admin] جلب تفاصيل مدينة واحدة"
)
async def get_city_details_endpoint(city_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل مدينة مرجعية بالـ ID الخاص بها."""
    return address_lookups_service.get_city_by_id_service(db=db, city_id=city_id)

@router.patch(
    "/cities/{city_id}",
    response_model=schemas.CityRead,
    summary="[Admin] تحديث مدينة",
    description="""
    تحديث مدينة مرجعية (حذف ناعم إذا كانت 'is_active' تُحدث).
    """,
)
async def update_city_endpoint(
    city_id: int,
    city_in: schemas.CityUpdate,
    db: Session = Depends(get_db)
):
    """تحديث مدينة."""
    return address_lookups_service.update_city(db=db, city_id=city_id, city_in=city_in)

@router.delete(
    "/cities/{city_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف مدينة (حذف ناعم)",
    description="""
    حذف مدينة مرجعية (حذف ناعم بتعيين 'is_active' إلى False).
    لا يمكن حذفها إذا كانت مرتبطة بأحياء نشطة.
    """,
)
async def soft_delete_city_endpoint(city_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف مدينة (حذف ناعم)."""
    return address_lookups_service.soft_delete_city_by_id(db=db, city_id=city_id)

# --- ترجمات المدن ---
@router.post(
    "/cities/{city_id}/translations",
    response_model=schemas.CityRead, # ترجع المدينة كاملاً مع ترجماتها المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لمدينة",
    description="""
    إنشاء ترجمة جديدة لمدينة بلغة معينة أو تحديث ترجمة موجودة.
    """,
)
async def create_city_translation_endpoint(
    city_id: int,
    trans_in: schemas.CityTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لمدينة."""
    return address_lookups_service.create_city_translation(db=db, city_id=city_id, trans_in=trans_in)

@router.get(
    "/cities/{city_id}/translations/{language_code}",
    response_model=schemas.CityTranslationRead,
    summary="[Admin] جلب ترجمة محددة لمدينة",
    description="""
    جلب ترجمة مدينة مرجعية بلغة محددة.
    """,
)
async def get_city_translation_details_endpoint(
    city_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة مدينة محددة."""
    return address_lookups_service.get_city_translation_details(db=db, city_id=city_id, language_code=language_code)

@router.patch(
    "/cities/{city_id}/translations/{language_code}",
    response_model=schemas.CityRead, # ترجع المدينة كاملاً مع ترجماتها المحدثة
    summary="[Admin] تحديث ترجمة مدينة",
    description="""
    تحديث ترجمة مدينة مرجعية بلغة محددة.
    """,
)
async def update_city_translation_endpoint(
    city_id: int,
    language_code: str,
    trans_in: schemas.CityTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة مدينة."""
    return address_lookups_service.update_city_translation(db=db, city_id=city_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/cities/{city_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة مدينة",
    description="""
    حذف ترجمة مدينة مرجعية بلغة محددة (حذف صارم).
    """,
)
async def remove_city_translation_endpoint(
    city_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة مدينة."""
    address_lookups_service.remove_city_translation(db=db, city_id=city_id, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول للأحياء (Districts) ---
# ================================================================

@router.post(
    "/districts",
    response_model=schemas.DistrictRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حي جديد"
)
async def create_district_endpoint(
    district_in: schemas.DistrictCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حي مرجعي جديد.
    """
    return address_lookups_service.create_new_district(db=db, district_in=district_in)

@router.get(
    "/districts",
    response_model=List[schemas.DistrictRead],
    summary="[Admin] جلب جميع الأحياء"
)
async def get_all_districts_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع الأحياء المرجعية في النظام."""
    return address_lookups_service.get_all_districts_service(db=db)

@router.get(
    "/districts/{district_id}",
    response_model=schemas.DistrictRead,
    summary="[Admin] جلب تفاصيل حي واحد"
)
async def get_district_details_endpoint(district_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل حي مرجعي بالـ ID الخاص بها."""
    return address_lookups_service.get_district_by_id_service(db=db, district_id=district_id)

@router.patch(
    "/districts/{district_id}",
    response_model=schemas.DistrictRead,
    summary="[Admin] تحديث حي",
    description="""
    تحديث حي مرجعي (حذف ناعم إذا كانت 'is_active' تُحدث).
    """,
)
async def update_district_endpoint(
    district_id: int,
    district_in: schemas.DistrictUpdate,
    db: Session = Depends(get_db)
):
    """تحديث حي."""
    return address_lookups_service.update_district(db=db, district_id=district_id, district_in=district_in)

@router.delete(
    "/districts/{district_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف حي (حذف ناعم)",
    description="""
    حذف حي مرجعي (حذف ناعم بتعيين 'is_active' إلى False).
    لا يمكن حذفها إذا كانت مرتبطة بعناوين نشطة.
    """,
)
async def soft_delete_district_endpoint(district_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف حي (حذف ناعم)."""
    return address_lookups_service.soft_delete_district_by_id(db=db, district_id=district_id)

# --- ترجمات الأحياء ---
@router.post(
    "/districts/{district_id}/translations",
    response_model=schemas.DistrictRead, # ترجع الحي كاملاً مع ترجماته المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لحي",
    description="""
    إنشاء ترجمة جديدة لحي بلغة معينة أو تحديث ترجمة موجودة.
    """,
)
async def create_district_translation_endpoint(
    district_id: int,
    trans_in: schemas.DistrictTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لحي."""
    return address_lookups_service.create_district_translation(db=db, district_id=district_id, trans_in=trans_in)

@router.get(
    "/districts/{district_id}/translations/{language_code}",
    response_model=schemas.DistrictTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحي",
    description="""
    جلب ترجمة حي مرجعية بلغة محددة.
    """,
)
async def get_district_translation_details_endpoint(
    district_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة حي محددة."""
    return address_lookups_service.get_district_translation_details(db=db, district_id=district_id, language_code=language_code)

@router.patch(
    "/districts/{district_id}/translations/{language_code}",
    response_model=schemas.DistrictRead, # ترجع الحي كاملاً مع ترجماته المحدثة
    summary="[Admin] تحديث ترجمة حي",
    description="""
    تحديث ترجمة حي مرجعية بلغة محددة.
    """,
)
async def update_district_translation_endpoint(
    district_id: int,
    language_code: str,
    trans_in: schemas.DistrictTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة حي."""
    return address_lookups_service.update_district_translation(db=db, district_id=district_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/districts/{district_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة حي",
    description="""
    حذف ترجمة حي مرجعية بلغة محددة (حذف صارم).
    """,
)
async def remove_district_translation_endpoint(
    district_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة حي."""
    address_lookups_service.remove_district_translation(db=db, district_id=district_id, language_code=language_code)
    return