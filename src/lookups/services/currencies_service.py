# backend\src\lookups\services\currencies_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # Currency, CurrencyTranslation, Language
# استيراد الـ CRUD
from src.lookups.crud import currencies_crud # لـ Currency, CurrencyTranslation CRUDs
from src.lookups.crud import languages_crud # للتحقق من وجود اللغة (Language)

# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # Currency, CurrencyTranslation

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for Currency (العملات) ---
# ==========================================================

def create_new_currency(db: Session, currency_in: schemas.CurrencyCreate) -> models.Currency:
    """
    خدمة لإنشاء عملة جديدة مع ترجماتها الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_in (schemas.CurrencyCreate): بيانات العملة للإنشاء.

    Returns:
        models.Currency: كائن العملة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت العملة بنفس الرمز أو المفتاح موجودة بالفعل.
        NotFoundException: إذا كانت اللغة المحددة للترجمة غير موجودة.
    """
    # 1. التحقق من عدم وجود عملة بنفس الرمز أو المفتاح
    existing_currency_by_code = currencies_crud.get_currency(db, currency_code=currency_in.currency_code)
    if existing_currency_by_code:
        raise ConflictException(detail=f"العملة بالرمز '{currency_in.currency_code}' موجودة بالفعل.")
    
    existing_currency_by_key = currencies_crud.get_currency_by_key(db, key=currency_in.currency_name_key)
    if existing_currency_by_key:
        raise ConflictException(detail=f"العملة بمفتاح الاسم '{currency_in.currency_name_key}' موجودة بالفعل.")
    
    # 2. التحقق من وجود اللغات المستخدمة في الترجمات
    if currency_in.translations:
        for trans_in in currency_in.translations:
            language_obj = languages_crud.get_language(db, language_code=trans_in.language_code)
            if not language_obj:
                raise NotFoundException(detail=f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    return currencies_crud.create_currency(db=db, currency_in=currency_in)

def get_all_currencies_service(db: Session, include_inactive: bool = False) -> List[models.Currency]:
    """خدمة لجلب قائمة بجميع العملات."""
    return currencies_crud.get_all_currencies(db, include_inactive=include_inactive)

def get_currency_by_code_service(db: Session, currency_code: str) -> models.Currency:
    """
    خدمة لجلب عملة واحدة بالرمز الخاص بها، مع معالجة عدم الوجود.
    """
    db_currency = currencies_crud.get_currency(db, currency_code=currency_code)
    if not db_currency:
        raise NotFoundException(detail=f"العملة بالرمز '{currency_code}' غير موجودة.")
    return db_currency

def update_currency(db: Session, currency_code: str, currency_in: schemas.CurrencyUpdate) -> models.Currency:
    """
    خدمة لتحديث عملة موجودة.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_code (str): رمز العملة المراد تحديثها.
        currency_in (schemas.CurrencyUpdate): البيانات المراد تحديثها.

    Returns:
        models.Currency: كائن العملة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على العملة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_currency = get_currency_by_code_service(db, currency_code=currency_code) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث currency_name_key
    if currency_in.currency_name_key and currency_in.currency_name_key != db_currency.currency_name_key:
        existing_currency_by_key = currencies_crud.get_currency_by_key(db, key=currency_in.currency_name_key)
        if existing_currency_by_key and existing_currency_by_key.currency_code != currency_code:
            raise ConflictException(detail=f"العملة بمفتاح الاسم '{currency_in.currency_name_key}' موجودة بالفعل.")

    return currencies_crud.update_currency(db, db_currency=db_currency, currency_in=currency_in)

def soft_delete_currency_by_code(db: Session, currency_code: str):
    """
    خدمة للحذف الناعم لعملة (بتعيين is_active إلى False).
    تتضمن التحقق من عدم وجود ارتباطات حيوية (مثل طلبات أو معاملات).

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_code (str): رمز العملة المراد حذفها ناعماً.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على العملة.
        BadRequestException: إذا كانت العملة غير نشطة بالفعل.
        ConflictException: إذا كانت هناك ارتباطات تمنع التعطيل.
    """
    db_currency = get_currency_by_code_service(db, currency_code=currency_code) # استخدام دالة الخدمة للتحقق

    if not db_currency.is_active:
        raise BadRequestException(detail=f"العملة بالرمز '{currency_code}' غير نشطة بالفعل.")

    # TODO: التحقق من عدم وجود ارتباطات حيوية (مثلاً Orders, WalletTransactions)
    #       هذا يتطلب دوال count في CRUD الخاص بتلك المودلات.
    #       orders_count = orders_crud.count_orders_with_currency(db, currency_code)
    #       if orders_count > 0:
    #           raise ConflictException(detail=f"لا يمكن تعطيل العملة '{currency_code}' لأنها مرتبطة بـ {orders_count} طلبات.")
    # TODO: تأكد من عدم تعطيل العملة الافتراضية للنظام (إذا وجدت).

    db_currency.is_active = False # تعيين is_active إلى False
    db.add(db_currency)
    db.commit()
    db.refresh(db_currency)
    return {"message": f"تم تعطيل العملة '{db_currency.currency_name_key}' بنجاح."}


# ==========================================================
# --- Services for CurrencyTranslation (ترجمات العملات) ---
# ==========================================================

def create_currency_translation(db: Session, currency_code: str, trans_in: schemas.CurrencyTranslationCreate) -> models.CurrencyTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لعملة.
    تتضمن التحقق من وجود العملة الأم وعدم تكرار الترجمة لنفس اللغة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_code (str): رمز العملة الأم.
        trans_in (schemas.CurrencyTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.CurrencyTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على العملة الأم أو اللغة.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    # 1. التحقق من وجود العملة الأم
    get_currency_by_code_service(db, currency_code=currency_code)

    # 2. التحقق من وجود اللغة
    language_obj = languages_crud.get_language(db, language_code=trans_in.language_code)
    if not language_obj:
        raise NotFoundException(detail=f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    # 3. التحقق من عدم وجود ترجمة بنفس اللغة
    existing_translation = currencies_crud.get_currency_translation(db, currency_code=currency_code, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة للعملة '{currency_code}' باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return currencies_crud.create_currency_translation(db=db, currency_code=currency_code, trans_in=trans_in)

def get_currency_translation_details(db: Session, currency_code: str, language_code: str) -> models.CurrencyTranslation:
    """
    خدمة لجلب ترجمة عملة محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_code (str): رمز العملة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        models.CurrencyTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = currencies_crud.get_currency_translation(db, currency_code=currency_code, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للعملة '{currency_code}' باللغة '{language_code}' غير موجودة.")
    return translation

def update_currency_translation(db: Session, currency_code: str, language_code: str, trans_in: schemas.CurrencyTranslationUpdate) -> models.CurrencyTranslation:
    """
    خدمة لتحديث ترجمة عملة موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_code (str): رمز العملة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.CurrencyTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.CurrencyTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_currency_translation_details(db, currency_code, language_code) # التحقق من وجود الترجمة
    return currencies_crud.update_currency_translation(db, db_translation=db_translation, trans_in=trans_in)

def remove_currency_translation(db: Session, currency_code: str, language_code: str):
    """
    خدمة لحذف ترجمة عملة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_code (str): رمز العملة الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_currency_translation_details(db, currency_code, language_code) # التحقق من وجود الترجمة
    currencies_crud.delete_currency_translation(db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة العملة بنجاح."}
    