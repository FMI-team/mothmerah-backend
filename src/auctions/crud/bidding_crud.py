# backend\src\auction\crud\bidding_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز من Auction
from src.auctions.models import bidding_models as models_bidding # AuctionParticipant, Bid, AutoBidSetting, AuctionWatchlist
from src.auctions.models import auctions_models as models_auction # Auction, AuctionLot (للعلاقات)
from src.users.models.core_models import User # User (للعلاقات)
# استيراد Schemas
from src.auctions.schemas import bidding_schemas as schemas


# ==========================================================
# --- CRUD Functions for AuctionParticipant (المشاركون في المزاد) ---
# ==========================================================

def create_auction_participant(db: Session, participant_in: schemas.AuctionParticipantCreate) -> models_bidding.AuctionParticipant:
    """
    ينشئ سجلاً جديداً لمشارك في المزاد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        participant_in (schemas.AuctionParticipantCreate): بيانات المشارك للإنشاء.

    Returns:
        models_bidding.AuctionParticipant: كائن المشارك الذي تم إنشاؤه.
    """
    db_participant = models_bidding.AuctionParticipant(
        auction_id=participant_in.auction_id,
        user_id=participant_in.user_id,
        participation_status=participant_in.participation_status
    )
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant

def get_auction_participant(db: Session, auction_participant_id: int) -> Optional[models_bidding.AuctionParticipant]:
    """
    يجلب سجل مشارك في المزاد واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_participant_id (int): معرف المشارك المطلوب.

    Returns:
        Optional[models_bidding.AuctionParticipant]: كائن المشارك أو None.
    """
    return db.query(models_bidding.AuctionParticipant).options(
        joinedload(models_bidding.AuctionParticipant.auction),
        joinedload(models_bidding.AuctionParticipant.user)
    ).filter(models_bidding.AuctionParticipant.auction_participant_id == auction_participant_id).first()

def get_all_auction_participants_for_auction(db: Session, auction_id: UUID) -> List[models_bidding.AuctionParticipant]:
    """
    يجلب جميع المشاركين في مزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد.

    Returns:
        List[models_bidding.AuctionParticipant]: قائمة بكائنات المشاركين.
    """
    return db.query(models_bidding.AuctionParticipant).filter(models_bidding.AuctionParticipant.auction_id == auction_id).all()

def update_auction_participant(db: Session, db_participant: models_bidding.AuctionParticipant, participant_in: schemas.AuctionParticipantUpdate) -> models_bidding.AuctionParticipant:
    """
    يحدث بيانات سجل مشارك في المزاد موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_participant (models_bidding.AuctionParticipant): كائن المشارك من قاعدة البيانات.
        participant_in (schemas.AuctionParticipantUpdate): البيانات المراد تحديثها.

    Returns:
        models_bidding.AuctionParticipant: كائن المشارك المحدث.
    """
    update_data = participant_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_participant, key, value)
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant

# لا يوجد delete_auction_participant مباشر، يتم إدارة الحالة عبر update_auction_participant (participation_status).


# ==========================================================
# --- CRUD Functions for Bid (المزايدات) ---
# ==========================================================

def create_bid(db: Session, bid_in: schemas.BidCreate) -> models_bidding.Bid:
    """
    ينشئ سجلاً جديداً للمزايدة في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        bid_in (schemas.BidCreate): بيانات المزايدة للإنشاء.

    Returns:
        models_bidding.Bid: كائن المزايدة الذي تم إنشاؤه.
    """
    db_bid = models_bidding.Bid(
        auction_id=bid_in.auction_id,
        lot_id=bid_in.lot_id,
        bidder_user_id=bid_in.bidder_user_id,
        bid_amount_per_unit=bid_in.bid_amount_per_unit,
        is_auto_bid=bid_in.is_auto_bid,
        # bid_timestamp و bid_status تُدار بواسطة المودل أو طبقة الخدمة
    )
    db.add(db_bid)
    db.commit()
    db.refresh(db_bid)
    return db_bid

def get_bid(db: Session, bid_id: int) -> Optional[models_bidding.Bid]:
    """
    يجلب سجل مزايدة واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        bid_id (int): معرف المزايدة المطلوب.

    Returns:
        Optional[models_bidding.Bid]: كائن المزايدة أو None.
    """
    return db.query(models_bidding.Bid).options(
        joinedload(models_bidding.Bid.auction),
        joinedload(models_bidding.Bid.lot),
        joinedload(models_bidding.Bid.bidder)
    ).filter(models_bidding.Bid.bid_id == bid_id).first()

def get_all_bids_for_auction(db: Session, auction_id: UUID) -> List[models_bidding.Bid]:
    """
    يجلب جميع المزايدات لمزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد.

    Returns:
        List[models_bidding.Bid]: قائمة بكائنات المزايدات.
    """
    return db.query(models_bidding.Bid).filter(models_bidding.Bid.auction_id == auction_id).order_by(models_bidding.Bid.bid_timestamp.desc()).all()

def get_highest_bid_for_auction(db: Session, auction_id: UUID) -> Optional[models_bidding.Bid]:
    """
    يجلب أعلى مزايدة حالية لمزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد.

    Returns:
        Optional[models_bidding.Bid]: كائن أعلى مزايدة أو None.
    """
    return db.query(models_bidding.Bid).filter(
        models_bidding.Bid.auction_id == auction_id
    ).order_by(
        models_bidding.Bid.bid_amount_per_unit.desc(),
        models_bidding.Bid.bid_timestamp.asc() # الأقدم في حال التساوي
    ).first()

# لا يوجد تحديث أو حذف للمزايدات لأنها سجلات غير قابلة للتعديل.


# ==========================================================
# --- CRUD Functions for AutoBidSetting (إعدادات المزايدة الآلية) ---
# ==========================================================

def create_auto_bid_setting(db: Session, setting_in: schemas.AutoBidSettingCreate) -> models_bidding.AutoBidSetting:
    """
    ينشئ إعداد مزايدة آلية جديد لمستخدم في مزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        setting_in (schemas.AutoBidSettingCreate): بيانات الإعداد للإنشاء.

    Returns:
        models_bidding.AutoBidSetting: كائن الإعداد الذي تم إنشاؤه.
    """
    db_setting = models_bidding.AutoBidSetting(
        auction_id=setting_in.auction_id,
        user_id=setting_in.user_id,
        max_bid_amount_per_unit=setting_in.max_bid_amount_per_unit,
        increment_amount=setting_in.increment_amount,
        is_active=setting_in.is_active
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def get_auto_bid_setting(db: Session, auto_bid_setting_id: int) -> Optional[models_bidding.AutoBidSetting]:
    """
    يجلب إعداد مزايدة آلية واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auto_bid_setting_id (int): معرف الإعداد المطلوب.

    Returns:
        Optional[models_bidding.AutoBidSetting]: كائن الإعداد أو None.
    """
    return db.query(models_bidding.AutoBidSetting).filter(models_bidding.AutoBidSetting.auto_bid_setting_id == auto_bid_setting_id).first()

def get_auto_bid_setting_by_user_and_auction(db: Session, user_id: UUID, auction_id: UUID) -> Optional[models_bidding.AutoBidSetting]:
    """
    يجلب إعداد مزايدة آلية لمستخدم معين في مزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.
        auction_id (UUID): معرف المزاد.

    Returns:
        Optional[models_bidding.AutoBidSetting]: كائن الإعداد أو None.
    """
    return db.query(models_bidding.AutoBidSetting).filter(
        and_(
            models_bidding.AutoBidSetting.user_id == user_id,
            models_bidding.AutoBidSetting.auction_id == auction_id
        )
    ).first()

def update_auto_bid_setting(db: Session, db_setting: models_bidding.AutoBidSetting, setting_in: schemas.AutoBidSettingUpdate) -> models_bidding.AutoBidSetting:
    """
    يحدث بيانات إعداد مزايدة آلية موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_setting (models_bidding.AutoBidSetting): كائن الإعداد من قاعدة البيانات.
        setting_in (schemas.AutoBidSettingUpdate): البيانات المراد تحديثها.

    Returns:
        models_bidding.AutoBidSetting: كائن الإعداد المحدث.
    """
    update_data = setting_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_setting, key, value)
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def soft_delete_auto_bid_setting(db: Session, db_setting: models_bidding.AutoBidSetting) -> models_bidding.AutoBidSetting:
    """
    يقوم بالحذف الناعم لإعداد مزايدة آلية عن طريق تعيين 'is_active' إلى False.
    """
    db_setting.is_active = False
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


# ==========================================================
# --- CRUD Functions for AuctionWatchlist (قوائم مراقبة المزادات) ---
# ==========================================================

def create_auction_watchlist_entry(db: Session, watchlist_in: schemas.AuctionWatchlistCreate) -> models_bidding.AuctionWatchlist:
    """
    ينشئ إدخالاً جديداً في قائمة مراقبة المزادات لمستخدم ومزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        watchlist_in (schemas.AuctionWatchlistCreate): بيانات الإدخال لقائمة المراقبة.

    Returns:
        models_bidding.AuctionWatchlist: كائن الإدخال الذي تم إنشاؤه.
    """
    db_entry = models_bidding.AuctionWatchlist(
        user_id=watchlist_in.user_id,
        auction_id=watchlist_in.auction_id
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

def get_auction_watchlist_entry(db: Session, watchlist_entry_id: int) -> Optional[models_bidding.AuctionWatchlist]:
    """
    يجلب إدخال قائمة مراقبة مزاد واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        watchlist_entry_id (int): معرف الإدخال المطلوب.

    Returns:
        Optional[models_bidding.AuctionWatchlist]: كائن الإدخال أو None.
    """
    return db.query(models_bidding.AuctionWatchlist).filter(models_bidding.AuctionWatchlist.watchlist_entry_id == watchlist_entry_id).first()

def get_auction_watchlist_by_user_and_auction(db: Session, user_id: UUID, auction_id: UUID) -> Optional[models_bidding.AuctionWatchlist]:
    """
    يجلب إدخال قائمة مراقبة مزاد لمستخدم معين ومزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.
        auction_id (UUID): معرف المزاد.

    Returns:
        Optional[models_bidding.AuctionWatchlist]: كائن الإدخال أو None.
    """
    return db.query(models_bidding.AuctionWatchlist).filter(
        and_(
            models_bidding.AuctionWatchlist.user_id == user_id,
            models_bidding.AuctionWatchlist.auction_id == auction_id
        )
    ).first()

def get_all_auction_watchlists_for_user(db: Session, user_id: UUID) -> List[models_bidding.AuctionWatchlist]:
    """
    يجلب جميع المزادات في قائمة مراقبة مستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.

    Returns:
        List[models_bidding.AuctionWatchlist]: قائمة بكائنات قائمة المراقبة.
    """
    return db.query(models_bidding.AuctionWatchlist).filter(models_bidding.AuctionWatchlist.user_id == user_id).all()

def delete_auction_watchlist_entry(db: Session, db_entry: models_bidding.AuctionWatchlist):
    """
    يحذف إدخال قائمة مراقبة مزاد معين (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_entry (models_bidding.AuctionWatchlist): كائن الإدخال من قاعدة البيانات.
    """
    db.delete(db_entry)
    db.commit()
    return