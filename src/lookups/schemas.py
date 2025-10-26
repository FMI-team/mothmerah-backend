# # backend\src\lookups\schemas.py

# from pydantic import BaseModel, Field, ConfigDict
# from typing import List, Optional
# from datetime import datetime, date # لـ created_at, updated_at, date_id


# # ==========================================================
# # --- Schemas للعملات (Currencies) ---
# #    (المودلات من src.lookups.models.py)
# # ==========================================================
# class CurrencyTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة العملة."""
#     currency_code: str
#     language_code: str
#     translated_currency_name: str
#     created_at: datetime
#     updated_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class CurrencyRead(BaseModel):
#     """نموذج لقراءة وعرض تفاصيل العملة."""
#     currency_code: str = Field(..., max_length=3)
#     currency_name_key: str = Field(..., max_length=50)
#     symbol: str = Field(..., max_length=5)
#     decimal_places: int
#     is_active: bool
#     created_at: datetime
#     updated_at: datetime
#     translations: List[CurrencyTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas للغات (Languages) ---
# #    (المودلات من src.lookups.models.py)
# # ==========================================================
# class LanguageRead(BaseModel):
#     """نموذج لقراءة وعرض تفاصيل اللغة."""
#     language_code: str = Field(..., max_length=10)
#     language_name_native: str = Field(..., max_length=50, description="اسم اللغة بلغتها الأصلية.")
#     language_name_en: str = Field(..., max_length=50, description="اسم اللغة بالإنجليزية كمرجع.")
#     text_direction: str = Field(..., max_length=3, description="اتجاه النص ('LTR' أو 'RTL').")
#     is_active_for_interface: bool
#     sort_order: Optional[int] = Field(None, description="لترتيب عرض اللغات في القوائم.")
#     created_at: datetime
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas للأبعاد الزمنية (DimDate) ---
# #    (المودلات من src.lookups.models.py)
# # ==========================================================
# class DimDateRead(BaseModel):
#     """نموذج لقراءة وعرض تفاصيل البعد الزمني (اليوم)."""
#     date_id: date
#     day_number_in_week: int
#     day_name_key: str
#     day_number_in_month: int
#     month_number_in_year: int
#     month_name_key: str
#     calendar_quarter: int
#     calendar_year: int
#     is_weekend_ksa: bool
#     is_official_holiday_ksa: bool
#     hijri_date: Optional[str] = None
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas لترجمات أيام الأسبوع والشهور (DayOfWeekTranslation, MonthTranslation) ---
# # ==========================================================
# class DayOfWeekTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة أيام الأسبوع."""
#     day_name_key: str
#     language_code: str
#     translated_day_name: str
#     created_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class MonthTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة الشهور."""
#     month_name_key: str
#     language_code: str
#     translated_month_name: str
#     created_at: datetime
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas لأنواع الأنشطة (ActivityType) ---
# # ==========================================================
# class ActivityTypeTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة نوع النشاط."""
#     activity_type_id: int
#     language_code: str
#     translated_activity_name: str
#     translated_activity_description: Optional[str] = None # Assuming it exists in model
#     created_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class ActivityTypeRead(BaseModel):
#     """نموذج لقراءة وعرض نوع النشاط."""
#     activity_type_id: int
#     activity_name_key: str
#     description_key: Optional[str] = None
#     created_at: datetime
#     translations: List[ActivityTypeTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas لأنواع أحداث الأمان (SecurityEventType) ---
# # ==========================================================
# class SecurityEventTypeTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة نوع حدث الأمان."""
#     security_event_type_id: int
#     language_code: str
#     translated_event_name: str
#     translated_event_description: Optional[str] = None # Assuming it exists in model
#     created_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class SecurityEventTypeRead(BaseModel):
#     """نموذج لقراءة وعرض نوع حدث الأمان."""
#     security_event_type_id: int
#     event_name_key: str
#     description_key: Optional[str] = None
#     severity_level: Optional[int] = None
#     created_at: datetime
#     translations: List[SecurityEventTypeTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas لأنواع الكيانات للمراجعة أو الصورة (Entity Types for Review or Image) ---
# # ==========================================================
# class EntityTypeTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة نوع الكيان."""
#     entity_type_code: str
#     language_code: str
#     translated_entity_type_name: str
#     translated_entity_description: Optional[str] = None
#     created_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class EntityTypeForReviewOrImageRead(BaseModel):
#     """نموذج لقراءة وعرض نوع الكيان الذي يمكن أن يرتبط بمراجعة أو صورة."""
#     entity_type_code: str = Field(..., max_length=50)
#     entity_type_name_key: str = Field(..., max_length=100)
#     description_key: Optional[str] = Field(None, max_length=255)
#     created_at: datetime
#     translations: List[EntityTypeTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)





# ## المجموعة الثالثة ##






# # ==========================================================
# # --- Schemas لحالات الطلب (Order Statuses) ---
# # ==========================================================
# class OrderStatusTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة حالة الطلب."""
#     order_status_id: int
#     language_code: str
#     translated_status_name: str
#     translated_status_description: Optional[str] = None # Assuming it exists in model
#     created_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class OrderStatusRead(BaseModel):
#     """نموذج لقراءة وعرض حالة الطلب."""
#     order_status_id: int
#     status_name_key: str
#     status_description_key: Optional[str] = None
#     is_active: bool
#     created_at: datetime
#     updated_at: datetime
#     translations: List[OrderStatusTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas لحالات الدفع (Payment Statuses) ---
# # ==========================================================
# class PaymentStatusTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة حالة الدفع."""
#     payment_status_id: int
#     language_code: str
#     translated_status_name: str
#     created_at: datetime
#     updated_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class PaymentStatusRead(BaseModel):
#     """نموذج لقراءة وعرض حالة الدفع."""
#     payment_status_id: int
#     status_name_key: str
#     created_at: datetime
#     updated_at: datetime
#     translations: List[PaymentStatusTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas لحالات بنود الطلب (Order Item Statuses) ---
# # ==========================================================
# class OrderItemStatusTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة حالة بند الطلب."""
#     item_status_id: int
#     language_code: str
#     translated_status_name: str
#     created_at: datetime
#     updated_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class OrderItemStatusRead(BaseModel):
#     """نموذج لقراءة وعرض حالة بند الطلب."""
#     item_status_id: int
#     status_name_key: str
#     created_at: datetime
#     updated_at: datetime
#     translations: List[OrderItemStatusTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas لحالات طلبات عروض الأسعار (Rfq Statuses) ---
# # ==========================================================
# class RfqStatusTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة حالة طلب عرض السعر."""
#     rfq_status_id: int
#     language_code: str
#     translated_status_name: str
#     created_at: datetime
#     updated_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class RfqStatusRead(BaseModel):
#     """نموذج لقراءة وعرض حالة طلب عرض السعر."""
#     rfq_status_id: int
#     status_name_key: str
#     created_at: datetime
#     updated_at: datetime
#     translations: List[RfqStatusTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas لحالات عرض السعر (Quote Statuses) ---
# # ==========================================================
# class QuoteStatusTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة حالة عرض السعر."""
#     quote_status_id: int
#     language_code: str
#     translated_status_name: str
#     translated_description: Optional[str] = None # Assuming it exists in model
#     created_at: datetime
#     updated_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class QuoteStatusRead(BaseModel):
#     """نموذج لقراءة وعرض حالة عرض السعر."""
#     quote_status_id: int
#     status_name_key: str
#     created_at: datetime
#     updated_at: datetime
#     translations: List[QuoteStatusTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)


# # ==========================================================
# # --- Schemas لحالات الشحن (Shipment Statuses) ---
# # ==========================================================
# class ShipmentStatusTranslationRead(BaseModel):
#     """نموذج لقراءة وعرض ترجمة حالة الشحن."""
#     shipment_status_id: int
#     language_code: str
#     translated_status_name: str
#     translated_description: Optional[str] = None # Assuming it exists in model
#     created_at: datetime
#     updated_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# class ShipmentStatusRead(BaseModel):
#     """نموذج لقراءة وعرض حالة الشحن."""
#     shipment_status_id: int
#     status_name_key: str
#     created_at: datetime
#     updated_at: datetime
#     translations: List[ShipmentStatusTranslationRead] = []
#     model_config = ConfigDict(from_attributes=True)