# backend\src\users\schemas\license_schemas.py

from pydantic import BaseModel,Field,ConfigDict
from typing import Optional,List
from uuid import UUID
from datetime import datetime, date

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas أخرى
# UserRead موجودة في core_schemas.py
from src.users.schemas.core_schemas import UserRead
# LicenseTypeRead, IssuingAuthorityRead, LicenseVerificationStatusRead موجودة الآن في verification_lookups_schemas.py
from src.users.schemas.verification_lookups_schemas import ( # <-- تم التعديل هنا
    LicenseTypeRead,
    IssuingAuthorityRead,
    LicenseVerificationStatusRead
)

# ==========================================================
# --- Schemas للتراخيص والوثائق الفعلية للمستخدمين (Licenses) ---
#    (المودلات من backend\src\users\models\verification_models.py)
# ==========================================================
class LicenseBase(BaseModel):
    """النموذج الأساسي لترخيص المستخدم: يصف الخصائص التي يتم إدخالها بواسطة المستخدم."""
    license_type_id: int = Field(..., description="معرف نوع الترخيص (سجل تجاري، عمل حر).")
    license_number: str = Field(..., max_length=100, description="رقم الترخيص أو الوثيقة.")
    issuing_authority_id: Optional[int] = Field(None, description="معرف الجهة المصدرة للترخيص.")
    issue_date: Optional[date] = Field(None, description="تاريخ إصدار الترخيص.")
    expiry_date: Optional[date] = Field(None, description="تاريخ انتهاء صلاحية الترخيص.")
    # file_storage_key: لا يتم تمريره مباشرة في Create/Update (يُدار بواسطة خدمة الرفع)
    # verification_status_id: لا يتم تمريره مباشرة من المستخدم (يُدار بواسطة النظام/المسؤول)

    # TODO: منطق عمل: التحقق من أن issue_date قبل expiry_date.
    # TODO: منطق عمل: التحقق من أن expiry_date في المستقبل عند الإنشاء (إذا كان الترخيص يجب أن يكون ساريًا).

class LicenseCreate(LicenseBase):
    """نموذج لإنشاء ترخيص جديد للمستخدم."""
    # user_id سيتم تعيينه في طبقة الخدمة.
    # file_data: Optional[bytes] # إذا كان الملف سيُرفع مباشرة مع البيانات (لكن عادةً يكون منفصلاً)
    pass

class LicenseUpdate(BaseModel):
    """نموذج لتحديث بيانات ترخيص موجود. جميع الحقول اختيارية للسماح بالتحديث الجزئي."""
    license_type_id: Optional[int] = None
    license_number: Optional[str] = Field(None, max_length=100)
    issuing_authority_id: Optional[int] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    # file_storage_key: لا يُحدث مباشرة
    verification_status_id: Optional[int] = Field(None, description="حالة التحقق الخاصة بهذا الترخيص (يُستخدم بواسطة المسؤولين).")

    # TODO: منطق عمل: عند تحديث verification_status_id يجب أن يكون بواسطة مسؤول فقط.

class LicenseRead(LicenseBase):
    """نموذج لقراءة وعرض تفاصيل الترخيص بشكل كامل، بما في ذلك معرفه والطوابع الزمنية،
    ورابط ملف التخزين، والكائنات المرتبطة بشكل متداخل.
    """
    license_id: int
    user_id: UUID
    file_storage_key: str = Field(..., description="رابط أو مفتاح الملف الفعلي المخزن في الخدمة السحابية.")
    verification_status_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

    # الكائنات المرتبطة بشكل متداخل (Nested Relationships)
    user: UserRead # المستخدم صاحب الترخيص
    license_type: LicenseTypeRead # نوع الترخيص
    issuing_authority: Optional[IssuingAuthorityRead] = None # الجهة المصدرة
    verification_status: LicenseVerificationStatusRead # حالة التحقق من الترخيص