# backend\src\auction\services\settlements_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # لاستخدام التواريخ والأوقات

# استيراد المودلز
from src.auctions.models import settlements_models as models_settlements
from src.auctions.models import auctions_models as models_auction # لـ Auction في العلاقات
from src.auctions.models import bidding_models as models_bidding # لـ Bid في العلاقات
from src.users.models.core_models import User # لـ User في العلاقات
# استيراد Schemas
from src.auctions.schemas import settlement_schemas as schemas
# استيراد دوال الـ CRUD
from src.auctions.crud import settlements_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.lookups.schemas import lookups_schemas as schemas_lookups

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.auctions.services.auctions_service import get_auction_details # للتحقق من وجود المزاد
from src.auctions.services.bidding_service import get_bid_details_service # للتحقق من وجود المزايدة الفائزة
from src.users.services.core_service import get_user_profile # للتحقق من وجود المستخدمين الفائز/البائع
# TODO: خدمة المحفظة (wallet_service) من Module 8 لمعالجة الدفع والتحصيل.
# TODO: خدمة الطلبات (orders_service) من Module 4 لإنشاء الطلب بعد التسوية.
# TODO: خدمة الإشعارات (notifications_service) من Module 11 لإرسال الإشعارات.


# ==========================================================
# --- خدمات تسويات المزادات (AuctionSettlement) ---
# ==========================================================

def create_auction_settlement(db: Session, settlement_in: schemas.AuctionSettlementCreate, current_user: User) -> models_settlements.AuctionSettlement:
    """
    خدمة لإنشاء سجل تسوية مزاد جديد.
    تتضمن التحقق من وجود المزاد والمزايدة الفائزة والمستخدمين، وتعيين الحالة الأولية.
    هذه العملية يجب أن يتم استدعاؤها بعد انتهاء المزاد وتحديد الفائز.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_in (schemas.AuctionSettlementCreate): بيانات التسوية للإنشاء.
        current_user (User): المستخدم الذي يقوم بإنشاء التسوية (غالباً النظام أو المسؤول).

    Returns:
        models_settlements.AuctionSettlement: كائن التسوية الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد، المزايدة، أو المستخدمين المرتبطين.
        ForbiddenException: إذا كان المستخدم غير مصرح له بإنشاء التسوية.
        BadRequestException: إذا كانت البيانات غير صالحة.
        ConflictException: إذا لم يتم العثور على حالة التسوية الأولية.
    """
    # 1. التحقق من صلاحيات المستخدم (يجب أن يكون مسؤول نظام أو خدمة خلفية)
    if not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بإنشاء تسوية مزاد.")

    # 2. التحقق من وجود المزاد والمزايدة الفائزة والمستخدمين
    db_auction = get_auction_details(db, settlement_in.auction_id)
    winning_bid = get_bid_details(db, settlement_in.winning_bid_id)
    winner_user = get_user_by_id(db, settlement_in.winner_user_id)
    seller_user = get_user_by_id(db, settlement_in.seller_user_id)

    # 3. التحقق من منطقية البيانات (مثلاً المزايدة الفائزة تنتمي للمزاد)
    if winning_bid.auction_id != db_auction.auction_id:
        raise BadRequestException(detail="المزايدة الفائزة لا تنتمي إلى هذا المزاد.")
    if winning_bid.bidder_user_id != winner_user.user_id:
        raise BadRequestException(detail="المزايد الفائز لا يتطابق مع المزايد في المزايدة الفائزة.")
    if db_auction.seller_user_id != seller_user.user_id:
        raise BadRequestException(detail="البائع في التسوية لا يتطابق مع بائع المزاد.")

    # 4. جلب الحالة الأولية للتسوية (مثلاً 'PENDING_PAYMENT')
    initial_settlement_status = db.query(models_settlements.AuctionSettlementStatus).filter(models_settlements.AuctionSettlementStatus.status_name_key == "PENDING_PAYMENT").first()
    if not initial_settlement_status:
        raise ConflictException(detail="حالة التسوية الأولية 'PENDING_PAYMENT' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    # 5. تعيين الحقول المحسوبة
    settlement_in.final_winning_price_per_unit = winning_bid.bid_amount_per_unit
    settlement_in.quantity_won = db_auction.quantity_offered # أو الكمية في اللوت إذا كان المزاد بلوطات

    settlement_in.total_settlement_amount = settlement_in.final_winning_price_per_unit * settlement_in.quantity_won
    
    # TODO: حساب عمولة المنصة (Module 8) وخصمها
    platform_commission_amount = 0.0 # Placeholder
    # TODO: ربط platform_commission_id هنا
    
    settlement_in.net_amount_to_seller = settlement_in.total_settlement_amount - platform_commission_amount
    settlement_in.settlement_status_id = initial_settlement_status.settlement_status_id
    settlement_in.settlement_timestamp = datetime.now(timezone.utc)

    # 6. استدعاء CRUD لإنشاء التسوية
    db_settlement = settlements_crud.create_auction_settlement(db=db, settlement_in=settlement_in)

    db.commit()
    db.refresh(db_settlement)

    # TODO: هـام: بدء عملية الدفع من المشتري الفائز (وحدة المحفظة - Module 8).
    #       مثلاً: wallet_service.deduct_funds_for_settlement(winner_user_id, total_settlement_amount, db_settlement.settlement_id)
    #       وربط payment_transaction_id.

    # TODO: هـام: إنشاء سجل طلب (Order) في Module 4 لتوثيق الصفقة.
    #       orders_service.create_new_order(...)

    # TODO: إخطار المشتري الفائز والبائع بأن المزاد قد تم تسويته وبدء عملية الدفع (وحدة الإشعارات).

    return db_settlement

def get_auction_settlement_details(db: Session, settlement_id: int, current_user: User) -> models_settlements.AuctionSettlement:
    """
    خدمة لجلب تفاصيل تسوية مزاد واحد بالـ ID، مع التحقق من صلاحيات المشتري الفائز أو البائع أو المسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_id (int): معرف التسوية المطلوب.
        current_user (User): المستخدم الحالي.

    Returns:
        models_settlements.AuctionSettlement: كائن التسوية المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على التسوية.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية التسوية.
    """
    settlement = settlements_crud.get_auction_settlement(db, settlement_id=settlement_id)
    if not settlement:
        raise NotFoundException(detail=f"تسوية المزاد بمعرف {settlement_id} غير موجودة.")

    # التحقق من الصلاحيات: الفائز، البائع، أو المسؤول
    is_winner = settlement.winner_user_id == current_user.user_id
    is_seller = settlement.seller_user_id == current_user.user_id
    is_admin = any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions) # TODO: صلاحية view settlement

    if not (is_winner or is_seller or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل تسوية المزاد هذه.")
    
    return settlement

def get_all_auction_settlements(db: Session, auction_id: Optional[UUID] = None, winner_user_id: Optional[UUID] = None, seller_user_id: Optional[UUID] = None, settlement_status_name_key: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models_settlements.AuctionSettlement]:
    """
    خدمة لجلب جميع تسويات المزادات، مع خيارات للتصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (Optional[UUID]): تصفية حسب معرف المزاد.
        winner_user_id (Optional[UUID]): تصفية حسب معرف المستخدم الفائز.
        seller_user_id (Optional[UUID]): تصفية حسب معرف البائع.
        settlement_status_name_key (Optional[str]): تصفية حسب مفتاح اسم حالة التسوية.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_settlements.AuctionSettlement]: قائمة بكائنات التسويات.

    Raises:
        BadRequestException: إذا كانت مفتاح حالة التسوية غير موجود.
    """
    settlement_status_id = None
    if settlement_status_name_key:
        status_obj = db.query(models_settlements.AuctionSettlementStatus).filter(models_settlements.AuctionSettlementStatus.status_name_key == settlement_status_name_key).first()
        if not status_obj:
            raise BadRequestException(detail=f"حالة التسوية '{settlement_status_name_key}' غير موجودة.")
        settlement_status_id = status_obj.settlement_status_id

    return settlements_crud.get_all_auction_settlements(
        db,
        auction_id=auction_id,
        winner_user_id=winner_user_id,
        seller_user_id=seller_user_id,
        settlement_status_id=settlement_status_id,
        skip=skip,
        limit=limit
    )

def update_auction_settlement(db: Session, settlement_id: int, settlement_in: schemas.AuctionSettlementUpdate, current_user: User) -> models_settlements.AuctionSettlement:
    """
    خدمة لتحديث سجل تسوية مزاد موجود.
    تتضمن التحقق من صلاحيات المسؤول فقط.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_id (int): معرف التسوية المراد تحديثها.
        settlement_in (schemas.AuctionSettlementUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_settlements.AuctionSettlement: كائن التسوية المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على التسوية.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له (ليس مسؤولاً).
        BadRequestException: إذا كانت البيانات غير صالحة.
        ConflictException: إذا لم يتم العثور على حالة التسوية الجديدة.
    """
    db_settlement = get_auction_settlement_details(db, settlement_id, current_user) # تتحقق من الوجود والصلاحيات

    # التحقق من أن المستخدم مسؤول فقط (للسماح بتعديل التسوية)
    if not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions): # TODO: صلاحية ADMIN_SETTLEMENT_MANAGE_ANY
        raise ForbiddenException(detail="غير مصرح لك بتحديث تسوية المزاد هذه.")

    # التحقق من وجود الحالة الجديدة إذا تم تحديثها
    if settlement_in.settlement_status_id:
        new_status = db.query(models_settlements.AuctionSettlementStatus).filter(models_settlements.AuctionSettlementStatus.settlement_status_id == settlement_in.settlement_status_id).first()
        if not new_status:
            raise BadRequestException(detail=f"حالة التسوية بمعرف {settlement_in.settlement_status_id} غير موجودة.")
        # TODO: آلة حالة التسوية: التحقق من الانتقالات المسموح بها.

    return settlements_crud.update_auction_settlement(db=db, db_settlement=db_settlement, settlement_in=settlement_in)

def update_auction_settlement_status(db: Session, settlement_id: int, new_status_id: int, current_user: User) -> models_settlements.AuctionSettlement:
    """
    خدمة لتحديث حالة تسوية مزاد.
    تتضمن التحقق من صلاحيات المسؤول فقط.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_id (int): معرف التسوية المراد تحديث حالتها.
        new_status_id (int): معرف الحالة الجديدة.
        current_user (User): المستخدم الحالي.

    Returns:
        models_settlements.AuctionSettlement: كائن التسوية بعد تحديث حالتها.

    Raises:
        NotFoundException: إذا لم يتم العثور على التسوية أو الحالة الجديدة.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له.
        BadRequestException: إذا كانت الحالة الجديدة غير موجودة أو الانتقال غير مسموح به.
    """
    db_settlement = get_auction_settlement_details(db, settlement_id, current_user) # تتحقق من الوجود والصلاحيات

    # التحقق من أن المستخدم مسؤول فقط
    if not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions): # TODO: صلاحية ADMIN_SETTLEMENT_MANAGE_ANY
        raise ForbiddenException(detail="غير مصرح لك بتغيير حالة تسوية المزاد هذه.")

    # التحقق من وجود الحالة الجديدة
    new_status = db.query(models_settlements.AuctionSettlementStatus).filter(models_settlements.AuctionSettlementStatus.settlement_status_id == new_status_id).first()
    if not new_status:
        raise BadRequestException(detail=f"حالة التسوية بمعرف {new_status_id} غير موجودة.")
    
    # TODO: آلة حالة التسوية: التحقق من الانتقالات المسموح بها.

    return settlements_crud.update_auction_settlement_status(db=db, db_settlement=db_settlement, new_status_id=new_status_id)


# ==========================================================
# --- خدمات حالات تسوية المزاد (AuctionSettlementStatus) ---
# ==========================================================

def create_new_auction_settlement_status(db: Session, status_in: schemas_lookups.AuctionSettlementStatusCreate) -> models_settlements.AuctionSettlementStatus:
    """
    خدمة لإنشاء حالة تسوية مزاد جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas.AuctionSettlementStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        models_settlements.AuctionSettlementStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    if db.query(models_settlements.AuctionSettlementStatus).filter(models_settlements.AuctionSettlementStatus.status_name_key == status_in.status_name_key).first():
        raise ConflictException(detail=f"حالة تسوية المزاد بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return settlements_crud.create_auction_settlement_status(db=db, status_in=status_in)

def get_auction_settlement_status_details_service(db: Session, settlement_status_id: int) -> models_settlements.AuctionSettlementStatus:
    """
    خدمة لجلب حالة تسوية مزاد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة.

    Returns:
        models_settlements.AuctionSettlementStatus: كائن الحالة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
    """
    status_obj = settlements_crud.get_auction_settlement_status(db, settlement_status_id=settlement_status_id)
    if not status_obj:
        raise NotFoundException(detail=f"حالة تسوية المزاد بمعرف {settlement_status_id} غير موجودة.")
    return status_obj

def get_all_auction_settlement_statuses_service(db: Session) -> List[models_settlements.AuctionSettlementStatus]:
    """
    خدمة لجلب جميع حالات تسوية المزاد المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[models_settlements.AuctionSettlementStatus]: قائمة بكائنات الحالات.
    """
    return settlements_crud.get_all_auction_settlement_statuses(db)

def update_auction_settlement_status_service(db: Session, settlement_status_id: int, status_in: schemas_lookups.AuctionSettlementStatusUpdate) -> models_settlements.AuctionSettlementStatus:
    """
    خدمة لتحديث حالة تسوية مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas.AuctionSettlementStatusUpdate): البيانات المراد تحديثها.

    Returns:
        models_settlements.AuctionSettlementStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_auction_settlement_status_details_service(db, settlement_status_id)
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        if db.query(models_settlements.AuctionSettlementStatus).filter(models_settlements.AuctionSettlementStatus.status_name_key == status_in.status_name_key).first():
            raise ConflictException(detail=f"حالة تسوية المزاد بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return settlements_crud.update_auction_settlement_status_crud(db=db, db_status=db_status, status_in=status_in)

def delete_auction_settlement_status_service(db: Session, settlement_status_id: int):
    """
    خدمة لحذف حالة تسوية مزاد (حذف صارم).
    تتضمن التحقق من عدم وجود تسويات مرتبطة بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ForbiddenException: إذا كانت الحالة مستخدمة حاليًا بواسطة أي تسويات.
    """
    db_status = get_auction_settlement_status_details_service(db, settlement_status_id)
    # TODO: التحقق من عدم وجود AuctionSettlement تستخدم settlement_status_id هذا
    # from src.auctions.models.settlements_models import AuctionSettlement
    # if db.query(AuctionSettlement).filter(AuctionSettlement.settlement_status_id == settlement_status_id).count() > 0:
    #     raise ForbiddenException(detail=f"لا يمكن حذف حالة تسوية المزاد بمعرف {settlement_status_id} لأنها تستخدم من قبل تسويات مزادات موجودة.")
    settlements_crud.delete_auction_settlement_status(db=db, db_status=db_status)
    return {"message": "تم حذف حالة تسوية المزاد بنجاح."}


# ==========================================================
# --- خدمات ترجمات حالات تسوية المزاد (AuctionSettlementStatusTranslation) ---
# ==========================================================

def create_auction_settlement_status_translation_service(db: Session, settlement_status_id: int, trans_in: schemas_lookups.AuctionSettlementStatusTranslationCreate) -> models_settlements.AuctionSettlementStatusTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لحالة تسوية مزاد معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة الأم.
        trans_in (schemas.AuctionSettlementStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models_settlements.AuctionSettlementStatusTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة الأم.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    get_auction_settlement_status_details_service(db, settlement_status_id)
    if settlements_crud.get_auction_settlement_status_translation(db, settlement_status_id=settlement_status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة لحالة تسوية المزاد بمعرف {settlement_status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")
    return settlements_crud.create_auction_settlement_status_translation(db=db, settlement_status_id=settlement_status_id, trans_in=trans_in)

def get_auction_settlement_status_translation_details(db: Session, settlement_status_id: int, language_code: str) -> models_settlements.AuctionSettlementStatusTranslation:
    """
    خدمة لجلب ترجمة حالة تسوية مزاد محددة بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة.

    Returns:
        models_settlements.AuctionSettlementStatusTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = settlements_crud.get_auction_settlement_status_translation(db, settlement_status_id=settlement_status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة تسوية المزاد بمعرف {settlement_status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_auction_settlement_status_translation_service(db: Session, settlement_status_id: int, language_code: str, trans_in: schemas_lookups.AuctionSettlementStatusTranslationUpdate) -> models_settlements.AuctionSettlementStatusTranslation:
    """
    خدمة لتحديث ترجمة حالة تسوية مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.AuctionSettlementStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models_settlements.AuctionSettlementStatusTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_auction_settlement_status_translation_details(db, settlement_status_id, language_code)
    return settlements_crud.update_auction_settlement_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_auction_settlement_status_translation_service(db: Session, settlement_status_id: int, language_code: str):
    """
    خدمة لحذف ترجمة حالة تسوية مزاد معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_auction_settlement_status_translation_details(db, settlement_status_id, language_code)
    settlements_crud.delete_auction_settlement_status_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة حالة تسوية المزاد بنجاح."}
