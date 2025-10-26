# backend\src\users\schemas\rbac_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID # لـ user_id في UserRole
from datetime import datetime # للطوابع الزمنية

# استيرادات Schemas الأخرى التي قد يحتاجها هذا الملف لـ Nested Read
# TODO: تأكد من أن UserRead موجودة في core_schemas.py
# from src.users.schemas.core_schemas import UserRead


# ==========================================================
# --- Schemas للأدوار (Roles) ---
#    (المودلات من backend\src\users\models\roles_models.py)
# ==========================================================
class RoleTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة الدور."""
    language_code: str = Field(..., max_length=10, description="رمز اللغة للترجمة (مثلاً: 'ar', 'en').")
    translated_role_name: str = Field(..., max_length=100, description="الاسم المترجم للدور (مثلاً: 'تاجر جملة').")
    translated_description: Optional[str] = Field(None, description="الوصف المترجم للدور.")

class RoleTranslationCreate(RoleTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لدور."""
    pass

class RoleTranslationUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث ترجمة دور موجودة."""
    translated_role_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class RoleTranslationRead(RoleTranslationBase):
    """نموذج لقراءة وعرض ترجمة الدور."""
    role_id: int # معرف الدور الأم
    model_config = ConfigDict(from_attributes=True)

class RoleBase(BaseModel):
    """النموذج الأساسي للدور."""
    role_name_key: str = Field(..., max_length=50, description="مفتاح نصي فريد لاسم الدور (مثلاً: 'WHOLESALER', 'ADMIN').")
    is_active: Optional[bool] = Field(True, description="هل هذا الدور نشط ومتاح للاستخدام؟")
    # TODO: يمكن إضافة description_key هنا إذا كان الوصف ليس في الترجمات مباشرة

class RoleCreate(RoleBase):
    """نموذج لإنشاء دور جديد، يتضمن ترجماته الأولية."""
    translations: Optional[List[RoleTranslationCreate]] = Field([], description="الترجمات الأولية للدور.")

class RoleUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث بيانات دور موجود."""
    role_name_key: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

class RoleRead(RoleBase):
    """نموذج لقراءة وعرض تفاصيل الدور، يتضمن ترجماته ومعرفه."""
    role_id: int
    created_at: datetime
    updated_at: datetime
    translations: List[RoleTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas للصلاحيات (Permissions) ---
#    (المودلات من backend\src\users\models\roles_models.py)
# ==========================================================
class PermissionRead(BaseModel): # <-- هذا هو الـ Schema الذي تحتاجه RoleWithPermissionsRead
    """نموذج لقراءة وعرض تفاصيل صلاحية واحدة."""
    permission_id: int
    permission_name_key: str = Field(..., max_length=100, description="مفتاح نصي فريد لاسم الصلاحية (مثلاً: 'CREATE_AUCTION', 'VIEW_ALL_ORDERS').")
    module_group: Optional[str] = Field(None, max_length=50, description="المجموعة الوظيفية التي تنتمي إليها الصلاحية.")
    description: Optional[str] = Field(None, description="وصف موجز للصلاحية (للمسؤولين).") # هذا الحقل نصي وليس key للترجمة
    is_active: bool = Field(True, description="هل هذه الصلاحية نشطة ومتاحة للاستخدام؟")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GroupedPermissionRead(BaseModel):
    """نموذج لعرض الصلاحيات مجمعة حسب الوحدة (Module Group)."""
    module_group: Optional[str] = Field(None, description="اسم مجموعة الوحدة.") # يمكن أن يكون None إذا كانت الصلاحية بدون مجموعة
    permissions: List[PermissionRead] = Field([])


class PermissionCreate(BaseModel):
    """نموذج لإنشاء صلاحية جديدة."""
    permission_name_key: str = Field(..., max_length=100)
    description: Optional[str] = Field(None)
    module_group: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = Field(True)

class PermissionUpdate(BaseModel):
    """نموذج لتحديث صلاحية موجودة."""
    permission_name_key: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)
    module_group: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


# هنا يجب تعريف RoleWithPermissionsRead
class RoleWithPermissionsRead(RoleRead): # <-- هذا هو الـ Schema الذي كنت تبحث عنه
    """Schema لعرض دور واحد مع قائمة صلاحياته الكاملة."""
    permissions: List[PermissionRead] = [] # يعتمد على PermissionRead
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لربط الأدوار بالصلاحيات (Role-Permissions) ---
#    (المودلات من backend\src\users\models\roles_models.py)
# ==========================================================
class RolePermissionBase(BaseModel):
    """النموذج الأساسي لربط دور بصلاحية."""
    role_id: int = Field(..., description="معرف الدور المرتبط.")
    permission_id: int = Field(..., description="معرف الصلاحية المرتبطة.")

class RolePermissionCreate(RolePermissionBase):
    """نموذج لإنشاء ربط جديد بين دور وصلاحية."""
    pass

class RolePermissionRead(RolePermissionBase):
    """نموذج لقراءة وعرض تفاصيل ربط دور بصلاحية."""
    role_permission_id: int
    granted_at: datetime # وقت منح الصلاحية للدور
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين RoleRead و PermissionRead بشكل متداخل.
    # role: RoleRead
    # permission: PermissionRead


# ==========================================================
# --- Schemas لربط المستخدمين بالأدوار (User-Roles) ---
#    (المودلات من backend\src\users\models\roles_models.py)
# ==========================================================
class UserRoleBase(BaseModel):
    """النموذج الأساسي لربط مستخدم بدور (للدوار الإضافية)."""
    user_id: UUID = Field(..., description="معرف المستخدم المرتبط.")
    role_id: int = Field(..., description="معرف الدور المرتبط.")
    assigned_by_user_id: Optional[UUID] = Field(None, description="معرف المستخدم الذي قام بإسناد هذا الدور (غالباً مسؤول).")

class UserRoleCreate(UserRoleBase):
    """نموذج لإنشاء ربط جديد بين مستخدم ودور."""
    pass

class UserRoleRead(UserRoleBase):
    """نموذج لقراءة وعرض تفاصيل ربط مستخدم بدور."""
    user_role_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين UserRead (لـ user و assigned_by_user) و RoleRead.
    # user: "UserRead"
    # role: RoleRead
    # assigned_by_user: "UserRead" (self-referencing)