# backend\src\auction\crud\settlements_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز من Auction
from src.auctions.models import settlements_models as models_settlements # AuctionSettlement, AuctionSettlementStatus, AuctionSettlementStatusTranslation
# استيراد Schemas
from src.auctions.schemas import settlement_schemas as schemas
from src.lookups.schemas import lookups_schemas 


# ==========================================================
# --- CRUD Functions for AuctionSettlement (تسويات المزادات) ---
# ==========================================================

def create_auction_settlement(db: Session, settlement_in: schemas.AuctionSettlementCreate) -> models_settlements.AuctionSettlement:
    """
    ينشئ سجلاً جديداً لتسوية المزاد في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_in (schemas.AuctionSettlementCreate): بيانات التسوية للإنشاء.

    Returns:
        models_settlements.AuctionSettlement: كائن التسوية الذي تم إنشاؤه.
    """
    db_settlement = models_settlements.AuctionSettlement(
        auction_id=settlement_in.auction_id,
        winning_bid_id=settlement_in.winning_bid_id,
        winner_user_id=settlement_in.winner_user_id,
        seller_user_id=settlement_in.seller_user_id,
        final_winning_price_per_unit=settlement_in.final_winning_price_per_unit,
        quantity_won=settlement_in.quantity_won,
        total_settlement_amount=settlement_in.total_settlement_amount,
        net_amount_to_seller=settlement_in.net_amount_to_seller,
        settlement_status_id=settlement_in.settlement_status_id,
        settlement_timestamp=settlement_in.settlement_timestamp,
        notes=settlement_in.notes,
        # TODO: platform_commission_id, payment_transaction_id, payout_transaction_id يتم تعيينها لاحقاً في الخدمة
    )
    db.add(db_settlement)
    db.commit()
    db.refresh(db_settlement)
    return db_settlement

def get_auction_settlement(db: Session, settlement_id: int) -> Optional[models_settlements.AuctionSettlement]:
    """
    يجلب سجل تسوية مزاد واحد بالـ ID الخاص به، مع الكائنات المرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_id (int): معرف التسوية المطلوب.

    Returns:
        Optional[models_settlements.AuctionSettlement]: كائن التسوية أو None.
    """
    return db.query(models_settlements.AuctionSettlement).options(
        joinedload(models_settlements.AuctionSettlement.auction),
        joinedload(models_settlements.AuctionSettlement.winning_bid),
        joinedload(models_settlements.AuctionSettlement.winner_user),
        joinedload(models_settlements.AuctionSettlement.seller_user),
        joinedload(models_settlements.AuctionSettlement.settlement_status)
        # TODO: تحميل PlatformCommission, WalletTransaction (إذا تم تعريف العلاقات)
    ).filter(models_settlements.AuctionSettlement.settlement_id == settlement_id).first()

def get_all_auction_settlements(db: Session, auction_id: Optional[UUID] = None, winner_user_id: Optional[UUID] = None, seller_user_id: Optional[UUID] = None, settlement_status_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models_settlements.AuctionSettlement]:
    """
    يجلب قائمة بجميع تسويات المزادات، مع خيارات للتصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (Optional[UUID]): تصفية حسب معرف المزاد.
        winner_user_id (Optional[UUID]): تصفية حسب معرف المستخدم الفائز.
        seller_user_id (Optional[UUID]): تصفية حسب معرف البائع.
        settlement_status_id (Optional[int]): تصفية حسب معرف حالة التسوية.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models_settlements.AuctionSettlement]: قائمة بكائنات التسويات.
    """
    query = db.query(models_settlements.AuctionSettlement).options(
        joinedload(models_settlements.AuctionSettlement.auction),
        joinedload(models_settlements.AuctionSettlement.settlement_status),
        joinedload(models_settlements.AuctionSettlement.winner_user),
        joinedload(models_settlements.AuctionSettlement.seller_user)
    )
    if auction_id:
        query = query.filter(models_settlements.AuctionSettlement.auction_id == auction_id)
    if winner_user_id:
        query = query.filter(models_settlements.AuctionSettlement.winner_user_id == winner_user_id)
    if seller_user_id:
        query = query.filter(models_settlements.AuctionSettlement.seller_user_id == seller_user_id)
    if settlement_status_id:
        query = query.filter(models_settlements.AuctionSettlement.settlement_status_id == settlement_status_id)
    
    return query.offset(skip).limit(limit).all()

def update_auction_settlement(db: Session, db_settlement: models_settlements.AuctionSettlement, settlement_in: schemas.AuctionSettlementUpdate) -> models_settlements.AuctionSettlement:
    """
    يحدث بيانات سجل تسوية مزاد موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_settlement (models_settlements.AuctionSettlement): كائن التسوية من قاعدة البيانات.
        settlement_in (schemas.AuctionSettlementUpdate): البيانات المراد تحديثها.

    Returns:
        models_settlements.AuctionSettlement: كائن التسوية المحدث.
    """
    update_data = settlement_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_settlement, key, value)
    db.add(db_settlement)
    db.commit()
    db.refresh(db_settlement)
    return db_settlement

def update_auction_settlement_status(db: Session, db_settlement: models_settlements.AuctionSettlement, new_status_id: int) -> models_settlements.AuctionSettlement:
    """
    يحدث حالة تسوية المزاد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_settlement (models_settlements.AuctionSettlement): كائن التسوية من قاعدة البيانات.
        new_status_id (int): معرف الحالة الجديدة للتسوية.

    Returns:
        models_settlements.AuctionSettlement: كائن التسوية بعد تحديث حالته.
    """
    db_settlement.settlement_status_id = new_status_id
    db.add(db_settlement)
    db.commit()
    db.refresh(db_settlement)
    return db_settlement

# لا يوجد delete_auction_settlement مباشر، يتم إدارة الحالة عبر تحديث settlement_status_id


# ==========================================================
# --- CRUD Functions for AuctionSettlementStatus (حالات تسوية المزاد) ---
# ==========================================================

def create_auction_settlement_status(db: Session, status_in: lookups_schemas.AuctionSettlementStatusCreate) -> models_settlements.AuctionSettlementStatus:
    """
    ينشئ حالة تسوية مزاد جديدة في قاعدة البيانات، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas.AuctionSettlementStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        models_settlements.AuctionSettlementStatus: كائن الحالة الذي تم إنشاؤه.
    """
    db_status = models_settlements.AuctionSettlementStatus(
        status_name_key=status_in.status_name_key,
        status_description_key=status_in.status_description_key # Assuming it exists in model
    )
    db.add(db_status)
    db.flush()

    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = models_settlements.AuctionSettlementStatusTranslation(
                settlement_status_id=db_status.settlement_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name,
                translated_description=trans_in.translated_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_auction_settlement_status(db: Session, settlement_status_id: int) -> Optional[models_settlements.AuctionSettlementStatus]:
    """
    يجلب حالة تسوية مزاد واحدة بالـ ID الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة المطلوب.

    Returns:
        Optional[models_settlements.AuctionSettlementStatus]: كائن الحالة أو None.
    """
    return db.query(models_settlements.AuctionSettlementStatus).options(
        joinedload(models_settlements.AuctionSettlementStatus.translations)
    ).filter(models_settlements.AuctionSettlementStatus.settlement_status_id == settlement_status_id).first()

def get_all_auction_settlement_statuses(db: Session) -> List[models_settlements.AuctionSettlementStatus]:
    """
    يجلب قائمة بجميع حالات تسوية المزاد.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[models_settlements.AuctionSettlementStatus]: قائمة بكائنات الحالات.
    """
    return db.query(models_settlements.AuctionSettlementStatus).options(
        joinedload(models_settlements.AuctionSettlementStatus.translations)
    ).all()

def update_auction_settlement_status_crud(db: Session, db_status: models_settlements.AuctionSettlementStatus, status_in: lookups_schemas.AuctionSettlementStatusUpdate) -> models_settlements.AuctionSettlementStatus:
    """
    يحدث بيانات حالة تسوية مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (models_settlements.AuctionSettlementStatus): كائن الحالة من قاعدة البيانات.
        status_in (schemas.AuctionSettlementStatusUpdate): البيانات المراد تحديثها.

    Returns:
        models_settlements.AuctionSettlementStatus: كائن الحالة المحدث.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_auction_settlement_status(db: Session, db_status: models_settlements.AuctionSettlementStatus):
    """
    يحذف حالة تسوية مزاد معينة (حذف صارم).
    TODO: التحقق من عدم وجود تسويات مرتبطة بهذه الحالة سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (models_settlements.AuctionSettlementStatus): كائن الحالة من قاعدة البيانات.
    """
    db.delete(db_status)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for AuctionSettlementStatusTranslation (ترجمات حالات تسوية المزاد) ---
# ==========================================================

def create_auction_settlement_status_translation(db: Session, settlement_status_id: int, trans_in: lookups_schemas.AuctionSettlementStatusTranslationCreate) -> models_settlements.AuctionSettlementStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة تسوية مزاد معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة الأم.
        trans_in (schemas.AuctionSettlementStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models_settlements.AuctionSettlementStatusTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models_settlements.AuctionSettlementStatusTranslation(
        settlement_status_id=settlement_status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_description=trans_in.translated_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_auction_settlement_status_translation(db: Session, settlement_status_id: int, language_code: str) -> Optional[models_settlements.AuctionSettlementStatusTranslation]:
    """
    يجلب ترجمة حالة تسوية مزاد محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        settlement_status_id (int): معرف الحالة.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models_settlements.AuctionSettlementStatusTranslation]: كائن الترجمة أو None.
    """
    return db.query(models_settlements.AuctionSettlementStatusTranslation).filter(
        and_(
            models_settlements.AuctionSettlementStatusTranslation.settlement_status_id == settlement_status_id,
            models_settlements.AuctionSettlementStatusTranslation.language_code == language_code
        )
    ).first()

def update_auction_settlement_status_translation(db: Session, db_translation: models_settlements.AuctionSettlementStatusTranslation, trans_in: lookups_schemas.AuctionSettlementStatusTranslationUpdate) -> models_settlements.AuctionSettlementStatusTranslation:
    """
    يحدث ترجمة حالة تسوية مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models_settlements.AuctionSettlementStatusTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.AuctionSettlementStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models_settlements.AuctionSettlementStatusTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_auction_settlement_status_translation(db: Session, db_translation: models_settlements.AuctionSettlementStatusTranslation):
    """
    يحذف ترجمة حالة تسوية مزاد معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models_settlements.AuctionSettlementStatusTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return