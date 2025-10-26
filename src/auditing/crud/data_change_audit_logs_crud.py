# backend\src\auditing\crud\data_change_audit_logs_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # DataChangeAuditLog
# استيراد Schemas (لـ type hinting في Create)
from src.auditing.schemas import audit_schemas as schemas


# ==========================================================
# --- CRUD Functions for DataChangeAuditLog ---
# ==========================================================

def create_data_change_audit_log(db: Session, log_in: schemas.DataChangeAuditLogCreate) -> models.DataChangeAuditLog:
    """
    ينشئ سجلاً جديداً في جدول سجلات تدقيق تغيير البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.DataChangeAuditLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.DataChangeAuditLog: كائن السجل الذي تم إنشاؤه.
    """
    db_log = models.DataChangeAuditLog(
        changed_by_user_id=log_in.changed_by_user_id,
        table_name=log_in.table_name,
        record_id=log_in.record_id,
        column_name=log_in.column_name,
        old_value=log_in.old_value,
        new_value=log_in.new_value,
        change_type=log_in.change_type,
        # created_at و change_timestamp سيتم تعيينهما افتراضياً في المودل
    )
    db.add(db_log)
    db.commit() # السجلات يتم حفظها فوراً
    db.refresh(db_log)
    return db_log

def get_data_change_audit_log(db: Session, change_log_id: int) -> Optional[models.DataChangeAuditLog]:
    """
    يجلب سجل تدقيق تغيير بيانات واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        change_log_id (int): معرف السجل المطلوب.

    Returns:
        Optional[models.DataChangeAuditLog]: كائن السجل أو None.
    """
    return db.query(models.DataChangeAuditLog).options(
        joinedload(models.DataChangeAuditLog.changed_by_user)
    ).filter(models.DataChangeAuditLog.change_log_id == change_log_id).first()

def get_all_data_change_audit_logs(
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
    يجلب قائمة بسجلات تدقيق تغيير البيانات، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        changed_by_user_id (Optional[UUID]): تصفية حسب معرف المستخدم الذي أجرى التغيير.
        table_name (Optional[str]): تصفية حسب اسم الجدول.
        record_id (Optional[str]): تصفية حسب معرف السجل المتأثر.
        action_type (Optional[str]): تصفية حسب نوع الإجراء (CREATE, UPDATE, DELETE).
        start_time (Optional[datetime]): تصفية حسب وقت التغيير (البدء).
        end_time (Optional[datetime]): تصفية حسب وقت التغيير (الانتهاء).
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.DataChangeAuditLog]: قائمة بكائنات السجلات.
    """
    query = db.query(models.DataChangeAuditLog).options(
        joinedload(models.DataChangeAuditLog.changed_by_user)
    )
    if changed_by_user_id:
        query = query.filter(models.DataChangeAuditLog.changed_by_user_id == changed_by_user_id)
    if table_name:
        query = query.filter(models.DataChangeAuditLog.table_name == table_name)
    if record_id:
        query = query.filter(models.DataChangeAuditLog.record_id == record_id)
    if action_type:
        query = query.filter(models.DataChangeAuditLog.action_type == action_type)
    if start_time:
        query = query.filter(models.DataChangeAuditLog.change_timestamp >= start_time)
    if end_time:
        query = query.filter(models.DataChangeAuditLog.change_timestamp <= end_time)
    
    return query.order_by(models.DataChangeAuditLog.change_timestamp.desc()).offset(skip).limit(limit).all()

# لا يوجد تحديث أو حذف مباشر لـ DataChangeAuditLog لأنه جدول سجلات تاريخية.