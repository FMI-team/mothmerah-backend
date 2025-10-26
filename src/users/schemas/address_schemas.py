# backend\src\users\schemas\address_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas الأخرى
from src.users.schemas.core_schemas import UserRead # للمستخدم المالك للعنوان
from src.users.schemas.address_lookups_schemas import ( # لجداول الـ Lookups الجغرافية وأنواع العناوين
    AddressTypeRead,
    CountryRead,
    GovernorateRead,
    CityRead,
    DistrictRead
)


# ==========================================================
# --- Schemas للعناوين (Addresses) ---
#    (المودلات من backend\src\users\models\addresses_models.py)
# ==========================================================
class AddressBase(BaseModel):
    """النموذج الأساسي لعنوان المستخدم: يصف الخصائص التي يتم إدخالها بواسطة المستخدم."""
    address_type_id: int = Field(..., description="معرف نوع العنوان (شحن، فوترة، عمل).")
    country_code: str = Field(..., max_length=2, description="رمز الدولة (ISO 3166-1 alpha-2).")
    governorate_id: Optional[int] = Field(None, description="معرف المحافظة (اختياري).")
    city_id: int = Field(..., description="معرف المدينة.")
    district_id: Optional[int] = Field(None, description="معرف الحي (اختياري).")
    street_name: str = Field(..., max_length=255, description="اسم الشارع.")
    building_number: Optional[str] = Field(None, max_length=50, description="رقم المبنى/الفيلا/الشقة (اختياري).")
    postal_code: Optional[str] = Field(None, max_length=20, description="الرمز البريدي (اختياري).")
    additional_details: Optional[str] = Field(None, description="تفاصيل إضافية للعنوان (مثلاً: رقم الدور، معلم مميز).")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="خط العرض الجغرافي (اختياري).")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="خط الطول الجغرافي (اختياري).")
    is_primary: bool = Field(False, description="هل هذا العنوان هو العنوان الأساسي الافتراضي للمستخدم؟")

class AddressCreate(AddressBase):
    """نموذج لإنشاء عنوان جديد للمستخدم."""
    # user_id سيتم تعيينه في طبقة الخدمة.
    # TODO: منطق عمل: التحقق من أن العنوان الأساسي (is_primary=True) هو واحد فقط لكل مستخدم ولكل نوع عنوان (إذا تم فرضه).
    pass

class AddressUpdate(BaseModel):
    """نموذج لتحديث بيانات عنوان موجود. جميع الحقول اختيارية للسماح بالتحديث الجزئي."""
    address_type_id: Optional[int] = None
    country_code: Optional[str] = Field(None, max_length=2)
    governorate_id: Optional[int] = None
    city_id: Optional[int] = None
    district_id: Optional[int] = None
    street_name: Optional[str] = Field(None, max_length=255)
    building_number: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    additional_details: Optional[str] = Field(None)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_primary: Optional[bool] = None
    # TODO: منطق عمل: عند تحديث is_primary إلى True، يجب إلغاء تعيين أي عنوان أساسي آخر لنفس المستخدم ونوع العنوان.

class AddressRead(AddressBase):
    """نموذج لقراءة وعرض تفاصيل العنوان بشكل كامل، بما في ذلك معرفه والطوابع الزمنية،
    بالإضافة إلى الكائنات المرتبطة بشكل متداخل لتحسين العرض.
    """
    address_id: int
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    
    # الكائنات المرتبطة بشكل متداخل (Nested Relationships)
    # TODO: يجب التأكد أن UserRead/AddressTypeRead/CountryRead/GovernorateRead/CityRead/DistrictRead موجودة ومستوردة
    user: UserRead # المستخدم المالك للعنوان
    address_type: AddressTypeRead # نوع العنوان
    country: CountryRead # الدولة
    governorate: Optional[GovernorateRead] = None # المحافظة (قد تكون None)
    city: CityRead # المدينة
    district: Optional[DistrictRead] = None # الحي (قد يكون None)