# backend\src\auditing\crud\system_audit_logs_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # SystemAuditLog
# استيراد Schemas (لـ type hinting في Create)
from src.auditing.schemas import audit_schemas as schemas


# ==========================================================
# --- CRUD Functions for SystemAuditLog ---
# ==========================================================

def create_system_audit_log(db: Session, log_in: schemas.SystemAuditLogCreate) -> models.SystemAuditLog:
    """
    ينشئ سجلاً جديداً في جدول سجلات تدقيق النظام العامة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.SystemAuditLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.SystemAuditLog: كائن السجل الذي تم إنشاؤه.
    """
    db_log = models.SystemAuditLog(
        user_id=log_in.user_id,
        event_type_id=log_in.event_type_id,
        event_description=log_in.event_description,
        ip_address=log_in.ip_address,
        target_entity_type=log_in.target_entity_type,
        target_entity_id=log_in.target_entity_id,
        details=log_in.details # هنا كان additional_data سابقاً، تم التغيير لـ details
    )
    db.add(db_log)
    db.commit() # السجلات يتم حفظها فوراً
    db.refresh(db_log)
    return db_log

def get_system_audit_log(db: Session, log_id: int) -> Optional[models.SystemAuditLog]:
    """
    يجلب سجل تدقيق نظام واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_id (int): معرف السجل المطلوب.

    Returns:
        Optional[models.SystemAuditLog]: كائن السجل أو None.
    """
    return db.query(models.SystemAuditLog).options(
        joinedload(models.SystemAuditLog.user),
        joinedload(models.SystemAuditLog.event_type)
    ).filter(models.SystemAuditLog.log_id == log_id).first()

def get_all_system_audit_logs(
    db: Session,
    user_id: Optional[UUID] = None,
    event_type_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.SystemAuditLog]:
    """
    يجلب قائمة بسجلات تدقيق النظام، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (Optional[UUID]): تصفية حسب معرف المستخدم.
        event_type_id (Optional[int]): تصفية حسب معرف نوع الحدث.
        start_time (Optional[datetime]): تصفية حسب وقت الحدث (البدء).
        end_time (Optional[datetime]): تصفية حسب وقت الحدث (الانتهاء).
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.SystemAuditLog]: قائمة بكائنات السجلات.
    """
    query = db.query(models.SystemAuditLog).options(
        joinedload(models.SystemAuditLog.user),
        joinedload(models.SystemAuditLog.event_type)
    )
    if user_id:
        query = query.filter(models.SystemAuditLog.user_id == user_id)
    if event_type_id:
        query = query.filter(models.SystemAuditLog.event_type_id == event_type_id)
    if start_time:
        query = query.filter(models.SystemAuditLog.event_timestamp >= start_time)
    if end_time:
        query = query.filter(models.SystemAuditLog.event_timestamp <= end_time)
    
    return query.order_by(models.SystemAuditLog.event_timestamp.desc()).offset(skip).limit(limit).all()

# لا يوجد تحديث أو حذف مباشر لـ SystemAuditLog لأنه جدول سجلات تاريخية.