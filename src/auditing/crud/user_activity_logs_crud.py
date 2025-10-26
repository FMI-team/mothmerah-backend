# backend\src\auditing\crud\user_activity_logs_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # UserActivityLog
# استيراد Schemas (لـ type hinting في Create)
from src.auditing.schemas import audit_schemas as schemas


# ==========================================================
# --- CRUD Functions for UserActivityLog ---
# ==========================================================

def create_user_activity_log(db: Session, log_in: schemas.UserActivityLogCreate) -> models.UserActivityLog:
    """
    ينشئ سجلاً جديداً في جدول سجلات أنشطة المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.UserActivityLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.UserActivityLog: كائن السجل الذي تم إنشاؤه.
    """
    db_log = models.UserActivityLog(
        user_id=log_in.user_id,
        session_id=log_in.session_id,
        activity_type_id=log_in.activity_type_id,
        # activity_timestamp سيتم تعيينه افتراضياً في المودل (server_default=func.now())
        entity_type=log_in.entity_type, # إذا كان موجوداً
        entity_id=log_in.entity_id,     # إذا كان موجوداً
        description=log_in.description,
        ip_address=log_in.ip_address,
        user_agent=log_in.user_agent,
        details=log_in.details # هنا كان additional_data سابقا
    )
    db.add(db_log)
    db.commit() # السجلات يتم حفظها فوراً
    db.refresh(db_log)
    return db_log

def get_user_activity_log(db: Session, activity_log_id: int) -> Optional[models.UserActivityLog]:
    """
    يجلب سجل نشاط مستخدم واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        activity_log_id (int): معرف السجل المطلوب.

    Returns:
        Optional[models.UserActivityLog]: كائن السجل أو None.
    """
    return db.query(models.UserActivityLog).options(
        joinedload(models.UserActivityLog.user),
        joinedload(models.UserActivityLog.session), # إذا كان موجوداً
        joinedload(models.UserActivityLog.activity_type)
    ).filter(models.UserActivityLog.activity_log_id == activity_log_id).first()

def get_all_user_activity_logs(
    db: Session,
    user_id: Optional[UUID] = None,
    activity_type_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.UserActivityLog]:
    """
    يجلب قائمة بسجلات أنشطة المستخدمين، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (Optional[UUID]): تصفية حسب معرف المستخدم.
        activity_type_id (Optional[int]): تصفية حسب معرف نوع النشاط.
        start_time (Optional[datetime]): تصفية حسب وقت النشاط (البدء).
        end_time (Optional[datetime]): تصفية حسب وقت النشاط (الانتهاء).
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.UserActivityLog]: قائمة بكائنات السجلات.
    """
    query = db.query(models.UserActivityLog).options(
        joinedload(models.UserActivityLog.user),
        joinedload(models.UserActivityLog.session),
        joinedload(models.UserActivityLog.activity_type)
    )
    if user_id:
        query = query.filter(models.UserActivityLog.user_id == user_id)
    if activity_type_id:
        query = query.filter(models.UserActivityLog.activity_type_id == activity_type_id)
    if start_time:
        query = query.filter(models.UserActivityLog.activity_timestamp >= start_time)
    if end_time:
        query = query.filter(models.UserActivityLog.activity_timestamp <= end_time)
    
    return query.order_by(models.UserActivityLog.activity_timestamp.desc()).offset(skip).limit(limit).all()

# لا يوجد تحديث أو حذف مباشر لـ UserActivityLog لأنه جدول سجلات تاريخية.