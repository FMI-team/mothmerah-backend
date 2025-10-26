from sqlalchemy import JSON
# backend\src\auditing\schemas\audit_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas الأخرى
# UserRead تستورد من src.users.schemas.core_schemas
if TYPE_CHECKING: # <-- هذا الاستيراد يتم فقط لفحص الأنواع، لا يتم تنفيذه في وقت التشغيل
    # استيراد Schemas المطلوبة للعلاقات المتداخلة
    # UserRead تستورد من src.users.schemas.core_schemas
    from src.users.schemas.core_schemas import UserRead # <-- تم نقل استيراد UserRead إلى هنا

# ActivityTypeRead, SecurityEventTypeRead, SystemEventTypeRead, EntityTypeForReviewOrImageRead تستورد من src.lookups.schemas
from src.lookups.schemas import (
    ActivityTypeRead,
    SecurityEventTypeRead,
    SystemEventTypeRead, # تم إضافة هذا
    EntityTypeForReviewOrImageRead # تم إضافة هذا
)


# ==========================================================
# --- Schemas لسجلات تدقيق النظام العامة (SystemAuditLog) ---
#    (المودلات من backend\src\auditing\models\logs_models.py)
# ==========================================================
class SystemAuditLogBase(BaseModel):
    """النموذج الأساسي لبيانات سجل تدقيق النظام."""
    event_type_id: int = Field(..., description="معرف نوع الحدث (من جدول system_event_types).")
    event_description: str = Field(..., description="وصف تفصيلي للحدث.")
    user_id: Optional[UUID] = Field(None, description="معرف المستخدم المرتبط بالحدث (إذا كان موجوداً).")
    ip_address: Optional[str] = Field(None, max_length=45, description="عنوان IP المصدر للطلب.")
    target_entity_type: Optional[str] = Field(None, max_length=50, description="نوع الكيان المتأثر (مثلاً 'USER', 'PRODUCT', 'ORDER').")
    target_entity_id: Optional[str] = Field(None, max_length=255, description="معرف الكيان الذي تأثر بالحدث.")
    details: Optional[dict] = Field(None, description="بيانات JSON إضافية حول الحدث.") # تفاصيل إضافية

class SystemAuditLogCreate(SystemAuditLogBase):
    """نموذج لإنشاء سجل تدقيق نظام جديد."""
    pass

# لا يوجد Update لجدول السجلات

class SystemAuditLogRead(SystemAuditLogBase):
    """نموذج لقراءة وعرض تفاصيل سجل تدقيق النظام."""
    log_id: int
    event_timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
    # الكائنات المرتبطة بشكل متداخل
    user: Optional["UserRead"] = None
    event_type: SystemEventTypeRead # <-- تم التعديل هنا: SystemEventTypeRead


# ==========================================================
# --- Schemas لسجلات أنشطة المستخدمين (UserActivityLog) ---
#    (المودلات من backend\src\auditing\models\logs_models.py)
# ==========================================================
class UserActivityLogBase(BaseModel):
    """النموذج الأساسي لبيانات سجل نشاط المستخدم."""
    user_id: UUID = Field(..., description="معرف المستخدم الذي قام بالنشاط.")
    session_id: Optional[UUID] = Field(None, description="معرف الجلسة المرتبطة بالنشاط.")
    activity_type_id: int = Field(..., description="معرف نوع النشاط (من جدول activity_types).")
    # TODO: entity_type, entity_id (للكيان المتأثر)
    # entity_type_code: Optional[str] = Field(None, max_length=50) # إذا أردنا استخدام EntityTypeForReviewOrImage
    # entity_id: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, description="وصف موجز للنشاط.")
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None)
    details: Optional[dict] = Field(None) # JSON field

class UserActivityLogCreate(UserActivityLogBase):
    """نموذج لإنشاء سجل نشاط مستخدم جديد."""
    pass

class UserActivityLogRead(UserActivityLogBase):
    """نموذج لقراءة وعرض تفاصيل سجل نشاط المستخدم."""
    activity_log_id: int
    activity_timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
    # الكائنات المرتبطة بشكل متداخل
    user: "UserRead"
    # TODO: session: UserSessionRead # تتطلب استيراد UserSessionRead
    activity_type: ActivityTypeRead
    # TODO: entity_type_obj: EntityTypeForReviewOrImageRead


# ==========================================================
# --- Schemas لسجلات البحث (SearchLog) ---
#    (المودلات من backend\src\auditing\models\logs_models.py)
# ==========================================================
class SearchLogBase(BaseModel):
    """النموذج الأساسي لبيانات سجل البحث."""
    user_id: Optional[UUID] = Field(None, description="معرف المستخدم الذي أجرى البحث (إذا كان مسجلاً الدخول).")
    session_id: Optional[UUID] = Field(None, description="معرف الجلسة المرتبطة بالبحث.")
    search_query: str = Field(..., max_length=255, description="نص استعلام البحث.")
    number_of_results_returned: Optional[int] = Field(None, ge=0, description="عدد النتائج التي تم إرجاعها.")
    filters_applied: Optional[dict] = Field(None, description="الفلاتر الإضافية المطبقة على البحث (JSON).")
    clicked_result_entity_type: Optional[str] = Field(None, max_length=50)
    clicked_result_entity_id: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    # TODO: user_agent (غير موجود في المودل الحالي)

class SearchLogCreate(SearchLogBase):
    """نموذج لإنشاء سجل بحث جديد."""
    pass

class SearchLogRead(SearchLogBase):
    """نموذج لقراءة وعرض تفاصيل سجل البحث."""
    search_log_id: int
    search_timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
    # الكائنات المرتبطة بشكل متداخل
    user: Optional["UserRead"] = None
    # TODO: session: UserSessionRead


# ==========================================================
# --- Schemas لسجلات أحداث الأمان (SecurityEventLog) ---
#    (المودلات من backend\src\auditing\models\logs_models.py)
# ==========================================================
class SecurityEventLogBase(BaseModel):
    """النموذج الأساسي لبيانات سجل حدث الأمان."""
    event_type_id: int = Field(..., description="معرف نوع حدث الأمان (من جدول security_event_types).")
    user_id: Optional[UUID] = Field(None, description="معرف المستخدم المرتبط بالحدث (إذا كان موجوداً).")
    target_user_id: Optional[UUID] = Field(None, description="معرف المستخدم الهدف (إذا كان الحدث يستهدف مستخدمًا آخر).")
    ip_address: Optional[str] = Field(None, max_length=45)
    details: Optional[str] = Field(None, description="وصف تفصيلي للحدث الأمني.")
    severity_level: Optional[int] = Field(None, ge=1, le=5)
    affected_entity_type: Optional[str] = Field(None, max_length=50)
    affected_entity_id: Optional[str] = Field(None, max_length=255)
    # TODO: additional_data (JSON)

class SecurityEventLogCreate(SecurityEventLogBase):
    """نموذج لإنشاء سجل حدث أمان جديد."""
    pass

class SecurityEventLogRead(SecurityEventLogBase):
    """نموذج لقراءة وعرض تفاصيل سجل حدث الأمان."""
    security_event_id: int
    event_timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
    # الكائنات المرتبطة بشكل متداخل
    user: Optional["UserRead"] = None
    target_user: Optional["UserRead"] = None # إذا كان target_user_id يشير إلى user
    event_type: SecurityEventTypeRead


# ==========================================================
# --- Schemas لسجلات تدقيق تغييرات البيانات (DataChangeAuditLog) ---
#    (المودلات من backend\src\auditing\models\logs_models.py)
# ==========================================================
class DataChangeAuditLogBase(BaseModel):
    """النموذج الأساسي لبيانات سجل تدقيق تغيير البيانات."""
    table_name: str = Field(..., max_length=100)
    record_id: str = Field(..., max_length=255)
    column_name: str = Field(..., max_length=100) # BRD: NOT NULL
    old_value: Optional[str] = Field(None)
    new_value: Optional[str] = Field(None)
    change_type: str = Field(..., max_length=20, description="نوع الإجراء (CREATE, UPDATE, DELETE).") # BRD: NOT NULL
    changed_by_user_id: Optional[UUID] = Field(None, description="معرف المستخدم الذي أجرى التغيير (إذا كان موجوداً).")
    # TODO: ip_address, user_agent (غير موجودين في المودل الحالي)

class DataChangeAuditLogCreate(DataChangeAuditLogBase):
    """نموذج لإنشاء سجل تدقيق تغيير بيانات جديد."""
    pass

class DataChangeAuditLogRead(DataChangeAuditLogBase):
    """نموذج لقراءة وعرض تفاصيل سجل تدقيق تغيير البيانات."""
    change_log_id: int
    change_timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
    # الكائنات المرتبطة بشكل متداخل
    changed_by_user: Optional["UserRead"] = None