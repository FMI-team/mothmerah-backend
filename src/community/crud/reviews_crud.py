# backend\src\community\crud\reviews_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.community.models import reviews_models as models # Review
# استيراد Schemas (لـ type hinting في Create/Update)
from src.community.schemas import reviews_schemas as schemas


# ==========================================================
# --- CRUD Functions for Review ---
# ==========================================================

def create_review(db: Session, review_in: schemas.ReviewCreate, reviewer_user_id: UUID, review_status_id: int) -> models.Review:
    """
    ينشئ مراجعة وتقييم جديدين في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        review_in (schemas.ReviewCreate): بيانات المراجعة للإنشاء.
        reviewer_user_id (UUID): معرف المستخدم الذي قدم المراجعة.
        review_status_id (int): معرف الحالة الأولية للمراجعة.

    Returns:
        models.Review: كائن المراجعة الذي تم إنشاؤه.
    """
    db_review = models.Review(
        reviewer_user_id=reviewer_user_id,
        reviewed_entity_id=review_in.reviewed_entity_id,
        reviewed_entity_type=review_in.reviewed_entity_type,
        related_order_id=review_in.related_order_id,
        rating_overall=review_in.rating_overall,
        review_title=review_in.review_title,
        review_text=review_in.review_text,
        review_status_id=review_status_id,
        # submission_timestamp, created_at, updated_at تدار تلقائياً
    )
    db.add(db_review)
    db.commit() # السجلات يتم حفظها فوراً
    db.refresh(db_review)
    return db_review

def get_review(db: Session, review_id: int) -> Optional[models.Review]:
    """
    يجلب مراجعة واحدة بالـ ID الخاص بها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        review_id (int): معرف المراجعة المطلوب.

    Returns:
        Optional[models.Review]: كائن المراجعة أو None.
    """
    return db.query(models.Review).options(
        joinedload(models.Review.reviewer_user),
        joinedload(models.Review.review_status),
        joinedload(models.Review.reviewed_entity_type_obj),
        joinedload(models.Review.related_order)
    ).filter(models.Review.review_id == review_id).first()

def get_all_reviews(
    db: Session,
    reviewer_user_id: Optional[UUID] = None,
    reviewed_entity_id: Optional[str] = None,
    reviewed_entity_type: Optional[str] = None,
    review_status_id: Optional[int] = None,
    rating_overall: Optional[int] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Review]:
    """
    يجلب قائمة بالمراجعات، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        reviewer_user_id (Optional[UUID]): تصفية حسب معرف المستخدم المراجع.
        reviewed_entity_id (Optional[str]): تصفية حسب معرف الكيان المُقيَّم.
        reviewed_entity_type (Optional[str]): تصفية حسب نوع الكيان المُقيَّم.
        review_status_id (Optional[int]): تصفية حسب حالة المراجعة.
        rating_overall (Optional[int]): تصفية حسب تقييم محدد.
        min_rating (Optional[int]): تصفية حسب الحد الأدنى للتقييم.
        max_rating (Optional[int]): تصفية حسب الحد الأقصى للتقييم.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.Review]: قائمة بكائنات المراجعات.
    """
    query = db.query(models.Review).options(
        joinedload(models.Review.reviewer_user),
        joinedload(models.Review.review_status),
        joinedload(models.Review.reviewed_entity_type_obj),
        joinedload(models.Review.related_order)
    )
    if reviewer_user_id:
        query = query.filter(models.Review.reviewer_user_id == reviewer_user_id)
    if reviewed_entity_id:
        query = query.filter(models.Review.reviewed_entity_id == reviewed_entity_id)
    if reviewed_entity_type:
        query = query.filter(models.Review.reviewed_entity_type == reviewed_entity_type)
    if review_status_id:
        query = query.filter(models.Review.review_status_id == review_status_id)
    if rating_overall:
        query = query.filter(models.Review.rating_overall == rating_overall)
    if min_rating:
        query = query.filter(models.Review.rating_overall >= min_rating)
    if max_rating:
        query = query.filter(models.Review.rating_overall <= max_rating)
    
    return query.order_by(models.Review.submission_timestamp.desc()).offset(skip).limit(limit).all()

def update_review(db: Session, db_review: models.Review, review_in: schemas.ReviewUpdate) -> models.Review:
    """
    يحدث بيانات مراجعة موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_review (models.Review): كائن المراجعة من قاعدة البيانات.
        review_in (schemas.ReviewUpdate): البيانات المراد تحديثها.

    Returns:
        models.Review: كائن المراجعة المحدث.
    """
    update_data = review_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_review, key, value)
    
    db_review.updated_at = datetime.now(timezone.utc)
    # إذا تم تغيير الحالة إلى "منشورة"، يتم تحديث publication_timestamp
    if 'review_status_id' in update_data and update_data['review_status_id'] == db.query(models.ReviewStatus).filter(models.ReviewStatus.status_name_key == "PUBLISHED").first().status_id: # TODO: يجب استيراد ReviewStatus
        db_review.publication_timestamp = datetime.now(timezone.utc)

    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

# لا يوجد حذف مباشر لـ Review (يتم عبر تغيير الحالة).