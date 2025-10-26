# backend\src\api\v1\routers\rfqs_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين والطلبات
from datetime import datetime, date # لاستخدام التواريخ

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User # مودل المستخدم، للتحقق من الصلاحيات

# استيراد Schemas (هياكل البيانات) الخاصة بـ RFQs
from src.market.schemas import rfq_schemas as schemas
from src.lookups.schemas import lookups_schemas 

# استيراد الخدمات (منطق العمل) المتعلقة بـ RFQs
from src.market.services import rfqs_service

# تعريف الراوتر الرئيسي لوحدة إدارة طلبات عروض الأسعار (RFQs).
# هذا الراوتر سيتعامل مع نقاط الوصول المتعلقة بـ RFQs للمشترين التجاريين والبائعين.
router = APIRouter(
    prefix="/rfqs", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/rfqs)
    tags=["Market - RFQs Management"] # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
)

# ================================================================
# --- نقاط الوصول لطلبات عروض الأسعار (Rfq) ---
#    (تتطلب صلاحية RFQ_CREATE_PURCHASE للمشتري، وصلاحيات VIEW/UPDATE_OWN للمشترين والبائعين)
# ================================================================

@router.post(
    "/",
    response_model=schemas.RfqRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Buyer] إنشاء طلب عرض أسعار (RFQ) جديد",
    description="""
    يسمح للمشترين التجاريين بإنشاء طلب عرض أسعار (RFQ) جديد ومفصل.
    يتضمن تحديد المنتجات، الكميات، المواصفات، والموعد النهائي لتقديم العروض.
    يتطلب صلاحية 'RFQ_CREATE_PURCHASE'.
    """,
)
async def create_new_rfq_endpoint(
    rfq_in: schemas.RfqCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("RFQ_CREATE_PURCHASE"))
):
    """نقطة وصول لإنشاء طلب عرض أسعار (RFQ) جديد."""
    return rfqs_service.create_new_rfq(db=db, rfq_in=rfq_in, current_user=current_user)

@router.get(
    "/me",
    response_model=List[schemas.RfqRead],
    summary="[Buyer] جلب طلبات عروض الأسعار (RFQs) الخاصة بي",
    description="""
    يجلب قائمة بجميع طلبات عروض الأسعار (RFQs) التي أنشأها المشتري الحالي.
    يتطلب صلاحية 'RFQ_MANAGE_OWN'.
    """,
)
async def get_my_rfqs_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("RFQ_MANAGE_OWN")),
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب طلبات عروض الأسعار (RFQs) الخاصة بالمشتري الحالي."""
    return rfqs_service.get_my_rfqs(db=db, current_user=current_user, skip=skip, limit=limit)

@router.get(
    "/available-for-me",
    response_model=List[schemas.RfqRead],
    summary="[Seller] جلب طلبات عروض الأسعار (RFQs) المتاحة للرد عليها",
    description="""
    يجلب قائمة بطلبات عروض الأسعار (RFQs) التي تم توجيهها للبائع الحالي أو المتاحة له للرد عليها.
    يتطلب صلاحية 'RFQ_VIEW_AVAILABLE'.
    """,
)
async def get_rfqs_available_for_seller_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("RFQ_VIEW_AVAILABLE")),
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب طلبات عروض الأسعار (RFQs) المتاحة للبائع الحالي للرد عليها."""
    return rfqs_service.get_rfqs_available_for_seller(db=db, current_user=current_user, skip=skip, limit=limit)


@router.get(
    "/{rfq_id}",
    response_model=schemas.RfqRead,
    summary="[Buyer/Seller/Admin] جلب تفاصيل طلب عرض أسعار (RFQ) واحد",
    description="""
    يجلب التفاصيل الكاملة لطلب عرض أسعار (RFQ) محدد بالـ ID الخاص به.
    يتطلب صلاحية 'RFQ_MANAGE_OWN' للمشتري، أو 'RFQ_VIEW_AVAILABLE' للبائع، أو صلاحية إدارية.
    """,
)
async def get_rfq_details_endpoint(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("RFQ_MANAGE_OWN")) # صلاحية عامة تغطي الرؤية
):
    """نقطة وصول لجلب تفاصيل طلب عرض أسعار (RFQ) محدد."""
    return rfqs_service.get_rfq_details(db=db, rfq_id=rfq_id, current_user=current_user)

@router.patch(
    "/{rfq_id}",
    response_model=schemas.RfqRead,
    summary="[Buyer/Admin] تحديث طلب عرض أسعار (RFQ)",
    description="""
    يسمح للمشتري أو المسؤول بتحديث تفاصيل طلب عرض أسعار يملكه (أو أي طلب للمسؤول).
    يتطلب صلاحية 'RFQ_MANAGE_OWN' للمشتري أو 'ADMIN_RFQ_MANAGE_ANY' للمسؤول.
    """,
)
async def update_rfq_endpoint(
    rfq_id: int,
    rfq_in: schemas.RfqUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("RFQ_MANAGE_OWN"))
):
    """نقطة وصول لتحديث طلب عرض أسعار (RFQ)."""
    return rfqs_service.update_rfq(db=db, rfq_id=rfq_id, rfq_in=rfq_in, current_user=current_user)

@router.delete(
    "/{rfq_id}",
    response_model=schemas.RfqRead, # ترجع الكائن بعد تحديث حالته إلى "ملغى"
    summary="[Buyer/Admin] إلغاء طلب عرض أسعار (RFQ)",
    description="""
    يسمح للمشتري أو المسؤول بإلغاء طلب عرض أسعار (يعادل الحذف الناعم).
    يتم التحقق من صلاحيات المستخدم ومرحلة الـ RFQ قبل الإلغاء.
    يتطلب صلاحية 'RFQ_MANAGE_OWN' للمشتري أو 'ADMIN_RFQ_MANAGE_ANY' للمسؤول.
    """,
)
async def cancel_rfq_endpoint(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("RFQ_MANAGE_OWN"))
):
    """نقطة وصول لإلغاء (حذف ناعم) طلب عرض أسعار (RFQ)."""
    return rfqs_service.cancel_rfq(db=db, rfq_id=rfq_id, current_user=current_user)

# ================================================================
# --- نقاط الوصول لحالات طلب عروض الأسعار (RfqStatus) ---
#    (هذه عادةً ما تُدار بواسطة المسؤولين، ولكن يمكن تضمين نقاط وصول عرض هنا)
# ================================================================

@router.get(
    "/statuses",
    response_model=List[lookups_schemas.RfqStatusRead],
    summary="[Public] جلب جميع حالات طلب عرض الأسعار (RFQs)",
    description="""
    يجلب قائمة بجميع الحالات المرجعية لطلبات عروض الأسعار (RFQs) في النظام.
    متاح للعامة لغرض العرض.
    """,
)
async def get_all_rfq_statuses_endpoint(db: Session = Depends(get_db)):
    """نقطة وصول لجلب جميع حالات طلبات عروض الأسعار."""
    return rfqs_service.get_all_rfq_statuses_service(db=db)

# TODO: نقاط وصول إدارة حالات الـ RFQ (POST, PATCH, DELETE) ستكون في product_admin_router.py

# ================================================================
# --- نقاط الوصول لترجمات حالات طلب عروض الأسعار (RfqStatusTranslation) ---
# ================================================================

@router.get(
    "/statuses/{rfq_status_id}/translations/{language_code}",
    response_model=lookups_schemas.RfqStatusTranslationRead,
    summary="[Public] جلب ترجمة محددة لحالة طلب عرض أسعار (RFQ)",
    description="""
    يجلب ترجمة محددة لحالة طلب عرض أسعار (RFQ) بلغة معينة.
    متاح للعامة لغرض العرض.
    """,
)
async def get_rfq_status_translation_details_endpoint(
    rfq_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة محددة لحالة طلب عرض أسعار."""
    return rfqs_service.get_rfq_status_translation_details(db=db, rfq_status_id=rfq_status_id, language_code=language_code)

# TODO: نقاط وصول إدارة ترجمات حالات الـ RFQ (POST, PATCH, DELETE) ستكون في product_admin_router.py