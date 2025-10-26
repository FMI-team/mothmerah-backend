# backend\src\community\crud\review_responses_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID # إذا كانت Review_id تستخدم UUID
from datetime import datetime, timezone

# استيراد المودلز
from src.community.models import reviews_models as models # ReviewResponse
# استيراد Schemas (لـ type hinting في Create/Update)
from src.community.schemas import reviews_schemas as schemas


# ==========================================================
# --- CRUD Functions for ReviewResponse ---
# ==========================================================

def create_review_response(db: Session, response_in: schemas.ReviewResponseCreate) -> models.ReviewResponse:
    """
    ينشئ رداً جديداً على مراجعة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        response_in (schemas.ReviewResponseCreate): بيانات الرد للإنشاء.

    Returns:
        models.ReviewResponse: كائن الرد الذي تم إنشاؤه.
    """
    db_response = models.ReviewResponse(
        review_id=response_in.review_id,
        responder_user_id=response_in.responder_user_id,
        response_text=response_in.response_text,
        is_approved=response_in.is_approved,
        approved_by_user_id=response_in.approved_by_user_id
        # response_timestamp, created_at, updated_at تدار تلقائياً
    )
    db.add(db_response)
    db.commit() # السجلات يتم حفظها فوراً
    db.refresh(db_response)
    return db_response

def get_review_response(db: Session, response_id: int) -> Optional[models.ReviewResponse]:
    """
    يجلب رداً على مراجعة بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        response_id (int): معرف الرد المطلوب.

    Returns:
        Optional[models.ReviewResponse]: كائن الرد أو None.
    """
    return db.query(models.ReviewResponse).options(
        joinedload(models.ReviewResponse.review),
        joinedload(models.ReviewResponse.responder_user),
        joinedload(models.ReviewResponse.approved_by_user)
    ).filter(models.ReviewResponse.response_id == response_id).first()

def get_review_response_by_review_id(db: Session, review_id: int) -> Optional[models.ReviewResponse]:
    """
    يجلب رداً على مراجعة بمعرف المراجعة.
    """
    return db.query(models.ReviewResponse).options(
        joinedload(models.ReviewResponse.review),
        joinedload(models.ReviewResponse.responder_user),
        joinedload(models.ReviewResponse.approved_by_user)
    ).filter(models.ReviewResponse.review_id == review_id).first()


def get_all_review_responses(
    db: Session,
    review_id: Optional[int] = None,
    responder_user_id: Optional[UUID] = None,
    is_approved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ReviewResponse]:
    """
    يجلب قائمة بالردود على المراجعات، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        review_id (Optional[int]): تصفية حسب معرف المراجعة الأم.
        responder_user_id (Optional[UUID]): تصفية حسب معرف المستخدم الذي قدم الرد.
        is_approved (Optional[bool]): تصفية حسب حالة الموافقة.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.ReviewResponse]: قائمة بكائنات الردود.
    """
    query = db.query(models.ReviewResponse).options(
        joinedload(models.ReviewResponse.review),
        joinedload(models.ReviewResponse.responder_user),
        joinedload(models.ReviewResponse.approved_by_user)
    )
    if review_id:
        query = query.filter(models.ReviewResponse.review_id == review_id)
    if responder_user_id:
        query = query.filter(models.ReviewResponse.responder_user_id == responder_user_id)
    if is_approved is not None:
        query = query.filter(models.ReviewResponse.is_approved == is_approved)
    
    return query.order_by(models.ReviewResponse.response_timestamp.desc()).offset(skip).limit(limit).all()

def update_review_response(db: Session, db_response: models.ReviewResponse, response_in: schemas.ReviewResponseUpdate, approved_by_user_id: Optional[UUID] = None) -> models.ReviewResponse:
    """
    يحدث بيانات رد على مراجعة موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_response (models.ReviewResponse): كائن الرد من قاعدة البيانات.
        response_in (schemas.ReviewResponseUpdate): البيانات المراد تحديثها.
        approved_by_user_id (Optional[UUID]): معرف المستخدم الذي وافق على التحديث (إذا كان هناك تغيير في is_approved).

    Returns:
        models.ReviewResponse: كائن الرد المحدث.
    """
    update_data = response_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_response, key, value)
    
    db_response.updated_at = datetime.now(timezone.utc)
    # إذا كان هناك تغيير في is_approved، قم بتعيين approved_by_user_id
    if 'is_approved' in update_data and update_data['is_approved'] != db_response.is_approved:
        db_response.approved_by_user_id = approved_by_user_id # سيتم تعيينه في طبقة الخدمة

    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

def delete_review_response(db: Session, db_response: models.ReviewResponse):
    """
    يحذف رداً على مراجعة (حذف صارم).
    """
    db.delete(db_response)
    db.commit()
    return