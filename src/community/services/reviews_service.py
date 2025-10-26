# backend\src\community\services\reviews_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.community.models import reviews_models as models # Review
# استيراد الـ CRUD
from src.community.crud import reviews_crud as crud
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)
from src.market.crud import orders_crud # للتحقق من وجود الطلب (Order)
from src.lookups.crud import review_statuses_crud # للتحقق من وجود حالة المراجعة
from src.lookups.crud import entity_types_crud # للتحقق من وجود نوع الكيان
# TODO: استيراد CRUDs لـ Product, Auction, AuctionLot إذا تم ربط المراجعات بها
# from src.products.crud import product_crud
# from src.auctions.crud import auctions_crud

# استيراد Schemas
from src.community.schemas import reviews_schemas as schemas # Review

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for Review ---
# ==========================================================

def create_new_review(db: Session, review_in: schemas.ReviewCreate, current_user: User) -> models.Review:
    """
    خدمة لإنشاء مراجعة وتقييم جديدين.
    تتضمن التحقق من صلاحية المستخدم (BR-43)، ووجود الكيانات المرتبطة، وتعيين الحالة الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        review_in (schemas.ReviewCreate): بيانات المراجعة للإنشاء.
        current_user (User): المستخدم الحالي الذي يقدم المراجعة.

    Returns:
        models.Review: كائن المراجعة الذي تم إنشاؤه.

    Raises:
        BadRequestException: إذا كانت البيانات غير صالحة.
        NotFoundException: إذا لم يتم العثور على الكيان المراجع أو حالة المراجعة.
        ForbiddenException: إذا كان المستخدم غير مصرح له بتقديم مراجعة للكيان المحدد.
    """
    # 1. التحقق من وجود الكيان المراجع (reviewed_entity_type)
    #    يمكن استخدام EntityTypeForReviewOrImage للتأكد من أن النوع صالح
    entity_type_obj = entity_types_crud.get_entity_type(db, entity_type_code=review_in.reviewed_entity_type)
    if not entity_type_obj:
        raise NotFoundException(detail=f"نوع الكيان '{review_in.reviewed_entity_type}' غير موجود أو غير صالح للمراجعات.")

    # 2. التحقق من أن المستخدم قام بإتمام عملية شراء فعلية (BR-43)
    #    هذا يتطلب أن يكون related_order_id موجوداً ومرتبطاً بالمستخدم والكيان
    if review_in.related_order_id:
        # TODO: get_order_details (من Market/OrdersService) يجب أن تجلب الطلب مع بنوده
        db_order = orders_crud.get_order(db, order_id=review_in.related_order_id)
        if not db_order:
            raise NotFoundException(detail=f"الطلب بمعرف {review_in.related_order_id} المرتبط بالمراجعة غير موجود.")
        
        # التأكد أن المستخدم هو المشتري للطلب
        if db_order.buyer_user_id != current_user.user_id:
            raise ForbiddenException(detail="غير مصرح لك بتقديم مراجعة لهذا الطلب (أنت لست المشتري).")
        
        # TODO: التأكد أن الطلب قد تم إتمامه (حالة الطلب "DELIVERED" أو "COMPLETED")
        # if db_order.order_status.status_name_key not in ["DELIVERED", "COMPLETED"]:
        #    raise ForbiddenException(detail="لا يمكن مراجعة طلب لم يتم إتمامه بعد.")

        # TODO: التحقق من أن reviewed_entity_id و reviewed_entity_type يتطابقان مع ما في الطلب
        #       مثلاً: إذا كان الكيان هو "منتج"، تأكد أن المنتج موجود في بنود الطلب.
    else:
        # إذا لم يكن هناك related_order_id، يجب أن تكون هناك سياسة أخرى لتحديد الأهلية للمراجعة.
        # لأغراض MVP، يمكن فرض أن جميع المراجعات يجب أن تكون مرتبطة بطلب.
        raise BadRequestException(detail="يجب ربط المراجعة بطلب مكتمل لضمان المصداقية.")


    # 3. جلب الحالة الأولية للمراجعة
    initial_status_key = "PENDING_REVIEW" # أو "APPROVED" إذا كانت تُنشر تلقائياً
    initial_review_status = review_statuses_crud.get_review_status_by_key(db, key=initial_status_key)
    if not initial_review_status:
        raise ConflictException(detail=f"حالة المراجعة الأولية '{initial_status_key}' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    # 4. استدعاء CRUD لإنشاء المراجعة
    db_review = crud.create_review(
        db=db,
        review_in=review_in,
        reviewer_user_id=current_user.user_id,
        review_status_id=initial_review_status.status_id
    )

    db.commit() # تأكيد العملية بالكامل
    db.refresh(db_review)

    # TODO: إخطار البائع بأن هناك مراجعة جديدة لمنتجه/خدمته (وحدة الإشعارات - Module 11).

    return db_review

def get_review_details(db: Session, review_id: int, current_user: Optional[User] = None) -> models.Review:
    """
    خدمة لجلب تفاصيل مراجعة واحدة، مع التحقق من الصلاحيات.
    يمكن لأي مستخدم رؤية المراجعات المنشورة.
    المراجع يرى مراجعته كلها.
    المسؤول يرى كل المراجعات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        review_id (int): معرف المراجعة المطلوب.
        current_user (Optional[User]): المستخدم الحالي.

    Returns:
        models.Review: كائن المراجعة.

    Raises:
        NotFoundException: إذا لم يتم العثور على المراجعة.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية المراجعة.
    """
    db_review = crud.get_review(db, review_id=review_id)
    if not db_review:
        raise NotFoundException(detail=f"المراجعة بمعرف {review_id} غير موجودة.")

    # 1. التحقق من صلاحيات العرض
    is_published = db_review.review_status.status_name_key == "PUBLISHED" # TODO: تأكد من اسم المفتاح لحالة "PUBLISHED"
    is_reviewer = current_user and db_review.reviewer_user_id == current_user.user_id
    is_admin = current_user and any(p.permission_name_key == "ADMIN_REVIEW_VIEW_ANY" for p in current_user.default_role.permissions)

    # TODO: إذا كان المستخدم هو البائع للكيان المراجع، فقد يحتاج لرؤية المراجعة حتى لو لم تنشر.
    # is_seller_of_reviewed_entity = False
    # if current_user and db_review.reviewed_entity_type == "PRODUCT":
    #    db_product = product_crud.get_product(db, db_review.reviewed_entity_id) # TODO: يجب أن تجلب المنتج
    #    if db_product and db_product.seller_user_id == current_user.user_id:
    #        is_seller_of_reviewed_entity = True

    if not (is_published or is_reviewer or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل هذه المراجعة.")
    
    return db_review


def get_all_reviews_service(
    db: Session,
    reviewer_user_id: Optional[UUID] = None,
    reviewed_entity_id: Optional[str] = None,
    reviewed_entity_type: Optional[str] = None,
    review_status_key: Optional[str] = None,
    rating_overall: Optional[int] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Review]:
    """
    خدمة لجلب جميع المراجعات، مع خيارات للتصفية.
    يمكن للمستخدمين العاديين جلب المراجعات المنشورة فقط.
    المسؤولون يمكنهم جلب كل المراجعات.
    """
    # TODO: يجب أن تفرق هذه الدالة بين طلب المستخدم العادي والمسؤول (User vs Admin view).
    #       الحل الأمثل هو تمرير current_user هنا وتطبيق الفلترة حسب الصلاحيات.
    #       لأغراض هذا التنفيذ، سنفترض أنها تستخدم للمسؤولين بشكل أساسي أو لعرض عام غير مقيد.

    review_status_id = None
    if review_status_key:
        status_obj = review_statuses_crud.get_review_status_by_key(db, key=review_status_key)
        if not status_obj:
            raise NotFoundException(detail=f"حالة المراجعة '{review_status_key}' غير موجودة.")
        review_status_id = status_obj.status_id

    return crud.get_all_reviews(
        db=db,
        reviewer_user_id=reviewer_user_id,
        reviewed_entity_id=reviewed_entity_id,
        reviewed_entity_type=reviewed_entity_type,
        review_status_id=review_status_id,
        rating_overall=rating_overall,
        min_rating=min_rating,
        max_rating=max_rating,
        skip=skip,
        limit=limit
    )

def update_review_service(db: Session, review_id: int, review_in: schemas.ReviewUpdate, current_user: User) -> models.Review:
    """
    خدمة لتحديث مراجعة موجودة.
    تتضمن التحقق من الصلاحيات (مالك المراجعة أو مسؤول) ومراحل دورة حياة المراجعة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        review_id (int): معرف المراجعة المراد تحديثها.
        review_in (schemas.ReviewUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models.Review: كائن المراجعة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على المراجعة.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بتحديث المراجعة.
        BadRequestException: إذا كانت البيانات غير صالحة.
    """
    db_review = get_review_details(db, review_id, current_user) # يتحقق من الوجود والصلاحية

    # 1. التحقق من أن المراجعة لا تزال في مرحلة تسمح بالتعديل
    # TODO: آلة حالة (State Machine) للمراجعة: لا يمكن تعديل مراجعة بعد نشرها إلا من المسؤول.
    # if db_review.review_status.status_name_key == "PUBLISHED" and not is_admin: # is_admin يجب أن تُحسب هنا
    #     raise BadRequestException(detail="لا يمكن تحديث مراجعة منشورة.")

    # 2. التحقق من وجود حالة المراجعة الجديدة إذا تم تحديثها
    if review_in.review_status_id and review_in.review_status_id != db_review.review_status_id:
        new_status_obj = review_statuses_crud.get_review_status(db, review_in.review_status_id)
        if not new_status_obj:
            raise NotFoundException(detail=f"حالة المراجعة بمعرف {review_in.review_status_id} غير موجودة.")
        # TODO: آلة حالة (State Machine) للمراجعة: التحقق من الانتقال المسموح به.

    # 3. إذا تم تغيير الحالة إلى "منشورة"، قم بتعيين publication_timestamp (هذا يتم في CRUD)
    #    db_review.publication_timestamp = datetime.now(timezone.utc)

    return crud.update_review(db=db, db_review=db_review, review_in=review_in)


def delete_review_service(db: Session, review_id: int, current_user: User) -> Dict[str, str]:
    """
    خدمة لحذف مراجعة (حذف ناعم عن طريق تغيير حالتها إلى "ARCHIVED" أو "DELETED").
    تتضمن التحقق من الصلاحيات ومراحل دورة حياة المراجعة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        review_id (int): معرف المراجعة المراد حذفها.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على المراجعة.
        ForbiddenException: إذا كان المستخدم غير مصرح له بالحذف.
        BadRequestException: إذا كانت المراجعة في حالة لا تسمح بالحذف.
        ConflictException: إذا لم يتم العثور على حالة الحذف.
    """
    db_review = get_review_details(db, review_id, current_user)

    # 1. التحقق من صلاحية المستخدم للحذف (مالك المراجعة أو مسؤول)
    is_reviewer = db_review.reviewer_user_id == current_user.user_id
    is_admin = any(p.permission_name_key == "ADMIN_REVIEW_MANAGE_ANY" for p in current_user.default_role.permissions)

    if not (is_reviewer or is_admin):
        raise ForbiddenException(detail="غير مصرح لك بحذف هذه المراجعة.")

    # 2. التحقق من المرحلة المسموح بها للحذف (Review State Machine)
    # TODO: تحديد الحالات التي لا يُسمح فيها بالحذف (مثلاً بعد أن تم حل بلاغ عنها).
    #       يمكن فقط تغيير حالتها إلى "مخفية" أو "مرفوضة".

    # 3. جلب حالة الحذف المناسبة
    deleted_status_key = "DELETED" # أو "ARCHIVED"
    deleted_status = review_statuses_crud.get_review_status_by_key(db, key=deleted_status_key)
    if not deleted_status:
        raise ConflictException(detail=f"حالة الحذف '{deleted_status_key}' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    # 4. تحديث حالة المراجعة (حذف ناعم)
    crud.update_review(db=db, db_review=db_review, review_in=schemas.ReviewUpdate(review_status_id=deleted_status.status_id))

    # TODO: عكس العمليات (إذا كان هناك متوسط تقييم يجب تحديثه).
    # TODO: إخطار البائع إذا تم حذف مراجعة لمنتجه.

    return {"message": f"تم حذف المراجعة بمعرف {review_id} بنجاح."}