# backend/src/users/crud/address_lookups_crud.py

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from src.users.models import addresses_models as models
from src.users.schemas import address_lookups_schemas as schemas

# ==========================================================
# --- CRUD Functions for AddressType ---
# ==========================================================

def get_all_address_types(db: Session) -> List[models.AddressType]:
    return db.query(models.AddressType).options(joinedload(models.AddressType.translations)).all()

def get_address_type_by_key(db: Session, key: str) -> Optional[models.AddressType]:
    return db.query(models.AddressType).filter(models.AddressType.address_type_name_key == key).first()

def get_address_type(db: Session, type_id: int) -> Optional[models.AddressType]:
    return db.query(models.AddressType).filter(models.AddressType.address_type_id == type_id).first()

def create_address_type(db: Session, type_in: schemas.AddressTypeCreate) -> models.AddressType:
    db_type = models.AddressType(address_type_name_key=type_in.address_type_name_key)
    if type_in.translations:
        for trans in type_in.translations:
            db_type.translations.append(models.AddressTypeTranslation(**trans.model_dump()))
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def count_addresses_for_address_type(db: Session, type_id: int) -> int:
    """يحسب عدد العناوين الفعلية المرتبطة بنوع عنوان معين."""
    return db.query(models.Address).filter(models.Address.address_type_id == type_id).count()

def reassign_addresses_to_default_type(db: Session, old_type_id: int, default_type_id: int):
    """يقوم بتحديث كل العناوين من نوع معين ونقلهم إلى النوع الافتراضي."""
    db.query(models.Address).filter(
        models.Address.address_type_id == old_type_id
    ).update({models.Address.address_type_id: default_type_id})
    return

def delete_address_type(db: Session, db_type: models.AddressType):
    """حذف نوع العنوان."""
    db.delete(db_type)
    # الـ Commit سيتم من طبقة الخدمات
    return

# ==========================================================
# --- CRUD Functions for Country ---
# ==========================================================

def get_all_countries(db: Session) -> List[models.Country]:
    return db.query(models.Country).options(joinedload(models.Country.translations)).all()

def get_country(db: Session, country_code: str) -> Optional[models.Country]:
    return db.query(models.Country).filter(models.Country.country_code == country_code).first()

def create_country(db: Session, country_in: schemas.CountryCreate) -> models.Country:
    db_country = models.Country(**country_in.model_dump(exclude={"translations"}))
    if country_in.translations:
        for trans in country_in.translations:
            db_country.translations.append(models.CountryTranslation(**trans.model_dump()))
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return db_country

def update_country(db: Session, db_country: models.Country, country_in: schemas.CountryUpdate) -> models.Country:
    update_data = country_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_country, key, value)
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return db_country

def delete_country(db: Session, db_country: models.Country):
    """حذف دولة (بعد التحقق من عدم وجود محافظات مرتبطة بها في طبقة الخدمات)."""
    db.delete(db_country)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for Governorate ---
# ==========================================================

def get_all_governorates(db: Session) -> List[models.Governorate]:
    """جلب كل المحافظات مع ترجماتها."""
    return db.query(models.Governorate).options(joinedload(models.Governorate.translations)).all()

def get_governorate(db: Session, governorate_id: int) -> Optional[models.Governorate]:
    """جلب محافظة واحدة عن طريق الـ ID الخاص بها."""
    return db.query(models.Governorate).filter(models.Governorate.governorate_id == governorate_id).first()

def create_governorate(db: Session, governorate_in: schemas.GovernorateCreate) -> models.Governorate:
    """إنشاء محافظة جديدة مع ترجماتها الأولية."""
    db_governorate = models.Governorate(**governorate_in.model_dump(exclude={"translations"}))
    if governorate_in.translations:
        for trans in governorate_in.translations:
            db_governorate.translations.append(models.GovernorateTranslation(**trans.model_dump()))
    db.add(db_governorate)
    db.commit()
    db.refresh(db_governorate)
    return db_governorate

def update_governorate(db: Session, db_governorate: models.Governorate, governorate_in: schemas.GovernorateUpdate) -> models.Governorate:
    """تحديث بيانات محافظة موجودة."""
    update_data = governorate_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_governorate, key, value)
    db.add(db_governorate)
    db.commit()
    db.refresh(db_governorate)
    return db_governorate

def delete_governorate(db: Session, db_governorate: models.Governorate) -> None:
    """حذف محافظة (بعد التحقق من عدم وجود مدن مرتبطة بها في طبقة الخدمات)."""
    db.delete(db_governorate)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for City ---
# ==========================================================

def get_all_cities(db: Session) -> List[models.City]:
    """جلب كل المدن مع ترجماتها."""
    return db.query(models.City).options(joinedload(models.City.translations)).all()

def get_city(db: Session, city_id: int) -> Optional[models.City]:
    """جلب مدينة واحدة عن طريق الـ ID الخاص بها."""
    return db.query(models.City).filter(models.City.city_id == city_id).first()

def create_city(db: Session, city_in: schemas.CityCreate) -> models.City:
    """إنشاء مدينة جديدة مع ترجماتها الأولية."""
    db_city = models.City(**city_in.model_dump(exclude={"translations"}))
    if city_in.translations:
        for trans in city_in.translations:
            db_city.translations.append(models.CityTranslation(**trans.model_dump()))
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

def update_city(db: Session, db_city: models.City, city_in: schemas.CityUpdate) -> models.City:
    """تحديث بيانات مدينة موجودة."""
    update_data = city_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_city, key, value)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

def delete_city(db: Session, db_city: models.City) -> None:
    """حذف مدينة (بعد التحقق من عدم وجود أحياء مرتبطة بها في طبقة الخدمات)."""
    db.delete(db_city)
    db.commit()
    return

# backend/src/users/crud/address_lookups_crud.py

# ... (دوال CRUD الحالية الخاصة بـ City) ...

# ==========================================================
# --- CRUD Functions for District ---
# ==========================================================

def get_all_districts(db: Session) -> List[models.District]:
    """جلب كل الأحياء مع ترجماتها."""
    return db.query(models.District).options(joinedload(models.District.translations)).all()

def get_district(db: Session, district_id: int) -> Optional[models.District]:
    """جلب حي واحد عن طريق الـ ID الخاص به."""
    return db.query(models.District).filter(models.District.district_id == district_id).first()

def create_district(db: Session, district_in: schemas.DistrictCreate) -> models.District:
    """إنشاء حي جديد مع ترجماته الأولية."""
    db_district = models.District(**district_in.model_dump(exclude={"translations"}))
    if district_in.translations:
        for trans in district_in.translations:
            db_district.translations.append(models.DistrictTranslation(**trans.model_dump()))
    db.add(db_district)
    db.commit()
    db.refresh(db_district)
    return db_district

def update_district(db: Session, db_district: models.District, district_in: schemas.DistrictUpdate) -> models.District:
    """تحديث بيانات حي موجود."""
    update_data = district_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_district, key, value)
    db.add(db_district)
    db.commit()
    db.refresh(db_district)
    return db_district

def delete_district(db: Session, db_district: models.District) -> None:
    """حذف حي (بعد التحقق من عدم وجود عناوين مرتبطة به في طبقة الخدمات)."""
    db.delete(db_district)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for AddressTypeTranslation ---
# ==========================================================

def add_or_update_address_type_translation(db: Session, type_id: int, trans_in: schemas.AddressTypeTranslationCreate) -> Optional[models.AddressType]:
    """
    إضافة أو تحديث ترجمة لنوع عنوان معين.
    يعيد الكائن الأب (AddressType) كاملاً مع كل ترجماته المحدثة.
    """
    db_type = db.query(models.AddressType).options(joinedload(models.AddressType.translations)).filter(models.AddressType.address_type_id == type_id).first()
    if not db_type:
        return None

    # البحث عن ترجمة موجودة بنفس اللغة
    existing_trans = next((t for t in db_type.translations if t.language_code == trans_in.language_code), None)

    if existing_trans:
        # تحديث الترجمة الموجودة
        existing_trans.translated_address_type_name = trans_in.translated_address_type_name
    else:
        # إضافة ترجمة جديدة
        new_trans = models.AddressTypeTranslation(
            address_type_id=type_id,
            language_code=trans_in.language_code,
            translated_address_type_name=trans_in.translated_address_type_name
        )
        db.add(new_trans)

    db.commit()
    db.refresh(db_type)
    return db_type

def delete_address_type_translation(db: Session, type_id: int, language_code: str) -> bool:
    """
    يحذف ترجمة معينة من قاعدة البيانات لنوع عنوان معين.
    :return: True إذا تم الحذف بنجاح, False إذا لم يتم العثور على الترجمة.
    """
    # البحث عن الترجمة أولاً
    translation = db.query(models.AddressTypeTranslation).filter(
        models.AddressTypeTranslation.address_type_id == type_id,
        models.AddressTypeTranslation.language_code == language_code
    ).first()

    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False

# ==========================================================
# --- CRUD Functions for CountryTranslation ---
# ==========================================================

def add_or_update_country_translation(db: Session, country_code: str, trans_in: schemas.CountryTranslationCreate) -> Optional[models.Country]:
    """
    إضافة أو تحديث ترجمة لدولة معينة.
    يعيد الكائن الأب (Country) كاملاً مع كل ترجماته المحدثة.
    """
    db_country = db.query(models.Country).options(joinedload(models.Country.translations)).filter(models.Country.country_code == country_code).first()
    if not db_country:
        return None

    # البحث عن ترجمة موجودة بنفس اللغة
    existing_trans = next((t for t in db_country.translations if t.language_code == trans_in.language_code), None)

    if existing_trans:
        # تحديث الترجمة الموجودة
        existing_trans.translated_country_name = trans_in.translated_country_name
    else:
        # إضافة ترجمة جديدة
        new_trans = models.CountryTranslation(
            country_code=country_code,
            language_code=trans_in.language_code,
            translated_country_name=trans_in.translated_country_name
        )
        db.add(new_trans)

    db.commit()
    db.refresh(db_country)
    return db_country

def delete_country_translation(db: Session, country_code: str, language_code: str) -> bool:
    """
    يحذف ترجمة معينة من قاعدة البيانات لدولة معينة.
    :return: True إذا تم الحذف بنجاح, False إذا لم يتم العثور على الترجمة.
    """
    # البحث عن الترجمة أولاً
    translation = db.query(models.CountryTranslation).filter(
        models.CountryTranslation.country_code == country_code,
        models.CountryTranslation.language_code == language_code
    ).first()

    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False

# ==========================================================
# --- CRUD Functions for GovernorateTranslation ---
# ==========================================================

def add_or_update_governorate_translation(db: Session, governorate_id: int, trans_in: schemas.GovernorateTranslationCreate) -> Optional[models.Governorate]:
    """
    إضافة أو تحديث ترجمة لمحافظة معينة.
    يعيد الكائن الأب (Governorate) كاملاً مع كل ترجماته المحدثة.
    """
    db_governorate = db.query(models.Governorate).options(joinedload(models.Governorate.translations)).filter(models.Governorate.governorate_id == governorate_id).first()
    if not db_governorate:
        return None

    # البحث عن ترجمة موجودة بنفس اللغة
    existing_trans = next((t for t in db_governorate.translations if t.language_code == trans_in.language_code), None)

    if existing_trans:
        # تحديث الترجمة الموجودة
        existing_trans.translated_governorate_name = trans_in.translated_governorate_name
    else:
        # إضافة ترجمة جديدة
        new_trans = models.GovernorateTranslation(
            governorate_id=governorate_id,
            language_code=trans_in.language_code,
            translated_governorate_name=trans_in.translated_governorate_name
        )
        db.add(new_trans)

    db.commit()
    db.refresh(db_governorate)
    return db_governorate

def delete_governorate_translation(db: Session, governorate_id: int, language_code: str) -> bool:
    """
    يحذف ترجمة معينة من قاعدة البيانات لمحافظة معينة.
    :return: True إذا تم الحذف بنجاح, False إذا لم يتم العثور على الترجمة.
    """
    # البحث عن الترجمة أولاً
    translation = db.query(models.GovernorateTranslation).filter(
        models.GovernorateTranslation.governorate_id == governorate_id,
        models.GovernorateTranslation.language_code == language_code
    ).first()

    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False

# ==========================================================
# --- CRUD Functions for CityTranslation ---
# ==========================================================

def add_or_update_city_translation(db: Session, city_id: int, trans_in: schemas.CityTranslationCreate) -> Optional[models.City]:
    """
    إضافة أو تحديث ترجمة لمدينة معينة.
    يعيد الكائن الأب (City) كاملاً مع كل ترجماته المحدثة.
    """
    db_city = db.query(models.City).options(joinedload(models.City.translations)).filter(models.City.city_id == city_id).first()
    if not db_city:
        return None

    # البحث عن ترجمة موجودة بنفس اللغة
    existing_trans = next((t for t in db_city.translations if t.language_code == trans_in.language_code), None)

    if existing_trans:
        # تحديث الترجمة الموجودة
        existing_trans.translated_city_name = trans_in.translated_city_name
    else:
        # إضافة ترجمة جديدة
        new_trans = models.CityTranslation(
            city_id=city_id,
            language_code=trans_in.language_code,
            translated_city_name=trans_in.translated_city_name
        )
        db.add(new_trans)

    db.commit()
    db.refresh(db_city)
    return db_city

def delete_city_translation(db: Session, city_id: int, language_code: str) -> bool:
    """
    يحذف ترجمة معينة من قاعدة البيانات لمدينة معينة.
    :return: True إذا تم الحذف بنجاح, False إذا لم يتم العثور على الترجمة.
    """
    # البحث عن الترجمة أولاً
    translation = db.query(models.CityTranslation).filter(
        models.CityTranslation.city_id == city_id,
        models.CityTranslation.language_code == language_code
    ).first()

    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False

# ==========================================================
# --- CRUD Functions for DistrictTranslation ---
# ==========================================================

def add_or_update_district_translation(db: Session, district_id: int, trans_in: schemas.DistrictTranslationCreate) -> Optional[models.District]:
    """
    إضافة أو تحديث ترجمة لحي معين.
    يعيد الكائن الأب (District) كاملاً مع كل ترجماته المحدثة.
    """
    db_district = db.query(models.District).options(joinedload(models.District.translations)).filter(models.District.district_id == district_id).first()
    if not db_district:
        return None

    # البحث عن ترجمة موجودة بنفس اللغة
    existing_trans = next((t for t in db_district.translations if t.language_code == trans_in.language_code), None)

    if existing_trans:
        # تحديث الترجمة الموجودة
        existing_trans.translated_district_name = trans_in.translated_district_name
    else:
        # إضافة ترجمة جديدة
        new_trans = models.DistrictTranslation(
            district_id=district_id,
            language_code=trans_in.language_code,
            translated_district_name=trans_in.translated_district_name
        )
        db.add(new_trans)

    db.commit()
    db.refresh(db_district)
    return db_district

def delete_district_translation(db: Session, district_id: int, language_code: str) -> bool:
    """
    يحذف ترجمة معينة من قاعدة البيانات لحي معين.
    :return: True إذا تم الحذف بنجاح, False إذا لم يتم العثور على الترجمة.
    """
    # البحث عن الترجمة أولاً
    translation = db.query(models.DistrictTranslation).filter(
        models.DistrictTranslation.district_id == district_id,
        models.DistrictTranslation.language_code == language_code
    ).first()

    if translation:
        db.delete(translation)
        db.commit()
        return True
    return False
