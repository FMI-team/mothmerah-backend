from sqlalchemy import JSON
# backend\src\system_settings\schemas\settings_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, date # لـ timestamps
from uuid import UUID # لـ user_ids

# استيراد Schemas المطلوبة للعلاقات المتداخلة
from src.users.schemas.core_schemas import UserRead # لـ UserRead
from src.lookups.schemas import LanguageRead # لـ LanguageRead


# ==========================================================
# --- Schemas لإعدادات التطبيق العامة (Application Settings) ---
#    (المودلات من backend\src\system_settings\models\settings_models.py)
# ==========================================================
class ApplicationSettingBase(BaseModel):
    """النموذج الأساسي لبيانات إعداد التطبيق."""
    setting_key: str = Field(..., max_length=255, description="مفتاح فريد للإعداد (مثلاً: 'platform_commission_rate').")
    setting_value: Optional[str] = Field(None, description="قيمة الإعداد (نصية، يتم تحويلها حسب setting_datatype).")
    setting_datatype: str = Field(..., max_length=50, description="نوع البيانات المتوقع للقيمة ('INTEGER', 'STRING', 'BOOLEAN', 'JSON', 'TEXT').")
    description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف الإعداد للترجمة.")
    module_scope: Optional[str] = Field(None, max_length=100, description="الوحدة التي ينتمي إليها الإعداد (مثلاً: 'AUCTIONS', 'PAYMENTS').")
    is_editable_by_admin: bool = Field(True, description="هل يمكن للمسؤول تعديل هذا الإعداد؟")

class ApplicationSettingCreate(ApplicationSettingBase):
    """نموذج لإنشاء إعداد تطبيق جديد."""
    translations: Optional[List["ApplicationSettingTranslationCreate"]] = Field([], description="الترجمات الأولية لوصف الإعداد وقيمته.")

class ApplicationSettingUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث إعداد تطبيق موجود."""
    setting_value: Optional[str] = Field(None)
    setting_datatype: Optional[str] = Field(None, max_length=50)
    description_key: Optional[str] = Field(None, max_length=255)
    module_scope: Optional[str] = Field(None, max_length=100)
    is_editable_by_admin: Optional[bool] = None

class ApplicationSettingRead(ApplicationSettingBase):
    """نموذج لقراءة وعرض تفاصيل إعداد التطبيق."""
    setting_id: int
    created_at: datetime
    updated_at: datetime
    updated_by_user_id: Optional[UUID] = None
    translations: List["ApplicationSettingTranslationRead"] = []
    last_updated_by_user: Optional[UserRead] = None # علاقة مع User
    model_config = ConfigDict(from_attributes=True)

# Schemas لترجمات إعدادات التطبيق (ApplicationSetting Translations)
class ApplicationSettingTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة إعداد التطبيق."""
    language_code: str = Field(..., max_length=10)
    translated_setting_value: Optional[str] = Field(None)
    translated_setting_description: str = Field(..., description="الوصف المترجم للإعداد.")

class ApplicationSettingTranslationCreate(ApplicationSettingTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لإعداد تطبيق."""
    pass

class ApplicationSettingTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة إعداد تطبيق موجودة."""
    translated_setting_value: Optional[str] = Field(None)
    translated_setting_description: Optional[str] = Field(None)

class ApplicationSettingTranslationRead(ApplicationSettingTranslationBase):
    """نموذج لقراءة وعرض ترجمة إعداد التطبيق."""
    setting_id: int # معرف الإعداد الأم
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لأعلام تفعيل الميزات (Feature Flags) ---
#    (المودلات من backend\src\system_settings\models\settings_models.py)
# ==========================================================
class FeatureFlagBase(BaseModel):
    """النموذج الأساسي لبيانات علم الميزة."""
    flag_name: str = Field(..., max_length=100, description="اسم علم الميزة الفريد (مثلاً: 'enable_new_auction_type').")
    description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف علم الميزة للترجمة.")
    is_enabled: bool = Field(False, description="حالة تفعيل الميزة (true: مفعلة، false: معطلة).")
    activation_rules: Optional[dict] = Field(None, description="قواعد تفعيل متقدمة (JSON).")

class FeatureFlagCreate(FeatureFlagBase):
    """نموذج لإنشاء علم ميزة جديد."""
    pass

class FeatureFlagUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث علم ميزة موجود."""
    description_key: Optional[str] = Field(None, max_length=255)
    is_enabled: Optional[bool] = None
    activation_rules: Optional[dict] = Field(None)

class FeatureFlagRead(FeatureFlagBase):
    """نموذج لقراءة وعرض تفاصيل علم الميزة."""
    flag_id: int
    created_at: datetime
    updated_at: datetime
    updated_by_user_id: Optional[UUID] = None
    last_updated_by_user: Optional[UserRead] = None # علاقة مع User
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لجدول صيانة النظام (SystemMaintenanceSchedule) ---
#    (المودلات من backend\src\system_settings\models\settings_models.py)
# ==========================================================
class SystemMaintenanceScheduleBase(BaseModel):
    """النموذج الأساسي لبيانات جدول صيانة النظام."""
    start_timestamp: datetime = Field(..., description="تاريخ ووقت بدء الصيانة.")
    end_timestamp: datetime = Field(..., description="تاريخ ووقت انتهاء الصيانة.")
    maintenance_message_key: str = Field(..., max_length=255, description="مفتاح لرسالة الصيانة (لترجمتها لاحقاً).")
    is_active: bool = Field(False, description="هل فترة الصيانة هذه نشطة حالياً؟")

class SystemMaintenanceScheduleCreate(SystemMaintenanceScheduleBase):
    """نموذج لإنشاء جدول صيانة جديد."""
    pass

class SystemMaintenanceScheduleUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث جدول صيانة موجود."""
    start_timestamp: Optional[datetime] = Field(None)
    end_timestamp: Optional[datetime] = Field(None)
    maintenance_message_key: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class SystemMaintenanceScheduleRead(SystemMaintenanceScheduleBase):
    """نموذج لقراءة وعرض تفاصيل جدول صيانة النظام."""
    maintenance_id: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[UUID] = None
    created_by_user: Optional[UserRead] = None # علاقة مع User
    model_config = ConfigDict(from_attributes=True)
