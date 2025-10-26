# backend\src\auditing\services\user_activity_logs_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # UserActivityLog
# استيراد الـ CRUD
from src.auditing.crud import user_activity_logs_crud as crud
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)
from src.users.crud import security_crud # للتحقق من وجود الجلسة (UserSession)
from src.lookups.crud import activity_types_crud # للتحقق من وجود نوع النشاط (ActivityType)
from src.lookups.crud import entity_types_crud # للتحقق من وجود نوع الكيان (EntityTypeForReviewOrImage)

# استيراد Schemas
from src.auditing.schemas import audit_schemas as schemas # UserActivityLog

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for UserActivityLog ---
# ==========================================================

def create_user_activity_log_service(db: Session, log_in: schemas.UserActivityLogCreate) -> models.UserActivityLog:
    """
    خدمة لإنشاء سجل جديد في جدول سجلات أنشطة المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.UserActivityLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.UserActivityLog: كائن السجل الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم المرتبط أو نوع النشاط أو الجلسة.
    """
    # 1. التحقق من وجود المستخدم
    user_exists = core_crud.get_user_by_id(db, log_in.user_id)
    if not user_exists:
        raise NotFoundException(detail=f"المستخدم بمعرف {log_in.user_id} المرتبط بسجل النشاط غير موجود.")
    
    # 2. التحقق من وجود نوع النشاط
    activity_type_exists = activity_types_crud.get_activity_type(db, log_in.activity_type_id)
    if not activity_type_exists:
        raise NotFoundException(detail=f"نوع النشاط بمعرف {log_in.activity_type_id} لسجل النشاط غير موجود.")

    # 3. التحقق من وجود الجلسة (إذا كان session_id موجوداً)
    if log_in.session_id:
        session_exists = security_crud.get_user_session_by_id(db, log_in.session_id)
        if not session_exists:
            raise NotFoundException(detail=f"الجلسة بمعرف {log_in.session_id} المرتبطة بسجل النشاط غير موجودة.")
    
    # 4. TODO: التحقق من وجود entity_type إذا كان موجوداً
    # if log_in.entity_type:
    #     entity_type_obj = entity_types_crud.get_entity_type(db, log_in.entity_type)
    #     if not entity_type_obj:
    #         raise NotFoundException(detail=f"نوع الكيان '{log_in.entity_type}' لسجل النشاط غير موجود.")


    return crud.create_user_activity_log(db=db, log_in=log_in)

def get_user_activity_log_details(db: Session, activity_log_id: int) -> models.UserActivityLog:
    """
    خدمة لجلب سجل نشاط مستخدم واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        activity_log_id (int): معرف السجل المطلوب.

    Returns:
        models.UserActivityLog: كائن السجل.

    Raises:
        NotFoundException: إذا لم يتم العثور على السجل.
    """
    db_log = crud.get_user_activity_log(db, activity_log_id=activity_log_id)
    if not db_log:
        raise NotFoundException(detail=f"سجل نشاط المستخدم بمعرف {activity_log_id} غير موجود.")
    return db_log

def get_all_user_activity_logs_service(
    db: Session,
    user_id: Optional[UUID] = None,
    activity_type_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.UserActivityLog]:
    """
    خدمة لجلب قائمة بسجلات أنشطة المستخدمين، مع خيارات التصفية والترقيم.
    """
    return crud.get_all_user_activity_logs(
        db=db,
        user_id=user_id,
        activity_type_id=activity_type_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

# لا توجد خدمات للتحديث أو الحذف المباشر لـ UserActivityLog.