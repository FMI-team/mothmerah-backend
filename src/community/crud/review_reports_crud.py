# backend\src\community\crud\review_reports_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

# استيراد المودلز
from src.community.models import reviews_models as models # ReviewReport
# استيراد Schemas (لـ type hinting في Create/Update)
from src.community.schemas import reviews_schemas as schemas


# ==========================================================
# --- CRUD Functions for ReviewReport ---
# ==========================================================

def create_review_report(db: Session, report_in: schemas.ReviewReportCreate) -> models.ReviewReport:
    """
    ينشئ سجلاً جديداً للإبلاغ عن مراجعة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        report_in (schemas.ReviewReportCreate): بيانات البلاغ للإنشاء.

    Returns:
        models.ReviewReport: كائن البلاغ الذي تم إنشاؤه.
    """
    db_report = models.ReviewReport(
        review_id=report_in.review_id,
        reporter_user_id=report_in.reporter_user_id,
        report_reason_id=report_in.report_reason_id,
        custom_report_reason=report_in.custom_report_reason,
        report_status=report_in.report_status,
        action_taken=report_in.action_taken,
        resolved_by_user_id=report_in.resolved_by_user_id,
        resolved_timestamp=report_in.resolved_timestamp
        # report_timestamp, created_at, updated_at تدار تلقائياً
    )
    db.add(db_report)
    db.commit() # السجلات يتم حفظها فوراً
    db.refresh(db_report)
    return db_report

def get_review_report(db: Session, report_id: int) -> Optional[models.ReviewReport]:
    """
    يجلب سجل إبلاغ عن مراجعة بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        report_id (int): معرف البلاغ المطلوب.

    Returns:
        Optional[models.ReviewReport]: كائن البلاغ أو None.
    """
    return db.query(models.ReviewReport).options(
        joinedload(models.ReviewReport.review),
        joinedload(models.ReviewReport.reporter_user),
        joinedload(models.ReviewReport.report_reason),
        joinedload(models.ReviewReport.resolved_by_user)
    ).filter(models.ReviewReport.report_id == report_id).first()

def get_all_review_reports(
    db: Session,
    review_id: Optional[int] = None,
    reporter_user_id: Optional[UUID] = None,
    report_reason_id: Optional[int] = None,
    report_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ReviewReport]:
    """
    يجلب قائمة بسجلات الإبلاغ عن المراجعات، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        review_id (Optional[int]): تصفية حسب معرف المراجعة المبلغ عنها.
        reporter_user_id (Optional[UUID]): تصفية حسب معرف المستخدم الذي قدم البلاغ.
        report_reason_id (Optional[int]): تصفية حسب معرف سبب الإبلاغ.
        report_status (Optional[str]): تصفية حسب حالة معالجة البلاغ.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.ReviewReport]: قائمة بكائنات البلاغات.
    """
    query = db.query(models.ReviewReport).options(
        joinedload(models.ReviewReport.review),
        joinedload(models.ReviewReport.reporter_user),
        joinedload(models.ReviewReport.report_reason),
        joinedload(models.ReviewReport.resolved_by_user)
    )
    if review_id:
        query = query.filter(models.ReviewReport.review_id == review_id)
    if reporter_user_id:
        query = query.filter(models.ReviewReport.reporter_user_id == reporter_user_id)
    if report_reason_id:
        query = query.filter(models.ReviewReport.report_reason_id == report_reason_id)
    if report_status:
        query = query.filter(models.ReviewReport.report_status == report_status)
    
    return query.order_by(models.ReviewReport.report_timestamp.desc()).offset(skip).limit(limit).all()

def update_review_report(db: Session, db_report: models.ReviewReport, report_in: schemas.ReviewReportUpdate, resolved_by_user_id: Optional[UUID] = None) -> models.ReviewReport:
    """
    يحدث بيانات سجل إبلاغ عن مراجعة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_report (models.ReviewReport): كائن البلاغ من قاعدة البيانات.
        report_in (schemas.ReviewReportUpdate): البيانات المراد تحديثها.
        resolved_by_user_id (Optional[UUID]): معرف المستخدم الذي حل البلاغ.

    Returns:
        models.ReviewReport: كائن البلاغ المحدث.
    """
    update_data = report_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_report, key, value)
    
    db_report.updated_at = datetime.now(timezone.utc)
    # إذا تم تغيير الحالة إلى "حلّت" أو "تم رفضها"، قم بتعيين resolved_by_user_id و resolved_timestamp
    if 'report_status' in update_data and update_data['report_status'] in ["RESOLVED", "DISMISSED"]: # TODO: تأكد من مفاتيح الحالات
        db_report.resolved_by_user_id = resolved_by_user_id
        db_report.resolved_timestamp = datetime.now(timezone.utc)

    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# لا يوجد حذف مباشر لـ ReviewReport لأنه جدول سجلات تاريخية.