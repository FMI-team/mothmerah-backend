# backend\src\auction\crud\auctions_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز من Auction
from src.auctions.models import auctions_models as models_auction # Auction, AuctionLot, AuctionLotTranslation, LotProduct, LotImage
from src.lookups.models import lookups_models as models_statuses # AuctionStatus, AuctionStatusTranslation, AuctionType, AuctionTypeTranslation
# استيراد الـ Schemas
from src.auctions.schemas import auction_schemas as schemas
from src.lookups.schemas import lookups_schemas 


# ==========================================================
# --- CRUD Functions for AuctionStatus (حالات المزاد) ---
# ==========================================================

def create_auction_status(db: Session, status_in: lookups_schemas.AuctionStatusCreate) -> models_statuses.AuctionStatus:
    """
    ينشئ حالة مزاد جديدة في قاعدة البيانات، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (lookups_schemas.AuctionStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        models_statuses.AuctionStatus: كائن الحالة الذي تم إنشاؤه.
    """
    db_status = models_statuses.AuctionStatus(
        status_name_key=status_in.status_name_key,
        status_description_key=status_in.status_description_key # Assuming it exists in model
    )
    db.add(db_status)
    db.flush()

    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = models_statuses.AuctionStatusTranslation(
                auction_status_id=db_status.auction_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name,
                translated_description=trans_in.translated_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_auction_status(db: Session, auction_status_id: int) -> Optional[models_statuses.AuctionStatus]:
    """
    يجلب حالة مزاد واحدة بالـ ID الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة المطلوب.

    Returns:
        Optional[models_statuses.AuctionStatus]: كائن الحالة أو None.
    """
    return db.query(models_statuses.AuctionStatus).options(
        joinedload(models_statuses.AuctionStatus.translations)
    ).filter(models_statuses.AuctionStatus.auction_status_id == auction_status_id).first()

def get_all_auction_statuses(db: Session) -> List[models_statuses.AuctionStatus]:
    """
    يجلب قائمة بجميع حالات المزاد.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[models_statuses.AuctionStatus]: قائمة بكائنات الحالات.
    """
    return db.query(models_statuses.AuctionStatus).options(
        joinedload(models_statuses.AuctionStatus.translations)
    ).all()

def update_auction_status_crud(db: Session, db_status: models_statuses.AuctionStatus, status_in: lookups_schemas.AuctionStatusUpdate) -> models_statuses.AuctionStatus:
    """
    يحدث بيانات حالة مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (models_statuses.AuctionStatus): كائن الحالة من قاعدة البيانات.
        status_in (schemas.AuctionStatusUpdate): البيانات المراد تحديثها.

    Returns:
        models_statuses.AuctionStatus: كائن الحالة المحدث.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_auction_status(db: Session, db_status: models_statuses.AuctionStatus):
    """
    يحذف حالة مزاد معينة (حذف صارم).
    TODO: التحقق من عدم وجود مزادات أو لوطات مرتبطة بهذه الحالة سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (models_statuses.AuctionStatus): كائن الحالة من قاعدة البيانات.
    """
    db.delete(db_status)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for AuctionStatusTranslation (ترجمات حالات المزاد) ---
# ==========================================================

def create_auction_status_translation(db: Session, auction_status_id: int, trans_in: lookups_schemas.AuctionStatusTranslationCreate) -> models_statuses.AuctionStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة مزاد معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة الأم.
        trans_in (lookups_schemas.AuctionStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models_statuses.AuctionStatusTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models_statuses.AuctionStatusTranslation(
        auction_status_id=auction_status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_description=trans_in.translated_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_auction_status_translation(db: Session, auction_status_id: int, language_code: str) -> Optional[models_statuses.AuctionStatusTranslation]:
    """
    يجلب ترجمة حالة مزاد محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models_statuses.AuctionStatusTranslation]: كائن الترجمة أو None.
    """
    return db.query(models_statuses.AuctionStatusTranslation).filter(
        and_(
            models_statuses.AuctionStatusTranslation.auction_status_id == auction_status_id,
            models_statuses.AuctionStatusTranslation.language_code == language_code
        )
    ).first()

def update_auction_status_translation(db: Session, db_translation: models_statuses.AuctionStatusTranslation, trans_in: lookups_schemas.AuctionStatusTranslationUpdate) -> models_statuses.AuctionStatusTranslation:
    """
    يحدث ترجمة حالة مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models_statuses.AuctionStatusTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.AuctionStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models_statuses.AuctionStatusTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_auction_status_translation(db: Session, db_translation: models_statuses.AuctionStatusTranslation):
    """
    يحذف ترجمة حالة مزاد معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models_statuses.AuctionStatusTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for AuctionType (أنواع المزادات) ---
# ==========================================================

def create_auction_type(db: Session, type_in: lookups_schemas.AuctionTypeCreate) -> models_statuses.AuctionType:
    """
    ينشئ نوع مزاد جديد في قاعدة البيانات، مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas.AuctionTypeCreate): بيانات النوع للإنشاء.

    Returns:
        models_statuses.AuctionType: كائن النوع الذي تم إنشاؤه.
    """
    db_type = models_statuses.AuctionType(
        type_name_key=type_in.type_name_key,
        description_key=type_in.description_key
    )
    db.add(db_type)
    db.flush()

    if type_in.translations:
        for trans_in in type_in.translations:
            db_translation = models_statuses.AuctionTypeTranslation(
                auction_type_id=db_type.auction_type_id,
                language_code=trans_in.language_code,
                translated_type_name=trans_in.translated_type_name,
                translated_type_description=trans_in.translated_type_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_type)
    return db_type

def get_auction_type(db: Session, auction_type_id: int) -> Optional[models_statuses.AuctionType]:
    """
    يجلب نوع مزاد واحد بالـ ID الخاص به، مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_type_id (int): معرف النوع المطلوب.

    Returns:
        Optional[models_statuses.AuctionType]: كائن النوع أو None.
    """
    return db.query(models_statuses.AuctionType).options(
        joinedload(models_statuses.AuctionType.translations)
    ).filter(models_statuses.AuctionType.auction_type_id == auction_type_id).first()

def get_all_auction_types(db: Session) -> List[models_statuses.AuctionType]:
    """
    يجلب قائمة بجميع أنواع المزادات.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[models_statuses.AuctionType]: قائمة بكائنات الأنواع.
    """
    return db.query(models_statuses.AuctionType).options(
        joinedload(models_statuses.AuctionType.translations)
    ).all()

def update_auction_type_crud(db: Session, db_type: models_statuses.AuctionType, type_in: lookups_schemas.AuctionTypeUpdate) -> models_statuses.AuctionType:
    """
    يحدث بيانات نوع مزاد موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_type (models_statuses.AuctionType): كائن النوع من قاعدة البيانات.
        type_in (schemas.AuctionTypeUpdate): البيانات المراد تحديثها.

    Returns:
        models_statuses.AuctionType: كائن النوع المحدث.
    """
    update_data = type_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_type, key, value)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def delete_auction_type(db: Session, db_type: models_statuses.AuctionType):
    """
    يحذف نوع مزاد معين (حذف صارم).
    TODO: التحقق من عدم وجود مزادات مرتبطة بهذا النوع سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_type (models_statuses.AuctionType): كائن النوع من قاعدة البيانات.
    """
    db.delete(db_type)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for AuctionTypeTranslation (ترجمات أنواع المزادات) ---
# ==========================================================

def create_auction_type_translation(db: Session, auction_type_id: int, trans_in: lookups_schemas.AuctionTypeTranslationCreate) -> models_statuses.AuctionTypeTranslation:
    """
    ينشئ ترجمة جديدة لنوع مزاد معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_type_id (int): معرف النوع الأم.
        trans_in (schemas.AuctionTypeTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models_statuses.AuctionTypeTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models_statuses.AuctionTypeTranslation(
        auction_type_id=auction_type_id,
        language_code=trans_in.language_code,
        translated_type_name=trans_in.translated_type_name,
        translated_type_description=trans_in.translated_type_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_auction_type_translation(db: Session, auction_type_id: int, language_code: str) -> Optional[models_statuses.AuctionTypeTranslation]:
    """
    يجلب ترجمة نوع مزاد محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_type_id (int): معرف النوع.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models_statuses.AuctionTypeTranslation]: كائن الترجمة أو None.
    """
    return db.query(models_statuses.AuctionTypeTranslation).filter(
        and_(
            models_statuses.AuctionTypeTranslation.auction_type_id == auction_type_id,
            models_statuses.AuctionTypeTranslation.language_code == language_code
        )
    ).first()

def update_auction_type_translation(db: Session, db_translation: models_statuses.AuctionTypeTranslation, trans_in: lookups_schemas.AuctionTypeTranslationUpdate) -> models_statuses.AuctionTypeTranslation:
    """
    يحدث ترجمة نوع مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models_statuses.AuctionTypeTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.AuctionTypeTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models_statuses.AuctionTypeTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_auction_type_translation(db: Session, db_translation: models_statuses.AuctionTypeTranslation):
    """
    يحذف ترجمة نوع مزاد معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models_statuses.AuctionTypeTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for Auction (المزادات) ---
# ==========================================================

def create_auction(db: Session, auction_in: schemas.AuctionCreate, seller_user_id: UUID, auction_status_id: int) -> models_auction.Auction:
    """
    ينشئ سجلاً جديداً للمزاد في قاعدة البيانات، بما في ذلك لوطاته المضمنة (Auction Lots).
    تتم الحسابات المالية وتعيين المعرفات الأولية بواسطة طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_in (schemas.AuctionCreate): بيانات المزاد للإنشاء، بما في ذلك قائمة لوطات المزاد.
        seller_user_id (UUID): معرف البائع الذي ينشئ المزاد.
        auction_status_id (int): معرف الحالة الأولية للمزاد (يُحدد في الخدمة).

    Returns:
        models_auction.Auction: كائن المزاد الذي تم إنشاؤه.
    """
    db_auction = models_auction.Auction(
        seller_user_id=seller_user_id,
        product_id=auction_in.product_id,
        auction_type_id=auction_in.auction_type_id,
        auction_status_id=auction_status_id,
        auction_title_key=auction_in.auction_title_key,
        custom_auction_title=auction_in.custom_auction_title,
        auction_description_key=auction_in.auction_description_key,
        custom_auction_description=auction_in.custom_auction_description,
        start_timestamp=auction_in.start_timestamp,
        end_timestamp=auction_in.end_timestamp,
        starting_price_per_unit=auction_in.starting_price_per_unit,
        minimum_bid_increment=auction_in.minimum_bid_increment,
        reserve_price_per_unit=auction_in.reserve_price_per_unit,
        quantity_offered=auction_in.quantity_offered,
        unit_of_measure_id_for_quantity=auction_in.unit_of_measure_id_for_quantity,
        is_private_auction=auction_in.is_private_auction,
        pre_arrival_shipping_info=auction_in.pre_arrival_shipping_info,
        cancellation_reason=auction_in.cancellation_reason
    )
    db.add(db_auction)
    db.flush() # للحصول على auction_id قبل حفظ اللوطات

    if auction_in.lots:
        for lot_in in auction_in.lots:
            # هنا يجب استدعاء دالة CRUD لإنشاء اللوتات وبنودها وصورها
            # لتبسيط الكود هنا، سنقوم بدمجها مباشرة.
            db_lot = models_auction.AuctionLot(
                auction_id=db_auction.auction_id,
                lot_title_key=lot_in.lot_title_key,
                custom_lot_title=lot_in.custom_lot_title,
                lot_description_key=lot_in.lot_description_key,
                custom_lot_description=lot_in.custom_lot_description,
                quantity_in_lot=lot_in.quantity_in_lot,
                lot_starting_price=lot_in.lot_starting_price,
                lot_status_id=lot_in.lot_status_id # TODO: يجب أن يكون هذا من حالة أولية لـ Lot
            )
            db.add(db_lot)
            db.flush() # للحصول على lot_id للبنود والصور

            if lot_in.translations: # ترجمات اللوت
                for trans_in in lot_in.translations:
                    db_lot_translation = models_auction.AuctionLotTranslation(
                        lot_id=db_lot.lot_id,
                        language_code=trans_in.language_code,
                        translated_lot_title=trans_in.translated_lot_title,
                        translated_lot_description=trans_in.translated_lot_description
                    )
                    db.add(db_lot_translation)

            if lot_in.products_in_lot: # منتجات اللوت المجمعة
                for product_in_lot in lot_in.products_in_lot:
                    db_lot_product = models_auction.LotProduct(
                        lot_id=db_lot.lot_id,
                        packaging_option_id=product_in_lot.packaging_option_id,
                        quantity_in_lot=product_in_lot.quantity_in_lot
                    )
                    db.add(db_lot_product)
            
            if lot_in.images: # صور اللوت
                for image_in_lot in lot_in.images:
                    db_lot_image = models_auction.LotImage(
                        lot_id=db_lot.lot_id,
                        image_id=image_in_lot.image_id, # TODO: هذا يجب أن يكون موجوداً مسبقاً
                        sort_order=image_in_lot.sort_order
                    )
                    db.add(db_lot_image)
            
    db.commit()
    db.refresh(db_auction)
    return db_auction

def get_auction(db: Session, auction_id: UUID) -> Optional[models_auction.Auction]:
    """
    يجلب سجل مزاد واحد بالـ ID الخاص به، بما في ذلك لوطاته والكائنات المرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد المطلوب.

    Returns:
        Optional[models_auction.Auction]: كائن المزاد أو None إذا لم يتم العثور عليه.
    """
    return db.query(models_auction.Auction).options(
        joinedload(models_auction.Auction.seller),
        joinedload(models_auction.Auction.product),
        joinedload(models_auction.Auction.auction_type),
        joinedload(models_auction.Auction.auction_status),
        joinedload(models_auction.Auction.current_highest_bidder),
        joinedload(models_auction.Auction.lots).joinedload(models_auction.AuctionLot.translations), # لوطات المزاد وترجماتها
        joinedload(models_auction.Auction.lots).joinedload(models_auction.AuctionLot.products_in_lot), # منتجات اللوت
        joinedload(models_auction.Auction.lots).joinedload(models_auction.AuctionLot.images), # صور اللوت
        # TODO: تحميل Bids, Participants, AutoBidSettings, Watchlists, Settlements
    ).filter(models_auction.Auction.auction_id == auction_id).first()

def get_all_auctions(db: Session, seller_user_id: Optional[UUID] = None, auction_status_id: Optional[int] = None, auction_type_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models_auction.Auction]:
    """
    يجلب قائمة بجميع المزادات، مع خيارات للتصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        seller_user_id (Optional[UUID]): تصفية حسب معرف البائع.
        auction_status_id (Optional[int]): تصفية حسب معرف حالة المزاد.
        auction_type_id (Optional[int]): تصفية حسب معرف نوع المزاد.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models_auction.Auction]: قائمة بكائنات المزادات.
    """
    query = db.query(models_auction.Auction).options(
        joinedload(models_auction.Auction.seller),
        joinedload(models_auction.Auction.product),
        joinedload(models_auction.Auction.auction_type),
        joinedload(models_auction.Auction.auction_status)
    )
    if seller_user_id:
        query = query.filter(models_auction.Auction.seller_user_id == seller_user_id)
    if auction_status_id:
        query = query.filter(models_auction.Auction.auction_status_id == auction_status_id)
    if auction_type_id:
        query = query.filter(models_auction.Auction.auction_type_id == auction_type_id)
    
    return query.offset(skip).limit(limit).all()

def update_auction(db: Session, db_auction: models_auction.Auction, auction_in: schemas.AuctionUpdate) -> models_auction.Auction:
    """
    يحدث بيانات سجل مزاد موجود.
    لا يقوم بتحديث اللوطات مباشرة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_auction (models_auction.Auction): كائن المزاد من قاعدة البيانات المراد تحديثه.
        auction_in (schemas.AuctionUpdate): البيانات المراد تحديثها.

    Returns:
        models_auction.Auction: كائن المزاد المحدث.
    """
    update_data = auction_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_auction, key, value)
    db.add(db_auction)
    db.commit()
    db.refresh(db_auction)
    return db_auction

def update_auction_status(db: Session, db_auction: models_auction.Auction, new_status_id: int) -> models_auction.Auction:
    """
    يحدث حالة المزاد (للحذف الناعم أو تغيير الحالة في دورة حياة المزاد).
    يجب أن يتم تسجيل هذا التغيير في AuctionStatusHistory (إذا وجد) في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_auction (models_auction.Auction): كائن المزاد من قاعدة البيانات.
        new_status_id (int): معرف الحالة الجديدة للمزاد.

    Returns:
        models_auction.Auction: كائن المزاد بعد تحديث حالته.
    """
    db_auction.auction_status_id = new_status_id
    db.add(db_auction)
    db.commit()
    db.refresh(db_auction)
    return db_auction

# لا يوجد delete_auction مباشر، يتم إدارة الحالة عبر تحديث auction_status_id


# ==========================================================
# --- CRUD Functions for AuctionLot (لوطات/دفعات المزاد) ---
# ==========================================================

def create_auction_lot(db: Session, lot_in: schemas.AuctionLotCreate) -> models_auction.AuctionLot:
    """
    ينشئ لوت مزاد جديد في قاعدة البيانات، بما في ذلك ترجماته ومنتجاته وصوره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_in (schemas.AuctionLotCreate): بيانات اللوت للإنشاء.

    Returns:
        models_auction.AuctionLot: كائن اللوت الذي تم إنشاؤه.
    """
    db_lot = models_auction.AuctionLot(
        auction_id=lot_in.auction_id,
        lot_title_key=lot_in.lot_title_key,
        custom_lot_title=lot_in.custom_lot_title,
        lot_description_key=lot_in.lot_description_key,
        custom_lot_description=lot_in.custom_lot_description,
        quantity_in_lot=lot_in.quantity_in_lot,
        lot_starting_price=lot_in.lot_starting_price,
        lot_status_id=lot_in.lot_status_id
    )
    db.add(db_lot)
    db.flush()

    if lot_in.translations:
        for trans_in in lot_in.translations:
            db_translation = models_auction.AuctionLotTranslation(
                lot_id=db_lot.lot_id,
                language_code=trans_in.language_code,
                translated_lot_title=trans_in.translated_lot_title,
                translated_lot_description=trans_in.translated_lot_description
            )
            db.add(db_translation)

    if lot_in.products_in_lot:
        for product_in_lot in lot_in.products_in_lot:
            db_lot_product = models_auction.LotProduct(
                lot_id=db_lot.lot_id,
                packaging_option_id=product_in_lot.packaging_option_id,
                quantity_in_lot=product_in_lot.quantity_in_lot
            )
            db.add(db_lot_product)
    
    if lot_in.images:
        for image_in_lot in lot_in.images:
            db_lot_image = models_auction.LotImage(
                lot_id=db_lot.lot_id,
                image_id=image_in_lot.image_id,
                sort_order=image_in_lot.sort_order
            )
            db.add(db_lot_image)

    db.commit()
    db.refresh(db_lot)
    return db_lot

def get_auction_lot(db: Session, lot_id: UUID) -> Optional[models_auction.AuctionLot]:
    """
    يجلب سجل لوت مزاد واحد بالـ ID الخاص به، بما في ذلك ترجماته ومنتجاته وصوره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت المطلوب.

    Returns:
        Optional[models_auction.AuctionLot]: كائن اللوت أو None.
    """
    return db.query(models_auction.AuctionLot).options(
        joinedload(models_auction.AuctionLot.translations),
        joinedload(models_auction.AuctionLot.products_in_lot),
        joinedload(models_auction.AuctionLot.images),
        joinedload(models_auction.AuctionLot.lot_status) # حالة اللوت
        # TODO: تحميل Bids إذا كانت موجودة
    ).filter(models_auction.AuctionLot.lot_id == lot_id).first()

def get_all_auction_lots_for_auction(db: Session, auction_id: UUID) -> List[models_auction.AuctionLot]:
    """
    يجلب جميع لوطات المزاد لمزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد الأب.

    Returns:
        List[models_auction.AuctionLot]: قائمة بكائنات اللوطات.
    """
    return db.query(models_auction.AuctionLot).filter(models_auction.AuctionLot.auction_id == auction_id).all()

def update_auction_lot(db: Session, db_lot: models_auction.AuctionLot, lot_in: schemas.AuctionLotUpdate) -> models_auction.AuctionLot:
    """
    يحدث بيانات سجل لوت مزاد موجود.
    لا يقوم بتحديث بنود اللوت أو صوره مباشرة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_lot (models_auction.AuctionLot): كائن اللوت من قاعدة البيانات.
        lot_in (schemas.AuctionLotUpdate): البيانات المراد تحديثها.

    Returns:
        models_auction.AuctionLot: كائن اللوت المحدث.
    """
    update_data = lot_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_lot, key, value)
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot

def delete_auction_lot(db: Session, db_lot: models_auction.AuctionLot):
    """
    يحذف لوت مزاد معين (حذف صارم).
    TODO: التحقق من عدم وجود مزايدات مرتبطة بهذا اللوت سيتم في طبقة الخدمة.
    """
    db.delete(db_lot)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for AuctionLotTranslation (ترجمات لوطات المزاد) ---
# ==========================================================

def create_auction_lot_translation(db: Session, lot_id: UUID, trans_in: schemas.AuctionLotTranslationCreate) -> models_auction.AuctionLotTranslation:
    """
    ينشئ ترجمة جديدة للوت مزاد معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت الأم.
        trans_in (schemas.AuctionLotTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models_auction.AuctionLotTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models_auction.AuctionLotTranslation(
        lot_id=lot_id,
        language_code=trans_in.language_code,
        translated_lot_title=trans_in.translated_lot_title,
        translated_lot_description=trans_in.translated_lot_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_auction_lot_translation(db: Session, lot_id: UUID, language_code: str) -> Optional[models_auction.AuctionLotTranslation]:
    """
    يجلب ترجمة لوت مزاد محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models_auction.AuctionLotTranslation]: كائن الترجمة أو None.
    """
    return db.query(models_auction.AuctionLotTranslation).filter(
        and_(
            models_auction.AuctionLotTranslation.lot_id == lot_id,
            models_auction.AuctionLotTranslation.language_code == language_code
        )
    ).first()

def update_auction_lot_translation(db: Session, db_translation: models_auction.AuctionLotTranslation, trans_in: schemas.AuctionLotTranslationUpdate) -> models_auction.AuctionLotTranslation:
    """
    يحدث ترجمة لوت مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models_auction.AuctionLotTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.AuctionLotTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models_auction.AuctionLotTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_auction_lot_translation(db: Session, db_translation: models_auction.AuctionLotTranslation):
    """
    يحذف ترجمة لوت مزاد معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models_auction.AuctionLotTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for LotProduct (منتجات اللوت) ---
# ==========================================================

def create_lot_product(db: Session, lot_product_in: schemas.LotProductCreate) -> models_auction.LotProduct:
    """
    ينشئ سجل منتج لوت جديد في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_product_in (schemas.LotProductCreate): بيانات منتج اللوت للإنشاء.

    Returns:
        models_auction.LotProduct: كائن منتج اللوت الذي تم إنشاؤه.
    """
    db_lot_product = models_auction.LotProduct(
        lot_id=lot_product_in.lot_id,
        packaging_option_id=lot_product_in.packaging_option_id,
        quantity_in_lot=lot_product_in.quantity_in_lot
    )
    db.add(db_lot_product)
    db.commit()
    db.refresh(db_lot_product)
    return db_lot_product

def get_lot_product(db: Session, lot_product_id: int) -> Optional[models_auction.LotProduct]:
    """
    يجلب سجل منتج لوت واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_product_id (int): معرف منتج اللوت المطلوب.

    Returns:
        Optional[models_auction.LotProduct]: كائن منتج اللوت أو None.
    """
    return db.query(models_auction.LotProduct).options(
        joinedload(models_auction.LotProduct.packaging_option) # خيار التعبئة
    ).filter(models_auction.LotProduct.lot_product_id == lot_product_id).first()

def get_all_lot_products_for_lot(db: Session, lot_id: UUID) -> List[models_auction.LotProduct]:
    """
    يجلب جميع منتجات اللوت للوت مزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت الأب.

    Returns:
        List[models_auction.LotProduct]: قائمة بكائنات منتجات اللوت.
    """
    return db.query(models_auction.LotProduct).filter(models_auction.LotProduct.lot_id == lot_id).all()

def update_lot_product(db: Session, db_lot_product: models_auction.LotProduct, lot_product_in: schemas.LotProductUpdate) -> models_auction.LotProduct:
    """
    يحدث بيانات سجل منتج لوت موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_lot_product (models_auction.LotProduct): كائن منتج اللوت من قاعدة البيانات.
        lot_product_in (schemas.LotProductUpdate): البيانات المراد تحديثها.

    Returns:
        models_auction.LotProduct: كائن منتج اللوت المحدث.
    """
    update_data = lot_product_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_lot_product, key, value)
    db.add(db_lot_product)
    db.commit()
    db.refresh(db_lot_product)
    return db_lot_product

def delete_lot_product(db: Session, db_lot_product: models_auction.LotProduct):
    """
    يحذف سجل منتج لوت معين (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_lot_product (models_auction.LotProduct): كائن منتج اللوت من قاعدة البيانات.
    """
    db.delete(db_lot_product)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for LotImage (صور اللوت) ---
# ==========================================================

def create_lot_image(db: Session, lot_image_in: schemas.LotImageCreate) -> models_auction.LotImage:
    """
    ينشئ سجل صورة لوت جديد في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_image_in (schemas.LotImageCreate): بيانات صورة اللوت للإنشاء.

    Returns:
        models_auction.LotImage: كائن صورة اللوت الذي تم إنشاؤه.
    """
    db_lot_image = models_auction.LotImage(
        lot_id=lot_image_in.lot_id,
        image_id=lot_image_in.image_id,
        sort_order=lot_image_in.sort_order
    )
    db.add(db_lot_image)
    db.commit()
    db.refresh(db_lot_image)
    return db_lot_image

def get_lot_image(db: Session, lot_image_id: int) -> Optional[models_auction.LotImage]:
    """
    يجلب سجل صورة لوت واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_image_id (int): معرف صورة اللوت المطلوب.

    Returns:
        Optional[models_auction.LotImage]: كائن صورة اللوت أو None.
    """
    return db.query(models_auction.LotImage).options(
        joinedload(models_auction.LotImage.image) # تحميل الصورة المرتبطة
    ).filter(models_auction.LotImage.lot_image_id == lot_image_id).first()

def get_all_lot_images_for_lot(db: Session, lot_id: UUID) -> List[models_auction.LotImage]:
    """
    يجلب جميع صور اللوت للوت مزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت الأب.

    Returns:
        List[models_auction.LotImage]: قائمة بكائنات صور اللوت.
    """
    return db.query(models_auction.LotImage).filter(models_auction.LotImage.lot_id == lot_id).order_by(models_auction.LotImage.sort_order).all()

def update_lot_image(db: Session, db_lot_image: models_auction.LotImage, lot_image_in: schemas.LotImageUpdate) -> models_auction.LotImage:
    """
    يحدث بيانات سجل صورة لوت موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_lot_image (models_auction.LotImage): كائن صورة اللوت من قاعدة البيانات.
        lot_image_in (schemas.LotImageUpdate): البيانات المراد تحديثها.

    Returns:
        models_auction.LotImage: كائن صورة اللوت المحدث.
    """
    update_data = lot_image_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_lot_image, key, value)
    db.add(db_lot_image)
    db.commit()
    db.refresh(db_lot_image)
    return db_lot_image

def delete_lot_image(db: Session, db_lot_image: models_auction.LotImage):
    """
    يحذف سجل صورة لوت معين (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_lot_image (models_auction.LotImage): كائن صورة اللوت من قاعدة البيانات.
    """
    db.delete(db_lot_image)
    db.commit()
    return