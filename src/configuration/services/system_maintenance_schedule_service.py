# backend\src\configuration\services\system_maintenance_schedule_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, date # استخدام timezone لتسجيل الوقت الحالي، و date لـ start/end_timestamp

# استيراد المودلز
from src.configuration.models import settings_models as models # SystemMaintenanceSchedule
# استيراد الـ CRUD
from src.configuration.crud import system_maintenance_schedule_crud as crud
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)

# استيراد Schemas
from src.configuration.schemas import settings_schemas as schemas # SystemMaintenanceSchedule

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for SystemMaintenanceSchedule ---
# ==========================================================

def create_new_system_maintenance_schedule(db: Session, schedule_in: schemas.SystemMaintenanceScheduleCreate, current_user: User) -> models.SystemMaintenanceSchedule:
    """
    خدمة لإنشاء جدول صيانة نظام جديد.
    تتضمن التحقق من عدم تداخل المواعيد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        schedule_in (schemas.SystemMaintenanceScheduleCreate): بيانات جدول الصيانة للإنشاء.
        current_user (User): المستخدم الذي ينشئ الجدول.

    Returns:
        models.SystemMaintenanceSchedule: كائن الجدول الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك فترة صيانة متداخلة.
        BadRequestException: إذا كانت التواريخ غير صحيحة.
    """
    # 1. التحقق من أن تواريخ البدء والانتهاء صحيحة
    if schedule_in.start_timestamp >= schedule_in.end_timestamp:
        raise BadRequestException(detail="تاريخ بدء الصيانة يجب أن يكون قبل تاريخ انتهائها.")
    if schedule_in.end_timestamp <= datetime.now(timezone.utc):
        raise BadRequestException(detail="تاريخ انتهاء الصيانة يجب أن يكون في المستقبل.")

    # 2. التحقق من عدم تداخل المواعيد مع جداول صيانة موجودة ونشطة
    overlapping_schedules = db.query(models.SystemMaintenanceSchedule).filter(
        models.SystemMaintenanceSchedule.is_active == True,
        or_(
            and_(
                models.SystemMaintenanceSchedule.start_timestamp <= schedule_in.end_timestamp,
                models.SystemMaintenanceSchedule.end_timestamp >= schedule_in.start_timestamp
            ),
            # حالات التداخل الأخرى
        )
    ).first()
    if overlapping_schedules:
        raise ConflictException(detail="توجد فترة صيانة نشطة متداخلة مع الموعد المقترح.")
    
    # 3. التحقق من المستخدم الذي يقوم بالإنشاء
    user_exists = core_crud.get_user_by_id(db, current_user.user_id)
    if not user_exists: # لا ينبغي أن يحدث هذا إذا كان current_user قادماً من dependency
        raise NotFoundException(detail=f"المستخدم بمعرف {current_user.user_id} غير موجود.")

    return crud.create_system_maintenance_schedule(db=db, schedule_in=schedule_in)

def get_all_system_maintenance_schedules_service(
    db: Session,
    is_active: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.SystemMaintenanceSchedule]:
    """خدمة لجلب قائمة بجداول صيانة النظام، مع خيارات التصفية والترقيم."""
    return crud.get_all_system_maintenance_schedules(
        db=db,
        is_active=is_active,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

def get_system_maintenance_schedule_details(db: Session, maintenance_id: int) -> models.SystemMaintenanceSchedule:
    """
    خدمة لجلب جدول صيانة نظام واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        maintenance_id (int): معرف جدول الصيانة المطلوب.

    Returns:
        models.SystemMaintenanceSchedule: كائن الجدول.

    Raises:
        NotFoundException: إذا لم يتم العثور على جدول الصيانة.
    """
    db_schedule = crud.get_system_maintenance_schedule(db, maintenance_id=maintenance_id)
    if not db_schedule:
        raise NotFoundException(detail=f"جدول صيانة النظام بمعرف {maintenance_id} غير موجود.")
    return db_schedule

def update_system_maintenance_schedule_service(db: Session, maintenance_id: int, schedule_in: schemas.SystemMaintenanceScheduleUpdate, current_user: User) -> models.SystemMaintenanceSchedule:
    """
    خدمة لتحديث جدول صيانة نظام موجود.
    تتضمن التحقق من صلاحية المستخدم للتعديل، وتداخل المواعيد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        maintenance_id (int): معرف جدول الصيانة المراد تحديثه.
        schedule_in (schemas.SystemMaintenanceScheduleUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الذي يجري التحديث (يجب أن يكون مسؤولاً).

    Returns:
        models.SystemMaintenanceSchedule: كائن الجدول المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الجدول.
        BadRequestException: إذا كانت التواريخ غير صحيحة أو تداخلت المواعيد.
    """
    db_schedule = get_system_maintenance_schedule_details(db, maintenance_id) # استخدام دالة الخدمة للتحقق

    # 1. التحقق من تواريخ البدء والانتهاء إذا تم تحديثها
    if schedule_in.start_timestamp and schedule_in.end_timestamp:
        if schedule_in.start_timestamp >= schedule_in.end_timestamp:
            raise BadRequestException(detail="تاريخ بدء الصيانة يجب أن يكون قبل تاريخ انتهائها.")
        if schedule_in.end_timestamp <= datetime.now(timezone.utc) and schedule_in.is_active is True:
             raise BadRequestException(detail="لا يمكن تفعيل فترة صيانة تنتهي في الماضي.")
    
    # 2. التحقق من عدم تداخل المواعيد مع جداول صيانة أخرى (إذا تم تحديث التواريخ أو is_active)
    if (schedule_in.start_timestamp is not None or schedule_in.end_timestamp is not None or schedule_in.is_active is not None) and \
       (schedule_in.is_active is None or schedule_in.is_active is True): # إذا كان سيظل نشطاً أو سيتم تفعيله
        
        # استخدم القيم الجديدة إن وجدت، وإلا استخدم القيم الحالية
        start_ts = schedule_in.start_timestamp or db_schedule.start_timestamp
        end_ts = schedule_in.end_timestamp or db_schedule.end_timestamp

        overlapping_schedules = db.query(models.SystemMaintenanceSchedule).filter(
            models.SystemMaintenanceSchedule.is_active == True,
            models.SystemMaintenanceSchedule.maintenance_id != maintenance_id, # استبعاد الجدول الحالي
            and_(
                models.SystemMaintenanceSchedule.start_timestamp <= end_ts,
                models.SystemMaintenanceSchedule.end_timestamp >= start_ts
            )
        ).first()
        if overlapping_schedules:
            raise ConflictException(detail="توجد فترة صيانة نشطة أخرى متداخلة مع الموعد المقترح.")

    return crud.update_system_maintenance_schedule(db, db_schedule=db_schedule, schedule_in=schedule_in, updated_by_user_id=current_user.user_id)

def delete_system_maintenance_schedule_service(db: Session, maintenance_id: int, current_user: User):
    """
    خدمة لحذف جدول صيانة نظام (حذف صارم).
    تتضمن التحقق من صلاحيات المستخدم وعدم حذف جداول الصيانة النشطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        maintenance_id (int): معرف جدول الصيانة المراد حذفه.
        current_user (User): المستخدم الذي يقوم بالحذف (يجب أن يكون مسؤولاً).

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الجدول.
        BadRequestException: إذا كان جدول الصيانة نشطاً حالياً.
    """
    db_schedule = get_system_maintenance_schedule_details(db, maintenance_id) # استخدام دالة الخدمة للتحقق

    # TODO: التحقق من صلاحية المستخدم (ADMIN_MANAGE_SETTINGS)

    if db_schedule.is_active:
        raise BadRequestException(detail="لا يمكن حذف جدول صيانة نشط حالياً. يرجى إلغاء تفعيله أولاً.")
    
    # TODO: التحقق من أن فترة الصيانة قد انتهت (إذا لم تكن نشطة ولكنها لم تنته بعد)

    crud.delete_system_maintenance_schedule(db=db, db_schedule=db_schedule)
    return {"message": f"تم حذف جدول صيانة النظام بمعرف {maintenance_id} بنجاح."}