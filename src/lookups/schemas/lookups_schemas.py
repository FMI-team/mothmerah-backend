# backend\src\lookups\schemas\lookups_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, date # لـ created_at, updated_at, date_id


# ==========================================================
# --- Schemas للعملات (Currencies) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class CurrencyBase(BaseModel):
    """النموذج الأساسي لبيانات العملة."""
    currency_code: str = Field(..., max_length=3, description="رمز العملة (ISO 4217).")
    currency_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم العملة للترجمة.")
    symbol: str = Field(..., max_length=5, description="رمز العملة (مثلاً: $، €، ر.س).")
    decimal_places: int = Field(2, ge=0, description="عدد الخانات العشرية للعملة.")
    is_active: bool = Field(True, description="هل العملة نشطة؟")

class CurrencyCreate(CurrencyBase):
    """نموذج لإنشاء عملة جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List["CurrencyTranslationCreate"]] = Field([], description="الترجمات الأولية لاسم العملة.")

class CurrencyUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث عملة موجودة."""
    currency_name_key: Optional[str] = Field(None, max_length=50)
    symbol: Optional[str] = Field(None, max_length=5)
    decimal_places: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class CurrencyRead(CurrencyBase):
    """نموذج لقراءة وعرض تفاصيل العملة، يتضمن ترجماتها ومعرفها."""
    created_at: datetime
    updated_at: datetime
    translations: List["CurrencyTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)

# Schemas لترجمات العملات (Currencies Translations)
class CurrencyTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة العملة."""
    language_code: str = Field(..., max_length=10)
    translated_currency_name: str = Field(..., max_length=100)

class CurrencyTranslationCreate(CurrencyTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لعملة."""
    pass

class CurrencyTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة عملة موجودة."""
    translated_currency_name: Optional[str] = Field(None, max_length=100)

class CurrencyTranslationRead(CurrencyTranslationBase):
    """نموذج لقراءة وعرض ترجمة العملة."""
    currency_code: str # رمز العملة الأم
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas للغات (Languages) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class LanguageBase(BaseModel):
    """النموذج الأساسي لبيانات اللغة."""
    language_code: str = Field(..., max_length=10, description="رمز اللغة (ISO 639-1 أو BCP 47).")
    language_name_native: str = Field(..., max_length=50, description="اسم اللغة بلغتها الأصلية (مثلاً: العربية).")
    language_name_en: str = Field(..., max_length=50, description="اسم اللغة بالإنجليزية كمرجع (مثلاً: Arabic).")
    text_direction: str = Field(..., max_length=3, description="اتجاه النص ('LTR' أو 'RTL').")
    is_active_for_interface: bool = Field(False, description="هل اللغة نشطة للاستخدام في واجهة المستخدم؟")
    sort_order: Optional[int] = Field(None, ge=0, description="ترتيب عرض اللغة في القوائم (اختياري).")

class LanguageCreate(LanguageBase):
    """نموذج لإنشاء لغة جديدة."""
    pass

class LanguageUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث لغة موجودة."""
    language_name_native: Optional[str] = Field(None, max_length=50)
    language_name_en: Optional[str] = Field(None, max_length=50)
    text_direction: Optional[str] = Field(None, max_length=3)
    is_active_for_interface: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)

class LanguageRead(LanguageBase):
    """نموذج لقراءة وعرض تفاصيل اللغة."""
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas للأبعاد الزمنية (DimDate) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class DimDateBase(BaseModel):
    """النموذج الأساسي لبيانات البعد الزمني (اليوم)."""
    date_id: date = Field(..., description="التاريخ الفريد لهذا السجل.")
    day_number_in_week: int = Field(..., ge=1, le=7)
    day_name_key: str = Field(..., max_length=20)
    day_number_in_month: int = Field(..., ge=1, le=31)
    month_number_in_year: int = Field(..., ge=1, le=12)
    month_name_key: str = Field(..., max_length=20)
    calendar_quarter: int = Field(..., ge=1, le=4)
    calendar_year: int = Field(..., ge=1900) # افتراض سنة معقولة
    is_weekend_ksa: bool
    is_official_holiday_ksa: bool
    hijri_date: Optional[str] = Field(None, max_length=20)

class DimDateCreate(DimDateBase):
    """نموذج لإنشاء سجل تاريخ جديد في جدول الأبعاد الزمنية."""
    pass

# لا يوجد DimDateUpdate أو Delete لأن هذا جدول ثابت ويتم ملؤه مرة واحدة.

class DimDateRead(DimDateBase):
    """نموذج لقراءة وعرض تفاصيل البعد الزمني (اليوم)."""
    model_config = ConfigDict(from_attributes=True)

# Schemas لترجمات أيام الأسبوع والشهور (DayOfWeekTranslation, MonthTranslation)
class DayOfWeekTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة أيام الأسبوع."""
    day_name_key: str = Field(..., max_length=20)
    language_code: str = Field(..., max_length=10)
    translated_day_name: str = Field(..., max_length=30)

class DayOfWeekTranslationCreate(DayOfWeekTranslationBase):
    """نموذج لإنشاء ترجمة جديدة ليوم الأسبوع."""
    pass

class DayOfWeekTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة يوم الأسبوع موجودة."""
    translated_day_name: Optional[str] = Field(None, max_length=30)

class DayOfWeekTranslationRead(DayOfWeekTranslationBase):
    """نموذج لقراءة وعرض ترجمة أيام الأسبوع."""
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MonthTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة الشهور."""
    month_name_key: str = Field(..., max_length=20)
    language_code: str = Field(..., max_length=10)
    translated_month_name: str = Field(..., max_length=30)

class MonthTranslationCreate(MonthTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لشهر."""
    pass

class MonthTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة شهر موجودة."""
    translated_month_name: Optional[str] = Field(None, max_length=30)

class MonthTranslationRead(MonthTranslationBase):
    """نموذج لقراءة وعرض ترجمة الشهور."""
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأنواع الأنشطة (ActivityType) ---
# ==========================================================
class ActivityTypeBase(BaseModel):
    """النموذج الأساسي لبيانات نوع النشاط."""
    activity_name_key: str = Field(..., max_length=100, description="مفتاح فريد لاسم نوع النشاط.")
    description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف نوع النشاط للترجمة.")

class ActivityTypeCreate(ActivityTypeBase):
    """نموذج لإنشاء نوع نشاط جديد، يتضمن ترجماته الأولية."""
    translations: Optional[List["ActivityTypeTranslationCreate"]] = Field([], description="الترجمات الأولية لنوع النشاط.")

class ActivityTypeUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث نوع نشاط موجود."""
    activity_name_key: Optional[str] = Field(None, max_length=100)
    description_key: Optional[str] = Field(None, max_length=255)

class ActivityTypeRead(ActivityTypeBase):
    """نموذج لقراءة وعرض نوع النشاط."""
    activity_type_id: int
    created_at: datetime
    translations: List["ActivityTypeTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)

# Schemas لترجمات أنواع الأنشطة (ActivityType Translations)
class ActivityTypeTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة نوع النشاط."""
    language_code: str = Field(..., max_length=10)
    translated_activity_name: str = Field(..., max_length=150)
    translated_activity_description: Optional[str] = Field(None)

class ActivityTypeTranslationCreate(ActivityTypeTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لنوع نشاط."""
    pass

class ActivityTypeTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة نوع نشاط موجودة."""
    translated_activity_name: Optional[str] = Field(None, max_length=150)
    translated_activity_description: Optional[str] = Field(None)

class ActivityTypeTranslationRead(ActivityTypeTranslationBase):
    """نموذج لقراءة وعرض ترجمة نوع النشاط."""
    activity_type_id: int # معرف النوع الأم
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأنواع أحداث الأمان (SecurityEventType) ---
# ==========================================================
class SecurityEventTypeBase(BaseModel):
    """النموذج الأساسي لبيانات نوع حدث الأمان."""
    event_name_key: str = Field(..., max_length=100, description="مفتاح فريد لاسم حدث الأمان.")
    description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف حدث الأمان للترجمة.")
    severity_level: Optional[int] = Field(None, ge=1, le=5, description="مستوى خطورة الحدث (1-5).")

class SecurityEventTypeCreate(SecurityEventTypeBase):
    """نموذج لإنشاء نوع حدث أمان جديد، يتضمن ترجماته الأولية."""
    translations: Optional[List["SecurityEventTypeTranslationCreate"]] = Field([], description="الترجمات الأولية لاسم الحدث ووصفه.")

class SecurityEventTypeUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث نوع حدث أمان موجود."""
    event_name_key: Optional[str] = Field(None, max_length=100)
    description_key: Optional[str] = Field(None, max_length=255)
    severity_level: Optional[int] = Field(None, ge=1, le=5)

class SecurityEventTypeRead(SecurityEventTypeBase):
    """نموذج لقراءة وعرض نوع حدث الأمان."""
    security_event_type_id: int
    created_at: datetime
    translations: List["SecurityEventTypeTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)

# Schemas لترجمات أنواع أحداث الأمان (SecurityEventType Translations)
class SecurityEventTypeTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة نوع حدث الأمان."""
    language_code: str = Field(..., max_length=10)
    translated_event_name: str = Field(..., max_length=150)
    translated_event_description: Optional[str] = Field(None)

class SecurityEventTypeTranslationCreate(SecurityEventTypeTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لنوع حدث أمان."""
    pass

class SecurityEventTypeTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة نوع حدث أمان موجودة."""
    translated_event_name: Optional[str] = Field(None, max_length=150)
    translated_event_description: Optional[str] = Field(None)

class SecurityEventTypeTranslationRead(SecurityEventTypeTranslationBase):
    """نموذج لقراءة وعرض ترجمة نوع حدث الأمان."""
    security_event_type_id: int # معرف النوع الأم
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأنواع الكيانات للمراجعة أو الصورة (Entity Types for Review or Image) ---
# ==========================================================
class EntityTypeForReviewOrImageBase(BaseModel):
    """النموذج الأساسي لبيانات نوع الكيان للمراجعة أو الصورة."""
    entity_type_code: str = Field(..., max_length=50, description="رمز فريد لنوع الكيان (مثلاً: 'PRODUCT', 'SELLER').")
    entity_type_name_key: str = Field(..., max_length=100, description="مفتاح فريد لاسم نوع الكيان للترجمة.")
    description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف نوع الكيان للترجمة.")

class EntityTypeForReviewOrImageCreate(EntityTypeForReviewOrImageBase):
    """نموذج لإنشاء نوع كيان جديد للمراجعة أو الصورة، يتضمن ترجماته الأولية."""
    translations: Optional[List["EntityTypeTranslationCreate"]] = Field([], description="الترجمات الأولية لنوع الكيان.")

class EntityTypeForReviewOrImageUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث نوع كيان للمراجعة أو الصورة موجود."""
    entity_type_name_key: Optional[str] = Field(None, max_length=100)
    description_key: Optional[str] = Field(None, max_length=255)

class EntityTypeForReviewOrImageRead(EntityTypeForReviewOrImageBase):
    """نموذج لقراءة وعرض نوع الكيان للمراجعة أو الصورة."""
    created_at: datetime
    translations: List["EntityTypeTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)

# Schemas لترجمات أنواع الكيانات للمراجعة أو الصورة (EntityType Translations)
class EntityTypeTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة نوع الكيان للمراجعة أو الصورة."""
    entity_type_code: str = Field(..., max_length=50)
    language_code: str = Field(..., max_length=10)
    translated_entity_type_name: str = Field(..., max_length=100)
    translated_entity_description: Optional[str] = Field(None)

class EntityTypeTranslationCreate(EntityTypeTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لنوع كيان للمراجعة أو الصورة."""
    pass

class EntityTypeTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة نوع كيان للمراجعة أو الصورة موجودة."""
    translated_entity_type_name: Optional[str] = Field(None, max_length=100)
    translated_entity_description: Optional[str] = Field(None)

class EntityTypeTranslationRead(EntityTypeTranslationBase):
    """نموذج لقراءة وعرض ترجمة نوع الكيان للمراجعة أو الصورة."""
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات الشحن (Shipment Statuses) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class ShipmentStatusBase(BaseModel):
    """النموذج الأساسي لحالة الشحن: يحدد الخصائص المشتركة بين الإنشاء والتحديث."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة للترجمة (مثلاً: 'PREPARING', 'IN_TRANSIT').")
    status_description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف الحالة للترجمة.")

class ShipmentStatusCreate(ShipmentStatusBase):
    """نموذج لإنشاء حالة شحن جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List["ShipmentStatusTranslationCreate"]] = []

class ShipmentStatusUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث حالة شحن موجودة."""
    status_name_key: Optional[str] = Field(None, max_length=50)
    status_description_key: Optional[str] = Field(None, max_length=255)

class ShipmentStatusRead(ShipmentStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة الشحن، يتضمن ترجماتها ومعرفها."""
    shipment_status_id: int
    translations: List["ShipmentStatusTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لترجمات حالات الشحن (Shipment Status Translations) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class ShipmentStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة الشحن."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)
    translated_description: Optional[str] = Field(None)

class ShipmentStatusTranslationCreate(ShipmentStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة الشحن."""
    pass

class ShipmentStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة شحن موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class ShipmentStatusTranslationRead(ShipmentStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة الشحن."""
    shipment_status_id: int
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لحالات طلبات عروض الأسعار (Rfq Statuses) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class RfqStatusBase(BaseModel):
    """النموذج الأساسي لحالة طلب عرض السعر: يحدد الخصائص المشتركة بين الإنشاء والتحديث."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة للترجمة (مثلاً: 'OPEN', 'CLOSED').")

class RfqStatusCreate(RfqStatusBase):
    """نموذج لإنشاء حالة طلب عرض سعر جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List["RfqStatusTranslationCreate"]] = []

class RfqStatusUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث حالة طلب عرض سعر موجودة."""
    status_name_key: Optional[str] = Field(None, max_length=50)

class RfqStatusRead(RfqStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة طلب عرض السعر، يتضمن ترجماتها ومعرفها."""
    rfq_status_id: int
    translations: List["RfqStatusTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لترجمات حالات طلبات عروض الأسعار (Rfq Status Translations) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class RfqStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة طلب عرض السعر."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)

class RfqStatusTranslationCreate(RfqStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة طلب عرض السعر."""
    pass

class RfqStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة طلب عرض سعر موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)

class RfqStatusTranslationRead(RfqStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة طلب عرض السعر."""
    rfq_status_id: int
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لحالات عرض السعر (Quote Statuses) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class QuoteStatusBase(BaseModel):
    """النموذج الأساسي لحالة عرض السعر: يحدد الخصائص المشتركة بين الإنشاء والتحديث."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة للترجمة (مثلاً: 'SUBMITTED', 'ACCEPTED').")
    status_description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف الحالة للترجمة.") # هذا الحقل موجود في جداول الحالات العامة

class QuoteStatusCreate(QuoteStatusBase):
    """نموذج لإنشاء حالة عرض سعر جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List["QuoteStatusTranslationCreate"]] = []

class QuoteStatusUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث حالة عرض سعر موجودة."""
    status_name_key: Optional[str] = Field(None, max_length=50)
    status_description_key: Optional[str] = Field(None, max_length=255)

class QuoteStatusRead(QuoteStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة عرض السعر، يتضمن ترجماتها ومعرفها."""
    quote_status_id: int
    translations: List["QuoteStatusTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لترجمات حالات عرض السعر (Quote Status Translations) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class QuoteStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة عرض السعر."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)
    translated_description: Optional[str] = Field(None) # هذا الحقل موجود في جداول الترجمة العامة

class QuoteStatusTranslationCreate(QuoteStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة عرض السعر."""
    pass

class QuoteStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة عرض سعر موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class QuoteStatusTranslationRead(QuoteStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة عرض السعر."""
    quote_status_id: int
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لحالات الطلب (Order Statuses) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class OrderStatusBase(BaseModel):
    """النموذج الأساسي لحالة الطلب: يحدد الخصائص المشتركة بين الإنشاء والتحديث."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة للترجمة (مثلاً: 'NEW', 'SHIPPED').")
    status_description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف الحالة للترجمة.")
    is_active: Optional[bool] = Field(True, description="هل هذه الحالة نشطة للاستخدام؟")

class OrderStatusCreate(OrderStatusBase):
    """نموذج لإنشاء حالة طلب جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List["OrderStatusTranslationCreate"]] = Field([], description="الترجمات الأولية لاسم الحالة ووصفها.")

class OrderStatusUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث حالة طلب موجودة."""
    status_name_key: Optional[str] = Field(None, max_length=50)
    status_description_key: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class OrderStatusRead(OrderStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة الطلب، يتضمن ترجماتها ومعرفها."""
    order_status_id: int
    translations: List["OrderStatusTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لترجمات حالات الطلب (Order Status Translations) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class OrderStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة الطلب."""
    language_code: str = Field(..., max_length=10, description="رمز اللغة للترجمة (مثلاً: 'ar', 'en').")
    translated_status_name: str = Field(..., max_length=100, description="الاسم المترجم للحالة.")
    translated_status_description: Optional[str] = Field(None, description="الوصف المترجم للحالة.")

class OrderStatusTranslationCreate(OrderStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة الطلب."""
    pass

class OrderStatusTranslationUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث ترجمة حالة طلب موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_status_description: Optional[str] = Field(None)

class OrderStatusTranslationRead(OrderStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة الطلب."""
    order_status_id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات الدفع (Payment Statuses) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class PaymentStatusBase(BaseModel):
    """النموذج الأساسي لحالة الدفع: يحدد الخصائص المشتركة بين الإنشاء والتحديث."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم حالة الدفع للترجمة.")

class PaymentStatusCreate(PaymentStatusBase):
    """نموذج لإنشاء حالة دفع جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List["PaymentStatusTranslationCreate"]] = []

class PaymentStatusUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث حالة دفع موجودة."""
    status_name_key: Optional[str] = Field(None, max_length=50)

class PaymentStatusRead(PaymentStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة الدفع، يتضمن ترجماتها ومعرفها."""
    payment_status_id: int
    translations: List["PaymentStatusTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لترجمات حالات الدفع (Payment Status Translations) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class PaymentStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة الدفع."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)

class PaymentStatusTranslationCreate(PaymentStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة الدفع."""
    pass

class PaymentStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة دفع موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)

class PaymentStatusTranslationRead(PaymentStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة الدفع."""
    payment_status_id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات بنود الطلب (Order Item Statuses) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class OrderItemStatusBase(BaseModel):
    """النموذج الأساسي لحالة بند الطلب."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة للترجمة.")

class OrderItemStatusCreate(OrderItemStatusBase):
    """نموذج لإنشاء حالة بند طلب جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List["OrderItemStatusTranslationCreate"]] = []

class OrderItemStatusUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث حالة بند طلب موجودة."""
    status_name_key: Optional[str] = Field(None, max_length=50)

class OrderItemStatusRead(OrderItemStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة بند الطلب."""
    item_status_id: int
    translations: List["OrderItemStatusTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لترجمات حالات بنود الطلب (Order Item Status Translations) ---
#    (المودلات من src.lookups.models.py)
# ==========================================================
class OrderItemStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة بند الطلب."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)

class OrderItemStatusTranslationCreate(OrderItemStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة بند الطلب."""
    pass

class OrderItemStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة بند طلب موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)

class OrderItemStatusTranslationRead(OrderItemStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة بند الطلب."""
    item_status_id: int
    model_config = ConfigDict(from_attributes=True)





## المجموعة 5 المزادات


# ==========================================================
# --- Schemas لحالات المزاد (Auction Statuses) ---
#    (المودلات من backend\src\auctions\models\auction_statuses_types_models.py)
# ==========================================================
class AuctionStatusBase(BaseModel):
    """النموذج الأساسي لحالة المزاد."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة للترجمة (مثلاً: 'SCHEDULED', 'ACTIVE', 'CLOSED').")
    status_description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف الحالة للترجمة.")

class AuctionStatusCreate(AuctionStatusBase):
    """نموذج لإنشاء حالة مزاد جديدة."""
    translations: Optional[List["AuctionStatusTranslationCreate"]] = Field([], description="الترجمات الأولية لاسم الحالة ووصفها.")

class AuctionStatusUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث حالة مزاد موجودة."""
    status_name_key: Optional[str] = Field(None, max_length=50)
    status_description_key: Optional[str] = Field(None, max_length=255)

class AuctionStatusRead(AuctionStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة المزاد."""
    auction_status_id: int
    translations: List["AuctionStatusTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لترجمات حالات المزاد (Auction Status Translations) ---
# ==========================================================
class AuctionStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة المزاد."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)
    translated_description: Optional[str] = Field(None)

class AuctionStatusTranslationCreate(AuctionStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة المزاد."""
    pass

class AuctionStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة مزاد موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class AuctionStatusTranslationRead(AuctionStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة المزاد."""
    auction_status_id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأنواع المزادات (Auction Types) ---
#    (المودلات من backend\src\auctions\models\auction_statuses_types_models.py)
# ==========================================================
class AuctionTypeBase(BaseModel):
    """النموذج الأساسي لنوع المزاد."""
    type_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم النوع للترجمة (مثلاً: 'ENGLISH', 'DUTCH').")
    description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف النوع للترجمة.")

class AuctionTypeCreate(AuctionTypeBase):
    """نموذج لإنشاء نوع مزاد جديد."""
    translations: Optional[List["AuctionTypeTranslationCreate"]] = []

class AuctionTypeUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث نوع مزاد موجود."""
    type_name_key: Optional[str] = Field(None, max_length=50)
    description_key: Optional[str] = Field(None, max_length=255)

class AuctionTypeRead(AuctionTypeBase):
    """نموذج لقراءة وعرض تفاصيل نوع المزاد."""
    auction_type_id: int
    translations: List["AuctionTypeTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لترجمات أنواع المزادات (Auction Type Translations) ---
# ==========================================================
class AuctionTypeTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة نوع المزاد."""
    language_code: str = Field(..., max_length=10)
    translated_type_name: str = Field(..., max_length=100)
    translated_type_description: Optional[str] = Field(None)

class AuctionTypeTranslationCreate(AuctionTypeTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لنوع مزاد."""
    pass

class AuctionTypeTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة نوع مزاد موجودة."""
    translated_type_name: Optional[str] = Field(None, max_length=100)
    translated_type_description: Optional[str] = Field(None)

class AuctionTypeTranslationRead(AuctionTypeTranslationBase):
    """نموذج لقراءة وعرض ترجمة نوع المزاد."""
    auction_type_id: int
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لحالات تسوية المزاد (Auction Settlement Statuses) ---
#    (المودلات من backend\src\auctions\models\settlements_models.py)
# ==========================================================
class AuctionSettlementStatusBase(BaseModel):
    """النموذج الأساسي لحالة تسوية المزاد."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة للترجمة (مثلاً: 'PENDING_PAYMENT', 'PAID', 'SETTLED_TO_SELLER').")
    status_description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف الحالة للترجمة.") # افتراض وجوده في المودل

class AuctionSettlementStatusCreate(AuctionSettlementStatusBase):
    """نموذج لإنشاء حالة تسوية مزاد جديدة."""
    translations: Optional[List["AuctionSettlementStatusTranslationCreate"]] = Field([], description="الترجمات الأولية لاسم الحالة ووصفها.")

class AuctionSettlementStatusUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث حالة تسوية مزاد موجودة."""
    status_name_key: Optional[str] = Field(None, max_length=50)
    status_description_key: Optional[str] = Field(None, max_length=255)

class AuctionSettlementStatusRead(AuctionSettlementStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة تسوية المزاد."""
    settlement_status_id: int
    translations: List["AuctionSettlementStatusTranslationRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لترجمات حالات تسوية المزاد (Auction Settlement Status Translations) ---
# ==========================================================
class AuctionSettlementStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة تسوية المزاد."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)
    translated_description: Optional[str] = Field(None)

class AuctionSettlementStatusTranslationCreate(AuctionSettlementStatusBase): # يمكن أن ترث من AuctionSettlementStatusTranslationBase
    """نموذج لإنشاء ترجمة جديدة لحالة تسوية مزاد."""
    pass

class AuctionSettlementStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة تسوية مزاد موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class AuctionSettlementStatusTranslationRead(AuctionSettlementStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة تسوية المزاد."""
    settlement_status_id: int
    model_config = ConfigDict(from_attributes=True)






# ==========================================================
# --- Schemas لحالات المنتج (Product Statuses) ---
# ==========================================================
class ProductStatusTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة حالة المنتج."""
    product_status_id: int
    language_code: str
    translated_status_name: str
    translated_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProductStatusRead(BaseModel):
    """نموذج لقراءة وعرض حالة المنتج."""
    product_status_id: int
    status_name_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[ProductStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات عنصر المخزون (Inventory Item Statuses) ---
# ==========================================================
class InventoryItemStatusTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة حالة عنصر المخزون."""
    inventory_item_status_id: int
    language_code: str
    translated_status_name: str
    translated_status_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InventoryItemStatusRead(BaseModel):
    """نموذج لقراءة وعرض حالة عنصر المخزون."""
    inventory_item_status_id: int
    status_name_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[InventoryItemStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأنواع حركات المخزون (Inventory Transaction Types) ---
# ==========================================================
class InventoryTransactionTypeTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة نوع حركة المخزون."""
    transaction_type_id: int
    language_code: str
    translated_transaction_type_name: str
    translated_transaction_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InventoryTransactionTypeRead(BaseModel):
    """نموذج لقراءة وعرض نوع حركة المخزون."""
    transaction_type_id: int
    transaction_type_name_key: str
    description_key: Optional[str] = None
    is_credit: bool
    created_at: datetime
    translations: List[InventoryTransactionTypeTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات المحاصيل المتوقعة (Expected Crop Statuses) ---
# ==========================================================
class ExpectedCropStatusTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة حالة المحصول المتوقع."""
    status_id: int
    language_code: str
    translated_status_name: str
    translated_description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ExpectedCropStatusRead(BaseModel):
    """نموذج لقراءة وعرض حالة المحصول المتوقع."""
    status_id: int
    status_name_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[ExpectedCropStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات المراجعة (Review Statuses) ---
# ==========================================================
class ReviewStatusTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة حالة المراجعة."""
    status_id: int
    language_code: str
    translated_status_name: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReviewStatusRead(BaseModel):
    """نموذج لقراءة وعرض حالة المراجعة."""
    status_id: int
    status_name_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[ReviewStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأسباب الإبلاغ عن المراجعات (Review Report Reasons) ---
# ==========================================================
class ReviewReportReasonTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة سبب الإبلاغ."""
    reason_id: int
    language_code: str
    translated_reason_text: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReviewReportReasonRead(BaseModel):
    """نموذج لقراءة وعرض سبب الإبلاغ عن مراجعة."""
    reason_id: int
    reason_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[ReviewReportReasonTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لمعايير التقييم (Review Criteria) ---
# ==========================================================
class ReviewCriterionTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة معيار التقييم."""
    criteria_id: int
    language_code: str
    translated_criteria_name: str
    translated_criteria_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReviewCriterionRead(BaseModel):
    """نموذج لقراءة وعرض معيار التقييم."""
    criteria_id: int
    criteria_name_key: str
    applicable_entity_type: Optional[str] = None # TODO: يمكن ربطها بـ EntityTypeForReviewOrImageRead
    is_active: bool
    created_at: datetime
    updated_at: datetime
    translations: List[ReviewCriterionTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات المحفظة (Wallet Statuses) ---
# ==========================================================
class WalletStatusTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة حالة المحفظة."""
    wallet_status_id: int
    language_code: str
    translated_wallet_status_name: str
    translated_wallet_status_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WalletStatusRead(BaseModel):
    """نموذج لقراءة وعرض حالة المحفظة."""
    wallet_status_id: int
    status_name_key: str
    description_key: Optional[str] = None
    created_at: datetime
    translations: List[WalletStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأنواع معاملات المحفظة (Transaction Types) ---
# ==========================================================
class TransactionTypeTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة نوع معاملة المحفظة."""
    transaction_type_id: int
    language_code: str
    translated_transaction_type_name: str
    translated_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TransactionTypeRead(BaseModel):
    """نموذج لقراءة وعرض نوع معاملة المحفظة."""
    transaction_type_id: int
    transaction_type_name_key: str
    description_key: Optional[str] = None
    is_credit: bool
    created_at: datetime
    translations: List[TransactionTypeTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لبوابات الدفع (Payment Gateways) ---
# ==========================================================
class PaymentGatewayRead(BaseModel):
    """نموذج لقراءة وعرض بوابة الدفع."""
    gateway_id: int
    gateway_name_key: str
    gateway_display_name_key: Optional[str] = None
    is_active: bool
    configuration_details: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين ترجمات (PaymentGatewayTranslationRead) إذا وجدت.


# ==========================================================
# --- Schemas لحالات طلبات سحب الرصيد (Withdrawal Request Statuses) ---
# ==========================================================
class WithdrawalRequestStatusTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة حالة طلب سحب الرصيد."""
    withdrawal_request_status_id: int
    language_code: str
    translated_status_name: str
    translated_status_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WithdrawalRequestStatusRead(BaseModel):
    """نموذج لقراءة وعرض حالة طلب سحب الرصيد."""
    withdrawal_request_status_id: int
    status_name_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[WithdrawalRequestStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات اتفاقيات الدفع الآجل (Deferred Payment Agreement Statuses) ---
# ==========================================================
class DeferredPaymentAgreementStatusTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة حالة اتفاقية الدفع الآجل."""
    deferred_payment_agreement_status_id: int
    language_code: str
    translated_status_name: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DeferredPaymentAgreementStatusRead(BaseModel):
    """نموذج لقراءة وعرض حالة اتفاقية الدفع الآجل."""
    deferred_payment_agreement_status_id: int
    status_name_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[DeferredPaymentAgreementStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات الأقساط (Installment Statuses) ---
# ==========================================================
class InstallmentStatusTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة حالة القسط."""
    installment_status_id: int
    language_code: str
    translated_status_name: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InstallmentStatusRead(BaseModel):
    """نموذج لقراءة وعرض حالة القسط."""
    installment_status_id: int
    status_name_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[InstallmentStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات مطالبات الضمان الذهبي (GG Claim Statuses) ---
# ==========================================================
class GGClaimStatusTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة حالة مطالبة الضمان الذهبي."""
    gg_claim_status_id: int
    language_code: str
    translated_status_name: str
    translated_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class GGClaimStatusRead(BaseModel):
    """نموذج لقراءة وعرض حالة مطالبة الضمان الذهبي."""
    gg_claim_status_id: int
    status_name_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[GGClaimStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأنواع حلول مطالبات الضمان الذهبي (GG Resolution Types) ---
# ==========================================================
class GGResolutionTypeTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة نوع حل مطالبة الضمان الذهبي."""
    gg_resolution_type_id: int
    language_code: str
    translated_resolution_type_name: str
    translated_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class GGResolutionTypeRead(BaseModel):
    """نموذج لقراءة وعرض نوع حل مطالبة الضمان الذهبي."""
    gg_resolution_type_id: int
    resolution_type_name_key: str
    created_at: datetime
    updated_at: datetime
    translations: List[GGResolutionTypeTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأنواع أحداث النظام العامة (System Event Types) ---
# ==========================================================
class SystemEventTypeTranslationRead(BaseModel):
    """نموذج لقراءة وعرض ترجمة نوع حدث النظام العام."""
    event_type_id: int
    language_code: str
    translated_event_type_name: str
    translated_description: Optional[str] = None # Assuming it exists in model
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SystemEventTypeRead(BaseModel):
    """نموذج لقراءة وعرض نوع حدث النظام العام."""
    event_type_id: int
    event_type_name_key: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    translations: List[SystemEventTypeTranslationRead] = []










class ProductStatusBase(BaseModel):
    status_name_key: str

class ProductStatusRead(ProductStatusBase):
    product_status_id: int
    model_config = ConfigDict(from_attributes=True)

class ProductStatusUpdate(ProductStatusBase):
    product_status_id: int = Field(..., description="The ID of the new product status to assign.")
        
# (في المستقبل، يمكن إضافة schemas أخرى مثل InventoryItemStatus هنا)




