# backend\src\auction\services\bidding_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

# استيراد المودلز
from src.auctions.models import bidding_models as models_bidding
from src.auctions.models import auctions_models as models_auction # لـ Auction في العلاقات
from src.users.models.core_models import User # لـ User في العلاقات
# استيراد Schemas
from src.auctions.schemas import bidding_schemas as schemas
# استيراد دوال الـ CRUD
from src.auctions.crud import bidding_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.auctions.services.auctions_service import get_auction_details # للتحقق من وجود المزاد
from src.users.services.core_service import get_user_profile # للتحقق من وجود المستخدم
# TODO: خدمة المحفظة (wallet_service) من Module 8 للتحقق من الرصيد وحجزه.
# TODO: خدمة الإشعارات (notifications_service) من Module 11 لإرسال الإشعارات.


# ==========================================================
# --- خدمات المشاركين في المزاد (AuctionParticipant) ---
# ==========================================================

def create_auction_participant(db: Session, participant_in: schemas.AuctionParticipantCreate, current_user: User) -> models_bidding.AuctionParticipant:
    """
    خدمة لتسجيل مشارك جديد في مزاد معين.
    تتضمن التحقق من وجود المزاد والمستخدم، ومنع التكرار، وتعيين حالة المشاركة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        participant_in (schemas.AuctionParticipantCreate): بيانات المشارك للإنشاء.
        current_user (User): المستخدم الحالي الذي يحاول المشاركة.

    Returns:
        models_bidding.AuctionParticipant: كائن المشارك الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد أو المستخدم.
        ConflictException: إذا كان المستخدم مسجلاً بالفعل في هذا المزاد.
        ForbiddenException: إذا كان المستخدم غير مؤهل للمشاركة (مثلاً البائع نفسه).
        BadRequestException: إذا كان المزاد في حالة لا تسمح بالتسجيل.
    """
    # 1. التحقق من وجود المزاد والمستخدم
    db_auction = get_auction_details(db, participant_in.auction_id)
    get_user_by_id(db, participant_in.user_id) # يجب أن يكون user_id هو current_user.user_id

    # 2. التحقق من أن المستخدم ليس هو بائع المزاد
    if db_auction.seller_user_id == current_user.user_id:
        raise ForbiddenException(detail="لا يمكن لبائع المزاد المشاركة كمزايد في مزاده الخاص.")

    # 3. التحقق من عدم تكرار التسجيل
    existing_participant = bidding_crud.get_auto_bid_setting_by_user_and_auction(db, user_id=current_user.user_id, auction_id=participant_in.auction_id) # استخدام نفس دالة الجلب للمفتاح الفريد
    if existing_participant:
        raise ConflictException(detail="أنت مسجل بالفعل في هذا المزاد.")

    # 4. التحقق من حالة المزاد (يجب أن يكون 'SCHEDULED' أو 'ACTIVE' للسماح بالتسجيل)
    if db_auction.auction_status.status_name_key not in ["SCHEDULED", "ACTIVE"]:
        raise BadRequestException(detail=f"لا يمكن التسجيل في مزاد في حالته الحالية: {db_auction.auction_status.status_name_key}.")

    # 5. تعيين حالة المشاركة الأولية (مثلاً 'REGISTERED')
    initial_status = "REGISTERED"
    # TODO: يمكن إضافة منطق معقد لتحديد الأهلية المسبقة (مثل التحقق من الرصيد) وتعيين حالة 'APPROVED_TO_BID'.

    return bidding_crud.create_auction_participant(db=db, participant_in=schemas.AuctionParticipantCreate(
        auction_id=participant_in.auction_id,
        user_id=current_user.user_id,
        participation_status=initial_status
    ))

def get_auction_participant_details(db: Session, auction_participant_id: int) -> models_bidding.AuctionParticipant:
    """
    خدمة لجلب تفاصيل مشارك في المزاد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_participant_id (int): معرف المشارك المطلوب.

    Returns:
        models_bidding.AuctionParticipant: كائن المشارك.

    Raises:
        NotFoundException: إذا لم يتم العثور على المشارك.
    """
    participant = bidding_crud.get_auction_participant(db, auction_participant_id=auction_participant_id)
    if not participant:
        raise NotFoundException(detail=f"مشارك المزاد بمعرف {auction_participant_id} غير موجود.")
    return participant

def get_all_auction_participants_for_auction(db: Session, auction_id: UUID, current_user: User) -> List[models_bidding.AuctionParticipant]:
    """
    خدمة لجلب جميع المشاركين في مزاد معين.
    تتطلب صلاحيات (بائع المزاد، مشرف، أو ميزة خاصة).

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد.
        current_user (User): المستخدم الحالي (للتحقق من الصلاحيات).

    Returns:
        List[models_bidding.AuctionParticipant]: قائمة بكائنات المشاركين.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له برؤية المشاركين.
    """
    db_auction = get_auction_details(db, auction_id)
    # التحقق من الصلاحيات: البائع المالك أو المسؤول
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك برؤية المشاركين في هذا المزاد.")
    return bidding_crud.get_all_auction_participants_for_auction(db, auction_id=auction_id)

def get_bid_details_service(db: Session, bid_id: int, current_user: Optional[User] = None) -> models_bidding.Bid:
    """
    خدمة لجلب تفاصيل مزايدة واحدة بالـ ID، مع التحقق من صلاحيات المستخدم.
    المستخدم يجب أن يكون هو صاحب المزايدة، أو صاحب المزاد، أو مسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        bid_id (int): معرف المزايدة المطلوب.
        current_user (Optional[User]): المستخدم الحالي (يمكن أن يكون None إذا كانت للعامة).

    Returns:
        models.Bid: كائن المزايدة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزايدة.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية المزايدة.
    """
    db_bid = bidding_crud.get_bid(db, bid_id=bid_id)
    if not db_bid:
        raise NotFoundException(detail=f"المزايدة بمعرف {bid_id} غير موجودة.")

    # التحقق من الصلاحيات: صاحب المزايدة أو صاحب المزاد أو مسؤول
    is_bidder = current_user and db_bid.bidder_user_id == current_user.user_id
    is_auction_owner = current_user and db_bid.auction.seller_user_id == current_user.user_id # يتطلب تحميل المزاد في CRUD
    is_admin = current_user and any(p.permission_name_key == "ADMIN_AUCTION_VIEW_ANY" for p in current_user.default_role.permissions)

    # TODO: يمكن أن تكون المزايدة الأخيرة مرئية للجميع في بعض أنواع المزادات.
    if not (is_bidder or is_auction_owner or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل هذه المزايدة.")
    
    return db_bid



def update_auction_participant_status(db: Session, auction_participant_id: int, new_status: str, current_user: User) -> models_bidding.AuctionParticipant:
    """
    خدمة لتحديث حالة مشارك في المزاد (مثلاً: الموافقة على المزايدة، حظر).
    تتطلب صلاحيات المسؤول أو بائع المزاد (بناءً على قواعد العمل).

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_participant_id (int): معرف المشارك المراد تحديث حالته.
        new_status (str): الحالة الجديدة (مثلاً 'APPROVED_TO_BID', 'BLOCKED').
        current_user (User): المستخدم الحالي.

    Returns:
        models_bidding.AuctionParticipant: كائن المشارك المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على المشارك.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له.
        BadRequestException: إذا كانت الحالة الجديدة غير صالحة.
    """
    db_participant = get_auction_participant_details(db, auction_participant_id)
    db_auction = get_auction_details(db, db_participant.auction_id)

    # التحقق من الصلاحيات: يجب أن يكون بائع المزاد أو مسؤولاً.
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بتحديث حالة مشارك المزاد هذا.")

    # TODO: التحقق من أن 'new_status' هي قيمة صالحة من قائمة الحالات المسموح بها ('REGISTERED', 'APPROVED_TO_BID', 'BLOCKED').
    # TODO: آلة حالة المشارك: التحقق من الانتقال المسموح به للحالة الجديدة.

    # يتم تحديث الحالة عبر دالة CRUD للتحديث العام
    return bidding_crud.update_auction_participant(db=db, db_participant=db_participant, participant_in=schemas.AuctionParticipantUpdate(participation_status=new_status))


# ==========================================================
# --- خدمات المزايدات (Bid) ---
# ==========================================================

def place_bid(db: Session, bid_in: schemas.BidCreate, current_user: User) -> models_bidding.Bid:
    """
    خدمة لتقديم مزايدة جديدة على مزاد.
    تتضمن التحقق من المزاد، المستخدم، قواعد المزايدة، والرصيد المالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        bid_in (schemas.BidCreate): بيانات المزايدة للإنشاء.
        current_user (User): المستخدم الحالي المزايد.

    Returns:
        models_bidding.Bid: كائن المزايدة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد أو اللوت.
        ForbiddenException: إذا لم يكن المستخدم مؤهلاً للمزايدة، أو رصيده غير كافٍ.
        BadRequestException: إذا كانت قيمة المزايدة غير صالحة (أقل من الحد الأدنى للزيادة، أو أقل من السعر الحالي).
        ConflictException: إذا كان المزاد ليس نشطًا.
    """
    # 1. التحقق من وجود المزاد وحالته
    db_auction = get_auction_details(db, bid_in.auction_id)
    if db_auction.auction_status.status_name_key != "ACTIVE":
        raise BadRequestException(detail=f"المزاد ليس نشطًا حاليًا، حالته: {db_auction.auction_status.status_name_key}.")

    # 2. التحقق من اللوت إذا كانت المزايدة على لوت محدد
    if bid_in.lot_id:
        # TODO: يجب استيراد get_auction_lot_details
        # db_lot = get_auction_lot_details(db, bid_in.lot_id)
        # if not db_lot or db_lot.auction_id != db_auction.auction_id:
        #     raise NotFoundException(detail="اللوت غير موجود أو لا ينتمي إلى هذا المزاد.")
        pass # التحقق سيكون في دالة get_auction_lot_details

    # 3. التحقق من أن المستخدم هو المشارك المؤهل
    # TODO: يجب استيراد AuctionParticipant model
    # participant = bidding_crud.get_auction_participant(db, auction_id=bid_in.auction_id, user_id=current_user.user_id)
    # if not participant or participant.participation_status != "APPROVED_TO_BID":
    #     raise ForbiddenException(detail="غير مؤهل للمزايدة في هذا المزاد. يرجى التأكد من التسجيل والتأهيل.")
    
    # 4. التحقق من أن المزايد ليس بائع المزاد
    if db_auction.seller_user_id == current_user.user_id:
        raise ForbiddenException(detail="لا يمكن لبائع المزاد المزايدة في مزاده الخاص.")

    # 5. التحقق من قيمة المزايدة
    if bid_in.bid_amount_per_unit <= 0:
        raise BadRequestException(detail="قيمة المزايدة يجب أن تكون أكبر من صفر.")
    
    required_bid = db_auction.current_highest_bid_amount_per_unit or db_auction.starting_price_per_unit
    required_bid += db_auction.minimum_bid_increment

    if bid_in.bid_amount_per_unit < required_bid:
        raise BadRequestException(detail=f"يجب أن تكون مزايدتك أعلى من السعر الحالي بمقدار لا يقل عن {db_auction.minimum_bid_increment} ريال. المزايدة المطلوبة هي: {required_bid} ريال.")

    # 6. التحقق من الرصيد المالي للمزايد (بالتكامل مع وحدة المحفظة)
    # TODO: هـام: استدعاء wallet_service.check_and_reserve_funds(current_user.user_id, bid_in.bid_amount_per_unit)
    #       هذا سيحجز المبلغ ويضمن أن المستخدم لديه رصيد كافٍ.
    #       إذا كان هناك نظام مزايدة آلية، قد يتم حجز الحد الأقصى للمزايدة الآلية.

    # 7. تحديث معلومات المزاد (current_highest_bid_amount, current_highest_bidder_user_id, total_bids_count)
    db_auction.current_highest_bid_amount_per_unit = bid_in.bid_amount_per_unit
    db_auction.current_highest_bidder_user_id = current_user.user_id
    db_auction.total_bids_count += 1
    
    # 8. استدعاء CRUD لإنشاء المزايدة
    db_bid = bidding_crud.create_bid(db=db, bid_in=bid_in)

    # TODO: إخطار المزايد الذي تم تجاوزه (وحدة الإشعارات).
    # TODO: إخطار المشاهدين في قائمة المراقبة (وحدة الإشعارات).
    # TODO: تشغيل منطق المزايدة الآلية (AutoBidService) إذا تم تجاوز مزايدة آلية.

    db.commit() # تأكيد المزايدة وتحديث المزاد في عملية واحدة
    db.refresh(db_auction) # لتحديث بيانات المزاد
    db.refresh(db_bid)

    return db_bid

def get_bids_for_auction(db: Session, auction_id: UUID, current_user: User, skip: int = 0, limit: int = 100) -> List[models_bidding.Bid]:
    """
    خدمة لجلب جميع المزايدات لمزاد معين.
    تتطلب صلاحيات (بائع المزاد، مشارك، مسؤول) لرؤية السجل الكامل.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد.
        current_user (User): المستخدم الحالي.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_bidding.Bid]: قائمة بكائنات المزايدات.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له برؤية سجل المزايدات.
    """
    db_auction = get_auction_details(db, auction_id)

    # التحقق من الصلاحيات: بائع المزاد، مشارك في المزاد، أو مسؤول.
    is_seller = db_auction.seller_user_id == current_user.user_id
    is_participant = db.query(models_bidding.AuctionParticipant).filter(
        and_(
            models_bidding.AuctionParticipant.auction_id == auction_id,
            models_bidding.AuctionParticipant.user_id == current_user.user_id
        )
    ).first()
    is_admin = any(p.permission_name_key == "ADMIN_AUCTION_VIEW_ANY" for p in current_user.default_role.permissions)

    if not (is_seller or is_participant or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية سجل المزايدات لهذا المزاد.")

    return bidding_crud.get_all_bids_for_auction(db=db, auction_id=auction_id)

def get_my_bids(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[models_bidding.Bid]:
    """
    خدمة لجلب جميع المزايدات التي قدمها المستخدم الحالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_bidding.Bid]: قائمة بكائنات المزايدات.
    """
    # TODO: يجب تحسين دالة CRUD لتدعم البحث عن المزايدات حسب bidder_user_id.
    # حالياً get_all_bids_for_auction تحتاج auction_id
    # سأقوم بتعديل بسيط هنا لاستخدام filter مباشر في الخدمة إذا لم يكن هناك دالة CRUD مخصصة.
    return db.query(models_bidding.Bid).filter(models_bidding.Bid.bidder_user_id == current_user.user_id).offset(skip).limit(limit).all()


# ==========================================================
# --- خدمات إعدادات المزايدة الآلية (AutoBidSetting) ---
# ==========================================================

def create_auto_bid_setting(db: Session, setting_in: schemas.AutoBidSettingCreate, current_user: User) -> models_bidding.AutoBidSetting:
    """
    خدمة لإنشاء أو تحديث إعداد مزايدة آلية لمستخدم في مزاد معين.
    تتضمن التحقق من وجود المزاد، المستخدم، ومنع الإعدادات المكررة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        setting_in (schemas.AutoBidSettingCreate): بيانات الإعداد للإنشاء.
        current_user (User): المستخدم الحالي الذي يحدد الإعداد.

    Returns:
        models_bidding.AutoBidSetting: كائن الإعداد الذي تم إنشاؤه أو تحديثه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد أو المستخدم.
        ConflictException: إذا كان هناك إعداد مزايدة آلية موجود بالفعل لنفس المستخدم والمزاد.
        BadRequestException: إذا كانت البيانات غير صالحة (مثلاً أقصى مبلغ مزايدة أقل من السعر الحالي).
    """
    # 1. التحقق من وجود المزاد والمستخدم
    get_auction_details(db, setting_in.auction_id)
    get_user_by_id(db, setting_in.user_id) # يجب أن يكون user_id هو current_user.user_id

    # 2. التحقق من أن المستخدم ليس بائع المزاد
    db_auction = get_auction_details(db, setting_in.auction_id)
    if db_auction.seller_user_id == current_user.user_id:
        raise ForbiddenException(detail="بائع المزاد لا يمكنه تفعيل المزايدة الآلية في مزاده الخاص.")
    
    # 3. التحقق من عدم وجود إعداد سابق لنفس المستخدم والمزاد
    existing_setting = bidding_crud.get_auto_bid_setting_by_user_and_auction(db, user_id=setting_in.user_id, auction_id=setting_in.auction_id)
    if existing_setting:
        raise ConflictException(detail="يوجد بالفعل إعداد مزايدة آلية لهذا المزاد من قبل هذا المستخدم. يرجى التحديث بدلاً من الإنشاء.")

    # 4. التحقق من أن أقصى مبلغ مزايدة أعلى من السعر الحالي للمزاد
    if db_auction.current_highest_bid_amount_per_unit is not None and setting_in.max_bid_amount_per_unit <= db_auction.current_highest_bid_amount_per_unit:
        raise BadRequestException(detail="أقصى مبلغ للمزايدة يجب أن يكون أعلى من السعر الحالي للمزاد.")
    
    # 5. التحقق من أن المزايد مؤهل للمزايدة
    # TODO: التحقق من أن المزايد مسجل كمشارك في المزاد وحالته 'APPROVED_TO_BID'
    # TODO: التحقق من أن المزايد لديه رصيد كافٍ في المحفظة لتغطية max_bid_amount_per_unit.

    return bidding_crud.create_auto_bid_setting(db=db, setting_in=setting_in)

def get_auto_bid_setting_details(db: Session, auto_bid_setting_id: int) -> models_bidding.AutoBidSetting:
    """
    خدمة لجلب تفاصيل إعداد مزايدة آلية واحد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auto_bid_setting_id (int): معرف الإعداد المطلوب.

    Returns:
        models_bidding.AutoBidSetting: كائن الإعداد.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإعداد.
    """
    setting = bidding_crud.get_auto_bid_setting(db, auto_bid_setting_id=auto_bid_setting_id)
    if not setting:
        raise NotFoundException(detail=f"إعداد المزايدة الآلية بمعرف {auto_bid_setting_id} غير موجود.")
    return setting

def get_my_auto_bid_setting_for_auction(db: Session, auction_id: UUID, current_user: User) -> Optional[models_bidding.AutoBidSetting]:
    """
    خدمة لجلب إعداد المزايدة الآلية للمستخدم الحالي في مزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد.
        current_user (User): المستخدم الحالي.

    Returns:
        Optional[models_bidding.AutoBidSetting]: كائن الإعداد أو None.
    """
    # التحقق من وجود المزاد
    get_auction_details(db, auction_id)
    return bidding_crud.get_auto_bid_setting_by_user_and_auction(db, user_id=current_user.user_id, auction_id=auction_id)


def update_auto_bid_setting(db: Session, auto_bid_setting_id: int, setting_in: schemas.AutoBidSettingUpdate, current_user: User) -> models_bidding.AutoBidSetting:
    """
    خدمة لتحديث إعداد مزايدة آلية موجود.
    تتضمن التحقق من ملكية المستخدم والمزاد، وتحديث قيمة أقصى مزايدة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auto_bid_setting_id (int): معرف الإعداد المراد تحديثه.
        setting_in (schemas.AutoBidSettingUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_bidding.AutoBidSetting: كائن الإعداد المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإعداد.
        ForbiddenException: إذا لم يكن المستخدم يملك الإعداد أو غير مصرح له.
        BadRequestException: إذا كانت البيانات غير صالحة.
    """
    db_setting = get_auto_bid_setting_details(db, auto_bid_setting_id)

    # 1. التحقق من ملكية المستخدم للإعداد
    if db_setting.user_id != current_user.user_id:
        raise ForbiddenException(detail="غير مصرح لك بتحديث إعداد المزايدة الآلية هذا.")
    
    # 2. التحقق من أن المستخدم ليس بائع المزاد
    db_auction = get_auction_details(db, db_setting.auction_id)
    if db_auction.seller_user_id == current_user.user_id:
        raise ForbiddenException(detail="بائع المزاد لا يمكنه تفعيل المزايدة الآلية في مزاده الخاص.")

    # 3. التحقق من قيمة max_bid_amount_per_unit إذا تم تحديثها
    if setting_in.max_bid_amount_per_unit is not None:
        if db_auction.current_highest_bid_amount_per_unit is not None and setting_in.max_bid_amount_per_unit <= db_auction.current_highest_bid_amount_per_unit:
            raise BadRequestException(detail="أقصى مبلغ للمزايدة يجب أن يكون أعلى من السعر الحالي للمزاد.")
        # TODO: التحقق من الرصيد الكافي إذا زادت قيمة max_bid.

    return bidding_crud.update_auto_bid_setting(db=db, db_setting=db_setting, setting_in=setting_in)

def deactivate_auto_bid_setting(db: Session, auto_bid_setting_id: int, current_user: User) -> models_bidding.AutoBidSetting:
    """
    خدمة لإلغاء تفعيل إعداد مزايدة آلية (حذف ناعم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        auto_bid_setting_id (int): معرف الإعداد المراد إلغاء تفعيله.
        current_user (User): المستخدم الحالي.

    Returns:
        models_bidding.AutoBidSetting: كائن الإعداد بعد إلغاء تفعيله.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإعداد.
        ForbiddenException: إذا لم يكن المستخدم يملك الإعداد أو غير مصرح له.
        BadRequestException: إذا كان الإعداد غير نشط بالفعل.
    """
    db_setting = get_auto_bid_setting_details(db, auto_bid_setting_id)

    if db_setting.user_id != current_user.user_id:
        raise ForbiddenException(detail="غير مصرح لك بإلغاء تفعيل إعداد المزايدة الآلية هذا.")
    
    if not db_setting.is_active:
        raise BadRequestException(detail=f"إعداد المزايدة الآلية بمعرف {auto_bid_setting_id} غير نشط بالفعل.")

    return bidding_crud.soft_delete_auto_bid_setting(db=db, db_setting=db_setting)

# ==========================================================
# --- خدمات قوائم مراقبة المزادات (AuctionWatchlist) ---
# ==========================================================

def create_auction_watchlist_entry(db: Session, watchlist_in: schemas.AuctionWatchlistCreate, current_user: User) -> models_bidding.AuctionWatchlist:
    """
    خدمة لإنشاء إدخال جديد في قائمة مراقبة المزادات لمستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        watchlist_in (schemas.AuctionWatchlistCreate): بيانات الإدخال لقائمة المراقبة.
        current_user (User): المستخدم الحالي.

    Returns:
        models_bidding.AuctionWatchlist: كائن الإدخال الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد أو المستخدم.
        ConflictException: إذا كان المزاد موجودًا بالفعل في قائمة مراقبة المستخدم.
        ForbiddenException: إذا كان المستخدم غير مصرح له.
    """
    # 1. التحقق من وجود المزاد والمستخدم
    get_auction_details(db, watchlist_in.auction_id)
    get_user_by_id(db, watchlist_in.user_id) # يجب أن يكون user_id هو current_user.user_id

    # 2. التحقق من عدم وجود تكرار لنفس المزاد والمستخدم
    existing_entry = bidding_crud.get_auction_watchlist_by_user_and_auction(db, user_id=current_user.user_id, auction_id=watchlist_in.auction_id)
    if existing_entry:
        raise ConflictException(detail="المزاد موجود بالفعل في قائمة المراقبة الخاصة بك.")

    return bidding_crud.create_auction_watchlist_entry(db=db, watchlist_in=watchlist_in)

def get_auction_watchlist_entry_details(db: Session, watchlist_entry_id: int) -> models_bidding.AuctionWatchlist:
    """
    خدمة لجلب تفاصيل إدخال قائمة مراقبة مزاد واحد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        watchlist_entry_id (int): معرف الإدخال المطلوب.

    Returns:
        models_bidding.AuctionWatchlist: كائن الإدخال.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإدخال.
    """
    entry = bidding_crud.get_auction_watchlist_entry(db, watchlist_entry_id=watchlist_entry_id)
    if not entry:
        raise NotFoundException(detail=f"إدخال قائمة المراقبة بمعرف {watchlist_entry_id} غير موجود.")
    return entry

def get_my_auction_watchlists(db: Session, current_user: User) -> List[models_bidding.AuctionWatchlist]:
    """
    خدمة لجلب جميع المزادات في قائمة مراقبة المستخدم الحالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي.

    Returns:
        List[models_bidding.AuctionWatchlist]: قائمة بكائنات قائمة المراقبة.
    """
    return bidding_crud.get_all_auction_watchlists_for_user(db, user_id=current_user.user_id)

def delete_auction_watchlist_entry(db: Session, watchlist_entry_id: int, current_user: User):
    """
    خدمة لحذف إدخال قائمة مراقبة مزاد معين (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        watchlist_entry_id (int): معرف الإدخال المراد حذفه.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإدخال.
        ForbiddenException: إذا لم يكن المستخدم يملك الإدخال أو غير مصرح له.
    """
    db_entry = get_auction_watchlist_entry_details(db, watchlist_entry_id)

    # 1. التحقق من ملكية المستخدم للإدخال
    if db_entry.user_id != current_user.user_id:
        raise ForbiddenException(detail="غير مصرح لك بحذف هذا الإدخال من قائمة المراقبة.")

    bidding_crud.delete_auction_watchlist_entry(db=db, db_entry=db_entry)
    return {"message": "تم حذف إدخال قائمة المراقبة بنجاح."}