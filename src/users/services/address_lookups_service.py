# backend/src/users/services/address_lookups_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from src.users.crud import address_lookups_crud as crud
from src.users.schemas import address_lookups_schemas as schemas
from src.users.models import addresses_models as models # لـ AddressType, Country, Governorate, City, District, Address
# استيراد المودلز من Lookups (لـ Language)
from src.lookups.models.lookups_models import Language # لـ Language (في الترجمات)
from src.exceptions import NotFoundException, ConflictException, BadRequestException, ForbiddenException # استيراد الاستثناءات المخصصة


# ==========================================================
# --- Services for AddressType (أنواع العناوين) ---
# ==========================================================

def create_new_address_type(db: Session, type_in: schemas.AddressTypeCreate) -> models.AddressType:
    """
    خدمة لإنشاء نوع عنوان جديد مع ترجماته الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas.AddressTypeCreate): بيانات النوع للإنشاء.

    Returns:
        models.AddressType: كائن النوع الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان نوع العنوان بمفتاح معين موجوداً بالفعل.
    """
    # 1. التحقق من عدم وجود نوع عنوان بنفس المفتاح
    existing_type = crud.get_address_type_by_key(db, key=type_in.address_type_name_key)
    if existing_type:
        raise ConflictException(detail=f"نوع العنوان بمفتاح '{type_in.address_type_name_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود الترجمة الافتراضية إذا كانت موجودة في schemas (TODO)
    # TODO: منطق عمل: التأكد من أن translations تحتوي على ترجمة افتراضية (مثلاً العربية) عند الإنشاء إذا كان address_type_name_key يُعرض للمستخدم مباشرة.

    return crud.create_address_type(db, type_in=type_in)

def get_all_address_types_service(db: Session) -> List[models.AddressType]:
    """خدمة لجلب كل أنواع العناوين."""
    return crud.get_all_address_types(db)

def get_address_type_by_id_service(db: Session, type_id: int) -> models.AddressType:
    """
    خدمة لجلب نوع عنوان واحد بالـ ID، مع معالجة عدم الوجود.
    """
    db_type = crud.get_address_type(db, type_id=type_id)
    if not db_type:
        raise NotFoundException(detail=f"نوع العنوان بمعرف {type_id} غير موجود.")
    return db_type

def update_address_type(db: Session, type_id: int, type_in: schemas.AddressTypeUpdate) -> models.AddressType:
    """
    خدمة لتحديث نوع عنوان موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.
    """
    db_type = get_address_type_by_id_service(db, type_id) # استخدام دالة الخدمة للتحقق من وجوده

    # التحقق من تفرد المفتاح إذا تم تحديث address_type_name_key
    if type_in.address_type_name_key and type_in.address_type_name_key != db_type.address_type_name_key:
        existing_type_by_key = crud.get_address_type_by_key(db, key=type_in.address_type_name_key)
        if existing_type_by_key and existing_type_by_key.address_type_id != type_id:
            raise ConflictException(detail=f"نوع العنوان بمفتاح '{type_in.address_type_name_key}' موجود بالفعل.")

    return crud.update_address_type(db, db_type=db_type, type_in=type_in)

def delete_address_type_by_id(db: Session, type_id: int):
    """
    خدمة لحذف نوع عنوان بشكل آمن.
    يعيد إسناد العناوين المرتبطة إلى النوع الافتراضي ثم يتم الحذف الفعلي.
    """
    db_type_to_delete = get_address_type_by_id_service(db, type_id) # استخدام دالة الخدمة للتحقق

    # جلب النوع الافتراضي (SHIPPING هو نوع افتراضي شائع للعناوين)
    DEFAULT_TYPE_KEY = "SHIPPING"
    default_type = crud.get_address_type_by_key(db, key=DEFAULT_TYPE_KEY)
    if not default_type:
        raise ConflictException(detail=f"نوع العنوان الافتراضي '{DEFAULT_TYPE_KEY}' غير موجود في قاعدة البيانات. يرجى تهيئة البيانات المرجعية.")
    
    # منع حذف النوع الافتراضي نفسه
    if db_type_to_delete.address_type_id == default_type.address_type_id:
        raise BadRequestException(detail="لا يمكن حذف نوع العنوان الافتراضي.")

    # 1. إعادة إسناد العناوين المرتبطة
    crud.reassign_addresses_to_default_type(db, old_type_id=type_id, default_type_id=default_type.address_type_id)

    # 2. الحذف الفعلي لنوع العنوان
    crud.delete_address_type(db, db_type=db_type_to_delete)
    
    db.commit() # تأكيد كل العمليات في transaction واحدة.
    return {"message": f"تم حذف نوع العنوان '{db_type_to_delete.address_type_name_key}' وإعادة إسناد العناوين المرتبطة إلى النوع الافتراضي."}

# --- خدمات إدارة الترجمات لنوع العنوان ---

def create_address_type_translation(db: Session, type_id: int, trans_in: schemas.AddressTypeTranslationCreate) -> models.AddressType:
    """
    خدمة لإنشاء ترجمة جديدة لنوع عنوان.
    تتضمن التحقق من وجود النوع الأم وعدم تكرار الترجمة لنفس اللغة.
    """
    db_type = get_address_type_by_id_service(db, type_id) # التحقق من وجود النوع الأم

    # التحقق من عدم وجود ترجمة بنفس اللغة
    if crud.get_address_type_translation(db, type_id=type_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة لنوع العنوان بمعرف {type_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    updated_type = crud.add_or_update_address_type_translation(db, type_id=type_id, trans_in=trans_in)
    db.commit()
    return updated_type

def get_address_type_translation_details(db: Session, type_id: int, language_code: str) -> models.AddressTypeTranslation:
    """
    خدمة لجلب ترجمة محددة لنوع عنوان.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع الأم.
        language_code (str): رمز اللغة.

    Returns:
        models.AddressTypeTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = crud.get_address_type_translation(db, type_id=type_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لنوع العنوان بمعرف {type_id} باللغة '{language_code}' غير موجودة.")
    return translation


def update_address_type_translation(db: Session, type_id: int, language_code: str, trans_in: schemas.AddressTypeTranslationUpdate) -> models.AddressType:
    """
    خدمة لتحديث ترجمة نوع عنوان موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.AddressTypeTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.AddressType: كائن النوع الأم المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_address_type_translation_details(db, type_id, language_code) # التحقق من وجود الترجمة
    updated_type = crud.add_or_update_address_type_translation(db, type_id=type_id, trans_in=schemas.AddressTypeTranslationCreate(
        language_code=language_code,
        translated_address_type_name=trans_in.translated_address_type_name # نحتاج الاسم القديم
    ))
    db.commit() # commit داخل الدالة crud
    return updated_type # ترجع النوع الأب بعد تحديث ترجمته


def remove_address_type_translation(db: Session, type_id: int, language_code: str):
    """
    خدمة لحذف ترجمة معينة لنوع عنوان.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_address_type_translation_details(db, type_id, language_code) # التحقق من وجود الترجمة
    crud.delete_address_type_translation(db, db_translation=db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة نوع العنوان بنجاح."}


# ==========================================================
# --- Services for Country (الدول) ---
# ==========================================================

def get_all_countries_service(db: Session) -> List[models.Country]:
    """خدمة لجلب كل الدول."""
    return crud.get_all_countries(db)

def get_country_by_code_service(db: Session, country_code: str) -> models.Country:
    """
    خدمة لجلب دولة واحدة بالـ Code، مع معالجة عدم الوجود.
    """
    db_country = crud.get_country(db, country_code=country_code)
    if not db_country:
        raise NotFoundException(detail=f"الدولة بالرمز '{country_code}' غير موجودة.")
    return db_country


def create_new_country(db: Session, country_in: schemas.CountryCreate) -> models.Country:
    """
    خدمة لإنشاء دولة جديدة مع ترجماتها الأولية.
    تتضمن التحقق من عدم التكرار.
    """
    # 1. التحقق من عدم وجود دولة بنفس الرمز
    existing = crud.get_country(db, country_code=country_in.country_code)
    if existing:
        raise ConflictException(detail=f"الدولة بالرمز '{country_in.country_code}' موجودة بالفعل.")
    
    # 2. التحقق من وجود الترجمة الافتراضية إذا كانت موجودة في schemas
    # TODO: منطق عمل: التأكد من أن translations تحتوي على ترجمة افتراضية (مثلاً العربية) عند الإنشاء.

    return crud.create_country(db, country_in=country_in)

def update_country(db: Session, country_code: str, country_in: schemas.CountryUpdate) -> models.Country:
    """
    خدمة لتحديث دولة موجودة.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.
    """
    db_country = get_country_by_code_service(db, country_code=country_code) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث country_name_key
    if country_in.country_name_key and country_in.country_name_key != db_country.country_name_key:
        existing_by_name = db.query(models.Country).filter(models.Country.country_name_key == country_in.country_name_key).first()
        if existing_by_name and existing_by_name.country_code != country_code:
            raise ConflictException(detail=f"الدولة بالاسم '{country_in.country_name_key}' موجودة بالفعل.")
    
    # TODO: التحقق من تفرد phone_country_code إذا تم تحديثه.

    return crud.update_country(db, db_country=db_country, country_in=country_in)

def soft_delete_country_by_code(db: Session, country_code: str):
    """
    خدمة للحذف الناعم لدولة (بتعيين is_active إلى False).
    تتضمن التحقق من عدم وجود محافظات أو عناوين مرتبطة بها.
    """
    db_country = get_country_by_code_service(db, country_code) # استخدام دالة الخدمة للتحقق

    if not db_country.is_active:
        raise BadRequestException(detail=f"الدولة '{country_code}' غير نشطة بالفعل.")

    # 1. التحقق من عدم وجود محافظات مرتبطة (Governorates)
    governorate_count = crud.count_governorates_in_country(db, country_code)
    if governorate_count > 0:
        raise ConflictException(detail=f"لا يمكن تعطيل الدولة '{country_code}' لأنها مرتبطة بـ {governorate_count} محافظة/محافظات نشطة. يرجى تعطيل المحافظات أولاً.")

    # 2. التحقق من عدم وجود عناوين (Addresses) مرتبطة مباشرة
    # TODO: يجب إضافة دالة CRUD لحساب العناوين المرتبطة في address_crud.py (أو core_crud.py)
    address_count = crud.count_addresses_in_country(db, country_code)
    if address_count > 0:
        raise ConflictException(detail=f"لا يمكن تعطيل الدولة '{country_code}' لأنها مرتبطة بـ {address_count} عنوان/عناوين نشطة. يرجى تعطيل العناوين أولاً.")


    db_country.is_active = False # تعيين is_active إلى False
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return {"message": f"تم تعطيل الدولة '{db_country.country_name_key}' بنجاح."}

# --- خدمات إدارة الترجمات للدولة ---

def create_country_translation(db: Session, country_code: str, trans_in: schemas.CountryTranslationCreate) -> models.Country:
    """
    خدمة لإنشاء ترجمة جديدة لدولة.
    تتضمن التحقق من وجود الدولة الأم وعدم تكرار الترجمة لنفس اللغة.
    """
    db_country = get_country_by_code_service(db, country_code=country_code) # التحقق من وجود الدولة الأم

    # التحقق من وجود الترجمة بنفس اللغة
    if crud.get_country_translation(db, country_code=country_code, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة للدولة '{country_code}' باللغة '{trans_in.language_code}' موجودة بالفعل.")

    updated_country = crud.add_or_update_country_translation(db, country_code=country_code, trans_in=trans_in)
    db.commit()
    return updated_country

def get_country_translation_details(db: Session, country_code: str, language_code: str) -> models.CountryTranslation:
    """
    خدمة لجلب ترجمة دولة محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        country_code (str): رمز الدولة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        models.CountryTranslation: كائن الترجمة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = crud.get_country_translation(db, country_code=country_code, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للدولة '{country_code}' باللغة '{language_code}' غير موجودة.")
    return translation

def update_country_translation(db: Session, country_code: str, language_code: str, trans_in: schemas.CountryTranslationUpdate) -> models.Country:
    """
    خدمة لتحديث ترجمة دولة موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        country_code (str): رمز الدولة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.CountryTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.Country: كائن الدولة الأم المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_country_translation_details(db, country_code, language_code) # التحقق من وجود الترجمة
    updated_country = crud.add_or_update_country_translation(db, country_code=country_code, trans_in=schemas.CountryTranslationCreate(
        language_code=language_code,
        translated_country_name=trans_in.translated_country_name,
        # TODO: تأكد من تمرير translated_description إذا كان موجوداً في schema.
    ))
    db.commit() # commit داخل الدالة crud
    return updated_country

def remove_country_translation(db: Session, country_code: str, language_code: str):
    """
    خدمة لحذف ترجمة معينة لدولة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        country_code (str): رمز الدولة الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_country_translation_details(db, country_code, language_code) # التحقق من وجود الترجمة
    crud.delete_country_translation(db, db_translation=db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة الدولة بنجاح."}


# ==========================================================
# --- Services for Governorate (المحافظات) ---
# ==========================================================

def get_all_governorates_service(db: Session) -> List[models.Governorate]:
    """خدمة لجلب كل المحافظات."""
    return crud.get_all_governorates(db)

def get_governorate_by_id_service(db: Session, governorate_id: int) -> models.Governorate:
    """
    خدمة لجلب محافظة واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    db_governorate = crud.get_governorate(db, governorate_id=governorate_id)
    if not db_governorate:
        raise NotFoundException(detail=f"المحافظة بمعرف {governorate_id} غير موجودة.")
    return db_governorate

def create_new_governorate(db: Session, governorate_in: schemas.GovernorateCreate) -> models.Governorate:
    """
    خدمة لإنشاء محافظة جديدة مع ترجماتها الأولية.
    تتضمن التحقق من وجود الدولة الأم وعدم التكرار.
    """
    # 1. التحقق من وجود الدولة الأم
    get_country_by_code_service(db, governorate_in.country_code) # هذه الدالة سترمي NotFoundException إن لم توجد الدولة.

    # 2. التحقق من عدم وجود محافظة بنفس المفتاح والدولة
    existing = db.query(models.Governorate).filter(
        models.Governorate.country_code == governorate_in.country_code,
        models.Governorate.governorate_name_key == governorate_in.governorate_name_key
    ).first()
    if existing:
        raise ConflictException(detail=f"المحافظة بمفتاح '{governorate_in.governorate_name_key}' موجودة بالفعل في الدولة '{governorate_in.country_code}'.")

    return crud.create_governorate(db, governorate_in=governorate_in)

def update_governorate(db: Session, governorate_id: int, governorate_in: schemas.GovernorateUpdate) -> models.Governorate:
    """
    خدمة لتحديث محافظة موجودة.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره، والتحقق من وجود الدولة الجديدة إن وجدت.
    """
    db_governorate = get_governorate_by_id_service(db, governorate_id=governorate_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث governorate_name_key
    if governorate_in.governorate_name_key and governorate_in.governorate_name_key != db_governorate.governorate_name_key:
        existing = db.query(models.Governorate).filter(
            models.Governorate.country_code == db_governorate.country_code, # في نفس الدولة
            models.Governorate.governorate_name_key == governorate_in.governorate_name_key
        ).first()
        if existing and existing.governorate_id != governorate_id:
            raise ConflictException(detail=f"المحافظة بمفتاح '{governorate_in.governorate_name_key}' موجودة بالفعل في الدولة '{db_governorate.country_code}'.")

    # التحقق من وجود الدولة الجديدة إذا تم تغيير country_code
    if governorate_in.country_code and governorate_in.country_code != db_governorate.country_code:
        get_country_by_code_service(db, governorate_in.country_code)

    return crud.update_governorate(db, db_governorate=db_governorate, governorate_in=governorate_in)

def soft_delete_governorate_by_id(db: Session, governorate_id: int):
    """
    خدمة للحذف الناعم لمحافظة (بتعيين is_active إلى False).
    تتضمن التحقق من عدم وجود مدن مرتبطة بها.
    """
    db_governorate = get_governorate_by_id_service(db, governorate_id) # استخدام دالة الخدمة للتحقق

    if not db_governorate.is_active:
        raise BadRequestException(detail=f"المحافظة بمعرف {governorate_id} غير نشطة بالفعل.")

    # التحقق من عدم وجود مدن مرتبطة (Cities)
    city_count = crud.count_cities_in_governorate(db, governorate_id=governorate_id)
    if city_count > 0:
        raise ConflictException(detail=f"لا يمكن تعطيل المحافظة بمعرف {governorate_id} لأنها مرتبطة بـ {city_count} مدينة/مدن نشطة. يرجى تعطيل المدن أولاً.")
    
    db_governorate.is_active = False
    db.add(db_governorate)
    db.commit()
    db.refresh(db_governorate)
    return {"message": f"تم تعطيل المحافظة '{db_governorate.governorate_name_key}' بنجاح."}


# --- خدمات إدارة الترجمات للمحافظة ---

def create_governorate_translation(db: Session, governorate_id: int, trans_in: schemas.GovernorateTranslationCreate) -> models.Governorate:
    """
    خدمة لإنشاء ترجمة جديدة لمحافظة.
    تتضمن التحقق من وجود المحافظة الأم وعدم تكرار الترجمة لنفس اللغة.
    """
    db_governorate = get_governorate_by_id_service(db, governorate_id) # التحقق من وجود المحافظة الأم

    # التحقق من وجود الترجمة بنفس اللغة
    if crud.get_governorate_translation(db, governorate_id=governorate_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة للمحافظة بمعرف {governorate_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    updated_governorate = crud.add_or_update_governorate_translation(db, governorate_id=governorate_id, trans_in=trans_in)
    db.commit()
    return updated_governorate

def get_governorate_translation_details(db: Session, governorate_id: int, language_code: str) -> models.GovernorateTranslation:
    """
    خدمة لجلب ترجمة محافظة محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        governorate_id (int): معرف المحافظة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        models.GovernorateTranslation: كائن الترجمة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = crud.get_governorate_translation(db, governorate_id=governorate_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للمحافظة بمعرف {governorate_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_governorate_translation(db: Session, governorate_id: int, language_code: str, trans_in: schemas.GovernorateTranslationUpdate) -> models.Governorate:
    """
    خدمة لتحديث ترجمة محافظة موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        governorate_id (int): معرف المحافظة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.GovernorateTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.Governorate: كائن المحافظة الأم المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_governorate_translation_details(db, governorate_id, language_code) # التحقق من وجود الترجمة
    updated_governorate = crud.add_or_update_governorate_translation(db, governorate_id=governorate_id, trans_in=schemas.GovernorateTranslationCreate(
        language_code=language_code,
        translated_governorate_name=trans_in.translated_governorate_name # نحتاج الاسم القديم
    ))
    db.commit() # commit داخل الدالة crud
    return updated_governorate # ترجع النوع الأب بعد تحديث ترجمته

def remove_governorate_translation(db: Session, governorate_id: int, language_code: str):
    """
    خدمة لحذف ترجمة معينة لمحافظة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        governorate_id (int): معرف المحافظة الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_governorate_translation_details(db, governorate_id, language_code) # التحقق من وجود الترجمة
    crud.delete_governorate_translation(db, db_translation=db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة المحافظة بنجاح."}


# ==========================================================
# --- Services for City (المدن) ---
# ==========================================================

def get_all_cities_service(db: Session) -> List[models.City]:
    """خدمة لجلب كل المدن."""
    return crud.get_all_cities(db)

def get_city_by_id_service(db: Session, city_id: int) -> models.City:
    """
    خدمة لجلب مدينة واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    db_city = crud.get_city(db, city_id=city_id)
    if not db_city:
        raise NotFoundException(detail=f"المدينة بمعرف {city_id} غير موجودة.")
    return db_city

def create_new_city(db: Session, city_in: schemas.CityCreate) -> models.City:
    """
    خدمة لإنشاء مدينة جديدة مع ترجماتها الأولية.
    تتضمن التحقق من وجود المحافظة الأم وعدم التكرار.
    """
    # 1. التحقق من وجود المحافظة الأم
    get_governorate_by_id_service(db, city_in.governorate_id) # هذه الدالة سترمي NotFoundException إن لم توجد المحافظة.

    # 2. التحقق من عدم وجود مدينة بنفس المفتاح والمحافظة
    existing = db.query(models.City).filter(
        models.City.governorate_id == city_in.governorate_id,
        models.City.city_name_key == city_in.city_name_key
    ).first()
    if existing:
        raise ConflictException(detail=f"المدينة بمفتاح '{city_in.city_name_key}' موجودة بالفعل في المحافظة بمعرف '{city_in.governorate_id}'.")

    return crud.create_city(db, city_in=city_in)

def update_city(db: Session, city_id: int, city_in: schemas.CityUpdate) -> models.City:
    """
    خدمة لتحديث مدينة موجودة.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره، والتحقق من وجود المحافظة الجديدة إن وجدت.
    """
    db_city = get_city_by_id_service(db, city_id=city_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث city_name_key
    if city_in.city_name_key and city_in.city_name_key != db_city.city_name_key:
        existing = db.query(models.City).filter(
            models.City.governorate_id == db_city.governorate_id, # في نفس المحافظة
            models.City.city_name_key == city_in.city_name_key
        ).first()
        if existing and existing.city_id != city_id:
            raise ConflictException(detail=f"المدينة بمفتاح '{city_in.city_name_key}' موجودة بالفعل في المحافظة بمعرف '{db_city.governorate_id}'.")

    # التحقق من وجود المحافظة الجديدة إذا تم تغيير governorate_id
    if city_in.governorate_id and city_in.governorate_id != db_city.governorate_id:
        get_governorate_by_id_service(db, city_in.governorate_id)

    return crud.update_city(db, db_city=db_city, city_in=city_in)

def soft_delete_city_by_id(db: Session, city_id: int):
    """
    خدمة للحذف الناعم لمدينة (بتعيين is_active إلى False).
    تتضمن التحقق من عدم وجود أحياء مرتبطة بها.
    """
    db_city = get_city_by_id_service(db, city_id) # استخدام دالة الخدمة للتحقق

    if not db_city.is_active:
        raise BadRequestException(detail=f"المدينة بمعرف {city_id} غير نشطة بالفعل.")

    # التحقق من عدم وجود أحياء مرتبطة (Districts)
    district_count = crud.count_districts_in_city(db, city_id=city_id)
    if district_count > 0:
        raise ConflictException(detail=f"لا يمكن تعطيل المدينة بمعرف {city_id} لأنها مرتبطة بـ {district_count} حي/أحياء نشطة. يرجى تعطيل الأحياء أولاً.")
    
    db_city.is_active = False
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return {"message": f"تم تعطيل المدينة '{db_city.city_name_key}' بنجاح."}

# --- خدمات إدارة الترجمات للمدينة ---

def create_city_translation(db: Session, city_id: int, trans_in: schemas.CityTranslationCreate) -> models.City:
    """خدمة لإنشاء ترجمة جديدة لمدينة."""
    db_city = get_city_by_id_service(db, city_id) # التحقق من وجود المدينة الأم

    # التحقق من وجود الترجمة بنفس اللغة
    if crud.get_city_translation(db, city_id=city_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة للمدينة بمعرف {city_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    updated_city = crud.add_or_update_city_translation(db, city_id=city_id, trans_in=trans_in)
    db.commit()
    return updated_city

def get_city_translation_details(db: Session, city_id: int, language_code: str) -> models.CityTranslation:
    """
    خدمة لجلب ترجمة مدينة محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        city_id (int): معرف المدينة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        models.CityTranslation: كائن الترجمة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = crud.get_city_translation(db, city_id=city_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للمدينة بمعرف {city_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_city_translation(db: Session, city_id: int, language_code: str, trans_in: schemas.CityTranslationUpdate) -> models.City:
    """
    خدمة لتحديث ترجمة مدينة موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        city_id (int): معرف المدينة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.CityTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.City: كائن المدينة الأم المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_city_translation_details(db, city_id, language_code) # التحقق من وجود الترجمة
    updated_city = crud.add_or_update_city_translation(db, city_id=city_id, trans_in=schemas.CityTranslationCreate(
        language_code=language_code,
        translated_city_name=trans_in.translated_city_name # نحتاج الاسم القديم
    ))
    db.commit() # commit داخل الدالة crud
    return updated_city # ترجع النوع الأب بعد تحديث ترجمته

def remove_city_translation(db: Session, city_id: int, language_code: str):
    """
    خدمة لحذف ترجمة معينة لمدينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        city_id (int): معرف المدينة الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_city_translation_details(db, city_id, language_code) # التحقق من وجود الترجمة
    crud.delete_city_translation(db, db_translation=db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة المدينة بنجاح."}


# ==========================================================
# --- Services for District (الأحياء) ---
# ==========================================================

def get_all_districts_service(db: Session) -> List[models.District]:
    """خدمة لجلب كل الأحياء."""
    return crud.get_all_districts(db)

def get_district_by_id_service(db: Session, district_id: int) -> models.District:
    """
    خدمة لجلب حي واحد بالـ ID، مع معالجة عدم الوجود.
    """
    db_district = crud.get_district(db, district_id=district_id)
    if not db_district:
        raise NotFoundException(detail=f"الحي بمعرف {district_id} غير موجود.")
    return db_district

def create_new_district(db: Session, district_in: schemas.DistrictCreate) -> models.District:
    """
    خدمة لإنشاء حي جديد مع ترجماتها الأولية.
    تتضمن التحقق من وجود المدينة الأم وعدم التكرار.
    """
    # 1. التحقق من وجود المدينة الأم
    get_city_by_id_service(db, district_in.city_id) # هذه الدالة سترمي NotFoundException إن لم توجد المدينة.

    # 2. التحقق من عدم وجود حي بنفس المفتاح والمدينة
    existing = db.query(models.District).filter(
        models.District.city_id == district_in.city_id,
        models.District.district_name_key == district_in.district_name_key
    ).first()
    if existing:
        raise ConflictException(detail=f"الحي بمفتاح '{district_in.district_name_key}' موجود بالفعل في المدينة بمعرف '{district_in.city_id}'.")

    return crud.create_district(db, district_in=district_in)

def update_district(db: Session, district_id: int, district_in: schemas.DistrictUpdate) -> models.District:
    """
    خدمة لتحديث حي.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره، والتحقق من وجود المدينة الجديدة إن وجدت.
    """
    db_district = get_district_by_id_service(db, district_id=district_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث district_name_key
    if district_in.district_name_key and district_in.district_name_key != db_district.district_name_key:
        existing = db.query(models.District).filter(
            models.District.city_id == db_district.city_id, # في نفس المدينة
            models.District.district_name_key == district_in.district_name_key
        ).first()
        if existing and existing.district_id != district_id:
            raise ConflictException(detail=f"الحي بمفتاح '{district_in.district_name_key}' موجود بالفعل في المدينة بمعرف '{db_district.city_id}'.")

    # التحقق من وجود المدينة الجديدة إذا تم تغيير city_id
    if district_in.city_id and district_in.city_id != db_district.city_id:
        get_city_by_id_service(db, district_in.city_id)

    return crud.update_district(db, db_district=db_district, district_in=district_in)

def soft_delete_district_by_id(db: Session, district_id: int):
    """
    خدمة للحذف الناعم لحي (بتعيين is_active إلى False).
    تتضمن التحقق من عدم وجود عناوين مرتبطة به.
    """
    db_district = get_district_by_id_service(db, district_id) # استخدام دالة الخدمة للتحقق

    if not db_district.is_active:
        raise BadRequestException(detail=f"الحي بمعرف {district_id} غير نشط بالفعل.")

    # التحقق من عدم وجود عناوين مرتبطة (Addresses)
    address_count = crud.count_addresses_in_district(db, district_id=district_id)
    if address_count > 0:
        raise ConflictException(detail=f"لا يمكن تعطيل الحي بمعرف {district_id} لأنه مرتبط بـ {address_count} عنوان/عناوين نشطة. يرجى تعطيل العناوين أولاً.")
    
    db_district.is_active = False
    db.add(db_district)
    db.commit()
    db.refresh(db_district)
    return {"message": f"تم تعطيل الحي '{db_district.district_name_key}' بنجاح."}

# --- خدمات إدارة الترجمات للحي ---

def create_district_translation(db: Session, district_id: int, trans_in: schemas.DistrictTranslationCreate) -> models.District:
    """خدمة لإنشاء ترجمة جديدة لحي."""
    db_district = get_district_by_id_service(db, district_id) # التحقق من وجود الحي الأم

    # التحقق من وجود الترجمة بنفس اللغة
    if crud.get_district_translation(db, district_id=district_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة للحي بمعرف {district_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    updated_district = crud.add_or_update_district_translation(db, district_id=district_id, trans_in=trans_in)
    db.commit()
    return updated_district

def get_district_translation_details(db: Session, district_id: int, language_code: str) -> models.DistrictTranslation:
    """
    خدمة لجلب ترجمة حي محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        district_id (int): معرف الحي الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        models.DistrictTranslation: كائن الترجمة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = crud.get_district_translation(db, district_id=district_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للحي بمعرف {district_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_district_translation(db: Session, district_id: int, language_code: str, trans_in: schemas.DistrictTranslationUpdate) -> models.District:
    """
    خدمة لتحديث ترجمة حي موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        district_id (int): معرف الحي الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.DistrictTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.District: كائن الحي الأم المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_district_translation_details(db, district_id, language_code) # التحقق من وجود الترجمة
    updated_district = crud.add_or_update_district_translation(db, district_id=district_id, trans_in=schemas.DistrictTranslationCreate(
        language_code=language_code,
        translated_district_name=trans_in.translated_district_name # نحتاج الاسم القديم
    ))
    db.commit() # commit داخل الدالة crud
    return updated_district # ترجع النوع الأب بعد تحديث ترجمته

def remove_district_translation(db: Session, district_id: int, language_code: str):
    """
    خدمة لحذف ترجمة معينة لحي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        district_id (int): معرف الحي الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_district_translation_details(db, district_id, language_code) # التحقق من وجود الترجمة
    crud.delete_district_translation(db, db_translation=db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة الحي بنجاح."}