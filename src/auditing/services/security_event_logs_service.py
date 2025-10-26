# backend\src\auditing\services\security_event_logs_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # SecurityEventLog
# استيراد الـ CRUD
from src.auditing.crud import security_event_logs_crud as crud
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)
from src.lookups.crud import security_event_types_crud # للتحقق من وجود نوع حدث الأمان (SecurityEventType)

# استيراد Schemas
from src.auditing.schemas import audit_schemas as schemas # SecurityEventLog

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for SecurityEventLog ---
# ==========================================================

def create_security_event_log_service(db: Session, log_in: schemas.SecurityEventLogCreate) -> models.SecurityEventLog:
    """
    خدمة لإنشاء سجل جديد في جدول سجلات أحداث الأمان.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.SecurityEventLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.SecurityEventLog: كائن السجل الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم المرتبط أو نوع الحدث.
    """
    # 1. التحقق من وجود المستخدم (إذا كان user_id أو target_user_id موجوداً)
    if log_in.user_id:
        user_exists = core_crud.get_user_by_id(db, log_in.user_id)
        if not user_exists:
            raise NotFoundException(detail=f"المستخدم بمعرف {log_in.user_id} المرتبط بحدث الأمان غير موجود.")
    if log_in.target_user_id:
        target_user_exists = core_crud.get_user_by_id(db, log_in.target_user_id)
        if not target_user_exists:
            raise NotFoundException(detail=f"المستخدم الهدف بمعرف {log_in.target_user_id} لحدث الأمان غير موجود.")
    
    # 2. التحقق من وجود نوع الحدث الأمني
    event_type_exists = security_event_types_crud.get_security_event_type(db, log_in.event_type_id)
    if not event_type_exists:
        raise NotFoundException(detail=f"نوع الحدث الأمني بمعرف {log_in.event_type_id} لسجل حدث الأمان غير موجود.")

    return crud.create_security_event_log(db=db, log_in=log_in)

def get_security_event_log_details(db: Session, security_event_id: int) -> models.SecurityEventLog:
    """
    خدمة لجلب سجل حدث أمان واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        security_event_id (int): معرف السجل المطلوب.

    Returns:
        models.SecurityEventLog: كائن السجل.

    Raises:
        NotFoundException: إذا لم يتم العثور على السجل.
    """
    db_log = crud.get_security_event_log(db, security_event_id=security_event_id)
    if not db_log:
        raise NotFoundException(detail=f"سجل حدث الأمان بمعرف {security_event_id} غير موجود.")
    return db_log

def get_all_security_event_logs_service(
    db: Session,
    user_id: Optional[UUID] = None,
    event_type_id: Optional[int] = None,
    severity_level: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.SecurityEventLog]:
    """
    خدمة لجلب قائمة بسجلات أحداث الأمان، مع خيارات التصفية والترقيم.
    """
    return crud.get_all_security_event_logs(
        db=db,
        user_id=user_id,
        event_type_id=event_type_id,
        severity_level=severity_level,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

# لا توجد خدمات للتحديث أو الحذف المباشر لـ SecurityEventLog.