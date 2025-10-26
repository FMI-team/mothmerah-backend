# backend\src\community\crud\review_ratings_by_criteria_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID # إذا كانت Review_id تستخدم UUID
from datetime import datetime, timezone

# استيراد المودلز
from src.community.models import reviews_models as models # ReviewRatingByCriterion
# استيراد Schemas (لـ type hinting في Create)
from src.community.schemas import reviews_schemas as schemas


# ==========================================================
# --- CRUD Functions for ReviewRatingByCriterion ---
# ==========================================================

def create_review_rating_by_criterion(db: Session, rating_in: schemas.ReviewRatingByCriterionCreate) -> models.ReviewRatingByCriterion:
    """
    ينشئ سجلاً جديداً لتقييم مراجعة حسب معيار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rating_in (schemas.ReviewRatingByCriterionCreate): بيانات التقييم للإنشاء.

    Returns:
        models.ReviewRatingByCriterion: كائن التقييم الذي تم إنشاؤه.
    """
    db_rating = models.ReviewRatingByCriterion(
        review_id=rating_in.review_id,
        criteria_id=rating_in.criteria_id,
        rating_value=rating_in.rating_value
        # created_at سيتم تعيينه افتراضياً في المودل
    )
    db.add(db_rating)
    db.commit() # السجلات يتم حفظها فوراً
    db.refresh(db_rating)
    return db_rating

def get_review_rating_by_criterion(db: Session, rating_by_criteria_id: int) -> Optional[models.ReviewRatingByCriterion]:
    """
    يجلب سجل تقييم مراجعة حسب معيار بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rating_by_criteria_id (int): معرف السجل المطلوب.

    Returns:
        Optional[models.ReviewRatingByCriterion]: كائن السجل أو None.
    """
    return db.query(models.ReviewRatingByCriterion).options(
        joinedload(models.ReviewRatingByCriterion.review),
        joinedload(models.ReviewRatingByCriterion.review_criterion)
    ).filter(models.ReviewRatingByCriterion.rating_by_criteria_id == rating_by_criteria_id).first()

def get_all_review_ratings_by_criterion(
    db: Session,
    review_id: Optional[int] = None,
    criteria_id: Optional[int] = None,
    min_rating_value: Optional[int] = None,
    max_rating_value: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ReviewRatingByCriterion]:
    """
    يجلب قائمة بتقييمات المراجعة حسب المعايير، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        review_id (Optional[int]): تصفية حسب معرف المراجعة الأم.
        criteria_id (Optional[int]): تصفية حسب معرف المعيار.
        min_rating_value (Optional[int]): تصفية حسب الحد الأدنى لقيمة التقييم.
        max_rating_value (Optional[int]): تصفية حسب الحد الأقصى لقيمة التقييم.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.ReviewRatingByCriterion]: قائمة بكائنات السجلات.
    """
    query = db.query(models.ReviewRatingByCriterion).options(
        joinedload(models.ReviewRatingByCriterion.review),
        joinedload(models.ReviewRatingByCriterion.review_criterion)
    )
    if review_id:
        query = query.filter(models.ReviewRatingByCriterion.review_id == review_id)
    if criteria_id:
        query = query.filter(models.ReviewRatingByCriterion.criteria_id == criteria_id)
    if min_rating_value:
        query = query.filter(models.ReviewRatingByCriterion.rating_value >= min_rating_value)
    if max_rating_value:
        query = query.filter(models.ReviewRatingByCriterion.rating_value <= max_rating_value)
    
    return query.order_by(models.ReviewRatingByCriterion.created_at.desc()).offset(skip).limit(limit).all()

def update_review_rating_by_criterion(db: Session, db_rating: models.ReviewRatingByCriterion, rating_in: schemas.ReviewRatingByCriterionUpdate) -> models.ReviewRatingByCriterion:
    """
    يحدث بيانات تقييم مراجعة حسب معيار.
    """
    update_data = rating_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rating, key, value)
    
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating

def delete_review_rating_by_criterion(db: Session, db_rating: models.ReviewRatingByCriterion):
    """
    يحذف تقييم مراجعة حسب معيار (حذف صارم).
    """
    db.delete(db_rating)
    db.commit()
    return