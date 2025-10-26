# backend\src\auditing\crud\search_logs_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.auditing.models import logs_models as models # SearchLog
# استيراد Schemas (لـ type hinting في Create)
from src.auditing.schemas import audit_schemas as schemas


# ==========================================================
# --- CRUD Functions for SearchLog ---
# ==========================================================

def create_search_log(db: Session, log_in: schemas.SearchLogCreate) -> models.SearchLog:
    """
    ينشئ سجلاً جديداً في جدول سجلات البحث.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_in (schemas.SearchLogCreate): بيانات السجل للإنشاء.

    Returns:
        models.SearchLog: كائن السجل الذي تم إنشاؤه.
    """
    db_log = models.SearchLog(
        user_id=log_in.user_id,
        session_id=log_in.session_id,
        search_query=log_in.search_query,
        # search_timestamp سيتم تعيينه افتراضياً في المودل
        number_of_results_returned=log_in.number_of_results_returned,
        filters_applied=log_in.filters_applied,
        clicked_result_entity_type=log_in.clicked_result_entity_type,
        clicked_result_entity_id=log_in.clicked_result_entity_id,
        ip_address=log_in.ip_address # تم إضافة ip_address
        # user_agent (غير موجود في المودل الحالي)
    )
    db.add(db_log)
    db.commit() # السجلات يتم حفظها فوراً
    db.refresh(db_log)
    return db_log

def get_search_log(db: Session, search_log_id: int) -> Optional[models.SearchLog]:
    """
    يجلب سجل بحث واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        search_log_id (int): معرف السجل المطلوب.

    Returns:
        Optional[models.SearchLog]: كائن السجل أو None.
    """
    return db.query(models.SearchLog).options(
        joinedload(models.SearchLog.user),
        joinedload(models.SearchLog.session) # إذا كان موجوداً
    ).filter(models.SearchLog.search_log_id == search_log_id).first()

def get_all_search_logs(
    db: Session,
    user_id: Optional[UUID] = None,
    search_query: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.SearchLog]:
    """
    يجلب قائمة بسجلات البحث، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (Optional[UUID]): تصفية حسب معرف المستخدم.
        search_query (Optional[str]): تصفية حسب نص استعلام البحث (جزئي).
        start_time (Optional[datetime]): تصفية حسب وقت البحث (البدء).
        end_time (Optional[datetime]): تصفية حسب وقت البحث (الانتهاء).
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.SearchLog]: قائمة بكائنات السجلات.
    """
    query = db.query(models.SearchLog).options(
        joinedload(models.SearchLog.user),
        joinedload(models.SearchLog.session)
    )
    if user_id:
        query = query.filter(models.SearchLog.user_id == user_id)
    if search_query:
        query = query.filter(models.SearchLog.search_query.ilike(f"%{search_query}%"))
    if start_time:
        query = query.filter(models.SearchLog.search_timestamp >= start_time)
    if end_time:
        query = query.filter(models.SearchLog.search_timestamp <= end_time)
    
    return query.order_by(models.SearchLog.search_timestamp.desc()).offset(skip).limit(limit).all()

# لا يوجد تحديث أو حذف مباشر لـ SearchLog لأنه جدول سجلات تاريخية.