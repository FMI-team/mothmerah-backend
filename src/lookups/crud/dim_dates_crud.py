# backend\src\lookups\crud\dim_dates_crud.py

from sqlalchemy.orm import Session
from sqlalchemy import exists, and_
from typing import List, Optional
from datetime import datetime, date, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # DimDate, DayOfWeekTranslation, MonthTranslation

# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # DimDate, DayOfWeekTranslation, MonthTranslation


# ==========================================================
# --- CRUD Functions for DimDate (جدول الأبعاد الزمنية) ---
# ==========================================================

def create_dim_date(db: Session, date_in: schemas.DimDateCreate) -> models.DimDate:
    """
    ينشئ سجل تاريخ جديد في جدول الأبعاد الزمنية.
    هذه الدالة تُستخدم عادةً لملء الجدول الأولي بالبيانات التاريخية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        date_in (schemas.DimDateCreate): بيانات التاريخ للإنشاء.

    Returns:
        models.DimDate: كائن التاريخ الذي تم إنشاؤه.
    """
    db_date = models.DimDate(
        date_id=date_in.date_id,
        day_number_in_week=date_in.day_number_in_week,
        day_name_key=date_in.day_name_key,
        day_number_in_month=date_in.day_number_in_month,
        month_number_in_year=date_in.month_number_in_year,
        month_name_key=date_in.month_name_key,
        calendar_quarter=date_in.calendar_quarter,
        calendar_year=date_in.calendar_year,
        is_weekend_ksa=date_in.is_weekend_ksa,
        is_official_holiday_ksa=date_in.is_official_holiday_ksa,
        hijri_date=date_in.hijri_date
    )
    db.add(db_date)
    db.commit() # يتم الـ commit هنا لأنها عملية ملء للبيانات الثابتة
    db.refresh(db_date)
    return db_date

def get_dim_date(db: Session, date_id: date) -> Optional[models.DimDate]:
    """
    يجلب سجل تاريخ واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        date_id (date): معرف التاريخ (التاريخ نفسه) المطلوب.

    Returns:
        Optional[models.DimDate]: كائن التاريخ أو None.
    """
    return db.query(models.DimDate).filter(models.DimDate.date_id == date_id).first()

def get_all_dim_dates(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.DimDate]:
    """
    يجلب قائمة بجميع التواريخ في جدول الأبعاد الزمنية، مع خيارات التصفية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        start_date (Optional[date]): تاريخ البدء للتصفية.
        end_date (Optional[date]): تاريخ الانتهاء للتصفية.

    Returns:
        List[models.DimDate]: قائمة بكائنات التواريخ.
    """
    query = db.query(models.DimDate)
    if start_date:
        query = query.filter(models.DimDate.date_id >= start_date)
    if end_date:
        query = query.filter(models.DimDate.date_id <= end_date)
    return query.order_by(models.DimDate.date_id).all()

# لا يوجد تحديث أو حذف لـ DimDate لأنه جدول أبعاد ثابت.


# ==========================================================
# --- CRUD Functions for DayOfWeekTranslation (ترجمات أيام الأسبوع) ---
# ==========================================================

def create_day_of_week_translation(db: Session, trans_in: schemas.DayOfWeekTranslationCreate) -> models.DayOfWeekTranslation:
    """
    ينشئ ترجمة جديدة لاسم يوم الأسبوع.

    Args:
        db (Session): جلسة قاعدة البيانات.
        trans_in (schemas.DayOfWeekTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.DayOfWeekTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models.DayOfWeekTranslation(
        day_name_key=trans_in.day_name_key,
        language_code=trans_in.language_code,
        translated_day_name=trans_in.translated_day_name
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_day_of_week_translation(db: Session, day_name_key: str, language_code: str) -> Optional[models.DayOfWeekTranslation]:
    """
    يجلب ترجمة يوم الأسبوع محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        day_name_key (str): مفتاح اسم اليوم.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models.DayOfWeekTranslation]: كائن الترجمة أو None.
    """
    return db.query(models.DayOfWeekTranslation).filter(
        and_(
            models.DayOfWeekTranslation.day_name_key == day_name_key,
            models.DayOfWeekTranslation.language_code == language_code
        )
    ).first()

def update_day_of_week_translation(db: Session, db_translation: models.DayOfWeekTranslation, trans_in: schemas.DayOfWeekTranslationUpdate) -> models.DayOfWeekTranslation:
    """
    يحدث ترجمة يوم الأسبوع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.DayOfWeekTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.DayOfWeekTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.DayOfWeekTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_day_of_week_translation(db: Session, db_translation: models.DayOfWeekTranslation):
    """
    يحذف ترجمة يوم الأسبوع معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.DayOfWeekTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for MonthTranslation (ترجمات الشهور) ---
# ==========================================================

def create_month_translation(db: Session, trans_in: schemas.MonthTranslationCreate) -> models.MonthTranslation:
    """
    ينشئ ترجمة جديدة لاسم الشهر.

    Args:
        db (Session): جلسة قاعدة البيانات.
        trans_in (schemas.MonthTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.MonthTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models.MonthTranslation(
        month_name_key=trans_in.month_name_key,
        language_code=trans_in.language_code,
        translated_month_name=trans_in.translated_month_name
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_month_translation(db: Session, month_name_key: str, language_code: str) -> Optional[models.MonthTranslation]:
    """
    يجلب ترجمة شهر محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        month_name_key (str): مفتاح اسم الشهر.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models.MonthTranslation]: كائن الترجمة أو None.
    """
    return db.query(models.MonthTranslation).filter(
        and_(
            models.MonthTranslation.month_name_key == month_name_key,
            models.MonthTranslation.language_code == language_code
        )
    ).first()

def update_month_translation(db: Session, db_translation: models.MonthTranslation, trans_in: schemas.MonthTranslationUpdate) -> models.MonthTranslation:
    """
    يحدث ترجمة شهر موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.MonthTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.MonthTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.MonthTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_month_translation(db: Session, db_translation: models.MonthTranslation):
    """
    يحذف ترجمة شهر معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.MonthTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return