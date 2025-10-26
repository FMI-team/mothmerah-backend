# backend\src\api\v1\routers\admin_community_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
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
from src.lookups.schemas import lookups_schemas # لأنواع الأنشطة وأحداث الأمان (للفلاتر)

# استيراد الخدمات (منطق العمل)
from src.community.services import ( # لجميع خدمات Community
    reviews_service,
    review_responses_service,
    review_reports_service,
    review_criteria_service,
    review_ratings_by_criteria_service,
    review_statuses_service,
    review_report_reasons_service
)


# تعريف الراوتر لإدارة المراجعات والتقييمات من جانب المسؤولين.
router = APIRouter(
    prefix="/community", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /admin/community)
    tags=["Admin - Community Management"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_VIEW_ANY"))] # صلاحية عامة لعرض المراجعات للمسؤول
)


# ================================================================
# --- نقاط الوصول لإدارة المراجعات (Reviews) كمسؤول ---
# ================================================================

@router.get(
    "/reviews/all", # مسار مختلف عن الراوتر العام للمستخدمين
    response_model=List[schemas.ReviewRead],
    summary="[Admin] جلب جميع المراجعات (بكل حالاتها)",
    description="""
    يسمح للمسؤولين بجلب جميع المراجعات في النظام، بغض النظر عن حالتها.
    """,
)
async def get_all_reviews_admin_endpoint(
    db: Session = Depends(get_db),
    reviewer_user_id: Optional[UUID] = None,
    reviewed_entity_id: Optional[str] = None,
    reviewed_entity_type: Optional[str] = None,
    review_status_key: Optional[str] = None,
    rating_overall: Optional[int] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب جميع المراجعات (للمسؤولين)."""
    return reviews_service.get_all_reviews_service(
        db=db,
        reviewer_user_id=reviewer_user_id,
        reviewed_entity_id=reviewed_entity_id,
        reviewed_entity_type=reviewed_entity_type,
        review_status_key=review_status_key,
        rating_overall=rating_overall,
        min_rating=min_rating,
        max_rating=max_rating,
        skip=skip,
        limit=limit
    )

@router.patch(
    "/reviews/{review_id}/status",
    response_model=schemas.ReviewRead,
    summary="[Admin] تحديث حالة مراجعة",
    description="""
    يسمح للمسؤولين بتغيير حالة مراجعة (مثلاً: من 'قيد المراجعة' إلى 'منشورة' أو 'مرفوضة').
    """,
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_ANY"))] # صلاحية المسؤول لإدارة المراجعات
)
async def update_review_status_admin_endpoint(
    review_id: int,
    status_update: schemas.ReviewUpdate, # يجب أن يحتوي على review_status_id
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لتحديث حالة مراجعة."""
    if status_update.review_status_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="يجب توفير معرف الحالة الجديدة (review_status_id).")
    return reviews_service.update_review_service(db=db, review_id=review_id, review_in=status_update, current_user=current_user)

@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف مراجعة",
    description="""
    يسمح للمسؤولين بحذف مراجعة (حذف ناعم عن طريق تغيير الحالة).
    """,
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_ANY"))]
)
async def delete_review_admin_endpoint(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف مراجعة."""
    return reviews_service.delete_review_service(db=db, review_id=review_id, current_user=current_user)


# ================================================================
# --- نقاط الوصول لإدارة الردود على المراجعات (Review Responses) كمسؤول ---
# ================================================================

@router.get(
    "/responses/all",
    response_model=List[schemas.ReviewResponseRead],
    summary="[Admin] جلب جميع الردود على المراجعات",
)
async def get_all_review_responses_admin_endpoint(
    db: Session = Depends(get_db),
    review_id: Optional[int] = None,
    responder_user_id: Optional[UUID] = None,
    is_approved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب جميع الردود على المراجعات (للمسؤولين)."""
    return review_responses_service.get_all_review_responses_service(
        db=db,
        review_id=review_id,
        responder_user_id=responder_user_id,
        is_approved=is_approved,
        skip=skip,
        limit=limit
    )

@router.patch(
    "/responses/{response_id}/approve",
    response_model=schemas.ReviewResponseRead,
    summary="[Admin] الموافقة على رد مراجعة",
    description="""
    يسمح للمسؤولين بالموافقة على رد مراجعة لجعله مرئياً للعامة.
    """,
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_ANY"))]
)
async def approve_review_response_endpoint(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول للموافقة على رد مراجعة."""
    update_data = schemas.ReviewResponseUpdate(is_approved=True)
    return review_responses_service.update_review_response_service(db=db, response_id=response_id, response_in=update_data, current_user=current_user)

@router.delete(
    "/responses/{response_id}",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str,str],
    summary="[Admin] حذف رد مراجعة",
    description="""
    يسمح للمسؤولين بحذف رد مراجعة.
    """,
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_ANY"))]
)
async def delete_review_response_admin_endpoint(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف رد مراجعة."""
    return review_responses_service.delete_review_response_service(db=db, response_id=response_id, current_user=current_user)


# ================================================================
# --- نقاط الوصول لإدارة بلاغات المراجعات (Review Reports) كمسؤول ---
# ================================================================

@router.get(
    "/reports/all",
    response_model=List[schemas.ReviewReportRead],
    summary="[Admin] جلب جميع بلاغات المراجعات",
)
async def get_all_review_reports_admin_endpoint(
    db: Session = Depends(get_db),
    review_id: Optional[int] = None,
    reporter_user_id: Optional[UUID] = None,
    report_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب جميع بلاغات المراجعات (للمسؤولين)."""
    return review_reports_service.get_all_review_reports_service(
        db=db,
        review_id=review_id,
        reporter_user_id=reporter_user_id,
        report_status=report_status,
        skip=skip,
        limit=limit
    )

@router.patch(
    "/reports/{report_id}/resolve",
    response_model=schemas.ReviewReportRead,
    summary="[Admin] تحديث حالة بلاغ مراجعة (حل/رفض)",
    description="""
    يسمح للمسؤولين بتحديث حالة بلاغ مراجعة (مثلاً: 'تم الحل' أو 'تم الرفض') وتحديد الإجراء المتخذ.
    """,
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_ANY"))]
)
async def resolve_review_report_endpoint(
    report_id: int,
    report_in: schemas.ReviewReportUpdate, # يجب أن يحتوي على report_status و action_taken
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحل بلاغ عن مراجعة."""
    if report_in.report_status not in ["RESOLVED", "DISMISSED"]: # TODO: استخدم مفاتيح حالات صحيحة من BRD
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="حالة البلاغ الجديدة غير صالحة.")
    
    return review_reports_service.update_review_report_service(db=db, report_id=report_id, report_in=report_in, current_user=current_user)

@router.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str,str],
    summary="[Admin] حذف بلاغ مراجعة",
    description="""
    يسمح للمسؤولين بحذف بلاغ مراجعة.
    """,
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_ANY"))]
)
async def delete_review_report_admin_endpoint(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف بلاغ مراجعة."""
    return review_reports_service.delete_review_report_service(db=db, report_id=report_id, current_user=current_user)


# ================================================================
# --- نقاط الوصول لإدارة معايير التقييم (Review Criteria) كمسؤول ---
# ================================================================

@router.post(
    "/criteria",
    response_model=lookups_schemas.ReviewCriterionRead, # Schema من lookups
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء معيار تقييم جديد",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))] # صلاحية لإدارة Lookups
)
async def create_review_criterion_endpoint(
    criterion_in: lookups_schemas.ReviewCriterionCreate, # Schema من lookups
    db: Session = Depends(get_db)
):
    """
    إنشاء معيار تقييم جديد (مثل: 'جودة التغليف', 'سرعة التوصيل').
    """
    return review_criteria_service.create_new_review_criterion(db=db, criterion_in=criterion_in)

@router.get(
    "/criteria",
    response_model=List[lookups_schemas.ReviewCriterionRead],
    summary="[Admin] جلب جميع معايير التقييم",
)
async def get_all_review_criteria_endpoint(
    db: Session = Depends(get_db),
    is_active: Optional[bool] = None,
    applicable_entity_type_code: Optional[str] = None
):
    """جلب قائمة بجميع معايير التقييم في النظام."""
    return review_criteria_service.get_all_review_criteria_service(
        db=db,
        is_active=is_active,
        applicable_entity_type_code=applicable_entity_type_code
    )

@router.get(
    "/criteria/{criteria_id}",
    response_model=lookups_schemas.ReviewCriterionRead,
    summary="[Admin] جلب تفاصيل معيار تقييم واحد",
)
async def get_review_criterion_details_endpoint(criteria_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل معيار تقييم واحد بالـ ID الخاص به."""
    return review_criteria_service.get_review_criterion_details(db=db, criteria_id=criteria_id)

@router.patch(
    "/criteria/{criteria_id}",
    response_model=lookups_schemas.ReviewCriterionRead,
    summary="[Admin] تحديث معيار تقييم",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def update_review_criterion_endpoint(
    criteria_id: int,
    criterion_in: lookups_schemas.ReviewCriterionUpdate,
    db: Session = Depends(get_db)
):
    """تحديث معيار تقييم موجود."""
    return review_criteria_service.update_review_criterion_service(db=db, criteria_id=criteria_id, criterion_in=criterion_in)

@router.delete(
    "/criteria/{criteria_id}",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str,str],
    summary="[Admin] حذف معيار تقييم",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def delete_review_criterion_endpoint(criteria_id: int, db: Session = Depends(get_db)):
    """حذف معيار تقييم (حذف صارم)."""
    return review_criteria_service.delete_review_criterion_service(db=db, criteria_id=criteria_id)

# --- ترجمات معايير التقييم ---
@router.post(
    "/criteria/{criteria_id}/translations",
    response_model=lookups_schemas.ReviewCriterionTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لمعيار تقييم",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def create_review_criterion_translation_endpoint(
    criteria_id: int,
    trans_in: lookups_schemas.ReviewCriterionTranslationCreate,
    db: Session = Depends(get_db)
):
    """إنشاء ترجمة جديدة لمعيار تقييم بلغة معينة."""
    return review_criteria_service.create_review_criterion_translation_service(db=db, criteria_id=criteria_id, trans_in=trans_in)

@router.get(
    "/criteria/{criteria_id}/translations/{language_code}",
    response_model=lookups_schemas.ReviewCriterionTranslationRead,
    summary="[Admin] جلب ترجمة محددة لمعيار تقييم",
)
async def get_review_criterion_translation_details_endpoint(
    criteria_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة معيار تقييم بلغة محددة."""
    return review_criteria_service.get_review_criterion_translation_details_service(db=db, criteria_id=criteria_id, language_code=language_code)

@router.patch(
    "/criteria/{criteria_id}/translations/{language_code}",
    response_model=lookups_schemas.ReviewCriterionTranslationRead,
    summary="[Admin] تحديث ترجمة معيار تقييم",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def update_review_criterion_translation_endpoint(
    criteria_id: int,
    language_code: str,
    trans_in: lookups_schemas.ReviewCriterionTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة معيار تقييم بلغة محددة."""
    return review_criteria_service.update_review_criterion_translation_service(db=db, criteria_id=criteria_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/criteria/{criteria_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة معيار تقييم",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def remove_review_criterion_translation_endpoint(
    criteria_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة معيار تقييم بلغة محددة."""
    return review_criteria_service.remove_review_criterion_translation_service(db=db, criteria_id=criteria_id, language_code=language_code)


# ================================================================
# --- نقاط الوصول لإدارة تقييمات المراجعات حسب المعايير (Review Ratings by Criteria) كمسؤول ---
# ================================================================

@router.post(
    "/ratings-by-criteria",
    response_model=schemas.ReviewRatingByCriterionRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء تقييم جديد لمراجعة حسب المعيار",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_ANY"))] # صلاحية المسؤول لإدارة المراجعات
)
async def create_review_rating_by_criterion_endpoint(
    rating_in: schemas.ReviewRatingByCriterionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """
    إنشاء تقييم جديد لمعيار محدد ضمن مراجعة.
    """
    return review_ratings_by_criteria_service.create_new_review_rating_by_criterion(db=db, rating_in=rating_in, current_user=current_user)

@router.get(
    "/ratings-by-criteria",
    response_model=List[schemas.ReviewRatingByCriterionRead],
    summary="[Admin] جلب جميع تقييمات المراجعات حسب المعايير",
)
async def get_all_review_ratings_by_criteria_endpoint(
    db: Session = Depends(get_db),
    review_id: Optional[int] = None,
    criteria_id: Optional[int] = None,
    min_rating_value: Optional[int] = None,
    max_rating_value: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب جميع تقييمات المراجعات حسب المعايير."""
    return review_ratings_by_criteria_service.get_all_review_ratings_by_criterion_service(
        db=db,
        review_id=review_id,
        criteria_id=criteria_id,
        min_rating_value=min_rating_value,
        max_rating_value=max_rating_value,
        skip=skip,
        limit=limit
    )

@router.get(
    "/ratings-by-criteria/{rating_by_criteria_id}",
    response_model=schemas.ReviewRatingByCriterionRead,
    summary="[Admin] جلب تفاصيل تقييم مراجعة حسب معيار واحد",
)
async def get_review_rating_by_criterion_details_endpoint(rating_by_criteria_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل تقييم مراجعة حسب معيار واحد بالـ ID الخاص به."""
    return review_ratings_by_criteria_service.get_review_rating_by_criterion_details_service(db=db, rating_by_criteria_id=rating_by_criteria_id)

@router.patch(
    "/ratings-by-criteria/{rating_by_criteria_id}",
    response_model=schemas.ReviewRatingByCriterionRead,
    summary="[Admin] تحديث تقييم مراجعة حسب معيار",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_ANY"))]
)
async def update_review_rating_by_criterion_endpoint(
    rating_by_criteria_id: int,
    rating_in: schemas.ReviewRatingByCriterionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """تحديث تقييم مراجعة حسب معيار موجود."""
    return review_ratings_by_criteria_service.update_review_rating_by_criterion_service(db=db, rating_by_criteria_id=rating_by_criteria_id, rating_in=rating_in, current_user=current_user)

@router.delete(
    "/ratings-by-criteria/{rating_by_criteria_id}",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str,str],
    summary="[Admin] حذف تقييم مراجعة حسب معيار",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_ANY"))]
)
async def delete_review_rating_by_criterion_endpoint(
    rating_by_criteria_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف تقييم مراجعة حسب معيار."""
    return review_ratings_by_criteria_service.delete_review_rating_by_criterion_service(db=db, rating_by_criteria_id=rating_by_criteria_id, current_user=current_user)


# ================================================================
# --- نقاط الوصول لإدارة حالات المراجعة (Review Statuses) كمسؤول ---
# ================================================================

@router.post(
    "/statuses",
    response_model=lookups_schemas.ReviewStatusRead, # Schema من lookups
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة مراجعة جديدة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))] # صلاحية لإدارة Lookups
)
async def create_review_status_endpoint(
    status_in: lookups_schemas.ReviewStatusCreate, # Schema من lookups
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مراجعة جديدة (مثل: 'قيد المراجعة', 'منشورة').
    """
    return review_statuses_service.create_new_review_status(db=db, status_in=status_in)

@router.get(
    "/statuses",
    response_model=List[lookups_schemas.ReviewStatusRead],
    summary="[Admin] جلب جميع حالات المراجعة",
)
async def get_all_review_statuses_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع حالات المراجعة في النظام."""
    return review_statuses_service.get_all_review_statuses_service(db=db)

@router.get(
    "/statuses/{status_id}",
    response_model=lookups_schemas.ReviewStatusRead,
    summary="[Admin] جلب تفاصيل حالة مراجعة واحدة",
)
async def get_review_status_details_endpoint(status_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل حالة مراجعة واحدة بالـ ID الخاص بها."""
    return review_statuses_service.get_review_status_details(db=db, status_id=status_id)

@router.patch(
    "/statuses/{status_id}",
    response_model=lookups_schemas.ReviewStatusRead,
    summary="[Admin] تحديث حالة مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def update_review_status_endpoint(
    status_id: int,
    status_in: lookups_schemas.ReviewStatusUpdate,
    db: Session = Depends(get_db)
):
    """تحديث حالة مراجعة موجودة."""
    return review_statuses_service.update_review_status_service(db=db, status_id=status_id, status_in=status_in)

@router.delete(
    "/statuses/{status_id}",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str,str],
    summary="[Admin] حذف حالة مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def delete_review_status_endpoint(status_id: int, db: Session = Depends(get_db)):
    """حذف حالة مراجعة (حذف صارم)."""
    return review_statuses_service.delete_review_status_service(db=db, status_id=status_id)

# --- ترجمات حالات المراجعة ---
@router.post(
    "/statuses/{status_id}/translations",
    response_model=lookups_schemas.ReviewStatusTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لحالة مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def create_review_status_translation_endpoint(
    status_id: int,
    trans_in: lookups_schemas.ReviewStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """إنشاء ترجمة جديدة لحالة مراجعة بلغة معينة."""
    return review_statuses_service.create_review_status_translation_service(db=db, status_id=status_id, trans_in=trans_in)

@router.get(
    "/statuses/{status_id}/translations/{language_code}",
    response_model=lookups_schemas.ReviewStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة مراجعة",
)
async def get_review_status_translation_details_endpoint(
    status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة حالة مراجعة بلغة محددة."""
    return review_statuses_service.get_review_status_translation_details_service(db=db, status_id=status_id, language_code=language_code)

@router.patch(
    "/statuses/{status_id}/translations/{language_code}",
    response_model=lookups_schemas.ReviewStatusTranslationRead,
    summary="[Admin] تحديث ترجمة حالة مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def update_review_status_translation_endpoint(
    status_id: int,
    language_code: str,
    trans_in: lookups_schemas.ReviewStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة حالة مراجعة بلغة محددة."""
    return review_statuses_service.update_review_status_translation_service(db=db, status_id=status_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/statuses/{status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة حالة مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def remove_review_status_translation_endpoint(
    status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة حالة مراجعة بلغة محددة."""
    return review_statuses_service.remove_review_status_translation_service(db=db, status_id=status_id, language_code=language_code)


# ================================================================
# --- نقاط الوصول لإدارة أسباب الإبلاغ عن المراجعات (Review Report Reasons) كمسؤول ---
# ================================================================

@router.post(
    "/report-reasons",
    response_model=lookups_schemas.ReviewReportReasonRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء سبب إبلاغ جديد عن مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def create_review_report_reason_endpoint(
    reason_in: lookups_schemas.ReviewReportReasonCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء سبب إبلاغ جديد (مثل: 'محتوى غير لائق', 'مراجعة مزيفة').
    """
    return review_report_reasons_service.create_new_review_report_reason(db=db, reason_in=reason_in)

@router.get(
    "/report-reasons",
    response_model=List[lookups_schemas.ReviewReportReasonRead],
    summary="[Admin] جلب جميع أسباب الإبلاغ عن المراجعات",
)
async def get_all_review_report_reasons_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع أسباب الإبلاغ عن المراجعات في النظام."""
    return review_report_reasons_service.get_all_review_report_reasons_service(db=db)

@router.get(
    "/report-reasons/{reason_id}",
    response_model=lookups_schemas.ReviewReportReasonRead,
    summary="[Admin] جلب تفاصيل سبب إبلاغ واحد عن مراجعة",
)
async def get_review_report_reason_details_endpoint(reason_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل سبب إبلاغ واحد عن مراجعة بالـ ID الخاص به."""
    return review_report_reasons_service.get_review_report_reason_details(db=db, reason_id=reason_id)

@router.patch(
    "/report-reasons/{reason_id}",
    response_model=lookups_schemas.ReviewReportReasonRead,
    summary="[Admin] تحديث سبب إبلاغ عن مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def update_review_report_reason_endpoint(
    reason_id: int,
    reason_in: lookups_schemas.ReviewReportReasonUpdate,
    db: Session = Depends(get_db)
):
    """تحديث سبب إبلاغ عن مراجعة موجود."""
    return review_report_reasons_service.update_review_report_reason_service(db=db, reason_id=reason_id, reason_in=reason_in)

@router.delete(
    "/report-reasons/{reason_id}",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str,str],
    summary="[Admin] حذف سبب إبلاغ عن مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def delete_review_report_reason_endpoint(reason_id: int, db: Session = Depends(get_db)):
    """حذف سبب إبلاغ عن مراجعة (حذف صارم)."""
    return review_report_reasons_service.delete_review_report_reason_service(db=db, reason_id=reason_id)

# --- ترجمات أسباب الإبلاغ عن المراجعات ---
@router.post(
    "/report-reasons/{reason_id}/translations",
    response_model=lookups_schemas.ReviewReportReasonTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لسبب إبلاغ عن مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def create_review_report_reason_translation_endpoint(
    reason_id: int,
    trans_in: lookups_schemas.ReviewReportReasonTranslationCreate,
    db: Session = Depends(get_db)
):
    """إنشاء ترجمة جديدة لسبب إبلاغ عن مراجعة بلغة معينة."""
    return review_report_reasons_service.create_review_report_reason_translation_service(db=db, reason_id=reason_id, trans_in=trans_in)

@router.get(
    "/report-reasons/{reason_id}/translations/{language_code}",
    response_model=lookups_schemas.ReviewReportReasonTranslationRead,
    summary="[Admin] جلب ترجمة محددة لسبب إبلاغ عن مراجعة",
)
async def get_review_report_reason_translation_details_endpoint(
    reason_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة سبب إبلاغ عن مراجعة بلغة محددة."""
    return review_report_reasons_service.get_review_report_reason_translation_details_service(db=db, reason_id=reason_id, language_code=language_code)

@router.patch(
    "/report-reasons/{reason_id}/translations/{language_code}",
    response_model=lookups_schemas.ReviewReportReasonTranslationRead,
    summary="[Admin] تحديث ترجمة سبب إبلاغ عن مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def update_review_report_reason_translation_endpoint(
    reason_id: int,
    language_code: str,
    trans_in: lookups_schemas.ReviewReportReasonTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة سبب إبلاغ عن مراجعة بلغة محددة."""
    return review_report_reasons_service.update_review_report_reason_translation_service(db=db, reason_id=reason_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/report-reasons/{reason_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة سبب إبلاغ عن مراجعة",
    dependencies=[Depends(dependencies.has_permission("ADMIN_REVIEW_MANAGE_LOOKUPS"))]
)
async def remove_review_report_reason_translation_endpoint(
    reason_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة سبب إبلاغ عن مراجعة بلغة محددة."""
    return review_report_reasons_service.remove_review_report_reason_translation_service(db=db, reason_id=reason_id, language_code=language_code)