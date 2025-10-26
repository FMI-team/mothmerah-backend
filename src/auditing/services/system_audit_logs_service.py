# backend\src\auditing\services\system_audit_logs_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # SystemAuditLog
# استيراد الـ CRUD
from src.auditing.crud import system_audit_logs_crud as crud
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)
from src.lookups.crud import security_event_types_crud # للتحقق من وجود نوع حدث الأمان (SystemEventType)

# استيراد Schemas
from src.auditing.schemas import audit_schemas as schemas # SystemAuditLog

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for SystemAuditLog ---
# ==========================================================

def create_system_audit_log_service(db: Session, log_in: schemas.SystemAuditLogCreate) -> models.SystemAuditLog:
    """
    خدمة لإنشاء سجل جديد في جدول سجلات تدقيق النظام العامة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.SystemAuditLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.SystemAuditLog: كائن السجل الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم المرتبط أو نوع الحدث.
    """
    # 1. التحقق من وجود المستخدم (إذا كان user_id موجوداً)
    if log_in.user_id:
        user_exists = core_crud.get_user_by_id(db, log_in.user_id)
        if not user_exists:
            raise NotFoundException(detail=f"المستخدم بمعرف {log_in.user_id} المرتبط بسجل التدقيق غير موجود.")
    
    # 2. التحقق من وجود نوع الحدث
    event_type_exists = security_event_types_crud.get_security_event_type(db, log_in.event_type_id)
    if not event_type_exists:
        raise NotFoundException(detail=f"نوع الحدث بمعرف {log_in.event_type_id} لسجل التدقيق غير موجود.")

    return crud.create_system_audit_log(db=db, log_in=log_in)

def get_system_audit_log_details(db: Session, log_id: int) -> models.SystemAuditLog:
    """
    خدمة لجلب سجل تدقيق نظام واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_id (int): معرف السجل المطلوب.

    Returns:
        models.SystemAuditLog: كائن السجل.

    Raises:
        NotFoundException: إذا لم يتم العثور على السجل.
    """
    db_log = crud.get_system_audit_log(db, log_id=log_id)
    if not db_log:
        raise NotFoundException(detail=f"سجل تدقيق النظام بمعرف {log_id} غير موجود.")
    return db_log

def get_all_system_audit_logs_service(
    db: Session,
    user_id: Optional[UUID] = None,
    event_type_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.SystemAuditLog]:
    """
    خدمة لجلب قائمة بسجلات تدقيق النظام، مع خيارات التصفية والترقيم.
    """
    return crud.get_all_system_audit_logs(
        db=db,
        user_id=user_id,
        event_type_id=event_type_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

# لا توجد خدمات للتحديث أو الحذف المباشر لـ SystemAuditLog.