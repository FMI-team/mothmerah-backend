# backend\src\api\v1\routers\quotes_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين وعروض الأسعار
from datetime import datetime # لاستخدام التواريخ

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User # مودل المستخدم، للتحقق من الصلاحيات

# استيراد Schemas (هياكل البيانات) الخاصة بعروض الأسعار
from src.market.schemas import quote_schemas as schemas

# استيراد الخدمات (منطق العمل) المتعلقة بعروض الأسعار
from src.market.services import quotes_service
from src.lookups.schemas import lookups_schemas 

# تعريف الراوتر الرئيسي لوحدة إدارة عروض الأسعار (Quotes).
# هذا الراوتر سيتعامل مع نقاط الوصول المتعلقة بعروض الأسعار للمشترين والبائعين.
router = APIRouter(
    prefix="/quotes", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/quotes)
    tags=["Market - Quotes Management"] # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
)

# ================================================================
# --- نقاط الوصول لعروض الأسعار (Quote) ---
#    (تتطلب صلاحية QUOTE_SUBMIT_OWN للبائع، وصلاحيات VIEW/ACCEPT للمشتري/المسؤول)
# ================================================================

@router.post(
    "/",
    response_model=schemas.QuoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller] تقديم عرض سعر جديد",
    description="""
    يسمح للبائع بتقديم عرض سعر جديد استجابة لطلب عرض أسعار (RFQ) محدد.
    يتضمن تفاصيل الأسعار، الكميات المعروضة، وشروط التسليم والدفع.
    يتطلب صلاحية 'QUOTE_SUBMIT_OWN'.
    """,
)
async def create_new_quote_endpoint(
    quote_in: schemas.QuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("QUOTE_SUBMIT_OWN"))
):
    """نقطة وصول لتقديم عرض سعر جديد."""
    return quotes_service.create_new_quote(db=db, quote_in=quote_in, current_user=current_user)

@router.get(
    "/for-my-rfq/{rfq_id}",
    response_model=List[schemas.QuoteRead],
    summary="[Buyer] جلب عروض الأسعار لطلب RFQ خاص بي",
    description="""
    يجلب قائمة بجميع عروض الأسعار المستلمة لطلب عرض أسعار (RFQ) يخص المشتري الحالي.
    يتطلب صلاحية 'RFQ_MANAGE_OWN' (للتحقق من ملكية RFQ).
    """,
)
async def get_quotes_for_my_rfq_endpoint(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("RFQ_MANAGE_OWN")), # المشترون الذين يملكون الـ RFQ يرون عروضه
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب عروض الأسعار المستلمة لطلب RFQ يخص المشتري الحالي."""
    return quotes_service.get_quotes_for_my_rfq(db=db, rfq_id=rfq_id, current_user=current_user, skip=skip, limit=limit)

@router.get(
    "/me",
    response_model=List[schemas.QuoteRead],
    summary="[Seller] جلب عروض الأسعار التي قدمتها",
    description="""
    يجلب قائمة بجميع عروض الأسعار التي قدمها البائع الحالي استجابة لطلبات RFQs.
    يتطلب صلاحية 'QUOTE_SUBMIT_OWN'.
    """,
)
async def get_my_submitted_quotes_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("QUOTE_SUBMIT_OWN")),
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب عروض الأسعار التي قدمها البائع الحالي."""
    return quotes_service.get_my_submitted_quotes(db=db, current_user=current_user, skip=skip, limit=limit)

@router.get(
    "/{quote_id}",
    response_model=schemas.QuoteRead,
    summary="[Buyer/Seller/Admin] جلب تفاصيل عرض سعر واحد",
    description="""
    يجلب التفاصيل الكاملة لعرض سعر محدد بالـ ID الخاص به.
    يتطلب صلاحية 'QUOTE_VIEW_ANY' للمسؤول، أو أن يكون المستخدم هو البائع مقدم العرض أو المشتري صاحب الـ RFQ المرتبط.
    """,
)
async def get_quote_details_endpoint(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("QUOTE_ACCEPT_ANY")) # صلاحية عامة تغطي الرؤية للمشتري/البائع/المسؤول
):
    """نقطة وصول لجلب تفاصيل عرض سعر محدد."""
    return quotes_service.get_quote_details(db=db, quote_id=quote_id, current_user=current_user)

@router.patch(
    "/{quote_id}",
    response_model=schemas.QuoteRead,
    summary="[Buyer/Seller/Admin] تحديث عرض سعر",
    description="""
    يسمح للمشتري (صاحب الـ RFQ) بتغيير حالة عرض السعر إلى "مقبول" أو "مرفوض"،
    أو يسمح للبائع بتعديل عرضه قبل القبول (إذا كانت الحالة تسمح بذلك).
    يتطلب صلاحية 'QUOTE_ACCEPT_ANY' للمشتري أو 'QUOTE_SUBMIT_OWN' للبائع، أو صلاحية إدارية.
    """,
)
async def update_quote_endpoint(
    quote_id: int,
    quote_in: schemas.QuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("QUOTE_ACCEPT_ANY")) # صلاحية عامة للتحديث/القبول/الرفض
):
    """نقطة وصول لتحديث عرض سعر محدد."""
    return quotes_service.update_quote(db=db, quote_id=quote_id, quote_in=quote_in, current_user=current_user)

@router.post(
    "/{quote_id}/accept",
    response_model=schemas.QuoteRead,
    summary="[Buyer] قبول عرض سعر",
    status_code=status.HTTP_200_OK,
    description="""
    يسمح للمشتري بقبول عرض سعر محدد.
    يؤدي القبول إلى تحديث حالة عرض السعر، وتغيير حالة الـ RFQ، وإنشاء طلب شراء جديد مؤكد.
    يتطلب صلاحية 'QUOTE_ACCEPT_ANY'.
    """,
)
async def accept_quote_endpoint(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("QUOTE_ACCEPT_ANY"))
):
    """نقطة وصول لقبول عرض سعر."""
    return quotes_service.accept_quote(db=db, quote_id=quote_id, current_user=current_user)

@router.post(
    "/{quote_id}/reject",
    response_model=schemas.QuoteRead,
    summary="[Buyer] رفض عرض سعر",
    status_code=status.HTTP_200_OK,
    description="""
    يسمح للمشتري برفض عرض سعر محدد.
    يؤدي الرفض إلى تحديث حالة عرض السعر.
    يتطلب صلاحية 'QUOTE_ACCEPT_ANY'.
    """,
)
async def reject_quote_endpoint(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("QUOTE_ACCEPT_ANY"))
):
    """نقطة وصول لرفض عرض سعر."""
    return quotes_service.reject_quote(db=db, quote_id=quote_id, current_user=current_user)

# ================================================================
# --- نقاط الوصول لحالات عرض السعر (QuoteStatus) ---
#    (هذه عادةً ما تُدار بواسطة المسؤولين، ولكن يمكن تضمين نقاط وصول عرض هنا)
# ================================================================

@router.get(
    "/statuses",
    response_model=List[lookups_schemas.QuoteStatusRead],
    summary="[Public] جلب جميع حالات عرض السعر",
    description="""
    يجلب قائمة بجميع الحالات المرجعية لعروض الأسعار في النظام.
    متاح للعامة لغرض العرض.
    """,
)
async def get_all_quote_statuses_endpoint(db: Session = Depends(get_db)):
    """نقطة وصول لجلب جميع حالات عرض السعر."""
    return quotes_service.get_all_quote_statuses_service(db=db)

# TODO: نقاط وصول إدارة حالات عرض السعر (POST, PATCH, DELETE) ستكون في product_admin_router.py

# ================================================================
# --- نقاط الوصول لترجمات حالات عرض السعر (QuoteStatusTranslation) ---
# ================================================================

@router.get(
    "/statuses/{quote_status_id}/translations/{language_code}",
    response_model=lookups_schemas.QuoteStatusTranslationRead,
    summary="[Public] جلب ترجمة محددة لحالة عرض سعر",
    description="""
    يجلب ترجمة محددة لحالة عرض سعر بلغة معينة.
    متاح للعامة لغرض العرض.
    """,
)
async def get_quote_status_translation_details_endpoint(
    quote_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة محددة لحالة عرض سعر."""
    return quotes_service.get_quote_status_translation_details(db=db, quote_status_id=quote_status_id, language_code=language_code)

# TODO: نقاط وصول إدارة ترجمات حالات عرض السعر (POST, PATCH, DELETE) ستكون في product_admin_router.py