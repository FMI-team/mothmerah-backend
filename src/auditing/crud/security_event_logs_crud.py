# backend\src\auditing\crud\security_event_logs_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # SecurityEventLog
# استيراد Schemas (لـ type hinting في Create)
from src.auditing.schemas import audit_schemas as schemas


# ==========================================================
# --- CRUD Functions for SecurityEventLog ---
# ==========================================================

def create_security_event_log(db: Session, log_in: schemas.SecurityEventLogCreate) -> models.SecurityEventLog:
    """
    ينشئ سجلاً جديداً في جدول سجلات أحداث الأمان.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.SecurityEventLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.SecurityEventLog: كائن السجل الذي تم إنشاؤه.
    """
    db_log = models.SecurityEventLog(
        user_id=log_in.user_id,
        target_user_id=log_in.target_user_id, # إذا كان موجوداً
        event_type_id=log_in.event_type_id,
        description=log_in.description, # تم تغيير الاسم إلى description
        severity_level=log_in.severity_level,
        ip_address=log_in.ip_address,
        affected_entity_type=log_in.affected_entity_type,
        affected_entity_id=log_in.affected_entity_id,
        details=log_in.additional_data # تم تغيير الاسم إلى details
    )
    db.add(db_log)
    db.commit() # السجلات يتم حفظها فوراً
    db.refresh(db_log)
    return db_log

def get_security_event_log(db: Session, security_event_id: int) -> Optional[models.SecurityEventLog]:
    """
    يجلب سجل حدث أمان واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        security_event_id (int): معرف السجل المطلوب.

    Returns:
        Optional[models.SecurityEventLog]: كائن السجل أو None.
    """
    return db.query(models.SecurityEventLog).options(
        joinedload(models.SecurityEventLog.user),
        joinedload(models.SecurityEventLog.target_user),
        joinedload(models.SecurityEventLog.event_type)
    ).filter(models.SecurityEventLog.security_event_id == security_event_id).first()

def get_all_security_event_logs(
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
    يجلب قائمة بسجلات أحداث الأمان، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (Optional[UUID]): تصفية حسب معرف المستخدم المرتبط.
        event_type_id (Optional[int]): تصفية حسب معرف نوع الحدث.
        severity_level (Optional[int]): تصفية حسب مستوى الخطورة.
        start_time (Optional[datetime]): تصفية حسب وقت الحدث (البدء).
        end_time (Optional[datetime]): تصفية حسب وقت الحدث (الانتهاء).
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.SecurityEventLog]: قائمة بكائنات السجلات.
    """
    query = db.query(models.SecurityEventLog).options(
        joinedload(models.SecurityEventLog.user),
        joinedload(models.SecurityEventLog.target_user),
        joinedload(models.SecurityEventLog.event_type)
    )
    if user_id:
        query = query.filter(models.SecurityEventLog.user_id == user_id)
    if event_type_id:
        query = query.filter(models.SecurityEventLog.event_type_id == event_type_id)
    if severity_level:
        query = query.filter(models.SecurityEventLog.severity_level == severity_level)
    if start_time:
        query = query.filter(models.SecurityEventLog.event_timestamp >= start_time)
    if end_time:
        query = query.filter(models.SecurityEventLog.event_timestamp <= end_time)
    
    return query.order_by(models.SecurityEventLog.event_timestamp.desc()).offset(skip).limit(limit).all()

# لا يوجد تحديث أو حذف مباشر لـ SecurityEventLog لأنه جدول سجلات تاريخية.