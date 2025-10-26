# backend\src\api\v1\routers\admin_auctions_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين والمزادات

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User # مودل المستخدم، للتحقق من الصلاحيات

# استيراد Schemas (هياكل البيانات) الخاصة بالمزادات
from src.auctions.schemas import auction_schemas # لـ Auction, AuctionLot, AuctionStatus, AuctionType
from src.auctions.schemas import bidding_schemas # لـ Bid, AuctionParticipant
from src.auctions.schemas import settlement_schemas # لـ AuctionSettlement, AuctionSettlementStatus
from src.lookups.schemas import lookups_schemas 

# استيراد الخدمات (منطق العمل) المتعلقة بالمزادات
from src.auctions.services import auctions_service
from src.auctions.services import bidding_service
from src.auctions.services import settlements_service

# تعريف الراوتر الرئيسي لإدارة المزادات من جانب المسؤولين.
router = APIRouter(
    prefix="/admin/auctions", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر
    tags=["Admin - Auction Management"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.has_permission("ADMIN_AUCTION_MANAGE_ANY"))] # صلاحية عامة لإدارة المزادات
)

# ================================================================
# --- نقاط الوصول لحالات المزاد (AuctionStatus) ---
# ================================================================

@router.post(
    "/statuses",
    response_model=lookups_schemas.AuctionStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة مزاد جديدة"
)
async def create_auction_status_endpoint(
    status_in: lookups_schemas.AuctionStatusCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مرجعية جديدة للمزاد (مثلاً: 'مجدول', 'نشط', 'مغلق ببيع').
    تتطلب صلاحية 'ADMIN_AUCTION_MANAGE_ANY'.
    """
    return auctions_service.create_new_auction_status(db=db, status_in=status_in)

@router.get(
    "/statuses",
    response_model=List[lookups_schemas.AuctionStatusRead],
    summary="[Admin] جلب جميع حالات المزاد"
)
async def get_all_auction_statuses_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع الحالات المرجعية للمزاد في النظام."""
    return auctions_service.get_all_auction_statuses_service(db=db)

@router.get(
    "/statuses/{auction_status_id}",
    response_model=lookups_schemas.AuctionStatusRead,
    summary="[Admin] جلب تفاصيل حالة مزاد واحدة"
)
async def get_auction_status_details_endpoint(auction_status_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل حالة مرجعية لمزاد بالـ ID الخاص بها."""
    return auctions_service.get_auction_status_details(db=db, auction_status_id=auction_status_id)

@router.patch(
    "/statuses/{auction_status_id}",
    response_model=lookups_schemas.AuctionStatusRead,
    summary="[Admin] تحديث حالة مزاد"
)
async def update_auction_status_endpoint(
    auction_status_id: int,
    status_in: lookups_schemas.AuctionStatusUpdate,
    db: Session = Depends(get_db)
):
    """تحديث حالة مرجعية لمزاد."""
    return auctions_service.update_auction_status_service(db=db, auction_status_id=auction_status_id, status_in=status_in)

@router.delete(
    "/statuses/{auction_status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف حالة مزاد"
)
async def delete_auction_status_endpoint(auction_status_id: int, db: Session = Depends(get_db)):
    """
    حذف حالة مرجعية لمزاد (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأي مزادات أو لوطات.
    """
    auctions_service.delete_auction_status_service(db=db, auction_status_id=auction_status_id)
    return

# ================================================================
# --- نقاط الوصول لترجمات حالات المزاد (AuctionStatusTranslation) ---
# ================================================================

@router.post(
    "/statuses/{auction_status_id}/translations",
    response_model=lookups_schemas.AuctionStatusTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لحالة مزاد أو تحديثها"
)
async def create_auction_status_translation_endpoint(
    auction_status_id: int,
    trans_in: lookups_schemas.AuctionStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء ترجمة جديدة لحالة مرجعية لمزاد بلغة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب بتضارب.
    """
    return auctions_service.create_auction_status_translation_service(db=db, auction_status_id=auction_status_id, trans_in=trans_in)

@router.get(
    "/statuses/{auction_status_id}/translations/{language_code}",
    response_model=lookups_schemas.AuctionStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة مزاد"
)
async def get_auction_status_translation_details_endpoint(
    auction_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة حالة مرجعية لمزاد بلغة محددة."""
    return auctions_service.get_auction_status_translation_details(db=db, auction_status_id=auction_status_id, language_code=language_code)

@router.patch(
    "/statuses/{auction_status_id}/translations/{language_code}",
    response_model=lookups_schemas.AuctionStatusTranslationRead,
    summary="[Admin] تحديث ترجمة حالة مزاد"
)
async def update_auction_status_translation_endpoint(
    auction_status_id: int,
    language_code: str,
    trans_in: lookups_schemas.AuctionStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة حالة مرجعية لمزاد بلغة محددة."""
    return auctions_service.update_auction_status_translation_service(db=db, auction_status_id=auction_status_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/statuses/{auction_status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة حالة مزاد"
)
async def delete_auction_status_translation_endpoint(
    auction_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة حالة مرجعية لمزاد بلغة محددة (حذف صارم)."""
    auctions_service.delete_auction_status_translation_service(db=db, auction_status_id=auction_status_id, language_code=language_code)
    return

# ================================================================
# --- نقاط الوصول لأنواع المزادات (AuctionType) ---
# ================================================================

@router.post(
    "/types",
    response_model=lookups_schemas.AuctionTypeRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء نوع مزاد جديد"
)
async def create_auction_type_endpoint(
    type_in: lookups_schemas.AuctionTypeCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء نوع مرجعي جديد للمزاد (مثلاً: 'مزاد عادي', 'مزاد هولندي').
    تتطلب صلاحية 'ADMIN_AUCTION_MANAGE_ANY'.
    """
    return auctions_service.create_new_auction_type(db=db, type_in=type_in)

@router.get(
    "/types",
    response_model=List[lookups_schemas.AuctionTypeRead],
    summary="[Admin] جلب جميع أنواع المزادات"
)
async def get_all_auction_types_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع أنواع المزادات المرجعية في النظام."""
    return auctions_service.get_all_auction_types_service(db=db)

@router.get(
    "/types/{auction_type_id}",
    response_model=lookups_schemas.AuctionTypeRead,
    summary="[Admin] جلب تفاصيل نوع مزاد واحد"
)
async def get_auction_type_details_endpoint(auction_type_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل نوع مرجعي لمزاد بالـ ID الخاص بها."""
    return auctions_service.get_auction_type_details(db=db, auction_type_id=auction_type_id)

@router.patch(
    "/types/{auction_type_id}",
    response_model=lookups_schemas.AuctionTypeRead,
    summary="[Admin] تحديث نوع مزاد"
)
async def update_auction_type_endpoint(
    auction_type_id: int,
    type_in: lookups_schemas.AuctionTypeUpdate,
    db: Session = Depends(get_db)
):
    """تحديث نوع مرجعي لمزاد."""
    return auctions_service.update_auction_type_service(db=db, auction_type_id=auction_type_id, type_in=type_in)

@router.delete(
    "/types/{auction_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف نوع مزاد"
)
async def delete_auction_type_endpoint(auction_type_id: int, db: Session = Depends(get_db)):
    """
    حذف نوع مرجعي لمزاد (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأي مزادات.
    """
    auctions_service.delete_auction_type_service(db=db, auction_type_id=auction_type_id)
    return

# ================================================================
# --- نقاط الوصول لترجمات أنواع المزادات (AuctionTypeTranslation) ---
# ================================================================

@router.post(
    "/types/{auction_type_id}/translations",
    response_model=lookups_schemas.AuctionTypeTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لنوع مزاد أو تحديثها"
)
async def create_auction_type_translation_endpoint(
    auction_type_id: int,
    trans_in: lookups_schemas.AuctionTypeTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء ترجمة جديدة لنوع مرجعي لمزاد بلغة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب بتضارب.
    """
    return auctions_service.create_auction_type_translation_service(db=db, auction_type_id=auction_type_id, trans_in=trans_in)

@router.get(
    "/types/{auction_type_id}/translations/{language_code}",
    response_model=lookups_schemas.AuctionTypeTranslationRead,
    summary="[Admin] جلب ترجمة محددة لنوع مزاد"
)
async def get_auction_type_translation_details_endpoint(
    auction_type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة نوع مرجعية لمزاد بلغة محددة."""
    return auctions_service.get_auction_type_translation_details(db=db, auction_type_id=auction_type_id, language_code=language_code)

@router.patch(
    "/types/{auction_type_id}/translations/{language_code}",
    response_model=lookups_schemas.AuctionTypeTranslationRead,
    summary="[Admin] تحديث ترجمة نوع مزاد"
)
async def update_auction_type_translation_endpoint(
    auction_type_id: int,
    language_code: str,
    trans_in: lookups_schemas.AuctionTypeTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة نوع مرجعية لمزاد بلغة محددة."""
    return auctions_service.update_auction_type_translation_service(db=db, auction_type_id=auction_type_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/types/{auction_type_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة نوع مزاد"
)
async def delete_auction_type_translation_endpoint(
    auction_type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة نوع مرجعية لمزاد بلغة محددة (حذف صارم)."""
    auctions_service.delete_auction_type_translation_service(db=db, auction_type_id=auction_type_id, language_code=language_code)
    return

# ================================================================
# --- نقاط الوصول لحالات تسوية المزاد (AuctionSettlementStatus) ---
# ================================================================

@router.post(
    "/settlement-statuses",
    response_model=lookups_schemas.AuctionSettlementStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة تسوية مزاد جديدة"
)
async def create_auction_settlement_status_endpoint(
    status_in: lookups_schemas.AuctionSettlementStatusCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مرجعية جديدة لتسوية المزاد (مثلاً: 'قيد الدفع', 'تم الدفع', 'تم التسوية للبائع').
    تتطلب صلاحية 'ADMIN_AUCTION_MANAGE_ANY'.
    """
    return settlements_service.create_new_auction_settlement_status(db=db, status_in=status_in)

@router.get(
    "/settlement-statuses",
    response_model=List[lookups_schemas.AuctionSettlementStatusRead],
    summary="[Admin] جلب جميع حالات تسوية المزاد"
)
async def get_all_auction_settlement_statuses_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع الحالات المرجعية لتسوية المزاد في النظام."""
    return settlements_service.get_all_auction_settlement_statuses_service(db=db)

@router.get(
    "/settlement-statuses/{settlement_status_id}",
    response_model=lookups_schemas.AuctionSettlementStatusRead,
    summary="[Admin] جلب تفاصيل حالة تسوية مزاد واحدة"
)
async def get_auction_settlement_status_details_endpoint(settlement_status_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل حالة مرجعية لتسوية مزاد بالـ ID الخاص بها."""
    return settlements_service.get_auction_settlement_status_details_service(db=db, settlement_status_id=settlement_status_id)

@router.patch(
    "/settlement-statuses/{settlement_status_id}",
    response_model=lookups_schemas.AuctionSettlementStatusRead,
    summary="[Admin] تحديث حالة تسوية مزاد"
)
async def update_auction_settlement_status_endpoint(
    settlement_status_id: int,
    status_in: lookups_schemas.AuctionSettlementStatusUpdate,
    db: Session = Depends(get_db)
):
    """تحديث حالة مرجعية لتسوية مزاد."""
    return settlements_service.update_auction_settlement_status_service(db=db, settlement_status_id=settlement_status_id, status_in=status_in)

@router.delete(
    "/settlement-statuses/{settlement_status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف حالة تسوية مزاد"
)
async def delete_auction_settlement_status_endpoint(settlement_status_id: int, db: Session = Depends(get_db)):
    """
    حذف حالة مرجعية لتسوية مزاد (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأي تسويات.
    """
    settlements_service.delete_auction_settlement_status_service(db=db, settlement_status_id=settlement_status_id)
    return

# ================================================================
# --- نقاط الوصول لترجمات حالات تسوية المزاد (AuctionSettlementStatusTranslation) ---
# ================================================================

@router.post(
    "/settlement-statuses/{settlement_status_id}/translations",
    response_model=lookups_schemas.AuctionSettlementStatusTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لحالة تسوية مزاد أو تحديثها"
)
async def create_auction_settlement_status_translation_endpoint(
    settlement_status_id: int,
    trans_in: lookups_schemas.AuctionSettlementStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء ترجمة جديدة لحالة مرجعية لتسوية مزاد بلغة معينة.
    إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب بتضارب.
    """
    return settlements_service.create_auction_settlement_status_translation_service(db=db, settlement_status_id=settlement_status_id, trans_in=trans_in)

@router.get(
    "/settlement-statuses/{settlement_status_id}/translations/{language_code}",
    response_model=lookups_schemas.AuctionSettlementStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة تسوية مزاد"
)
async def get_auction_settlement_status_translation_details_endpoint(
    settlement_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة حالة مرجعية لتسوية مزاد بلغة محددة."""
    return settlements_service.get_auction_settlement_status_translation_details(db=db, settlement_status_id=settlement_status_id, language_code=language_code)

@router.patch(
    "/settlement-statuses/{settlement_status_id}/translations/{language_code}",
    response_model=lookups_schemas.AuctionSettlementStatusTranslationRead,
    summary="[Admin] تحديث ترجمة حالة تسوية مزاد"
)
async def update_auction_settlement_status_translation_endpoint(
    settlement_status_id: int,
    language_code: str,
    trans_in: lookups_schemas.AuctionSettlementStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة حالة مرجعية لتسوية مزاد بلغة محددة."""
    return settlements_service.update_auction_settlement_status_translation_service(db=db, settlement_status_id=settlement_status_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/settlement-statuses/{settlement_status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة حالة تسوية مزاد"
)
async def delete_auction_settlement_status_translation_endpoint(
    settlement_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة حالة مرجعية لتسوية مزاد بلغة محددة (حذف صارم)."""
    settlements_service.delete_auction_settlement_status_translation_service(db=db, settlement_status_id=settlement_status_id, language_code=language_code)
    return