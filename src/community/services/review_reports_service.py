# backend\src\community\services\review_reports_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

# استيراد المودلز
from src.community.models import reviews_models as models # ReviewReport
# استيراد الـ CRUD
from src.community.crud import review_reports_crud as crud
from src.community.crud import reviews_crud # للتحقق من وجود المراجعة (Review)
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)
from src.lookups.crud import review_report_reasons_crud # للتحقق من وجود سبب الإبلاغ

# استيراد Schemas
from src.community.schemas import reviews_schemas as schemas # ReviewReport

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for ReviewReport ---
# ==========================================================

def create_new_review_report(db: Session, report_in: schemas.ReviewReportCreate, current_user: User) -> models.ReviewReport:
    """
    خدمة لإنشاء بلاغ جديد عن مراجعة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        report_in (schemas.ReviewReportCreate): بيانات البلاغ للإنشاء.
        current_user (User): المستخدم الحالي الذي يقدم البلاغ.

    Returns:
        models.ReviewReport: كائن البلاغ الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المراجعة المبلغ عنها أو المستخدم أو سبب البلاغ.
        ForbiddenException: إذا كان المستخدم غير مصرح له بتقديم بلاغ (مثلاً، إذا كان هو المراجع نفسه).
        ConflictException: إذا كان هناك بلاغ موجود بالفعل على نفس المراجعة من نفس المستخدم.
    """
    # 1. التحقق من وجود المراجعة المبلغ عنها
    db_review = reviews_crud.get_review(db, review_id=report_in.review_id)
    if not db_review:
        raise NotFoundException(detail=f"المراجعة بمعرف {report_in.review_id} المبلغ عنها غير موجودة.")
    
    # 2. التحقق من أن المستخدم ليس هو المراجع نفسه (عادة لا يُسمح بذلك)
    if db_review.reviewer_user_id == current_user.user_id:
        raise BadRequestException(detail="لا يمكنك الإبلاغ عن مراجعتك الخاصة.")

    # 3. التحقق من وجود سبب الإبلاغ (إذا تم تحديده)
    if report_in.report_reason_id:
        reason_obj = review_report_reasons_crud.get_review_report_reason(db, reason_id=report_in.report_reason_id)
        if not reason_obj:
            raise NotFoundException(detail=f"سبب الإبلاغ بمعرف {report_in.report_reason_id} غير موجود.")
    
    # 4. التحقق من عدم وجود بلاغ مكرر من نفس المستخدم لنفس المراجعة
    existing_report = crud.get_all_review_reports(db, review_id=report_in.review_id, reporter_user_id=current_user.user_id)
    if existing_report:
        raise ConflictException(detail="لقد قمت بتقديم بلاغ بالفعل على هذه المراجعة.")

    # 5. تعيين المستخدم الذي قام بالبلاغ
    report_in.reporter_user_id = current_user.user_id

    return crud.create_review_report(db=db, report_in=report_in)

def get_review_report_details_service(db: Session, report_id: int, current_user: Optional[User] = None) -> models.ReviewReport:
    """
    خدمة لجلب تفاصيل بلاغ عن مراجعة واحد بالـ ID الخاص به.
    يمكن للمسؤولين فقط رؤية تفاصيل البلاغات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        report_id (int): معرف البلاغ المطلوب.
        current_user (Optional[User]): المستخدم الحالي.

    Returns:
        models.ReviewReport: كائن البلاغ.

    Raises:
        NotFoundException: إذا لم يتم العثور على البلاغ.
        ForbiddenException: إذا لم يكن المستخدم مصرح له برؤية البلاغ.
    """
    db_report = crud.get_review_report(db, report_id=report_id)
    if not db_report:
        raise NotFoundException(detail=f"البلاغ بمعرف {report_id} غير موجود.")
    
    # التحقق من صلاحيات العرض (فقط المسؤولين يمكنهم رؤية البلاغات)
    is_admin = current_user and any(p.permission_name_key == "ADMIN_REVIEW_VIEW_ANY" for p in current_user.default_role.permissions)

    if not is_admin:
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل هذا البلاغ عن المراجعة.")
    
    return db_report

def get_all_review_reports_service(
    db: Session,
    review_id: Optional[int] = None,
    reporter_user_id: Optional[UUID] = None,
    report_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ReviewReport]:
    """
    خدمة لجلب جميع بلاغات المراجعات، مع خيارات للتصفية والترقيم.
    تُستخدم للمسؤولين فقط.
    """
    # TODO: يجب إضافة تحقق صلاحية المسؤول ADMIN_REVIEW_VIEW_ANY هنا أو في نقطة الوصول
    return crud.get_all_review_reports(
        db=db,
        review_id=review_id,
        reporter_user_id=reporter_user_id,
        report_status=report_status,
        skip=skip,
        limit=limit
    )

def update_review_report_service(db: Session, report_id: int, report_in: schemas.ReviewReportUpdate, current_user: User) -> models.ReviewReport:
    """
    خدمة لتحديث بلاغ عن مراجعة موجود.
    تتضمن التحقق من الصلاحيات (المسؤولين فقط).

    Args:
        db (Session): جلسة قاعدة البيانات.
        report_id (int): معرف البلاغ المراد تحديثه.
        report_in (schemas.ReviewReportUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي (يجب أن يكون مسؤولاً).

    Returns:
        models.ReviewReport: كائن البلاغ المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على البلاغ.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بتحديث البلاغ.
        BadRequestException: إذا كانت البيانات غير صالحة.
    """
    db_report = get_review_report_details_service(db, report_id, current_user) # يتحقق من الوجود والصلاحية

    # 1. التحقق من صلاحية المستخدم (المسؤول فقط)
    is_admin = any(p.permission_name_key == "ADMIN_REVIEW_MANAGE_ANY" for p in current_user.default_role.permissions)
    if not is_admin:
        raise ForbiddenException(detail="غير مصرح لك بتحديث هذا البلاغ.")
    
    # 2. إذا تم تغيير الحالة إلى 'تم الحل' أو 'تم الرفض'، قم بتعيين resolved_by_user_id و resolved_timestamp
    if report_in.report_status in ["RESOLVED", "DISMISSED"] and not db_report.resolved_timestamp:
        report_in.resolved_by_user_id = current_user.user_id
        report_in.resolved_timestamp = datetime.now(timezone.utc)

    # 3. TODO: إضافة منطق عمل إضافي هنا، مثلاً:
    #    - إذا تم حل البلاغ (RESOLVED)، قم بتغيير حالة المراجعة الأصلية (review) إذا لزم الأمر.
    #    - إرسال إشعارات للمراجع والمبلغ (وحدة الإشعارات).

    return crud.update_review_report(db=db, db_report=db_report, report_in=report_in, resolved_by_user_id=current_user.user_id)


def delete_review_report_service(db: Session, report_id: int, current_user: User) -> Dict[str, str]:
    """
    خدمة لحذف بلاغ عن مراجعة (حذف صارم).
    تتضمن التحقق من صلاحيات المستخدم (المسؤولين فقط).

    Args:
        db (Session): جلسة قاعدة البيانات.
        report_id (int): معرف البلاغ المراد حذفه.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على البلاغ.
        ForbiddenException: إذا كان المستخدم غير مصرح له بحذف البلاغ.
    """
    db_report = get_review_report_details_service(db, report_id, current_user) # يتحقق من الوجود والصلاحية

    # 1. التحقق من صلاحية المستخدم (المسؤول فقط)
    is_admin = any(p.permission_name_key == "ADMIN_REVIEW_MANAGE_ANY" for p in current_user.default_role.permissions)
    if not is_admin:
        raise ForbiddenException(detail="غير مصرح لك بحذف هذا البلاغ.")
    
    # TODO: التحقق من أن البلاغ ليس في حالة "قيد المراجعة" إذا كانت هذه سياسة.

    crud.delete_review_report(db=db, db_report=db_report)
    return {"message": f"تم حذف البلاغ بمعرف {report_id} بنجاح."}