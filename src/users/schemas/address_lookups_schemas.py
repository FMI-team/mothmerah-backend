# backend\src\users\schemas\address_lookups_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime # لـ created_at و updated_at في بعض الـ Read Schemas


# ==========================================================
# --- Schemas لأنواع العناوين (Address Types) ---
#    (المودلات من backend\src\users\models\addresses_models.py)
# ==========================================================
class AddressTypeTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة نوع العنوان."""
    language_code: str = Field(..., max_length=10, description="رمز اللغة للترجمة (مثلاً: 'ar', 'en').")
    translated_address_type_name: str = Field(..., max_length=100, description="الاسم المترجم لنوع العنوان.")

class AddressTypeTranslationCreate(AddressTypeTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لنوع عنوان."""
    pass

class AddressTypeTranslationUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث ترجمة نوع عنوان موجودة."""
    translated_address_type_name: Optional[str] = Field(None, max_length=100)

class AddressTypeTranslationRead(AddressTypeTranslationBase):
    """نموذج لقراءة وعرض ترجمة نوع العنوان."""
    address_type_id: int # معرف النوع الأم
    model_config = ConfigDict(from_attributes=True)

class AddressTypeBase(BaseModel):
    """النموذج الأساسي لنوع العنوان."""
    address_type_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم نوع العنوان (مثلاً: 'SHIPPING', 'BILLING').")

class AddressTypeCreate(AddressTypeBase):
    """نموذج لإنشاء نوع عنوان جديد، يتضمن ترجماته الأولية."""
    translations: Optional[List[AddressTypeTranslationCreate]] = Field([], description="الترجمات الأولية لنوع العنوان.")

class AddressTypeUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث بيانات نوع عنوان أساسية."""
    address_type_name_key: Optional[str] = Field(None, max_length=50)

class AddressTypeRead(AddressTypeBase):
    """نموذج لقراءة وعرض تفاصيل نوع العنوان، يتضمن ترجماته ومعرفه."""
    address_type_id: int
    translations: List[AddressTypeTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas للدول (Countries) ---
#    (المودلات من backend\src\users\models\addresses_models.py)
# ==========================================================
class CountryTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة الدولة."""
    language_code: str = Field(..., max_length=10)
    translated_country_name: str = Field(..., max_length=100)

class CountryTranslationCreate(CountryTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لدولة."""
    pass

class CountryTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة دولة موجودة."""
    translated_country_name: Optional[str] = Field(None, max_length=100)

class CountryTranslationRead(CountryTranslationBase):
    """نموذج لقراءة وعرض ترجمة الدولة."""
    country_code: str # رمز الدولة الأم
    model_config = ConfigDict(from_attributes=True)

class CountryBase(BaseModel):
    """النموذج الأساسي للدولة."""
    country_code: str = Field(..., max_length=2, description="رمز ISO 3166-1 alpha-2 للدولة (مثلاً: 'SA').")
    country_name_key: str = Field(..., max_length=100, description="مفتاح فريد لاسم الدولة للترجمة.")
    phone_country_code: Optional[str] = Field(None, max_length=5, description="رمز الاتصال الدولي للدولة (مثلاً: '+966').")
    is_active: Optional[bool] = Field(True, description="هل الدولة نشطة ومعتمدة في النظام؟")

class CountryCreate(CountryBase):
    """نموذج لإنشاء دولة جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List[CountryTranslationCreate]] = Field([], description="الترجمات الأولية لاسم الدولة.")

class CountryUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث بيانات دولة موجودة."""
    country_name_key: Optional[str] = Field(None, max_length=100)
    phone_country_code: Optional[str] = Field(None, max_length=5)
    is_active: Optional[bool] = None

class CountryRead(CountryBase):
    """نموذج لقراءة وعرض تفاصيل الدولة، يتضمن ترجماتها ورمزها."""
    created_at: datetime
    updated_at: datetime
    translations: List[CountryTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas للمحافظات (Governorates) ---
#    (المودلات من backend\src\users\models\addresses_models.py)
# ==========================================================
class GovernorateTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة المحافظة."""
    language_code: str = Field(..., max_length=10)
    translated_governorate_name: str = Field(..., max_length=100)

class GovernorateTranslationCreate(GovernorateTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لمحافظة."""
    pass

class GovernorateTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة محافظة موجودة."""
    translated_governorate_name: Optional[str] = Field(None, max_length=100)

class GovernorateTranslationRead(GovernorateTranslationBase):
    """نموذج لقراءة وعرض ترجمة المحافظة."""
    governorate_id: int # معرف المحافظة الأم
    model_config = ConfigDict(from_attributes=True)

class GovernorateBase(BaseModel):
    """النموذج الأساسي للمحافظة."""
    governorate_name_key: str = Field(..., max_length=100, description="مفتاح فريد لاسم المحافظة للترجمة.")
    country_code: str = Field(..., max_length=2, description="رمز الدولة التي تقع فيها المحافظة.")
    is_active: Optional[bool] = Field(True, description="هل المحافظة نشطة ومعتمدة؟")

class GovernorateCreate(GovernorateBase):
    """نموذج لإنشاء محافظة جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List[GovernorateTranslationCreate]] = Field([], description="الترجمات الأولية للمحافظة.")

class GovernorateUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث بيانات محافظة موجودة."""
    governorate_name_key: Optional[str] = Field(None, max_length=100)
    country_code: Optional[str] = Field(None, max_length=2)
    is_active: Optional[bool] = None

class GovernorateRead(GovernorateBase):
    """نموذج لقراءة وعرض تفاصيل المحافظة، يتضمن ترجماتها ومعرفها."""
    governorate_id: int
    created_at: datetime
    updated_at: datetime
    translations: List[GovernorateTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات الدولة (CountryRead) بشكل متداخل.
    # country: "CountryRead"


# ==========================================================
# --- Schemas للمدن (Cities) ---
#    (المودلات من backend\src\users\models\addresses_models.py)
# ==========================================================
class CityTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة المدينة."""
    language_code: str = Field(..., max_length=10)
    translated_city_name: str = Field(..., max_length=100)

class CityTranslationCreate(CityTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لمدينة."""
    pass

class CityTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة مدينة موجودة."""
    translated_city_name: Optional[str] = Field(None, max_length=100)

class CityTranslationRead(CityTranslationBase):
    """نموذج لقراءة وعرض ترجمة المدينة."""
    city_id: int # معرف المدينة الأم
    model_config = ConfigDict(from_attributes=True)

class CityBase(BaseModel):
    """النموذج الأساسي للمدينة."""
    city_name_key: str = Field(..., max_length=100, description="مفتاح فريد لاسم المدينة للترجمة.")
    governorate_id: int = Field(..., description="معرف المحافظة التي تقع فيها المدينة.")
    is_active: Optional[bool] = Field(True, description="هل المدينة نشطة ومعتمدة؟")

class CityCreate(CityBase):
    """نموذج لإنشاء مدينة جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List[CityTranslationCreate]] = Field([], description="الترجمات الأولية للمدينة.")

class CityUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث بيانات مدينة موجودة."""
    city_name_key: Optional[str] = Field(None, max_length=100)
    governorate_id: Optional[int] = Field(None)
    is_active: Optional[bool] = None

class CityRead(CityBase):
    """نموذج لقراءة وعرض تفاصيل المدينة، يتضمن ترجماتها ومعرفها."""
    city_id: int
    created_at: datetime
    updated_at: datetime
    translations: List[CityTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات المحافظة (GovernorateRead) بشكل متداخل.
    # governorate: "GovernorateRead"


# ==========================================================
# --- Schemas للأحياء (Districts) ---
#    (المودلات من backend\src\users\models\addresses_models.py)
# ==========================================================
class DistrictTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة الحي."""
    language_code: str = Field(..., max_length=10)
    translated_district_name: str = Field(..., max_length=100)

class DistrictTranslationCreate(DistrictTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحي."""
    pass

class DistrictTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حي موجودة."""
    translated_district_name: Optional[str] = Field(None, max_length=100)

class DistrictTranslationRead(DistrictTranslationBase):
    """نموذج لقراءة وعرض ترجمة الحي."""
    district_id: int # معرف الحي الأم
    model_config = ConfigDict(from_attributes=True)


class DistrictBase(BaseModel):
    """النموذج الأساسي للحي."""
    district_name_key: str = Field(..., max_length=100, description="مفتاح فريد لاسم الحي للترجمة.")
    city_id: int = Field(..., description="معرف المدينة التي يقع فيها الحي.")
    is_active: Optional[bool] = Field(True, description="هل الحي نشط ومعتمد؟")

class DistrictCreate(DistrictBase):
    """نموذج لإنشاء حي جديد، يتضمن ترجماته الأولية."""
    translations: Optional[List[DistrictTranslationCreate]] = Field([], description="الترجمات الأولية للحي.")

class DistrictUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث بيانات حي موجود."""
    district_name_key: Optional[str] = Field(None, max_length=100)
    city_id: Optional[int] = Field(None)
    is_active: Optional[bool] = None

class DistrictRead(DistrictBase):
    """نموذج لقراءة وعرض تفاصيل الحي، يتضمن ترجماته ومعرفه."""
    district_id: int
    created_at: datetime
    updated_at: datetime
    translations: List[DistrictTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات المدينة (CityRead) بشكل متداخل.
    # city: "CityRead"