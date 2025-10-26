# backend\src\api\v1\routers\admin_lookups_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional, Dict # لتعريف أنواع البيانات في Python
from datetime import date # لتواريخ DimDate

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي

# استيراد Schemas (هياكل البيانات)
from src.lookups.schemas import lookups_schemas as schemas # لجميع Schemas Lookups العامة

# استيراد الخدمات (منطق العمل)
from src.lookups.services import ( # لجميع خدمات Lookups العامة
    currencies_service,
    languages_service,
    dim_dates_service,
    activity_types_service,
    security_event_types_service,
    entity_types_service
)


# تعريف الراوتر لإدارة الجداول المرجعية العامة من جانب المسؤولين.
router = APIRouter(
    prefix="/general-lookups", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /admin/general-lookups)
    tags=["Admin - General Lookup Tables"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_LOOKUPS"))] # صلاحية عامة لإدارة جداول Lookups
)

# ================================================================
# --- نقاط الوصول للعملات (Currencies) ---
# ================================================================

@router.post(
    "/currencies",
    response_model=schemas.CurrencyRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء عملة جديدة"
)
async def create_currency_endpoint(
    currency_in: schemas.CurrencyCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء عملة مرجعية جديدة في النظام.
    """
    return currencies_service.create_new_currency(db=db, currency_in=currency_in)

@router.get(
    "/currencies",
    response_model=List[schemas.CurrencyRead],
    summary="[Admin] جلب جميع العملات"
)
async def get_all_currencies_endpoint(
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """جلب قائمة بجميع العملات المرجعية في النظام."""
    return currencies_service.get_all_currencies_service(db=db, include_inactive=include_inactive)

@router.get(
    "/currencies/{currency_code}",
    response_model=schemas.CurrencyRead,
    summary="[Admin] جلب تفاصيل عملة واحدة"
)
async def get_currency_details_endpoint(currency_code: str, db: Session = Depends(get_db)):
    """جلب تفاصيل عملة مرجعية بالرمز الخاص بها."""
    return currencies_service.get_currency_by_code_service(db=db, currency_code=currency_code)

@router.patch(
    "/currencies/{currency_code}",
    response_model=schemas.CurrencyRead,
    summary="[Admin] تحديث عملة",
)
async def update_currency_endpoint(
    currency_code: str,
    currency_in: schemas.CurrencyUpdate,
    db: Session = Depends(get_db)
):
    """تحديث عملة مرجعية."""
    return currencies_service.update_currency(db=db, currency_code=currency_code, currency_in=currency_in)

@router.delete(
    "/currencies/{currency_code}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف عملة (حذف ناعم)",
    description="""
    حذف عملة مرجعية (حذف ناعم بتعيين 'is_active' إلى False).
    لا يمكن حذفها إذا كانت مرتبطة بكيانات حيوية (مثل الطلبات أو المعاملات).
    """,
)
async def soft_delete_currency_endpoint(currency_code: str, db: Session = Depends(get_db)):
    """نقطة وصول لحذف عملة (حذف ناعم)."""
    return currencies_service.soft_delete_currency_by_code(db=db, currency_code=currency_code)

# --- ترجمات العملات ---
@router.post(
    "/currencies/{currency_code}/translations",
    response_model=schemas.CurrencyTranslationRead, # ترجع الترجمة المنشأة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لعملة",
)
async def create_currency_translation_endpoint(
    currency_code: str,
    trans_in: schemas.CurrencyTranslationCreate,
    db: Session = Depends(get_db)
):
    """إنشاء ترجمة جديدة لعملة مرجعية بلغة معينة."""
    return currencies_service.create_currency_translation(db=db, currency_code=currency_code, trans_in=trans_in)

@router.get(
    "/currencies/{currency_code}/translations/{language_code}",
    response_model=schemas.CurrencyTranslationRead,
    summary="[Admin] جلب ترجمة محددة لعملة",
)
async def get_currency_translation_details_endpoint(
    currency_code: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة عملة مرجعية بلغة محددة."""
    return currencies_service.get_currency_translation_details(db=db, currency_code=currency_code, language_code=language_code)

@router.patch(
    "/currencies/{currency_code}/translations/{language_code}",
    response_model=schemas.CurrencyTranslationRead, # ترجع الترجمة المحدثة
    summary="[Admin] تحديث ترجمة عملة",
)
async def update_currency_translation_endpoint(
    currency_code: str,
    language_code: str,
    trans_in: schemas.CurrencyTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة عملة مرجعية بلغة محددة."""
    return currencies_service.update_currency_translation(db=db, currency_code=currency_code, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/currencies/{currency_code}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة عملة",
)
async def remove_currency_translation_endpoint(
    currency_code: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة عملة مرجعية بلغة محددة (حذف صارم)."""
    currencies_service.remove_currency_translation(db=db, currency_code=currency_code, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول للغات (Languages) ---
# ================================================================

@router.post(
    "/languages",
    response_model=schemas.LanguageRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء لغة جديدة"
)
async def create_language_endpoint(
    language_in: schemas.LanguageCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء لغة مرجعية جديدة في النظام.
    """
    return languages_service.create_new_language(db=db, language_in=language_in)

@router.get(
    "/languages",
    response_model=List[schemas.LanguageRead],
    summary="[Admin] جلب جميع اللغات"
)
async def get_all_languages_endpoint(
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """جلب قائمة بجميع اللغات المرجعية في النظام."""
    return languages_service.get_all_languages_service(db=db, include_inactive=include_inactive)

@router.get(
    "/languages/{language_code}",
    response_model=schemas.LanguageRead,
    summary="[Admin] جلب تفاصيل لغة واحدة"
)
async def get_language_details_endpoint(language_code: str, db: Session = Depends(get_db)):
    """جلب تفاصيل لغة مرجعية بالرمز الخاص بها."""
    return languages_service.get_language_by_code_service(db=db, language_code=language_code)

@router.patch(
    "/languages/{language_code}",
    response_model=schemas.LanguageRead,
    summary="[Admin] تحديث لغة",
)
async def update_language_endpoint(
    language_code: str,
    language_in: schemas.LanguageUpdate,
    db: Session = Depends(get_db)
):
    """تحديث لغة مرجعية."""
    return languages_service.update_language(db=db, language_code=language_code, language_in=language_in)

@router.delete(
    "/languages/{language_code}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف لغة (حذف ناعم)",
    description="""
    حذف لغة مرجعية (حذف ناعم بتعيين 'is_active_for_interface' إلى False).
    لا يمكن حذفها إذا كانت مرتبطة بترجمات أو تفضيلات مستخدمين.
    """,
)
async def soft_delete_language_endpoint(language_code: str, db: Session = Depends(get_db)):
    """نقطة وصول لحذف لغة (حذف ناعم)."""
    return languages_service.soft_delete_language_by_code(db=db, language_code=language_code)


# ================================================================
# --- نقاط الوصول للأبعاد الزمنية (DimDate) ---
# ================================================================

@router.post(
    "/dim-dates",
    response_model=schemas.DimDateRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء سجل تاريخ جديد في جدول الأبعاد الزمنية"
)
async def create_dim_date_endpoint(
    date_in: schemas.DimDateCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء سجل تاريخ جديد في جدول الأبعاد الزمنية (عادةً لملء الجدول الأولي).
    """
    return dim_dates_service.create_new_dim_date(db=db, date_in=date_in)

@router.get(
    "/dim-dates",
    response_model=List[schemas.DimDateRead],
    summary="[Admin] جلب جميع سجلات الأبعاد الزمنية"
)
async def get_all_dim_dates_endpoint(
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """جلب قائمة بجميع التواريخ في جدول الأبعاد الزمنية."""
    return dim_dates_service.get_all_dim_dates_service(db=db, start_date=start_date, end_date=end_date)

@router.get(
    "/dim-dates/{date_id}",
    response_model=schemas.DimDateRead,
    summary="[Admin] جلب تفاصيل سجل تاريخ واحد"
)
async def get_dim_date_details_endpoint(date_id: date, db: Session = Depends(get_db)):
    """جلب تفاصيل سجل تاريخ واحد من جدول الأبعاد الزمنية بالـ ID الخاص بها."""
    return dim_dates_service.get_dim_date_details(db=db, date_id=date_id)

# لا توجد نقاط وصول للتحديث أو الحذف لـ DimDate لأنه جدول أبعاد ثابت.

# --- ترجمات أيام الأسبوع ---
@router.post(
    "/dim-dates/day-of-week-translations",
    response_model=schemas.DayOfWeekTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة ليوم الأسبوع",
)
async def create_day_of_week_translation_endpoint(
    trans_in: schemas.DayOfWeekTranslationCreate,
    db: Session = Depends(get_db)
):
    """إنشاء ترجمة جديدة ليوم الأسبوع بلغة معينة."""
    return dim_dates_service.create_day_of_week_translation(db=db, trans_in=trans_in)

@router.get(
    "/dim-dates/day-of-week-translations/{day_name_key}/{language_code}",
    response_model=schemas.DayOfWeekTranslationRead,
    summary="[Admin] جلب ترجمة محددة ليوم الأسبوع",
)
async def get_day_of_week_translation_details_endpoint(
    day_name_key: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة يوم الأسبوع بلغة محددة."""
    return dim_dates_service.get_day_of_week_translation_details(db=db, day_name_key=day_name_key, language_code=language_code)

@router.patch(
    "/dim-dates/day-of-week-translations/{day_name_key}/{language_code}",
    response_model=schemas.DayOfWeekTranslationRead,
    summary="[Admin] تحديث ترجمة يوم الأسبوع",
)
async def update_day_of_week_translation_endpoint(
    day_name_key: str,
    language_code: str,
    trans_in: schemas.DayOfWeekTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة يوم الأسبوع بلغة محددة."""
    return dim_dates_service.update_day_of_week_translation(db=db, day_name_key=day_name_key, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/dim-dates/day-of-week-translations/{day_name_key}/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة يوم الأسبوع",
)
async def remove_day_of_week_translation_endpoint(
    day_name_key: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة يوم الأسبوع بلغة محددة (حذف صارم)."""
    dim_dates_service.remove_day_of_week_translation(db=db, day_name_key=day_name_key, language_code=language_code)
    return

# --- ترجمات الشهور ---
@router.post(
    "/dim-dates/month-translations",
    response_model=schemas.MonthTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لشهر",
)
async def create_month_translation_endpoint(
    trans_in: schemas.MonthTranslationCreate,
    db: Session = Depends(get_db)
):
    """إنشاء ترجمة جديدة لاسم الشهر بلغة معينة."""
    return dim_dates_service.create_month_translation(db=db, trans_in=trans_in)

@router.get(
    "/dim-dates/month-translations/{month_name_key}/{language_code}",
    response_model=schemas.MonthTranslationRead,
    summary="[Admin] جلب ترجمة محددة لشهر",
)
async def get_month_translation_details_endpoint(
    month_name_key: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة شهر بلغة محددة."""
    return dim_dates_service.get_month_translation_details(db=db, month_name_key=month_name_key, language_code=language_code)

@router.patch(
    "/dim-dates/month-translations/{month_name_key}/{language_code}",
    response_model=schemas.MonthTranslationRead,
    summary="[Admin] تحديث ترجمة شهر",
)
async def update_month_translation_endpoint(
    month_name_key: str,
    language_code: str,
    trans_in: schemas.MonthTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة شهر بلغة محددة."""
    return dim_dates_service.update_month_translation(db=db, month_name_key=month_name_key, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/dim-dates/month-translations/{month_name_key}/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة شهر",
)
async def remove_month_translation_endpoint(
    month_name_key: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة شهر بلغة محددة (حذف صارم)."""
    dim_dates_service.remove_month_translation(db=db, month_name_key=month_name_key, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول لأنواع الأنشطة (Activity Types) ---
# ================================================================

@router.post(
    "/activity-types",
    response_model=schemas.ActivityTypeRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء نوع نشاط جديد"
)
async def create_activity_type_endpoint(
    type_in: schemas.ActivityTypeCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء نوع مرجعي جديد للنشاط (مثل 'عرض منتج', 'تقديم مزايدة').
    """
    return activity_types_service.create_new_activity_type(db=db, type_in=type_in)

@router.get(
    "/activity-types",
    response_model=List[schemas.ActivityTypeRead],
    summary="[Admin] جلب جميع أنواع الأنشطة"
)
async def get_all_activity_types_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع أنواع الأنشطة المرجعية في النظام."""
    return activity_types_service.get_all_activity_types_service(db=db)

@router.get(
    "/activity-types/{type_id}",
    response_model=schemas.ActivityTypeRead,
    summary="[Admin] جلب تفاصيل نوع نشاط واحد"
)
async def get_activity_type_details_endpoint(type_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل نوع مرجعي لنشاط بالـ ID الخاص بها."""
    return activity_types_service.get_activity_type_details(db=db, type_id=type_id)

@router.patch(
    "/activity-types/{type_id}",
    response_model=schemas.ActivityTypeRead,
    summary="[Admin] تحديث نوع نشاط",
)
async def update_activity_type_endpoint(
    type_id: int,
    type_in: schemas.ActivityTypeUpdate,
    db: Session = Depends(get_db)
):
    """تحديث نوع مرجعي لنشاط."""
    return activity_types_service.update_activity_type(db=db, type_id=type_id, type_in=type_in)

@router.delete(
    "/activity-types/{type_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف نوع نشاط",
    description="""
    حذف نوع نشاط مرجعي (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بسجلات أنشطة مستخدم.
    """,
)
async def delete_activity_type_endpoint(type_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف نوع نشاط."""
    return activity_types_service.delete_activity_type_by_id(db=db, type_id=type_id)

# --- ترجمات أنواع الأنشطة ---
@router.post(
    "/activity-types/{type_id}/translations",
    response_model=schemas.ActivityTypeTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لنوع نشاط",
)
async def create_activity_type_translation_endpoint(
    type_id: int,
    trans_in: schemas.ActivityTypeTranslationCreate,
    db: Session = Depends(get_db)
):
    """إنشاء ترجمة جديدة لنوع نشاط مرجعي بلغة معينة."""
    return activity_types_service.create_activity_type_translation(db=db, type_id=type_id, trans_in=trans_in)

@router.get(
    "/activity-types/{type_id}/translations/{language_code}",
    response_model=schemas.ActivityTypeTranslationRead,
    summary="[Admin] جلب ترجمة محددة لنوع نشاط",
)
async def get_activity_type_translation_details_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة نوع نشاط مرجعي بلغة محددة."""
    return activity_types_service.get_activity_type_translation_details(db=db, type_id=type_id, language_code=language_code)

@router.patch(
    "/activity-types/{type_id}/translations/{language_code}",
    response_model=schemas.ActivityTypeTranslationRead,
    summary="[Admin] تحديث ترجمة نوع نشاط",
)
async def update_activity_type_translation_endpoint(
    type_id: int,
    language_code: str,
    trans_in: schemas.ActivityTypeTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة نوع نشاط مرجعي بلغة محددة."""
    return activity_types_service.update_activity_type_translation(db=db, type_id=type_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/activity-types/{type_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة نوع نشاط",
)
async def delete_activity_type_translation_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة نوع نشاط مرجعي بلغة محددة (حذف صارم)."""
    activity_types_service.remove_activity_type_translation(db=db, type_id=type_id, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول لأنواع أحداث الأمان (Security Event Types) ---
# ================================================================

@router.post(
    "/security-event-types",
    response_model=schemas.SecurityEventTypeRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء نوع حدث أمان جديد"
)
async def create_security_event_type_endpoint(
    type_in: schemas.SecurityEventTypeCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء نوع مرجعي جديد لحدث الأمان (مثل 'محاولة تسجيل دخول فاشلة').
    """
    return security_event_types_service.create_new_security_event_type(db=db, type_in=type_in)

@router.get(
    "/security-event-types",
    response_model=List[schemas.SecurityEventTypeRead],
    summary="[Admin] جلب جميع أنواع أحداث الأمان"
)
async def get_all_security_event_types_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع أنواع أحداث الأمان المرجعية في النظام."""
    return security_event_types_service.get_all_security_event_types_service(db=db)

@router.get(
    "/security-event-types/{type_id}",
    response_model=schemas.SecurityEventTypeRead,
    summary="[Admin] جلب تفاصيل نوع حدث أمان واحد"
)
async def get_security_event_type_details_endpoint(type_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل نوع مرجعي لحدث أمان بالـ ID الخاص بها."""
    return security_event_types_service.get_security_event_type_details(db=db, type_id=type_id)

@router.patch(
    "/security-event-types/{type_id}",
    response_model=schemas.SecurityEventTypeRead,
    summary="[Admin] تحديث نوع حدث أمان",
)
async def update_security_event_type_endpoint(
    type_id: int,
    type_in: schemas.SecurityEventTypeUpdate,
    db: Session = Depends(get_db)
):
    """تحديث نوع مرجعي لحدث أمان."""
    return security_event_types_service.update_security_event_type(db=db, type_id=type_id, type_in=type_in)

@router.delete(
    "/security-event-types/{type_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف نوع حدث أمان",
    description="""
    حذف نوع حدث أمان مرجعي (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بسجلات أحداث أمان.
    """,
)
async def delete_security_event_type_endpoint(type_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف نوع حدث أمان."""
    return security_event_types_service.delete_security_event_type_by_id(db=db, type_id=type_id)

# --- ترجمات أنواع أحداث الأمان ---
@router.post(
    "/security-event-types/{type_id}/translations",
    response_model=schemas.SecurityEventTypeTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لنوع حدث أمان",
)
async def create_security_event_type_translation_endpoint(
    type_id: int,
    trans_in: schemas.SecurityEventTypeTranslationCreate,
    db: Session = Depends(get_db)
):
    """إنشاء ترجمة جديدة لنوع حدث أمان مرجعي بلغة معينة."""
    return security_event_types_service.create_security_event_type_translation(db=db, type_id=type_id, trans_in=trans_in)

@router.get(
    "/security-event-types/{type_id}/translations/{language_code}",
    response_model=schemas.SecurityEventTypeTranslationRead,
    summary="[Admin] جلب ترجمة محددة لنوع حدث أمان",
)
async def get_security_event_type_translation_details_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة نوع حدث أمان مرجعي بلغة محددة."""
    return security_event_types_service.get_security_event_type_translation_details(db=db, type_id=type_id, language_code=language_code)

@router.patch(
    "/security-event-types/{type_id}/translations/{language_code}",
    response_model=schemas.SecurityEventTypeTranslationRead,
    summary="[Admin] تحديث ترجمة نوع حدث أمان",
)
async def update_security_event_type_translation_endpoint(
    type_id: int,
    language_code: str,
    trans_in: schemas.SecurityEventTypeTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة نوع حدث أمان مرجعي بلغة محددة."""
    return security_event_types_service.update_security_event_type_translation(db=db, type_id=type_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/security-event-types/{type_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة نوع حدث أمان",
)
async def remove_security_event_type_translation_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة نوع حدث أمان مرجعي بلغة محددة (حذف صارم)."""
    security_event_types_service.remove_security_event_type_translation(db=db, type_id=type_id, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول لأنواع الكيانات للمراجعة أو الصورة (Entity Types) ---
# ================================================================

@router.post(
    "/entity-types",
    response_model=schemas.EntityTypeForReviewOrImageRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء نوع كيان جديد للمراجعة أو الصورة"
)
async def create_entity_type_endpoint(
    type_in: schemas.EntityTypeForReviewOrImageCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء نوع كيان مرجعي جديد يمكن أن يرتبط بمراجعات أو صور (مثل 'منتج', 'بائع').
    """
    return entity_types_service.create_new_entity_type(db=db, type_in=type_in)

@router.get(
    "/entity-types",
    response_model=List[schemas.EntityTypeForReviewOrImageRead],
    summary="[Admin] جلب جميع أنواع الكيانات للمراجعة أو الصورة"
)
async def get_all_entity_types_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع أنواع الكيانات المرجعية للمراجعة أو الصورة في النظام."""
    return entity_types_service.get_all_entity_types_service(db=db)

@router.get(
    "/entity-types/{entity_type_code}",
    response_model=schemas.EntityTypeForReviewOrImageRead,
    summary="[Admin] جلب تفاصيل نوع كيان واحد للمراجعة أو الصورة"
)
async def get_entity_type_details_endpoint(entity_type_code: str, db: Session = Depends(get_db)):
    """جلب تفاصيل نوع كيان مرجعي للمراجعة أو الصورة بالرمز الخاص بها."""
    return entity_types_service.get_entity_type_details(db=db, entity_type_code=entity_type_code)

@router.patch(
    "/entity-types/{entity_type_code}",
    response_model=schemas.EntityTypeForReviewOrImageRead,
    summary="[Admin] تحديث نوع كيان للمراجعة أو الصورة",
)
async def update_entity_type_endpoint(
    entity_type_code: str,
    type_in: schemas.EntityTypeForReviewOrImageUpdate,
    db: Session = Depends(get_db)
):
    """تحديث نوع كيان مرجعي للمراجعة أو الصورة."""
    return entity_types_service.update_entity_type(db=db, entity_type_code=entity_type_code, type_in=type_in)

@router.delete(
    "/entity-types/{entity_type_code}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف نوع كيان للمراجعة أو الصورة",
    description="""
    حذف نوع كيان مرجعي للمراجعة أو الصورة (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بمراجعات أو صور.
    """,
)
async def delete_entity_type_endpoint(entity_type_code: str, db: Session = Depends(get_db)):
    """نقطة وصول لحذف نوع كيان للمراجعة أو الصورة."""
    return entity_types_service.delete_entity_type_by_code(db=db, entity_type_code=entity_type_code)

# --- ترجمات أنواع الكيانات للمراجعة أو الصورة ---
@router.post(
    "/entity-types/{entity_type_code}/translations",
    response_model=schemas.EntityTypeTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لنوع كيان للمراجعة أو الصورة",
)
async def create_entity_type_translation_endpoint(
    entity_type_code: str,
    trans_in: schemas.EntityTypeTranslationCreate,
    db: Session = Depends(get_db)
):
    """إنشاء ترجمة جديدة لنوع كيان مرجعي للمراجعة أو الصورة بلغة معينة."""
    return entity_types_service.create_entity_type_translation(db=db, entity_type_code=entity_type_code, trans_in=trans_in)

@router.get(
    "/entity-types/{entity_type_code}/translations/{language_code}",
    response_model=schemas.EntityTypeTranslationRead,
    summary="[Admin] جلب ترجمة محددة لنوع كيان للمراجعة أو الصورة",
)
async def get_entity_type_translation_details_endpoint(
    entity_type_code: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة نوع كيان مرجعي للمراجعة أو الصورة بلغة محددة."""
    return entity_types_service.get_entity_type_translation_details(db=db, entity_type_code=entity_type_code, language_code=language_code)

@router.patch(
    "/entity-types/{entity_type_code}/translations/{language_code}",
    response_model=schemas.EntityTypeTranslationRead,
    summary="[Admin] تحديث ترجمة نوع كيان للمراجعة أو الصورة",
)
async def update_entity_type_translation_endpoint(
    entity_type_code: str,
    language_code: str,
    trans_in: schemas.EntityTypeTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة نوع كيان مرجعي للمراجعة أو الصورة بلغة محددة."""
    return entity_types_service.update_entity_type_translation(db=db, entity_type_code=entity_type_code, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/entity-types/{entity_type_code}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة نوع كيان للمراجعة أو الصورة",
)
async def remove_entity_type_translation_endpoint(
    entity_type_code: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة نوع كيان مرجعي للمراجعة أو الصورة بلغة محددة (حذف صارم)."""
    entity_types_service.remove_entity_type_translation(db=db, entity_type_code=entity_type_code, language_code=language_code)
    return