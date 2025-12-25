# backend\src\users\schemas\management_schemas.py

from pydantic import BaseModel, Field, ConfigDict, EmailStr, constr
from typing import List, Optional
from uuid import UUID # لـ user_id إذا تم ربطه بسجل مراجعة
from datetime import datetime # إذا تم استخدام تواريخ في المستقبل

# ================================================================
# --- Schemas لإجراءات المسؤول على المستخدمين (Admin actions on Users) ---
#    (هذه Schemas مخصصة للمسؤولين لتعديل بيانات المستخدمين أو حالتهم)
# ================================================================

class AdminUserStatusUpdate(BaseModel):
    """
    Schema يستخدمه المسؤول لتحديث حالة حساب مستخدم.
    يتضمن الحالة الجديدة المطلوبة وسبب التغيير لأغراض التدقيق.
    """
    new_status_id: int = Field(..., description="معرف الحالة الجديدة للحساب (من جدول account_statuses).")
    reason_for_change: str = Field(..., min_length=10, description="سبب إلزامي لتغيير حالة الحساب لأغراض التدقيق والسجلات.")
    # TODO: يمكن إضافة حقول لربط المراجعة اليدوية (ManualVerificationLog) هنا
    #       مثل log_id أو notes_for_reviewer_id إذا أردنا توثيق المراجعة بشكل مباشر.

# ملاحظة: جميع Schemas الأخرى التي كانت هنا سابقًا (مثل UserType, UserPreference, AccountStatus, LicenseType, IssuingAuthority, VerificationStatus)
#         قد تم نقلها إلى ملفات Schemas المناسبة لها (مثل core_schemas.py أو verification_lookups_schemas.py).
#         تأكد من إزالة أي تعريفات مكررة من هذا الملف.

# Request Schema (for creating users)
class AdminUserCreate(BaseModel):
    """Schema for creating a new admin user."""
    phone_number: constr(pattern=r'^\+9665[0-9]{8}$')
    email: Optional[EmailStr] = None
    first_name: str
    last_name: str
    password: str
    default_user_role_id: Optional[int] = None
    user_type_id: int
    account_status_id: int
    user_verification_status_id: Optional[int] = None
    preferred_language_code: Optional[str] = "ar"
    additional_data: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)

class AdminUserCreatedResponse(BaseModel):
    """Schema for RESPONSE after creating a user - excludes sensitive data."""
    user_id: UUID
    phone_number: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # Add other non-sensitive fields you want to return
    
    model_config = ConfigDict(from_attributes=True)