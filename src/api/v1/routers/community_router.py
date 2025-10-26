# backend\src\api\v1\routers\community_router.py

from fastapi import APIRouter, Depends, status, HTTPException, Body # Body لـ Pydantic Model في Request Body
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional, Dict # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين
from datetime import datetime # لتصفية الوقت في السجلات

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User as UserModel # مودل المستخدم، لضمان User type hint

# استيراد Schemas (هياكل البيانات)
from src.community.schemas import reviews_schemas as schemas # لجميع Schemas Reviews
from src.lookups.schemas import lookups_schemas # لأنواع الكيانات (للفلاتر)

# استيراد الخدمات (منطق العمل)
from src.community.services import ( # لجميع خدمات Community
    reviews_service,
    review_responses_service,
    review_reports_service
)


# تعريف الراوتر للمراجعات والتقييمات التي تواجه المستخدم.
router = APIRouter(
    prefix="/community/reviews", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر
    tags=["Community - Reviews"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
)


# ================================================================
# --- نقاط الوصول للمراجعات والتقييمات (User Facing) ---
# ================================================================

@router.post(
    "/",
    response_model=schemas.ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Authenticated User] إنشاء مراجعة وتقييم جديدين",
    description="""
    يسمح للمشترين الموثقين بإنشاء مراجعات وتقييمات للمنتجات أو البائعين المرتبطين بطلبات مكتملة.
    (REQ-FUN-028, BR-43)
    """,
    dependencies=[Depends(dependencies.has_permission("REVIEW_CREATE_OWN"))]
)
async def create_review_endpoint(
    review_in: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لإنشاء مراجعة جديدة."""
    return reviews_service.create_new_review(db=db, review_in=review_in, current_user=current_user)

@router.get(
    "/",
    response_model=List[schemas.ReviewRead],
    summary="[Public] جلب المراجعات المنشورة",
    description="""
    يجلب قائمة بالمراجعات المنشورة (المعتمدة)، مع خيارات تصفية وعرض.
    (UR-26)
    """,
)
async def get_published_reviews_endpoint(
    db: Session = Depends(get_db),
    reviewed_entity_id: Optional[str] = None, # لتصفية المراجعات لمنتج/بائع معين
    reviewed_entity_type: Optional[str] = None, # لتصفية المراجعات حسب نوع الكيان (Product, Seller)
    rating_overall: Optional[int] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب المراجعات المنشورة."""
    # فقط جلب المراجعات التي حالتها "منشورة"
    published_status = lookups_schemas.ReviewStatusRead(status_name_key="PUBLISHED") # تأكد من أن هذا موجود
    # TODO: يجب أن تستخدم خدمة get_all_reviews_service لفلترة الحالات المنشورة فقط
    return reviews_service.get_all_reviews_service(
        db=db,
        reviewed_entity_id=reviewed_entity_id,
        reviewed_entity_type=reviewed_entity_type,
        review_status_key=published_status.status_name_key, # فلترة حسب حالة النشر
        rating_overall=rating_overall,
        min_rating=min_rating,
        max_rating=max_rating,
        skip=skip,
        limit=limit
    )

@router.get(
    "/{review_id}",
    response_model=schemas.ReviewRead,
    summary="[Public] جلب تفاصيل مراجعة واحدة",
)
async def get_review_details_endpoint(review_id: int, db: Session = Depends(get_db), current_user: Optional[UserModel] = Depends(dependencies.get_current_user_or_none)):
    """
    جلب تفاصيل مراجعة واحدة بالـ ID الخاص بها.
    مرئية للعامة إذا كانت منشورة، أو للمالك/المسؤول إذا لم تنشر بعد.
    """
    return reviews_service.get_review_details(db=db, review_id=review_id, current_user=current_user)


# ================================================================
# --- نقاط الوصول للردود على المراجعات (Review Responses) ---
# ================================================================

@router.post(
    "/{review_id}/responses",
    response_model=schemas.ReviewResponseRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Authenticated User / Seller] إضافة رد على مراجعة",
    description="""
    يسمح للبائعين بالرد على المراجعات التي تلقوها، أو للمسؤولين بالرد نيابة عن المنصة.
    (BR-44)
    """,
    dependencies=[Depends(dependencies.has_permission("REVIEW_RESPONSE_CREATE_OWN_OR_ADMIN"))] # صلاحية مخصصة
)
async def create_review_response_endpoint(
    review_id: int,
    response_in: schemas.ReviewResponseCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لإضافة رد على مراجعة."""
    response_in.review_id = review_id # تعيين معرف المراجعة من المسار
    response_in.responder_user_id = current_user.user_id # تعيين المستخدم الحالي كرد
    return review_responses_service.create_new_review_response(db=db, response_in=response_in, current_user=current_user)

@router.get(
    "/{review_id}/responses/{response_id}",
    response_model=schemas.ReviewResponseRead,
    summary="[Public] جلب تفاصيل رد على مراجعة",
)
async def get_review_response_details_endpoint(response_id: int, db: Session = Depends(get_db), current_user: Optional[UserModel] = Depends(dependencies.get_current_user_or_none)):
    """جلب تفاصيل رد على مراجعة بالـ ID الخاص به."""
    return review_responses_service.get_review_response_details_service(db=db, response_id=response_id, current_user=current_user)


# ================================================================
# --- نقاط الوصول للإبلاغات عن المراجعات (Review Reports) ---
# ================================================================

@router.post(
    "/{review_id}/reports",
    response_model=schemas.ReviewReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Authenticated User] الإبلاغ عن مراجعة",
    description="""
    يسمح للمستخدمين بالإبلاغ عن مراجعات يعتقدون أنها تخالف سياسات المنصة.
    (BR-45, UR-44)
    """,
    dependencies=[Depends(dependencies.has_permission("REVIEW_REPORT_CREATE_OWN"))] # صلاحية لتقديم بلاغ
)
async def create_review_report_endpoint(
    review_id: int,
    report_in: schemas.ReviewReportCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول للإبلاغ عن مراجعة."""
    report_in.review_id = review_id # تعيين معرف المراجعة من المسار
    report_in.reporter_user_id = current_user.user_id # تعيين المستخدم الحالي كمبلغ
    return review_reports_service.create_new_review_report(db=db, report_in=report_in, current_user=current_user)


@router.get(
    "/{review_id}/reports/{report_id}",
    response_model=schemas.ReviewReportRead,
    summary="[Admin] جلب تفاصيل بلاغ عن مراجعة",
    description="""
    يسمح للمسؤولين بجلب تفاصيل بلاغ عن مراجعة.
    """,
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_VIEW_ANY"))] # صلاحية المسؤول
)
async def get_review_report_details_endpoint(report_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(dependencies.get_current_active_user)):
    """جلب تفاصيل بلاغ عن مراجعة بالـ ID الخاص به."""
    return review_reports_service.get_review_report_details_service(db=db, report_id=report_id, current_user=current_user)