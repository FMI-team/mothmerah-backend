# backend\src\users\schemas\security_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# هذا الملف يجب أن يحتوي على تعريفات Pydantic Schemas فقط.

# ==========================================================
# --- Schemas لرموز إعادة تعيين كلمة المرور (Password Reset Tokens) ---
# ==========================================================
class PasswordResetRequestSchema(BaseModel):
    """نموذج لطلب إعادة تعيين كلمة مرور: يتطلب رقم الجوال."""
    phone_number: str = Field(..., examples=["+966500000000"], description="رقم الجوال لتلقي رمز إعادة التعيين.")

class PasswordResetConfirmSchema(BaseModel):
    """نموذج لتأكيد إعادة تعيين كلمة مرور: يتطلب رقم الجوال، الرمز الجديد، وكلمة المرور الجديدة."""
    phone_number: str = Field(..., examples=["+966500000000"], description="رقم الجوال المرتبط بطلب إعادة التعيين.")
    token: str = Field(..., min_length=6, max_length=6, description="رمز التحقق (OTP) الذي تم إرساله إلى رقم الجوال.")
    new_password: str = Field(..., description="كلمة المرور الجديدة.")
    # TODO: يمكن إضافة تأكيد كلمة المرور هنا أيضاً (confirm_new_password) كـ model_validator.

class PasswordResetTokenRead(BaseModel):
    """نموذج لقراءة وعرض تفاصيل رمز إعادة تعيين كلمة المرور (للاستخدام الداخلي/التدقيق)."""
    token_id: int
    user_id: UUID
    expiry_timestamp: datetime
    is_used: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لطلبات تغيير رقم الجوال (Phone Change Requests) ---
# ==========================================================
class PhoneChangeRequestCreate(BaseModel):
    """نموذج لبدء طلب تغيير رقم الجوال: يتطلب رقم الجوال الجديد."""
    new_phone_number: str = Field(..., examples=["+9665XXXXXXXXX"], description="رقم الجوال الجديد الذي يرغب المستخدم في ربطه بحسابه.")

class PhoneChangeVerify(BaseModel):
    """نموذج للتحقق من رمز OTP لتغيير رقم الجوال: يتطلب معرف الطلب ورمز OTP."""
    request_id: int = Field(..., description="معرف طلب تغيير رقم الجوال الذي تم إنشاؤه مسبقًا.")
    otp_code: str = Field(..., min_length=6, max_length=6, description="رمز التحقق (OTP) المكون من 6 أرقام والذي تم إرساله.")

class PhoneChangeRequestRead(BaseModel):
    """نموذج لقراءة وعرض حالة طلب تغيير رقم الجوال للمستخدم."""
    request_id: int
    user_id: UUID # المستخدم الذي قدم الطلب
    old_phone_number: str
    new_phone_number: str
    request_status: str # حالة الطلب (مثلاً: 'PENDING_OLD_PHONE_VERIFICATION', 'COMPLETED')
    request_timestamp: datetime # وقت تقديم الطلب
    verification_attempts: int # عدد المحاولات الفاشلة
    last_attempt_timestamp: Optional[datetime] = None # وقت آخر محاولة
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين UserRead للمستخدم (user_id) بشكل متداخل.


# ==========================================================
# --- Schemas لجلسات المستخدمين (User Sessions) ---
# ==========================================================
class UserSessionRead(BaseModel):
    """نموذج لقراءة وعرض تفاصيل جلسة مستخدم نشطة."""
    session_id: UUID
    user_id: UUID # المستخدم صاحب الجلسة
    device_identifier: Optional[str] = Field(None, description="معرف فريد للجهاز أو المتصفح.")
    ip_address: Optional[str] = Field(None, description="عنوان IP الذي تم منه تسجيل الدخول.")
    user_agent: Optional[str] = Field(None, description="معلومات وكيل المستخدم (المتصفح/التطبيق).")
    login_timestamp: datetime
    last_activity_timestamp: datetime
    expiry_timestamp: datetime
    is_active: bool
    logout_timestamp: Optional[datetime] = None
    # refresh_token_hash: لا يُعرض في الـ Read Schema لأسباب أمنية.
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين UserRead للمستخدم (user_id) بشكل متداخل.


# ==========================================================
# --- Schemas لحمولة توكن JWT (Token Payload) ---
#    هذا الـ Schema يُستخدم داخلياً لتمثيل محتوى توكن JWT
# ==========================================================
class TokenPayload(BaseModel):
    """
    نموذج Pydantic لحمولة (payload) توكن JWT.
    """
    sub: str = Field(..., description="الموضوع (subject) للتوكن، عادة ما يكون user_id.")
    # exp: int = Field(..., description="وقت انتهاء الصلاحية.") # يتم التعامل معه بواسطة مكتبة PyJWT
    # iat: int = Field(..., description="وقت الإصدار.") # يتم التعامل معه بواسطة مكتبة PyJWTs