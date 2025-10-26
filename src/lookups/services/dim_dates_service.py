# backend\src\lookups\services\dim_dates_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, date, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # DimDate, DayOfWeekTranslation, MonthTranslation, Language
# استيراد الـ CRUD
from src.lookups.crud import dim_dates_crud # لـ DimDate, DayOfWeekTranslation, MonthTranslation CRUDs
from src.lookups.crud import languages_crud # للتحقق من وجود اللغة (Language)

# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # DimDate, DayOfWeekTranslation, MonthTranslation

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for DimDate (جدول الأبعاد الزمنية) ---
# ==========================================================

def create_new_dim_date(db: Session, date_in: schemas.DimDateCreate) -> models.DimDate:
    """
    خدمة لإنشاء سجل تاريخ جديد في جدول الأبعاد الزمنية.
    تُستخدم عادةً لملء الجدول الأولي بالبيانات التاريخية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        date_in (schemas.DimDateCreate): بيانات التاريخ للإنشاء.

    Returns:
        models.DimDate: كائن التاريخ الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان التاريخ موجوداً بالفعل.
    """
    existing_date = dim_dates_crud.get_dim_date(db, date_id=date_in.date_id)
    if existing_date:
        raise ConflictException(detail=f"التاريخ '{date_in.date_id}' موجود بالفعل في جدول الأبعاد الزمنية.")
    
    return dim_dates_crud.create_dim_date(db=db, date_in=date_in)

def get_dim_date_details(db: Session, date_id: date) -> models.DimDate:
    """
    خدمة لجلب سجل تاريخ واحد بالـ ID الخاص به، مع معالجة عدم الوجود.
    """
    db_date = dim_dates_crud.get_dim_date(db, date_id=date_id)
    if not db_date:
        raise NotFoundException(detail=f"التاريخ '{date_id}' غير موجود في جدول الأبعاد الزمنية.")
    return db_date

def get_all_dim_dates_service(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DimDate]:
    """خدمة لجلب قائمة بجميع التواريخ في جدول الأبعاد الزمنية، مع خيارات التصفية."""
    return dim_dates_crud.get_all_dim_dates(db, start_date=start_date, end_date=end_date)

# لا توجد خدمات للتحديث أو الحذف لـ DimDate لأنه جدول أبعاد ثابت.


# ==========================================================
# --- Services for DayOfWeekTranslation (ترجمات أيام الأسبوع) ---
# ==========================================================

def create_day_of_week_translation(db: Session, trans_in: schemas.DayOfWeekTranslationCreate) -> models.DayOfWeekTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لاسم يوم الأسبوع.
    تتضمن التحقق من عدم التكرار ووجود اللغة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        trans_in (schemas.DayOfWeekTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.DayOfWeekTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت الترجمة بنفس المفتاح واللغة موجودة بالفعل.
        NotFoundException: إذا كانت اللغة غير موجودة.
    """
    # 1. التحقق من وجود اللغة
    languages_crud.get_language(db, language_code=trans_in.language_code)

    # 2. التحقق من عدم وجود ترجمة بنفس المفتاح واللغة
    existing_translation = dim_dates_crud.get_day_of_week_translation(db, day_name_key=trans_in.day_name_key, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة ليوم '{trans_in.day_name_key}' باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return dim_dates_crud.create_day_of_week_translation(db=db, trans_in=trans_in)

def get_day_of_week_translation_details(db: Session, day_name_key: str, language_code: str) -> models.DayOfWeekTranslation:
    """
    خدمة لجلب ترجمة يوم الأسبوع محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        day_name_key (str): مفتاح اسم اليوم.
        language_code (str): رمز اللغة.

    Returns:
        models.DayOfWeekTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = dim_dates_crud.get_day_of_week_translation(db, day_name_key=day_name_key, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة ليوم '{day_name_key}' باللغة '{language_code}' غير موجودة.")
    return translation

def update_day_of_week_translation(db: Session, day_name_key: str, language_code: str, trans_in: schemas.DayOfWeekTranslationUpdate) -> models.DayOfWeekTranslation:
    """
    خدمة لتحديث ترجمة يوم الأسبوع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        day_name_key (str): مفتاح اسم اليوم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.DayOfWeekTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.DayOfWeekTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_day_of_week_translation_details(db, day_name_key, language_code) # التحقق من وجود الترجمة
    return dim_dates_crud.update_day_of_week_translation(db, db_translation=db_translation, trans_in=trans_in)

def remove_day_of_week_translation(db: Session, day_name_key: str, language_code: str):
    """
    خدمة لحذف ترجمة يوم الأسبوع معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        day_name_key (str): مفتاح اسم اليوم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_day_of_week_translation_details(db, day_name_key, language_code) # التحقق من وجود الترجمة
    dim_dates_crud.delete_day_of_week_translation(db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة يوم الأسبوع بنجاح."}


# ==========================================================
# --- Services for MonthTranslation (ترجمات الشهور) ---
# ==========================================================

def create_month_translation(db: Session, trans_in: schemas.MonthTranslationCreate) -> models.MonthTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لاسم الشهر.
    تتضمن التحقق من عدم التكرار ووجود اللغة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        trans_in (schemas.MonthTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.MonthTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت الترجمة بنفس المفتاح واللغة موجودة بالفعل.
        NotFoundException: إذا كانت اللغة غير موجودة.
    """
    # 1. التحقق من وجود اللغة
    languages_crud.get_language(db, language_code=trans_in.language_code)

    # 2. التحقق من عدم وجود ترجمة بنفس المفتاح واللغة
    existing_translation = dim_dates_crud.get_month_translation(db, month_name_key=trans_in.month_name_key, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة لشهر '{trans_in.month_name_key}' باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return dim_dates_crud.create_month_translation(db=db, trans_in=trans_in)

def get_month_translation_details(db: Session, month_name_key: str, language_code: str) -> models.MonthTranslation:
    """
    خدمة لجلب ترجمة شهر محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        month_name_key (str): مفتاح اسم الشهر.
        language_code (str): رمز اللغة.

    Returns:
        models.MonthTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = dim_dates_crud.get_month_translation(db, month_name_key=month_name_key, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لشهر '{month_name_key}' باللغة '{language_code}' غير موجودة.")
    return translation

def update_month_translation(db: Session, month_name_key: str, language_code: str, trans_in: schemas.MonthTranslationUpdate) -> models.MonthTranslation:
    """
    خدمة لتحديث ترجمة شهر موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        month_name_key (str): مفتاح اسم الشهر.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.MonthTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.MonthTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_month_translation_details(db, month_name_key, language_code) # التحقق من وجود الترجمة
    return dim_dates_crud.update_month_translation(db, db_translation=db_translation, trans_in=trans_in)

def remove_month_translation(db: Session, month_name_key: str, language_code: str):
    """
    خدمة لحذف ترجمة شهر معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        month_name_key (str): مفتاح اسم الشهر.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_month_translation_details(db, month_name_key, language_code) # التحقق من وجود الترجمة
    dim_dates_crud.delete_month_translation(db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة الشهر بنجاح."}