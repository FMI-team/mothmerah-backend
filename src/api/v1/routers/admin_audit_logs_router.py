# backend\src\api\v1\routers\admin_audit_logs_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional, Dict # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين
from datetime import datetime # لتصفية الوقت في السجلات

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي

# استيراد Schemas (هياكل البيانات)
from src.auditing.schemas import audit_schemas as schemas # لجميع Schemas Audit Logs Read
from src.lookups.schemas import lookups_schemas # لأنواع الأنشطة وأحداث الأمان (للفلاتر)

# استيراد الخدمات (منطق العمل)
from src.auditing.services import ( # لجميع خدمات Audit Logs
    system_audit_logs_service,
    user_activity_logs_service,
    search_logs_service,
    security_event_logs_service,
    data_change_audit_logs_service
)


# تعريف الراوتر لإدارة سجلات التدقيق والأنشطة من جانب المسؤولين.
router = APIRouter(
    prefix="/audit-logs", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /admin/audit-logs)
    tags=["Admin - Audit & Activity Logs"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.has_permission("ADMIN_VIEW_AUDIT_LOGS"))] # صلاحية عامة لعرض سجلات التدقيق
)

# ================================================================
# --- نقاط الوصول لسجلات تدقيق النظام (SystemAuditLog) ---
# ================================================================

@router.get(
    "/system",
    response_model=List[schemas.SystemAuditLogRead],
    summary="[Admin] جلب سجلات تدقيق النظام العامة",
    description="""
    يسمح للمسؤولين بجلب سجلات تدقيق النظام العامة، مع خيارات تصفية.
    """,
)
async def get_system_audit_logs_endpoint(
    db: Session = Depends(get_db),
    user_id: Optional[UUID] = None,
    event_type_id: Optional[int] = None, # من SystemEventType
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب سجلات تدقيق النظام."""
    return system_audit_logs_service.get_all_system_audit_logs_service(
        db=db,
        user_id=user_id,
        event_type_id=event_type_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

@router.get(
    "/system/{log_id}",
    response_model=schemas.SystemAuditLogRead,
    summary="[Admin] جلب تفاصيل سجل تدقيق نظام واحد",
)
async def get_system_audit_log_details_endpoint(log_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل سجل تدقيق نظام واحد بالـ ID الخاص به."""
    return system_audit_logs_service.get_system_audit_log_details(db=db, log_id=log_id)


# ================================================================
# --- نقاط الوصول لسجلات أنشطة المستخدمين (UserActivityLog) ---
# ================================================================

@router.get(
    "/user-activity",
    response_model=List[schemas.UserActivityLogRead],
    summary="[Admin] جلب سجلات أنشطة المستخدمين",
)
async def get_user_activity_logs_endpoint(
    db: Session = Depends(get_db),
    user_id: Optional[UUID] = None,
    activity_type_id: Optional[int] = None, # من ActivityType
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب سجلات أنشطة المستخدمين."""
    return user_activity_logs_service.get_all_user_activity_logs_service(
        db=db,
        user_id=user_id,
        activity_type_id=activity_type_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

@router.get(
    "/user-activity/{activity_log_id}",
    response_model=schemas.UserActivityLogRead,
    summary="[Admin] جلب تفاصيل سجل نشاط مستخدم واحد",
)
async def get_user_activity_log_details_endpoint(activity_log_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل سجل نشاط مستخدم واحد بالـ ID الخاص به."""
    return user_activity_logs_service.get_user_activity_log_details(db=db, activity_log_id=activity_log_id)


# ================================================================
# --- نقاط الوصول لسجلات البحث (SearchLog) ---
# ================================================================

@router.get(
    "/search",
    response_model=List[schemas.SearchLogRead],
    summary="[Admin] جلب سجلات البحث",
)
async def get_search_logs_endpoint(
    db: Session = Depends(get_db),
    user_id: Optional[UUID] = None,
    search_query: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب سجلات البحث."""
    return search_logs_service.get_all_search_logs_service(
        db=db,
        user_id=user_id,
        search_query=search_query,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

@router.get(
    "/search/{search_log_id}",
    response_model=schemas.SearchLogRead,
    summary="[Admin] جلب تفاصيل سجل بحث واحد",
)
async def get_search_log_details_endpoint(search_log_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل سجل بحث واحد بالـ ID الخاص به."""
    return search_logs_service.get_search_log_details(db=db, search_log_id=search_log_id)


# ================================================================
# --- نقاط الوصول لسجلات أحداث الأمان (SecurityEventLog) ---
# ================================================================

@router.get(
    "/security",
    response_model=List[schemas.SecurityEventLogRead],
    summary="[Admin] جلب سجلات أحداث الأمان",
)
async def get_security_event_logs_endpoint(
    db: Session = Depends(get_db),
    user_id: Optional[UUID] = None,
    event_type_id: Optional[int] = None, # من SecurityEventType
    severity_level: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب سجلات أحداث الأمان."""
    return security_event_logs_service.get_all_security_event_logs_service(
        db=db,
        user_id=user_id,
        event_type_id=event_type_id,
        severity_level=severity_level,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

@router.get(
    "/security/{security_event_id}",
    response_model=schemas.SecurityEventLogRead,
    summary="[Admin] جلب تفاصيل سجل حدث أمان واحد",
)
async def get_security_event_log_details_endpoint(security_event_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل سجل حدث أمان واحد بالـ ID الخاص به."""
    return security_event_logs_service.get_security_event_log_details(db=db, security_event_id=security_event_id)


# ================================================================
# --- نقاط الوصول لسجلات تدقيق تغييرات البيانات (DataChangeAuditLog) ---
# ================================================================

@router.get(
    "/data-changes",
    response_model=List[schemas.DataChangeAuditLogRead],
    summary="[Admin] جلب سجلات تدقيق تغييرات البيانات",
)
async def get_data_change_audit_logs_endpoint(
    db: Session = Depends(get_db),
    changed_by_user_id: Optional[UUID] = None,
    table_name: Optional[str] = None,
    record_id: Optional[str] = None,
    action_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب سجلات تدقيق تغييرات البيانات."""
    return data_change_audit_logs_service.get_all_data_change_audit_logs_service(
        db=db,
        changed_by_user_id=changed_by_user_id,
        table_name=table_name,
        record_id=record_id,
        action_type=action_type,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

@router.get(
    "/data-changes/{change_log_id}",
    response_model=schemas.DataChangeAuditLogRead,
    summary="[Admin] جلب تفاصيل سجل تدقيق تغيير بيانات واحد",
)
async def get_data_change_audit_log_details_endpoint(change_log_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل سجل تدقيق تغيير بيانات واحد بالـ ID الخاص به."""
    return data_change_audit_logs_service.get_data_change_audit_log_details(db=db, change_log_id=change_log_id)