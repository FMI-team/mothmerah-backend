# backend\src\configuration\crud\system_maintenance_schedule_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.configuration.models import settings_models as models # SystemMaintenanceSchedule
# استيراد Schemas (لـ type hinting في Create/Update)
from src.configuration.schemas import settings_schemas as schemas
# استيراد مودل User للتحقق من وجود FKs في جداول SystemMaintenanceSchedule
from src.users.models.core_models import User


# ==========================================================
# --- CRUD Functions for SystemMaintenanceSchedule ---
# ==========================================================

def create_system_maintenance_schedule(db: Session, schedule_in: schemas.SystemMaintenanceScheduleCreate) -> models.SystemMaintenanceSchedule:
    """
    ينشئ جدول صيانة نظام جديد في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        schedule_in (schemas.SystemMaintenanceScheduleCreate): بيانات الجدول للإنشاء.

    Returns:
        models.SystemMaintenanceSchedule: كائن الجدول الذي تم إنشاؤه.
    """
    db_schedule = models.SystemMaintenanceSchedule(
        start_timestamp=schedule_in.start_timestamp,
        end_timestamp=schedule_in.end_timestamp,
        maintenance_message_key=schedule_in.maintenance_message_key,
        is_active=schedule_in.is_active,
        # created_at, updated_at سيتم تعيينهما افتراضياً في المودل
        # created_by_user_id سيتم تعيينه في طبقة الخدمة
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def get_system_maintenance_schedule(db: Session, maintenance_id: int) -> Optional[models.SystemMaintenanceSchedule]:
    """
    يجلب جدول صيانة نظام واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        maintenance_id (int): معرف جدول الصيانة المطلوب.

    Returns:
        Optional[models.SystemMaintenanceSchedule]: كائن الجدول أو None.
    """
    return db.query(models.SystemMaintenanceSchedule).options(
        joinedload(models.SystemMaintenanceSchedule.created_by_user)
    ).filter(models.SystemMaintenanceSchedule.maintenance_id == maintenance_id).first()

def get_all_system_maintenance_schedules(
    db: Session,
    is_active: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.SystemMaintenanceSchedule]:
    """
    يجلب قائمة بجداول صيانة النظام، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        is_active (Optional[bool]): تصفية حسب حالة النشاط.
        start_time (Optional[datetime]): تصفية حسب وقت البدء.
        end_time (Optional[datetime]): تصفية حسب وقت الانتهاء.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.SystemMaintenanceSchedule]: قائمة بكائنات الجداول.
    """
    query = db.query(models.SystemMaintenanceSchedule).options(
        joinedload(models.SystemMaintenanceSchedule.created_by_user)
    )
    if is_active is not None:
        query = query.filter(models.SystemMaintenanceSchedule.is_active == is_active)
    if start_time:
        query = query.filter(models.SystemMaintenanceSchedule.start_timestamp >= start_time)
    if end_time:
        query = query.filter(models.SystemMaintenanceSchedule.end_timestamp <= end_time)
    
    return query.order_by(models.SystemMaintenanceSchedule.start_timestamp.desc()).offset(skip).limit(limit).all()

def update_system_maintenance_schedule(db: Session, db_schedule: models.SystemMaintenanceSchedule, schedule_in: schemas.SystemMaintenanceScheduleUpdate, updated_by_user_id: Optional[UUID] = None) -> models.SystemMaintenanceSchedule:
    """
    يحدث بيانات جدول صيانة نظام موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_schedule (models.SystemMaintenanceSchedule): كائن الجدول من قاعدة البيانات.
        schedule_in (schemas.SystemMaintenanceScheduleUpdate): البيانات المراد تحديثها.
        updated_by_user_id (Optional[UUID]): معرف المستخدم الذي أجرى التحديث.

    Returns:
        models.SystemMaintenanceSchedule: كائن الجدول المحدث.
    """
    update_data = schedule_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_schedule, key, value)
    
    db_schedule.updated_at = datetime.now(timezone.utc)
    # TODO: لا يوجد حقل updated_by_user_id مباشر في المودل لهذا الجدول، فقط created_by_user_id
    #       إذا أردت تتبع من قام بالتحديث، يجب إضافة هذا الحقل إلى المودل.
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def delete_system_maintenance_schedule(db: Session, db_schedule: models.SystemMaintenanceSchedule):
    """
    يحذف جدول صيانة نظام معين (حذف صارم).
    TODO: التحقق من أن الجدول غير نشط أو انتهت فترته قبل الحذف.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_schedule (models.SystemMaintenanceSchedule): كائن الجدول من قاعدة البيانات.
    """
    db.delete(db_schedule)
    db.commit()
    return