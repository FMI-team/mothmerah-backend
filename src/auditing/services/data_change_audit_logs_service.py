# backend\src\auditing\services\data_change_audit_logs_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # DataChangeAuditLog
# استيراد الـ CRUD
from src.auditing.crud import data_change_audit_logs_crud as crud
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)

# استيراد Schemas
from src.auditing.schemas import audit_schemas as schemas # DataChangeAuditLog

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for DataChangeAuditLog ---
# ==========================================================

def create_data_change_audit_log_service(db: Session, log_in: schemas.DataChangeAuditLogCreate) -> models.DataChangeAuditLog:
    """
    خدمة لإنشاء سجل جديد في جدول سجلات تدقيق تغيير البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.DataChangeAuditLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.DataChangeAuditLog: كائن السجل الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم الذي أجرى التغيير.
    """
    # 1. التحقق من وجود المستخدم الذي أجرى التغيير (إذا كان changed_by_user_id موجوداً)
    if log_in.changed_by_user_id:
        user_exists = core_crud.get_user_by_id(db, log_in.changed_by_user_id)
        if not user_exists:
            raise NotFoundException(detail=f"المستخدم بمعرف {log_in.changed_by_user_id} الذي أجرى التغيير غير موجود.")
    
    # 2. TODO: يمكن إضافة تحققات إضافية هنا (مثلاً التحقق من table_name أو action_type).

    return crud.create_data_change_audit_log(db=db, log_in=log_in)

def get_data_change_audit_log_details(db: Session, change_log_id: int) -> models.DataChangeAuditLog:
    """
    خدمة لجلب سجل تدقيق تغيير بيانات واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        change_log_id (int): معرف السجل المطلوب.

    Returns:
        models.DataChangeAuditLog: كائن السجل.

    Raises:
        NotFoundException: إذا لم يتم العثور على السجل.
    """
    db_log = crud.get_data_change_audit_log(db, change_log_id=change_log_id)
    if not db_log:
        raise NotFoundException(detail=f"سجل تدقيق تغيير البيانات بمعرف {change_log_id} غير موجود.")
    return db_log

def get_all_data_change_audit_logs_service(
    db: Session,
    changed_by_user_id: Optional[UUID] = None,
    table_name: Optional[str] = None,
    record_id: Optional[str] = None,
    action_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.DataChangeAuditLog]:
    """
    خدمة لجلب قائمة بسجلات تدقيق تغيير البيانات، مع خيارات التصفية والترقيم.
    """
    return crud.get_all_data_change_audit_logs(
        db=db,
        changed_by_user_id=changed_by_user_id,
        table_name=table_name,
        record_id=record_id,
        action_type=action_type,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

# لا توجد خدمات للتحديث أو الحذف المباشر لـ DataChangeAuditLog.