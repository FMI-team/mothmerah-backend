# backend\src\api\v1\routers\auctions_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين والمزادات

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User # مودل المستخدم، للتحقق من الصلاحيات

# استيراد Schemas (هياكل البيانات) الخاصة بالمزادات
from src.auctions.schemas import auction_schemas as auction_schemas # لـ Auction, AuctionLot
from src.auctions.schemas import bidding_schemas as bidding_schemas # لـ Bid, AutoBidSetting, AuctionParticipant, AuctionWatchlist

# استيراد الخدمات (منطق العمل) المتعلقة بالمزادات
from src.auctions.services import auctions_service
from src.auctions.services import bidding_service

# تعريف الراوتر الرئيسي لوحدة إدارة المزادات.
# هذا الراوتر سيتعامل مع نقاط الوصول المتعلقة بالمزادات للمشترين والبائعين.
router = APIRouter(
    prefix="/auctions", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/auctions)
    tags=["Auction Management - User Facing"] # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
)

# ================================================================
# --- نقاط الوصول للمزادات (Auction) ---
#    (تتطلب صلاحية AUCTION_CREATE_OWN للبائع، وصلاحيات VIEW/BID للمشترين)
# ================================================================

@router.post(
    "/",
    response_model=auction_schemas.AuctionRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller] إنشاء مزاد جديد",
    description="""
    يسمح للبائع بإنشاء مزاد جديد مع تفاصيله ولوطاته.
    تُعيّن الحالة الأولية للمزاد تلقائيًا (عادةً 'مجدول').
    يتطلب صلاحية 'AUCTION_CREATE_OWN'.
    """,
)
async def create_new_auction_endpoint(
    auction_in: auction_schemas.AuctionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_CREATE_OWN"))
):
    """نقطة وصول لإنشاء مزاد جديد."""
    return auctions_service.create_new_auction(db=db, auction_in=auction_in, current_user=current_user)

@router.get(
    "/",
    response_model=List[auction_schemas.AuctionRead],
    summary="[Public] جلب جميع المزادات المتاحة",
    description="""
    يجلب قائمة بالمزادات المتاحة (النشطة والمجدولة) في النظام.
    متاحة للعامة (غير المصادقين) لغرض التصفح، وقد تظهر تفاصيل إضافية للمستخدمين المسجلين.
    """,
)
async def get_all_public_auctions_endpoint(
    db: Session = Depends(get_db),
    status_name_key: Optional[str] = "ACTIVE", # افتراضيًا جلب النشطة
    type_name_key: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب جميع المزادات المتاحة."""
    return auctions_service.get_all_auctions(
        db=db, status_name_key=status_name_key, type_name_key=type_name_key, skip=skip, limit=limit
    )

@router.get(
    "/me/created",
    response_model=List[auction_schemas.AuctionRead],
    summary="[Seller] جلب المزادات التي أنشأتها",
    description="""
    يجلب قائمة بجميع المزادات التي قام البائع الحالي بإنشائها.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def get_my_created_auctions_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN")),
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب المزادات التي أنشأها البائع الحالي."""
    return auctions_service.get_my_created_auctions(db=db, current_user=current_user, skip=skip, limit=limit)


@router.get(
    "/{auction_id}",
    response_model=auction_schemas.AuctionRead,
    summary="[Public] جلب تفاصيل مزاد واحد",
    description="""
    يجلب التفاصيل الكاملة لمزاد محدد بالـ ID الخاص به.
    متاح للعامة، ولكن قد تظهر تفاصيل إضافية للمشاركين أو للمالك (مثل سجل المزايدات الكامل).
    """,
)
async def get_auction_details_endpoint(
    auction_id: UUID,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب تفاصيل مزاد محدد."""
    # خدمة get_auction_details لا تتحقق من المستخدم، التحقق من الصلاحيات الإضافية سيكون في وظائف أخرى
    return auctions_service.get_auction_details(db=db, auction_id=auction_id)

@router.patch(
    "/{auction_id}",
    response_model=auction_schemas.AuctionRead,
    summary="[Seller] تحديث مزاد",
    description="""
    يسمح للبائع بتحديث تفاصيل مزاد يملكه.
    يمكن تعديل المزادات فقط عندما تكون 'مجدولة' وقبل أن تبدأ.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def update_auction_endpoint(
    auction_id: UUID,
    auction_in: auction_schemas.AuctionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لتحديث مزاد محدد."""
    return auctions_service.update_auction(db=db, auction_id=auction_id, auction_in=auction_in, current_user=current_user)

@router.delete(
    "/{auction_id}",
    response_model=auction_schemas.AuctionRead, # ترجع الكائن بعد تحديث حالته إلى "ملغى"
    summary="[Seller] إلغاء مزاد",
    description="""
    يسمح للبائع بإلغاء مزاد يملكه (يعادل الحذف الناعم).
    يمكن إلغاء المزادات فقط إذا كانت 'مجدولة' ولم تتلق مزايدات بعد.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def cancel_auction_endpoint(
    auction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لإلغاء (حذف ناعم) مزاد محدد."""
    return auctions_service.cancel_auction(db=db, auction_id=auction_id, current_user=current_user)

# ================================================================
# --- نقاط الوصول لوطات/دفعات المزاد (AuctionLot) ---
#    (تتطلب صلاحية AUCTION_MANAGE_OWN)
# ================================================================

@router.post(
    "/{auction_id}/lots",
    response_model=auction_schemas.AuctionLotRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller] إنشاء لوت مزاد جديد",
    description="""
    يسمح للبائع بإنشاء لوت (دفعة) جديدة ضمن مزاد معين.
    يمكن إضافة لوطات فقط للمزادات المجدولة وقبل أن تبدأ.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def create_auction_lot_endpoint(
    auction_id: UUID,
    lot_in: auction_schemas.AuctionLotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لإنشاء لوت مزاد جديد."""
    if lot_in.auction_id != auction_id:
        raise BadRequestException(detail="معرف المزاد في المسار لا يتطابق مع معرف المزاد في البيانات.")
    return auctions_service.create_auction_lot(db=db, lot_in=lot_in, current_user=current_user)

@router.get(
    "/{auction_id}/lots",
    response_model=List[auction_schemas.AuctionLotRead],
    summary="[Public] جلب لوطات مزاد معين",
    description="""
    يجلب قائمة بجميع اللوطات (الدفعات) ضمن مزاد محدد.
    متاح للعامة لغرض العرض.
    """,
)
async def get_all_auction_lots_for_auction_endpoint(
    auction_id: UUID,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب لوطات مزاد معين."""
    return auctions_service.get_all_auction_lots_for_auction(db=db, auction_id=auction_id)

@router.get(
    "/lots/{lot_id}",
    response_model=auction_schemas.AuctionLotRead,
    summary="[Public] جلب تفاصيل لوت مزاد واحد",
    description="""
    يجلب التفاصيل الكاملة للوت مزاد محدد بالـ ID الخاص به.
    متاح للعامة.
    """,
)
async def get_auction_lot_details_endpoint(
    lot_id: UUID,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب تفاصيل لوت مزاد محدد."""
    return auctions_service.get_auction_lot_details(db=db, lot_id=lot_id)

@router.patch(
    "/lots/{lot_id}",
    response_model=auction_schemas.AuctionLotRead,
    summary="[Seller] تحديث لوت مزاد",
    description="""
    يسمح للبائع بتحديث تفاصيل لوت مزاد يملكه.
    يمكن تعديل اللوطات فقط إذا كان المزاد الأم 'مجدولاً' وقبل أن يبدأ.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def update_auction_lot_endpoint(
    lot_id: UUID,
    lot_in: auction_schemas.AuctionLotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لتحديث لوت مزاد محدد."""
    return auctions_service.update_auction_lot(db=db, lot_id=lot_id, lot_in=lot_in, current_user=current_user)

@router.delete(
    "/lots/{lot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Seller] حذف لوت مزاد",
    description="""
    يسمح للبائع بحذف لوت مزاد يملكه (حذف صارم).
    يمكن حذف اللوطات فقط إذا كان المزاد الأم 'مجدولاً' ولم يتلق مزايدات بعد.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def delete_auction_lot_endpoint(
    lot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لحذف لوت مزاد محدد."""
    auctions_service.delete_auction_lot(db=db, lot_id=lot_id, current_user=current_user)
    return


# ================================================================
# --- نقاط الوصول لترجمات لوطات المزاد (AuctionLotTranslation) ---
# ================================================================

@router.post(
    "/lots/{lot_id}/translations",
    response_model=auction_schemas.AuctionLotTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller] إنشاء/تحديث ترجمة للوت مزاد",
    description="""
    يسمح للبائع بإنشاء ترجمة جديدة (أو تحديث ترجمة موجودة بنفس اللغة) للوت مزاد.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """
)
async def create_auction_lot_translation_endpoint(
    lot_id: UUID,
    trans_in: auction_schemas.AuctionLotTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لإنشاء/تحديث ترجمة للوت مزاد."""
    return auctions_service.create_auction_lot_translation(db=db, lot_id=lot_id, trans_in=trans_in, current_user=current_user)

@router.get(
    "/lots/{lot_id}/translations/{language_code}",
    response_model=auction_schemas.AuctionLotTranslationRead,
    summary="[Public] جلب ترجمة محددة للوت مزاد",
    description="""
    يجلب ترجمة محددة للوت مزاد بلغة معينة.
    متاح للعامة لغرض العرض.
    """,
)
async def get_auction_lot_translation_details_endpoint(
    lot_id: UUID,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة محددة للوت مزاد."""
    return auctions_service.get_auction_lot_translation_details(db=db, lot_id=lot_id, language_code=language_code)

@router.patch(
    "/lots/{lot_id}/translations/{language_code}",
    response_model=auction_schemas.AuctionLotTranslationRead,
    summary="[Seller] تحديث ترجمة لوت مزاد",
    description="""
    يسمح للبائع بتحديث ترجمة موجودة للوت مزاد.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """
)
async def update_auction_lot_translation_endpoint(
    lot_id: UUID,
    language_code: str,
    trans_in: auction_schemas.AuctionLotTranslationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لتحديث ترجمة لوت مزاد."""
    return auctions_service.update_auction_lot_translation(db=db, lot_id=lot_id, language_code=language_code, trans_in=trans_in, current_user=current_user)

@router.delete(
    "/lots/{lot_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Seller] حذف ترجمة لوت مزاد",
    description="""
    يسمح للبائع بحذف ترجمة معينة للوت مزاد (حذف صارم).
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def delete_auction_lot_translation_endpoint(
    lot_id: UUID,
    language_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لحذف ترجمة لوت مزاد."""
    auctions_service.delete_auction_lot_translation(db=db, lot_id=lot_id, language_code=language_code, current_user=current_user)
    return

# ================================================================
# --- نقاط الوصول لمنتجات اللوت (LotProduct) ---
# ================================================================

@router.post(
    "/lots/{lot_id}/products",
    response_model=auction_schemas.LotProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller] إضافة منتج لوت جديد",
    description="""
    يسمح للبائع بإضافة منتج جديد إلى لوت مزاد مجمع.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def create_lot_product_endpoint(
    lot_id: UUID,
    lot_product_in: auction_schemas.LotProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لإضافة منتج لوت جديد."""
    if lot_product_in.lot_id != lot_id:
        raise BadRequestException(detail="معرف اللوت في المسار لا يتطابق مع معرف اللوت في البيانات.")
    return auctions_service.create_lot_product(db=db, lot_product_in=lot_product_in, current_user=current_user)

@router.get(
    "/lots/{lot_id}/products",
    response_model=List[auction_schemas.LotProductRead],
    summary="[Public] جلب منتجات لوت مزاد معين",
    description="""
    يجلب قائمة بجميع المنتجات المحددة ضمن لوت مزاد مجمع.
    متاح للعامة لغرض العرض.
    """,
)
async def get_all_lot_products_for_lot_endpoint(
    lot_id: UUID,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب منتجات لوت مزاد معين."""
    return auctions_service.get_all_lot_products_for_lot(db=db, lot_id=lot_id)

@router.get(
    "/lots/products/{lot_product_id}",
    response_model=auction_schemas.LotProductRead,
    summary="[Public] جلب تفاصيل منتج لوت واحد",
    description="""
    يجلب التفاصيل الكاملة لمنتج لوت محدد بالـ ID الخاص به.
    متاح للعامة.
    """,
)
async def get_lot_product_details_endpoint(
    lot_product_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب تفاصيل منتج لوت محدد."""
    return auctions_service.get_lot_product_details(db=db, lot_product_id=lot_product_id)

@router.patch(
    "/lots/products/{lot_product_id}",
    response_model=auction_schemas.LotProductRead,
    summary="[Seller] تحديث منتج لوت",
    description="""
    يسمح للبائع بتحديث تفاصيل منتج لوت موجود (مثل الكمية).
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def update_lot_product_endpoint(
    lot_product_id: int,
    lot_product_in: auction_schemas.LotProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لتحديث منتج لوت محدد."""
    return auctions_service.update_lot_product(db=db, lot_product_id=lot_product_id, lot_product_in=lot_product_in, current_user=current_user)

@router.delete(
    "/lots/products/{lot_product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Seller] حذف منتج لوت",
    description="""
    يسمح للبائع بحذف منتج لوت محدد (حذف صارم).
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def delete_lot_product_endpoint(
    lot_product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لحذف منتج لوت محدد."""
    auctions_service.delete_lot_product(db=db, lot_product_id=lot_product_id, current_user=current_user)
    return


# ================================================================
# --- نقاط الوصول لصور اللوت (LotImage) ---
# ================================================================

@router.post(
    "/lots/{lot_id}/images",
    response_model=auction_schemas.LotImageRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller] إضافة صورة جديدة للوت مزاد",
    description="""
    يسمح للبائع بإضافة صورة جديدة إلى لوت مزاد.
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def create_lot_image_endpoint(
    lot_id: UUID,
    lot_image_in: auction_schemas.LotImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لإضافة صورة جديدة للوت مزاد."""
    if lot_image_in.lot_id != lot_id:
        raise BadRequestException(detail="معرف اللوت في المسار لا يتطابق مع معرف اللوت في البيانات.")
    return auctions_service.create_lot_image(db=db, lot_image_in=lot_image_in, current_user=current_user)

@router.get(
    "/lots/{lot_id}/images",
    response_model=List[auction_schemas.LotImageRead],
    summary="[Public] جلب صور لوت مزاد معين",
    description="""
    يجلب قائمة بجميع الصور المرتبطة بلوت مزاد معين.
    متاح للعامة لغرض العرض.
    """,
)
async def get_all_lot_images_for_lot_endpoint(
    lot_id: UUID,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب صور لوت مزاد معين."""
    return auctions_service.get_all_lot_images_for_lot(db=db, lot_id=lot_id)

@router.get(
    "/lots/images/{lot_image_id}",
    response_model=auction_schemas.LotImageRead,
    summary="[Public] جلب تفاصيل صورة لوت واحدة",
    description="""
    يجلب التفاصيل الكاملة لصورة لوت محددة بالـ ID الخاص بها.
    متاح للعامة.
    """,
)
async def get_lot_image_details_endpoint(
    lot_image_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب تفاصيل صورة لوت محددة."""
    return auctions_service.get_lot_image_details(db=db, lot_image_id=lot_image_id)

@router.patch(
    "/lots/images/{lot_image_id}",
    response_model=auction_schemas.LotImageRead,
    summary="[Seller] تحديث صورة لوت",
    description="""
    يسمح للبائع بتحديث تفاصيل صورة لوت موجودة (مثل ترتيب العرض).
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def update_lot_image_endpoint(
    lot_image_id: int,
    lot_image_in: auction_schemas.LotImageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لتحديث صورة لوت محددة."""
    return auctions_service.update_lot_image(db=db, lot_image_id=lot_image_id, lot_image_in=lot_image_in, current_user=current_user)

@router.delete(
    "/lots/images/{lot_image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Seller] حذف صورة لوت",
    description="""
    يسمح للبائع بحذف صورة لوت محددة (حذف صارم).
    يتطلب صلاحية 'AUCTION_MANAGE_OWN'.
    """,
)
async def delete_lot_image_endpoint(
    lot_image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("AUCTION_MANAGE_OWN"))
):
    """نقطة وصول لحذف صورة لوت محددة."""
    auctions_service.delete_lot_image(db=db, lot_image_id=lot_image_id, current_user=current_user)
    return