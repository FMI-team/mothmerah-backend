# backend\src\auditing\services\search_logs_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # SearchLog
# استيراد الـ CRUD
from src.auditing.crud import search_logs_crud as crud
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)
from src.users.crud import security_crud # للتحقق من وجود الجلسة (UserSession)

# استيراد Schemas
from src.auditing.schemas import audit_schemas as schemas # SearchLog

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for SearchLog ---
# ==========================================================

def create_search_log_service(db: Session, log_in: schemas.SearchLogCreate) -> models.SearchLog:
    """
    خدمة لإنشاء سجل جديد في جدول سجلات البحث.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.SearchLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.SearchLog: كائن السجل الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم المرتبط أو الجلسة.
    """
    # 1. التحقق من وجود المستخدم (إذا كان user_id موجوداً)
    if log_in.user_id:
        user_exists = core_crud.get_user_by_id(db, log_in.user_id)
        if not user_exists:
            raise NotFoundException(detail=f"المستخدم بمعرف {log_in.user_id} المرتبط بسجل البحث غير موجود.")
    
    # 2. التحقق من وجود الجلسة (إذا كان session_id موجوداً)
    if log_in.session_id:
        session_exists = security_crud.get_user_session_by_id(db, log_in.session_id)
        if not session_exists:
            raise NotFoundException(detail=f"الجلسة بمعرف {log_in.session_id} المرتبطة بسجل البحث غير موجودة.")

    return crud.create_search_log(db=db, log_in=log_in)

def get_search_log_details(db: Session, search_log_id: int) -> models.SearchLog:
    """
    خدمة لجلب سجل بحث واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        search_log_id (int): معرف السجل المطلوب.

    Returns:
        models.SearchLog: كائن السجل.

    Raises:
        NotFoundException: إذا لم يتم العثور على السجل.
    """
    db_log = crud.get_search_log(db, search_log_id=search_log_id)
    if not db_log:
        raise NotFoundException(detail=f"سجل البحث بمعرف {search_log_id} غير موجود.")
    return db_log

def get_all_search_logs_service(
    db: Session,
    user_id: Optional[UUID] = None,
    search_query: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.SearchLog]:
    """
    خدمة لجلب قائمة بسجلات البحث، مع خيارات التصفية والترقيم.
    """
    return crud.get_all_search_logs(
        db=db,
        user_id=user_id,
        search_query=search_query,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

# لا توجد خدمات للتحديث أو الحذف المباشر لـ SearchLog.