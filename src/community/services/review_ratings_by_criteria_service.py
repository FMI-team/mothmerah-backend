# backend\src\community\services\review_ratings_by_criteria_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID # إذا تم استخدام user_id
from datetime import datetime, timezone

# استيراد المودلز
from src.community.models import reviews_models as models # ReviewRatingByCriterion
# استيراد الـ CRUD
from src.community.crud import review_ratings_by_criteria_crud as crud
from src.community.crud import reviews_crud # للتحقق من وجود المراجعة (Review)
from src.lookups.crud import review_criteria_crud # للتحقق من وجود معيار التقييم (ReviewCriterion)

# استيراد Schemas
from src.community.schemas import reviews_schemas as schemas # ReviewRatingByCriterion

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for ReviewRatingByCriterion ---
# ==========================================================

def create_new_review_rating_by_criterion(db: Session, rating_in: schemas.ReviewRatingByCriterionCreate, current_user: Optional[User] = None) -> models.ReviewRatingByCriterion:
    """
    خدمة لإنشاء تقييم جديد لمراجعة حسب معيار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rating_in (schemas.ReviewRatingByCriterionCreate): بيانات التقييم للإنشاء.
        current_user (Optional[User]): المستخدم الحالي الذي يقدم التقييم (يمكن أن يكون None إذا كانت مراجعة داخلية).

    Returns:
        models.ReviewRatingByCriterion: كائن التقييم الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المراجعة الأم أو المعيار.
        ForbiddenException: إذا كان المستخدم غير مصرح له (إذا كان هناك تحقق ملكية).
        ConflictException: إذا كان هناك تقييم موجود بالفعل لنفس المراجعة والمعيار.
    """
    # 1. التحقق من وجود المراجعة الأم
    # TODO: يجب استخدام get_review_details من reviews_service
    db_review = reviews_crud.get_review(db, review_id=rating_in.review_id)
    if not db_review:
        raise NotFoundException(detail=f"المراجعة بمعرف {rating_in.review_id} غير موجودة.")
    
    # 2. التحقق من وجود المعيار
    db_criterion = review_criteria_crud.get_review_criterion(db, criteria_id=rating_in.criteria_id)
    if not db_criterion:
        raise NotFoundException(detail=f"معيار التقييم بمعرف {rating_in.criteria_id} غير موجود.")

    # 3. التحقق من أن المستخدم هو صاحب المراجعة أو مسؤول (إذا كان التقييم يضاف لاحقاً)
    #    بالنسبة لهذا الجدول، عادة ما يتم إنشاء التقييمات حسب المعايير كجزء من عملية إنشاء المراجعة الأصلية.
    #    لذلك، يجب أن يكون المستخدم الحالي هو المراجع الأصلي.
    #    if current_user and db_review.reviewer_user_id != current_user.user_id:
    #        raise ForbiddenException(detail="غير مصرح لك بإضافة تقييم لهذا المعيار لهذه المراجعة.")
    #    TODO: التحقق من وجود صلاحية ADMIN_REVIEW_MANAGE_ANY للمسؤولين.

    # 4. التحقق من عدم وجود تقييم موجود لنفس المراجعة والمعيار
    existing_rating = crud.get_review_rating_by_criterion(db, review_id=rating_in.review_id, criteria_id=rating_in.criteria_id)
    if existing_rating:
        raise ConflictException(detail=f"يوجد تقييم بالفعل للمراجعة {rating_in.review_id} ومعيار {rating_in.criteria_id}.")

    return crud.create_review_rating_by_criterion(db=db, rating_in=rating_in)


def get_review_rating_by_criterion_details_service(db: Session, rating_by_criteria_id: int, current_user: Optional[User] = None) -> models.ReviewRatingByCriterion:
    """
    خدمة لجلب تفاصيل تقييم مراجعة حسب معيار واحد بالـ ID الخاص به.
    """
    db_rating = crud.get_review_rating_by_criterion(db, rating_by_criteria_id=rating_by_criteria_id)
    if not db_rating:
        raise NotFoundException(detail=f"تقييم المراجعة بمعرف {rating_by_criteria_id} غير موجود.")
    
    # الصلاحيات تعتمد على صلاحيات المراجعة الأم
    # TODO: يجب استخدام get_review_details من reviews_service
    # reviews_service.get_review_details(db, db_rating.review_id, current_user)

    return db_rating


def get_all_review_ratings_by_criterion_service(
    db: Session,
    review_id: Optional[int] = None,
    criteria_id: Optional[int] = None,
    min_rating_value: Optional[int] = None,
    max_rating_value: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ReviewRatingByCriterion]:
    """خدمة لجلب قائمة بتقييمات المراجعة حسب المعايير، مع خيارات التصفية والترقيم."""
    # TODO: يجب إضافة تحقق صلاحية المسؤول ADMIN_REVIEW_VIEW_ANY هنا أو في نقطة الوصول
    return crud.get_all_review_ratings_by_criterion(
        db=db,
        review_id=review_id,
        criteria_id=criteria_id,
        min_rating_value=min_rating_value,
        max_rating_value=max_rating_value,
        skip=skip,
        limit=limit
    )

def update_review_rating_by_criterion_service(db: Session, rating_by_criteria_id: int, rating_in: schemas.ReviewRatingByCriterionUpdate, current_user: User) -> models.ReviewRatingByCriterion:
    """
    خدمة لتحديث تقييم مراجعة حسب معيار موجود.
    تتضمن التحقق من الصلاحيات (مالك المراجعة أو مسؤول).

    Args:
        db (Session): جلسة قاعدة البيانات.
        rating_by_criteria_id (int): معرف التقييم المراد تحديثه.
        rating_in (schemas.ReviewRatingByCriterionUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models.ReviewRatingByCriterion: كائن التقييم المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على التقييم.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بتحديث التقييم.
        BadRequestException: إذا كانت البيانات غير صالحة.
    """
    db_rating = get_review_rating_by_criterion_details_service(db, rating_by_criteria_id, current_user) # يتحقق من الوجود والصلاحية

    # التحقق من أن المستخدم هو المراجع الأصلي أو مسؤول
    # TODO: يجب استخدام get_review_details من reviews_service للحصول على المراجع الأصلي
    # review_obj = reviews_service.get_review_details(db, db_rating.review_id, current_user)
    # is_reviewer = review_obj.reviewer_user_id == current_user.user_id
    # is_admin = any(p.permission_name_key == "ADMIN_REVIEW_MANAGE_ANY" for p in current_user.default_role.permissions)
    # if not (is_reviewer or is_admin):
    #     raise ForbiddenException(detail="غير مصرح لك بتحديث هذا التقييم.")

    return crud.update_review_rating_by_criterion(db=db, db_rating=db_rating, rating_in=rating_in)

def delete_review_rating_by_criterion_service(db: Session, rating_by_criteria_id: int, current_user: User) -> Dict[str, str]:
    """
    خدمة لحذف تقييم مراجعة حسب معيار (حذف صارم).
    تتضمن التحقق من الصلاحيات (مالك المراجعة أو مسؤول).

    Args:
        db (Session): جلسة قاعدة البيانات.
        rating_by_criteria_id (int): معرف التقييم المراد حذفه.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على التقييم.
        ForbiddenException: إذا كان المستخدم غير مصرح له بالحذف.
    """
    db_rating = get_review_rating_by_criterion_details_service(db, rating_by_criteria_id, current_user) # يتحقق من الوجود والصلاحية

    # التحقق من صلاحية المستخدم للحذف
    # TODO: نفس التحقق من الصلاحية في update_review_rating_by_criterion_service
    # reviews_service.get_review_details(db, db_rating.review_id, current_user)

    crud.delete_review_rating_by_criterion(db=db, db_rating=db_rating)
    return {"message": f"تم حذف تقييم المراجعة بمعرف {rating_by_criteria_id} بنجاح."}