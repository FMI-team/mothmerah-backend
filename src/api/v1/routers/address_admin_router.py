# backend/src/api/v1/routers/address_admin_router.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.api.v1 import dependencies
from src.users.schemas import address_lookups_schemas as schemas
from src.users.services import address_lookups_service as service

# --- الراوتر الرئيسي لإدارة العناوين ---
router = APIRouter(
    prefix="/addresses", # المسار الأساسي لكل ما في هذا الملف
    tags=["Admin - Addresses & Geolocation"],
    dependencies=[Depends(dependencies.has_permission("MANAGE_GEODATA"))] # صلاحية مقترحة
)

# ==========================================================
# --- Endpoints for AddressType Management ---
# ==========================================================

@router.get("/types", response_model=List[schemas.AddressTypeRead], summary="جلب كل أنواع العناوين")
def get_all_address_types(db: Session = Depends(get_db)):
    return service.get_all_address_types(db)

@router.post("/types", response_model=schemas.AddressTypeRead, status_code=status.HTTP_201_CREATED, summary="إنشاء نوع عنوان جديد")
def create_address_type(type_in: schemas.AddressTypeCreate, db: Session = Depends(get_db)):
    return service.create_new_address_type(db, type_in=type_in)

@router.patch("/types/{type_id}", response_model=schemas.AddressTypeRead, summary="تحديث نوع عنوان")
def update_address_type(type_id: int, type_in: schemas.AddressTypeUpdate, db: Session = Depends(get_db)):
    return service.update_address_type(db, type_id=type_id, type_in=type_in)

@router.delete("/types/{type_id}", response_model=dict, summary="حذف نوع عنوان")
def delete_address_type(type_id: int, db: Session = Depends(get_db)):
    return service.delete_address_type_by_id(db, type_id=type_id)

# --- Endpoints for AddressType Translations ---

@router.post("/types/{type_id}/translations", response_model=schemas.AddressTypeRead, summary="إدارة ترجمات نوع العنوان")
def manage_address_type_translations(type_id: int, trans_in: schemas.AddressTypeTranslationCreate, db: Session = Depends(get_db)):
    return service.manage_address_type_translation(db, type_id=type_id, trans_in=trans_in)

@router.delete("/types/{type_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT, summary="حذف ترجمة نوع العنوان")
def delete_address_type_translation(type_id: int, language_code: str, db: Session = Depends(get_db)):
    service.remove_address_type_translation(db, type_id=type_id, language_code=language_code)
    return

# ==========================================================
# --- Endpoints for Country Management ---
# ==========================================================

@router.get("/countries", response_model=List[schemas.CountryRead], summary="جلب كل الدول")
def get_all_countries(db: Session = Depends(get_db)):
    return service.get_all_countries(db)

@router.post("/countries", response_model=schemas.CountryRead, status_code=status.HTTP_201_CREATED, summary="إنشاء دولة جديدة")
def create_country(country_in: schemas.CountryCreate, db: Session = Depends(get_db)):
    return service.create_new_country(db, country_in=country_in)

@router.patch("/countries/{country_code}", response_model=schemas.CountryRead, summary="تحديث دولة")
def update_country(country_code: str, country_in: schemas.CountryUpdate, db: Session = Depends(get_db)):
    return service.update_country(db, country_code=country_code, country_in=country_in)

@router.delete("/countries/{country_code}", response_model=dict, summary="حذف دولة")
def delete_country(country_code: str, db: Session = Depends(get_db)):
    return service.delete_country_by_code(db, country_code=country_code)

# --- Endpoints for Country Translations ---

@router.post("/countries/{country_code}/translations", response_model=schemas.CountryRead, summary="إدارة ترجمات الدولة")
def manage_country_translations(country_code: str, trans_in: schemas.CountryTranslationCreate, db: Session = Depends(get_db)):
    return service.manage_country_translation(db, country_code=country_code, trans_in=trans_in)

@router.delete("/countries/{country_code}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT, summary="حذف ترجمة الدولة")
def delete_country_translation(country_code: str, language_code: str, db: Session = Depends(get_db)):
    service.remove_country_translation(db, country_code=country_code, language_code=language_code)
    return

# backend/src/api/v1/routers/address_admin_router.py

# ... (الاستيرادات ونقاط وصول Country الحالية) ...

# ==========================================================
# --- Endpoints for Governorate Management ---
# ==========================================================

@router.get("/governorates", response_model=List[schemas.GovernorateRead], summary="جلب كل المحافظات")
def get_all_governorates(db: Session = Depends(get_db)):
    return service.get_all_governorates(db)

@router.post("/governorates", response_model=schemas.GovernorateRead, status_code=status.HTTP_201_CREATED, summary="إنشاء محافظة جديدة")
def create_governorate(governorate_in: schemas.GovernorateCreate, db: Session = Depends(get_db)):
    return service.create_new_governorate(db, governorate_in=governorate_in)

@router.patch("/governorates/{governorate_id}", response_model=schemas.GovernorateRead, summary="تحديث محافظة")
def update_governorate(governorate_id: int, governorate_in: schemas.GovernorateUpdate, db: Session = Depends(get_db)):
    return service.update_governorate(db, governorate_id=governorate_id, governorate_in=governorate_in)

@router.delete("/governorates/{governorate_id}", response_model=dict, summary="حذف محافظة")
def delete_governorate(governorate_id: int, db: Session = Depends(get_db)):
    return service.delete_governorate_by_id(db, governorate_id=governorate_id)

# --- Endpoints for Governorate Translations ---

@router.post("/governorates/{governorate_id}/translations", response_model=schemas.GovernorateRead, summary="إدارة ترجمات المحافظة")
def manage_governorate_translations(governorate_id: int, trans_in: schemas.GovernorateTranslationCreate, db: Session = Depends(get_db)):
    return service.manage_governorate_translation(db, governorate_id=governorate_id, trans_in=trans_in)

@router.delete("/governorates/{governorate_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT, summary="حذف ترجمة المحافظة")
def delete_governorate_translation(governorate_id: int, language_code: str, db: Session = Depends(get_db)):
    service.remove_governorate_translation(db, governorate_id=governorate_id, language_code=language_code)
    return

# backend/src/api/v1/routers/address_admin_router.py

# ... (الاستيرادات ونقاط وصول Governorate الحالية) ...

# ==========================================================
# --- Endpoints for City Management ---
# ==========================================================

@router.get("/cities", response_model=List[schemas.CityRead], summary="جلب كل المدن")
def get_all_cities(db: Session = Depends(get_db)):
    return service.get_all_cities(db)

@router.post("/cities", response_model=schemas.CityRead, status_code=status.HTTP_201_CREATED, summary="إنشاء مدينة جديدة")
def create_city(city_in: schemas.CityCreate, db: Session = Depends(get_db)):
    return service.create_new_city(db, city_in=city_in)

@router.patch("/cities/{city_id}", response_model=schemas.CityRead, summary="تحديث مدينة")
def update_city(city_id: int, city_in: schemas.CityUpdate, db: Session = Depends(get_db)):
    return service.update_city(db, city_id=city_id, city_in=city_in)

@router.delete("/cities/{city_id}", response_model=dict, summary="حذف مدينة")
def delete_city(city_id: int, db: Session = Depends(get_db)):
    return service.delete_city_by_id(db, city_id=city_id)

# --- Endpoints for City Translations ---

@router.post("/cities/{city_id}/translations", response_model=schemas.CityRead, summary="إدارة ترجمات المدينة")
def manage_city_translations(city_id: int, trans_in: schemas.CityTranslationCreate, db: Session = Depends(get_db)):
    return service.manage_city_translation(db, city_id=city_id, trans_in=trans_in)

@router.delete("/cities/{city_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT, summary="حذف ترجمة المدينة")
def delete_city_translation(city_id: int, language_code: str, db: Session = Depends(get_db)):
    service.remove_city_translation(db, city_id=city_id, language_code=language_code)
    return

# backend/src/api/v1/routers/address_admin_router.py

# ... (الاستيرادات ونقاط وصول City الحالية) ...

# ==========================================================
# --- Endpoints for District Management ---
# ==========================================================

@router.get("/districts", response_model=List[schemas.DistrictRead], summary="جلب كل الأحياء")
def get_all_districts(db: Session = Depends(get_db)):
    return service.get_all_districts(db)

@router.post("/districts", response_model=schemas.DistrictRead, status_code=status.HTTP_201_CREATED, summary="إنشاء حي جديد")
def create_district(district_in: schemas.DistrictCreate, db: Session = Depends(get_db)):
    return service.create_new_district(db, district_in=district_in)

@router.patch("/districts/{district_id}", response_model=schemas.DistrictRead, summary="تحديث حي")
def update_district(district_id: int, district_in: schemas.DistrictUpdate, db: Session = Depends(get_db)):
    return service.update_district(db, district_id=district_id, district_in=district_in)

@router.delete("/districts/{district_id}", response_model=dict, summary="حذف حي")
def delete_district(district_id: int, db: Session = Depends(get_db)):
    return service.delete_district_by_id(db, district_id=district_id)

# --- Endpoints for District Translations ---

@router.post("/districts/{district_id}/translations", response_model=schemas.DistrictRead, summary="إدارة ترجمات الحي")
def manage_district_translations(district_id: int, trans_in: schemas.DistrictTranslationCreate, db: Session = Depends(get_db)):
    return service.manage_district_translation(db, district_id=district_id, trans_in=trans_in)

@router.delete("/districts/{district_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT, summary="حذف ترجمة الحي")
def delete_district_translation(district_id: int, language_code: str, db: Session = Depends(get_db)):
    service.remove_district_translation(db, district_id=district_id, language_code=language_code)
    return

