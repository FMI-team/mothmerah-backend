# backend\src\users\schemas\verification_lookups_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime # لـ created_at و updated_at
from uuid import UUID # لـ user_id, changed_by_user_id, reviewer_user_id (إذا تم استخدامه)

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas أخرى
# CountryRead تستورد من address_lookups_schemas.py
from src.users.schemas.address_lookups_schemas import CountryRead

# LanguageRead تستورد من src.lookups.schemas
from src.lookups.schemas import LanguageRead

# TODO: إذا كنت تستخدم UserRead أو AccountStatusRead في UserVerificationHistoryRead أو ManualVerificationLogRead،
#       يجب استيرادها من core_schemas.py هنا.
# from src.users.schemas.core_schemas import UserRead, AccountStatusRead


# ==========================================================
# --- Schemas لأنواع التراخيص (License Types) ---
#    (المودلات من backend\src\users\models\verification_models.py)
# ==========================================================
class LicenseTypeTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة نوع الترخيص."""
    language_code: str = Field(..., max_length=10)
    translated_license_type_name: str = Field(..., max_length=100)
    translated_description: Optional[str] = Field(None)

class LicenseTypeTranslationCreate(LicenseTypeTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لنوع ترخيص."""
    pass

class LicenseTypeTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة نوع ترخيص موجودة."""
    translated_license_type_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class LicenseTypeTranslationRead(LicenseTypeTranslationBase):
    """نموذج لقراءة وعرض ترجمة نوع ترخيص."""
    license_type_id: int # معرف النوع الأم
    model_config = ConfigDict(from_attributes=True)

class LicenseTypeBase(BaseModel):
    """النموذج الأساسي لنوع الترخيص."""
    license_type_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم نوع الترخيص.")
    is_mandatory_for_role: Optional[bool] = Field(False, description="هل هذا النوع إلزامي لدور معين؟")

class LicenseTypeCreate(LicenseTypeBase):
    """نموذج لإنشاء نوع ترخيص جديد، يتضمن ترجماته الأولية."""
    translations: Optional[List[LicenseTypeTranslationCreate]] = Field([], description="الترجمات الأولية لنوع الترخيص.")

class LicenseTypeUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث بيانات نوع ترخيص أساسية."""
    license_type_name_key: Optional[str] = Field(None, max_length=50)
    is_mandatory_for_role: Optional[bool] = None

class LicenseTypeRead(LicenseTypeBase):
    """نموذج لقراءة وعرض تفاصيل نوع الترخيص، يتضمن ترجماته ومعرفه."""
    license_type_id: int
    created_at: datetime
    updated_at: datetime
    translations: List[LicenseTypeTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas للجهات المصدرة للتراخيص (Issuing Authorities) ---
#    (المودلات من backend\src\users\models\verification_models.py)
# ==========================================================
class IssuingAuthorityTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة الجهة المصدرة."""
    language_code: str = Field(..., max_length=10)
    translated_authority_name: str = Field(..., max_length=150)
    translated_description: Optional[str] = Field(None)

class IssuingAuthorityTranslationCreate(IssuingAuthorityTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لجهة مصدرة."""
    pass

class IssuingAuthorityTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة جهة إصدار موجودة."""
    translated_authority_name: Optional[str] = Field(None, max_length=150)
    translated_description: Optional[str] = Field(None)

class IssuingAuthorityTranslationRead(IssuingAuthorityTranslationBase):
    """نموذج لقراءة وعرض ترجمة جهة إصدار."""
    authority_id: int # معرف الجهة الأم
    model_config = ConfigDict(from_attributes=True)

class IssuingAuthorityBase(BaseModel):
    """النموذج الأساسي للجهة المصدرة للتراخيص."""
    authority_name_key: str = Field(..., max_length=100, description="مفتاح فريد لاسم الجهة المصدرة.")
    country_code: str = Field(..., max_length=2, description="رمز الدولة التي تعمل فيها هذه الجهة.")

class IssuingAuthorityCreate(IssuingAuthorityBase):
    """نموذج لإنشاء جهة مصدرة جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List[IssuingAuthorityTranslationCreate]] = Field([], description="الترجمات الأولية لجهة الإصدار.")

class IssuingAuthorityUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث بيانات جهة إصدار موجودة."""
    authority_name_key: Optional[str] = Field(None, max_length=100)
    country_code: Optional[str] = Field(None, max_length=2)

class IssuingAuthorityRead(IssuingAuthorityBase):
    """نموذج لقراءة وعرض تفاصيل الجهة المصدرة، يتضمن ترجماتها ومعرفها."""
    authority_id: int
    created_at: datetime
    updated_at: datetime
    translations: List[IssuingAuthorityTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)
    country: Optional[CountryRead] = None # معلومات الدولة (تتطلب استيراد CountryRead)


# ==========================================================
# --- Schemas لحالات التحقق من المستخدم (User Verification Statuses) ---
#    (المودلات من backend\src\users\models\verification_models.py)
# ==========================================================
class UserVerificationStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة التحقق من المستخدم."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)
    translated_description: Optional[str] = Field(None)

class UserVerificationStatusTranslationCreate(UserVerificationStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة تحقق مستخدم."""
    pass

class UserVerificationStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة تحقق مستخدم موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class UserVerificationStatusTranslationRead(UserVerificationStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة تحقق مستخدم."""
    user_verification_status_id: int # معرف الحالة الأم
    model_config = ConfigDict(from_attributes=True)

class UserVerificationStatusBase(BaseModel):
    """النموذج الأساسي لحالة التحقق من المستخدم."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة (مثلاً: 'NOT_VERIFIED', 'PENDING_REVIEW', 'VERIFIED').")
    description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف الحالة للترجمة.")

class UserVerificationStatusCreate(UserVerificationStatusBase):
    """نموذج لإنشاء حالة تحقق مستخدم جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List[UserVerificationStatusTranslationCreate]] = Field([], description="الترجمات الأولية لحالة التحقق من المستخدم.")

class UserVerificationStatusUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث بيانات حالة تحقق مستخدم أساسية."""
    status_name_key: Optional[str] = Field(None, max_length=50)
    description_key: Optional[str] = Field(None, max_length=255)

class UserVerificationStatusRead(UserVerificationStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة التحقق من المستخدم، يتضمن ترجماتها ومعرفها."""
    user_verification_status_id: int
    created_at: datetime
    updated_at: datetime
    translations: List[UserVerificationStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات التحقق من التراخيص (License Verification Statuses) ---
#    (المودلات من backend\src\users\models\verification_models.py)
# ==========================================================
class LicenseVerificationStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة التحقق من الترخيص."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)
    translated_description: Optional[str] = Field(None)

class LicenseVerificationStatusTranslationCreate(LicenseVerificationStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة تحقق ترخيص."""
    pass

class LicenseVerificationStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة تحقق ترخيص موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class LicenseVerificationStatusTranslationRead(LicenseVerificationStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة تحقق ترخيص."""
    license_verification_status_id: int # معرف الحالة الأم
    model_config = ConfigDict(from_attributes=True)

class LicenseVerificationStatusBase(BaseModel):
    """النموذج الأساسي لحالة التحقق من الترخيص."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة (مثلاً: 'PENDING', 'APPROVED', 'REJECTED').")
    description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف الحالة للترجمة.")

class LicenseVerificationStatusCreate(LicenseVerificationStatusBase):
    """نموذج لإنشاء حالة تحقق ترخيص جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List[LicenseVerificationStatusTranslationCreate]] = Field([], description="الترجمات الأولية لحالة التحقق من الترخيص.")

class LicenseVerificationStatusUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث بيانات حالة تحقق ترخيص أساسية."""
    status_name_key: Optional[str] = Field(None, max_length=50)
    description_key: Optional[str] = Field(None, max_length=255)

class LicenseVerificationStatusRead(LicenseVerificationStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة التحقق من الترخيص، يتضمن ترجماتها ومعرفها."""
    license_verification_status_id: int
    created_at: datetime
    updated_at: datetime
    translations: List[LicenseVerificationStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لسجل تغييرات حالة التحقق للمستخدم (User Verification History) ---
#    (المودلات من backend\src\users\models\verification_models.py)
#    هذا الجدول يُنشأ تلقائياً ولا يُعدّل أو يُحذف مباشرةً عبر API.
# ==========================================================
class UserVerificationHistoryRead(BaseModel):
    """نموذج لقراءة وعرض تفاصيل سجل تغييرات حالة التحقق للمستخدم."""
    history_id: int
    user_id: UUID
    old_user_verification_status_id: Optional[int] = Field(None, description="معرف الحالة القديمة للتحقق للمستخدم.")
    new_user_verification_status_id: int = Field(..., description="معرف الحالة الجديدة للتحقق للمستخدم.")
    changed_by_user_id: Optional[UUID] = Field(None, description="معرف المستخدم الذي أجرى التغيير (إذا لم يكن النظام).")
    notes: Optional[str] = Field(None, description="ملاحظات حول سبب التغيير.")
    created_at: datetime
    # TODO: يمكن تضمين UserRead (لـ user و changed_by_user) و UserVerificationStatusRead (للحالتين).
    # user: "UserRead"
    # old_user_verification_status: UserVerificationStatusRead
    # new_user_verification_status: UserVerificationStatusRead
    # changed_by_user: "UserRead" (self-referencing)
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لسجل المراجعة اليدوية (Manual Verification Log) ---
#    (المودلات من backend\src\users\models\verification_models.py)
#    هذا الجدول يُنشأ تلقائياً ولا يُعدّل أو يُحذف مباشرةً عبر API.
# ==========================================================
class ManualVerificationLogRead(BaseModel):
    """نموذج لقراءة وعرض تفاصيل سجل المراجعة اليدوية."""
    log_id: int
    reviewer_user_id: Optional[UUID] = Field(None, description="معرف الموظف المسؤول الذي قام بالمراجعة.")
    entity_type: str = Field(..., max_length=50, description="نوع الكيان الذي تمت مراجعته (مثلاً: 'LICENSE', 'USER_PROFILE').")
    entity_id: int = Field(..., description="معرف الكيان الذي تمت مراجعته (مثلاً: license_id, user_id).")
    action_taken: str = Field(..., max_length=50, description="الإجراء المتخذ (مثلاً: 'APPROVED', 'REJECTED').")
    notes: Optional[str] = Field(None, description="ملاحظات تفصيلية من المراجع.")
    created_at: datetime
    # TODO: يمكن تضمين UserRead لـ reviewer_user.
    model_config = ConfigDict(from_attributes=True)