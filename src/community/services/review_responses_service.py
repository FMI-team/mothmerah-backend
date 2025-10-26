# backend\src\community\services\review_responses_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

# استيراد المودلز
from src.community.models import reviews_models as models # ReviewResponse
# استيراد الـ CRUD
from src.community.crud import review_responses_crud as crud
from src.community.crud import reviews_crud # للتحقق من وجود المراجعة (Review)
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)

# استيراد Schemas
from src.community.schemas import reviews_schemas as schemas # ReviewResponse

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for ReviewResponse ---
# ==========================================================

def create_new_review_response(db: Session, response_in: schemas.ReviewResponseCreate, current_user: User) -> models.ReviewResponse:
    """
    خدمة لإنشاء رد جديد على مراجعة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        response_in (schemas.ReviewResponseCreate): بيانات الرد للإنشاء.
        current_user (User): المستخدم الحالي الذي يقدم الرد (البائع أو المسؤول).

    Returns:
        models.ReviewResponse: كائن الرد الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المراجعة الأم أو المستخدم.
        ForbiddenException: إذا كان المستخدم غير مصرح له بالرد على هذه المراجعة.
        ConflictException: إذا كان هناك رد موجود بالفعل على نفس المراجعة.
    """
    # 1. التحقق من وجود المراجعة الأم
    # TODO: يجب استخدام get_review_details من reviews_service
    db_review = reviews_crud.get_review(db, review_id=response_in.review_id)
    if not db_review:
        raise NotFoundException(detail=f"المراجعة بمعرف {response_in.review_id} غير موجودة.")
    
    # 2. التحقق من أن المستخدم هو البائع للكيان المراجع أو مسؤول (BR-44)
    #    (هذا يتطلب تحميل المنتج أو الكيان المراجع ومعرفة بائعه)
    #    لأغراض MVP، سنبسط ونسمح للبائع بالرد إذا كان هو بائع المنتج/المزاد
    #    و للمسؤولين (ADMIN_REVIEW_MANAGE_ANY)
    # TODO: يجب توسيع هذا التحقق ليشمل البائع الفعلي للمنتج أو لوت المزاد.
    is_review_owner = db_review.reviewer_user_id == current_user.user_id # المراجع يمكنه الرد على مراجعته (نادر)
    is_admin = any(p.permission_name_key == "ADMIN_REVIEW_MANAGE_ANY" for p in current_user.default_role.permissions)

    # مؤقتاً: السماح للبائعين بالرد إذا كانوا يملكون المنتجات المراجعة
    is_seller_of_reviewed_entity = False
    # if db_review.reviewed_entity_type == "PRODUCT":
    #    product_seller_id = product_crud.get_product_seller_id(db, db_review.reviewed_entity_id) # دالة غير موجودة بعد
    #    if product_seller_id == current_user.user_id:
    #        is_seller_of_reviewed_entity = True
    # TODO: يجب إحضار المنتج/الكيان المراجع هنا والتحقق من هوية البائع.

    if not (is_review_owner or is_seller_of_reviewed_entity or is_admin):
        raise ForbiddenException(detail="غير مصرح لك بالرد على هذه المراجعة.")
    
    # 3. التحقق من عدم وجود رد موجود بالفعل على نفس المراجعة (unique=True في المودل)
    existing_response = crud.get_review_response_by_review_id(db, review_id=response_in.review_id)
    if existing_response:
        raise ConflictException(detail=f"يوجد رد بالفعل على المراجعة بمعرف {response_in.review_id}. لا يمكن إضافة أكثر من رد.")

    # 4. التحقق من وجود المستخدم الذي يقدم الرد
    responder_user_exists = core_crud.get_user_by_id(db, response_in.responder_user_id)
    if not responder_user_exists:
        raise NotFoundException(detail=f"المستخدم بمعرف {response_in.responder_user_id} الذي يقدم الرد غير موجود.")

    # 5. تعيين approved_by_user_id إذا كان الرد سيتم الموافقة عليه فوراً (غالباً بواسطة المسؤول)
    approved_by_user_id = current_user.user_id if response_in.is_approved else None

    return crud.create_review_response(db=db, response_in=response_in, approved_by_user_id=approved_by_user_id)


def get_review_response_details_service(db: Session, response_id: int, current_user: Optional[User] = None) -> models.ReviewResponse:
    """
    خدمة لجلب تفاصيل رد على مراجعة واحد بالـ ID الخاص به.
    يمكن لأي مستخدم رؤية الردود الموافق عليها.
    المسؤول يرى كل الردود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        response_id (int): معرف الرد المطلوب.
        current_user (Optional[User]): المستخدم الحالي.

    Returns:
        models.ReviewResponse: كائن الرد.

    Raises:
        NotFoundException: إذا لم يتم العثور على الرد.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية الرد.
    """
    db_response = crud.get_review_response(db, response_id=response_id)
    if not db_response:
        raise NotFoundException(detail=f"الرد على المراجعة بمعرف {response_id} غير موجود.")
    
    # 1. التحقق من صلاحيات العرض
    is_approved_publicly = db_response.is_approved is True
    is_admin = current_user and any(p.permission_name_key == "ADMIN_REVIEW_VIEW_ANY" for p in current_user.default_role.permissions)

    if not (is_approved_publicly or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل هذا الرد على المراجعة.")
    
    return db_response


def get_all_review_responses_service(
    db: Session,
    review_id: Optional[int] = None,
    responder_user_id: Optional[UUID] = None,
    is_approved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ReviewResponse]:
    """
    خدمة لجلب قائمة بالردود على المراجعات، مع خيارات التصفية والترقيم.
    تُستخدم للمسؤولين أو لعرض الردود العامة.
    """
    return crud.get_all_review_responses(
        db=db,
        review_id=review_id,
        responder_user_id=responder_user_id,
        is_approved=is_approved,
        skip=skip,
        limit=limit
    )

def update_review_response_service(db: Session, response_id: int, response_in: schemas.ReviewResponseUpdate, current_user: User) -> models.ReviewResponse:
    """
    خدمة لتحديث رد على مراجعة موجود.
    تتضمن التحقق من الصلاحيات (صاحب الرد أو مسؤول).

    Args:
        db (Session): جلسة قاعدة البيانات.
        response_id (int): معرف الرد المراد تحديثه.
        response_in (schemas.ReviewResponseUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models.ReviewResponse: كائن الرد المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الرد.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بتحديث الرد.
    """
    db_response = get_review_response_details_service(db, response_id, current_user) # يتحقق من الوجود والصلاحية

    # 1. التحقق من صلاحية المستخدم (صاحب الرد أو المسؤول الذي وافق عليه أو مسؤول عام)
    is_owner = db_response.responder_user_id == current_user.user_id
    is_admin = any(p.permission_name_key == "ADMIN_REVIEW_MANAGE_ANY" for p in current_user.default_role.permissions)

    if not (is_owner or is_admin):
        raise ForbiddenException(detail="غير مصرح لك بتحديث هذا الرد.")
    
    # 2. تعيين approved_by_user_id إذا تم تحديث is_approved من قبل مسؤول
    approved_by_user_id = current_user.user_id if response_in.is_approved is True else None

    return crud.update_review_response(db=db, db_response=db_response, response_in=response_in, approved_by_user_id=approved_by_user_id)


def delete_review_response_service(db: Session, response_id: int, current_user: User) -> Dict[str, str]:
    """
    خدمة لحذف رد على مراجعة.
    تتضمن التحقق من الصلاحيات (صاحب الرد أو مسؤول).

    Args:
        db (Session): جلسة قاعدة البيانات.
        response_id (int): معرف الرد المراد حذفه.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الرد.
        ForbiddenException: إذا كان المستخدم غير مصرح له بحذف الرد.
    """
    db_response = get_review_response_details_service(db, response_id, current_user) # يتحقق من الوجود والصلاحية

    # 1. التحقق من صلاحية المستخدم للحذف
    is_owner = db_response.responder_user_id == current_user.user_id
    is_admin = any(p.permission_name_key == "ADMIN_REVIEW_MANAGE_ANY" for p in current_user.default_role.permissions)

    if not (is_owner or is_admin):
        raise ForbiddenException(detail="غير مصرح لك بحذف هذا الرد.")
    
    crud.delete_review_response(db=db, db_response=db_response)
    return {"message": f"تم حذف الرد على المراجعة بمعرف {response_id} بنجاح."}