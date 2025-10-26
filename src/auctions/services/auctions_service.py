# backend\src\auction\services\auctions_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone # لاستخدام التواريخ والأوقات

# استيراد المودلز
from src.auctions.models import auctions_models as models_auction
from src.lookups.models import lookups_models as models_statuses
# استيراد Schemas
from src.auctions.schemas import auction_schemas as schemas
from src.lookups.schemas import lookups_schemas as schemas_lookups

# استيراد دوال الـ CRUD
from src.auctions.crud import auctions_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.users.services.core_service import get_user_profile # للتحقق من وجود البائع والمزايد
from src.products.services.product_service import get_product_by_id_for_user as get_product_details # للتحقق من وجود المنتج
from src.products.services.unit_of_measure_service import get_unit_of_measure_details # للتحقق من وحدة القياس
# TODO: خدمة المخزون (inventory_service) لحجز الكميات.
# TODO: خدمة الإشعارات (notifications_service) لإرسال التنبيهات.
# TODO: خدمة التسوية (settlements_service) لتشغيل التسوية بعد انتهاء المزاد.
# TODO: خدمة RFQ (rfqs_service) / Quote (quotes_service) للمقارنة مع المزادات.


# ==========================================================
# --- خدمات حالات المزاد (AuctionStatus) ---
# ==========================================================

def create_new_auction_status(db: Session, status_in: schemas_lookups.AuctionStatusCreate) -> models_statuses.AuctionStatus:
    """
    خدمة لإنشاء حالة مزاد جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas.AuctionStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        models_statuses.AuctionStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    if db.query(models_statuses.AuctionStatus).filter(models_statuses.AuctionStatus.status_name_key == status_in.status_name_key).first():
        raise ConflictException(detail=f"حالة المزاد بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return auctions_crud.create_auction_status(db=db, status_in=status_in)

def get_auction_status_details(db: Session, auction_status_id: int) -> models_statuses.AuctionStatus:
    """
    خدمة لجلب حالة مزاد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة.

    Returns:
        models_statuses.AuctionStatus: كائن الحالة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
    """
    status_obj = auctions_crud.get_auction_status(db, auction_status_id=auction_status_id)
    if not status_obj:
        raise NotFoundException(detail=f"حالة المزاد بمعرف {auction_status_id} غير موجودة.")
    return status_obj

def get_all_auction_statuses_service(db: Session) -> List[models_statuses.AuctionStatus]:
    """
    خدمة لجلب جميع حالات المزاد المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[models_statuses.AuctionStatus]: قائمة بكائنات الحالات.
    """
    return auctions_crud.get_all_auction_statuses(db)

def update_auction_status_service(db: Session, auction_status_id: int, status_in: schemas_lookups.AuctionStatusUpdate) -> models_statuses.AuctionStatus:
    """
    خدمة لتحديث حالة مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas.AuctionStatusUpdate): البيانات المراد تحديثها.

    Returns:
        models_statuses.AuctionStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_auction_status_details(db, auction_status_id)
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        if db.query(models_statuses.AuctionStatus).filter(models_statuses.AuctionStatus.status_name_key == status_in.status_name_key).first():
            raise ConflictException(detail=f"حالة المزاد بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return auctions_crud.update_auction_status_crud(db=db, db_status=db_status, status_in=status_in)

def delete_auction_status_service(db: Session, auction_status_id: int):
    """
    خدمة لحذف حالة مزاد (حذف صارم).
    تتضمن التحقق من عدم وجود مزادات أو لوطات مرتبطة بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ForbiddenException: إذا كانت الحالة مستخدمة حاليًا بواسطة أي مزادات.
    """
    db_status = get_auction_status_details(db, auction_status_id)
    # التحقق من عدم وجود Auction أو AuctionLot تستخدم auction_status_id هذا
    if db.query(models_auction.Auction).filter(models_auction.Auction.auction_status_id == auction_status_id).count() > 0 or \
       db.query(models_auction.AuctionLot).filter(models_auction.AuctionLot.lot_status_id == auction_status_id).count() > 0:
        raise ForbiddenException(detail=f"لا يمكن حذف حالة المزاد بمعرف {auction_status_id} لأنها تستخدم من قبل مزادات أو لوطات موجودة.")
    auctions_crud.delete_auction_status(db=db, db_status=db_status)
    return {"message": "تم حذف حالة المزاد بنجاح."}


# ==========================================================
# --- خدمات ترجمات حالات المزاد (AuctionStatusTranslation) ---
# ==========================================================

def create_auction_status_translation_service(db: Session, auction_status_id: int, trans_in: schemas_lookups.AuctionStatusTranslationCreate) -> models_statuses.AuctionStatusTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لحالة مزاد معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة الأم.
        trans_in (schemas.AuctionStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models_statuses.AuctionStatusTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة الأم.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    get_auction_status_details(db, auction_status_id)
    if auctions_crud.get_auction_status_translation(db, auction_status_id=auction_status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة لحالة المزاد بمعرف {auction_status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")
    return auctions_crud.create_auction_status_translation(db=db, auction_status_id=auction_status_id, trans_in=trans_in)

def get_auction_status_translation_details(db: Session, auction_status_id: int, language_code: str) -> models_statuses.AuctionStatusTranslation:
    """
    خدمة لجلب ترجمة حالة مزاد محددة بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة.

    Returns:
        models_statuses.AuctionStatusTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = auctions_crud.get_auction_status_translation(db, auction_status_id=auction_status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة المزاد بمعرف {auction_status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_auction_status_translation_service(db: Session, auction_status_id: int, language_code: str, trans_in: schemas_lookups.AuctionStatusTranslationUpdate) -> models_statuses.AuctionStatusTranslation:
    """
    خدمة لتحديث ترجمة حالة مزاد موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.AuctionStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models_statuses.AuctionStatusTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_auction_status_translation_details(db, auction_status_id, language_code)
    return auctions_crud.update_auction_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_auction_status_translation_service(db: Session, auction_status_id: int, language_code: str):
    """
    خدمة لحذف ترجمة حالة مزاد معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_auction_status_translation_details(db, auction_status_id, language_code)
    auctions_crud.delete_auction_status_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة حالة المزاد بنجاح."}


# ==========================================================
# --- خدمات أنواع المزادات (AuctionType) ---
# ==========================================================

def create_new_auction_type(db: Session, type_in: schemas_lookups.AuctionTypeCreate) -> models_statuses.AuctionType:
    """
    خدمة لإنشاء نوع مزاد جديد مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas.AuctionTypeCreate): بيانات النوع للإنشاء.

    Returns:
        models_statuses.AuctionType: كائن النوع الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان هناك نوع بنفس المفتاح موجود بالفعل.
    """
    if db.query(models_statuses.AuctionType).filter(models_statuses.AuctionType.type_name_key == type_in.type_name_key).first():
        raise ConflictException(detail=f"نوع المزاد بمفتاح '{type_in.type_name_key}' موجود بالفعل.")
    return auctions_crud.create_auction_type(db=db, type_in=type_in)

def get_auction_type_details(db: Session, auction_type_id: int) -> models_statuses.AuctionType:
    """
    خدمة لجلب نوع مزاد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_type_id (int): معرف النوع.

    Returns:
        models_statuses.AuctionType: كائن النوع.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
    """
    type_obj = auctions_crud.get_auction_type(db, auction_type_id=auction_type_id)
    if not type_obj:
        raise NotFoundException(detail=f"نوع المزاد بمعرف {auction_type_id} غير موجود.")
    return type_obj

def get_all_auction_types_service(db: Session) -> List[models_statuses.AuctionType]:
    """
    خدمة لجلب جميع أنواع المزادات المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[models_statuses.AuctionType]: قائمة بكائنات الأنواع.
    """
    return auctions_crud.get_all_auction_types(db)

def update_auction_type_service(db: Session, auction_type_id: int, type_in: schemas_lookups.AuctionTypeUpdate) -> models_statuses.AuctionType:
    """
    خدمة لتحديث نوع مزاد موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_type_id (int): معرف النوع المراد تحديثه.
        type_in (schemas.AuctionTypeUpdate): البيانات المراد تحديثها.

    Returns:
        models_statuses.AuctionType: كائن النوع المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_type = get_auction_type_details(db, auction_type_id)
    if type_in.type_name_key and type_in.type_name_key != db_type.type_name_key:
        if db.query(models_statuses.AuctionType).filter(models_statuses.AuctionType.type_name_key == type_in.type_name_key).first():
            raise ConflictException(detail=f"نوع المزاد بمفتاح '{type_in.type_name_key}' موجود بالفعل.")
    return auctions_crud.update_auction_type_crud(db=db, db_type=db_type, type_in=type_in)

def delete_auction_type_service(db: Session, auction_type_id: int):
    """
    خدمة لحذف نوع مزاد (حذف صارم).
    تتضمن التحقق من عدم وجود مزادات مرتبطة بهذا النوع.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_type_id (int): معرف النوع المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
        ForbiddenException: إذا كان النوع مستخدمًا حاليًا بواسطة أي مزادات.
    """
    db_type = get_auction_type_details(db, auction_type_id)
    if db.query(models_auction.Auction).filter(models_auction.Auction.auction_type_id == auction_type_id).count() > 0:
        raise ForbiddenException(detail=f"لا يمكن حذف نوع المزاد بمعرف {auction_type_id} لأنه يستخدم من قبل مزادات موجودة.")
    auctions_crud.delete_auction_type(db=db, db_type=db_type)
    return {"message": "تم حذف نوع المزاد بنجاح."}


# ==========================================================
# --- خدمات المزادات (Auction) ---
# ==========================================================

def create_new_auction(db: Session, auction_in: schemas.AuctionCreate, current_user: User) -> models_auction.Auction:
    """
    خدمة لإنشاء مزاد جديد بواسطة بائع.
    تتضمن التحقق من صحة البيانات، وجود الكيانات المرتبطة، وتعيين الحالة الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_in (schemas.AuctionCreate): بيانات المزاد للإنشاء، بما في ذلك لوطاته.
        current_user (User): المستخدم الحالي (البائع).

    Returns:
        models_auction.Auction: كائن المزاد الذي تم إنشاؤه.

    Raises:
        BadRequestException: إذا كانت البيانات غير صالحة (مثلاً تواريخ غير منطقية، أسعار غير صالحة).
        NotFoundException: إذا لم يتم العثور على المنتج، نوع المزاد، وحدة القياس.
        ForbiddenException: إذا كان المستخدم غير مصرح له بإنشاء مزاد.
        ConflictException: إذا لم يتم العثور على حالة المزاد الأولية.
    """
    # 1. التحقق من صلاحية البائع
    if not current_user.is_seller: # افتراض وجود خاصية is_seller في User model أو فحص الأدوار
        raise ForbiddenException(detail="غير مصرح لك بإنشاء مزادات.")

    # 2. التحقق من وجود المنتج
    get_product_details(db, auction_in.product_id, current_user) # TODO: get_product_details يجب أن تسمح بالوصول للمنتج بغض النظر عن الملكية للبائع.

    # 3. التحقق من وجود نوع المزاد
    get_auction_type_details(db, auction_in.auction_type_id)

    # 4. التحقق من وجود وحدة القياس
    get_unit_of_measure_details(db, auction_in.unit_of_measure_id_for_quantity)

    # 5. التحقق من منطقية التواريخ
    if auction_in.start_timestamp >= auction_in.end_timestamp:
        raise BadRequestException(detail="تاريخ بدء المزاد يجب أن يكون قبل تاريخ انتهائه.")
    if auction_in.start_timestamp < datetime.now(timezone.utc):
        raise BadRequestException(detail="تاريخ بدء المزاد يجب أن يكون في المستقبل.")

    # 6. التحقق من الأسعار
    if auction_in.reserve_price_per_unit is not None and auction_in.reserve_price_per_unit < auction_in.starting_price_per_unit:
        raise BadRequestException(detail="السعر الاحتياطي يجب أن يكون أكبر من أو يساوي السعر الافتتاحي.")
    if auction_in.minimum_bid_increment <= 0:
        raise BadRequestException(detail="أقل قيمة لزيادة المزايدة يجب أن تكون أكبر من صفر.")

    # 7. جلب الحالة الأولية للمزاد (عادةً 'SCHEDULED')
    initial_auction_status = db.query(models_statuses.AuctionStatus).filter(models_statuses.AuctionStatus.status_name_key == "SCHEDULED").first()
    if not initial_auction_status:
        raise ConflictException(detail="حالة المزاد الأولية 'SCHEDULED' غير موجودة.")

    # 8. التحقق من اللوطات (إذا وجدت)
    if auction_in.lots:
        total_lot_quantity = sum(lot.quantity_in_lot for lot in auction_in.lots if lot.quantity_in_lot is not None)
        if total_lot_quantity > auction_in.quantity_offered:
            raise BadRequestException(detail="إجمالي كميات اللوطات يتجاوز الكمية المعروضة في المزاد الرئيسي.")
        # TODO: تحقق من منطقية أسعار بدء اللوطات (lot_starting_price) بالنسبة لسعر بدء المزاد الرئيسي.
        # TODO: تحقق من حالة اللوت (lot_status_id) إذا تم تعيينها في الإنشاء.
        # TODO: تحقق من منتجات اللوت وصوره (LotProduct, LotImage) إذا كانت صحيحة.

    # 9. استدعاء CRUD لإنشاء المزاد (مع لوطاته).
    db_auction = auctions_crud.create_auction(
        db=db,
        auction_in=auction_in,
        seller_user_id=current_user.user_id,
        auction_status_id=initial_auction_status.auction_status_id
    )

    # TODO: هـام: حجز الكمية المعروضة من المخزون (inventory_service).
    #       استدعاء: inventory_service.adjust_stock_level(db, packaging_option_id, -quantity_offered, reason="حجز للمزاد")
    #       يتطلب معرفة packaging_option_id للمنتج المعروض.

    # TODO: إخطار وحدة الإشعارات (Module 11) بأن المزاد قد تم جدولته.
    # TODO: جدولة مهمة خلفية (Celery Task) لبدء المزاد تلقائيًا في start_timestamp.

    return db_auction

def get_auction_details(db: Session, auction_id: UUID) -> models_auction.Auction:
    """
    خدمة لجلب تفاصيل مزاد واحد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد المطلوب.

    Returns:
        models_auction.Auction: كائن المزاد المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد.
    """
    auction = auctions_crud.get_auction(db, auction_id=auction_id)
    if not auction:
        raise NotFoundException(detail=f"المزاد بمعرف {auction_id} غير موجود.")
    return auction

def get_all_auctions(db: Session, status_name_key: Optional[str] = None, type_name_key: Optional[str] = None, seller_user_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[models_auction.Auction]:
    """
    خدمة لجلب جميع المزادات، مع خيارات للتصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_name_key (Optional[str]): تصفية حسب مفتاح اسم الحالة (مثلاً 'ACTIVE', 'SCHEDULED').
        type_name_key (Optional[str]): تصفية حسب مفتاح اسم النوع (مثلاً 'ENGLISH').
        seller_user_id (Optional[UUID]): تصفية حسب معرف البائع.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_auction.Auction]: قائمة بكائنات المزادات.

    Raises:
        BadRequestException: إذا كانت مفاتيح الحالة أو النوع غير موجودة.
    """
    auction_status_id = None
    if status_name_key:
        status_obj = db.query(models_statuses.AuctionStatus).filter(models_statuses.AuctionStatus.status_name_key == status_name_key).first()
        if not status_obj:
            raise BadRequestException(detail=f"حالة المزاد '{status_name_key}' غير موجودة.")
        auction_status_id = status_obj.auction_status_id

    auction_type_id = None
    if type_name_key:
        type_obj = db.query(models_statuses.AuctionType).filter(models_statuses.AuctionType.type_name_key == type_name_key).first()
        if not type_obj:
            raise BadRequestException(detail=f"نوع المزاد '{type_name_key}' غير موجود.")
        auction_type_id = type_obj.auction_type_id

    return auctions_crud.get_all_auctions(db, seller_user_id=seller_user_id, auction_status_id=auction_status_id, auction_type_id=auction_type_id, skip=skip, limit=limit)

def get_my_created_auctions(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[models_auction.Auction]:
    """
    خدمة لجلب جميع المزادات التي أنشأها البائع الحالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي (البائع).
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_auction.Auction]: قائمة بكائنات المزادات.
    """
    # التحقق من أن المستخدم لديه صلاحية لعرض المزادات التي أنشأها.
    # هذه الدالة تتطلب صلاحية 'AUCTION_CREATE_OWN' أو 'AUCTION_MANAGE_OWN'
    # TODO: إضافة تحقق صلاحية أكثر صرامة إذا كانت 'AUCTION_VIEW_OWN' موجودة.

    return auctions_crud.get_all_auctions(db, seller_user_id=current_user.user_id, skip=skip, limit=limit)


def update_auction(db: Session, auction_id: UUID, auction_in: schemas.AuctionUpdate, current_user: User) -> models_auction.Auction:
    """
    خدمة لتحديث مزاد موجود.
    تتضمن التحقق من ملكية البائع، وصلاحياته، ومراحل المزاد المسموح بها للتحديث.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد المراد تحديثه.
        auction_in (schemas.AuctionUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_auction.Auction: كائن المزاد المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد أو غير مصرح له.
        BadRequestException: إذا كانت البيانات غير صالحة، أو إذا كان المزاد في حالة لا تسمح بالتحديث.
        ConflictException: إذا كانت الحالة الجديدة غير موجودة، أو التغيير يؤدي إلى تعارض.
    """
    db_auction = get_auction_details(db, auction_id)

    # 1. التحقق من صلاحيات المستخدم: يجب أن يكون البائع المالك أو مسؤولاً.
    is_owner = db_auction.seller_user_id == current_user.user_id
    is_admin = any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions)

    if not (is_owner or is_admin):
        raise ForbiddenException(detail="غير مصرح لك بتحديث هذا المزاد.")

    # 2. منطق عمل: التحقق من أن المزاد لا يزال في حالة تسمح بالتعديل.
    #    - عادةً، يمكن تعديل المزادات فقط عندما تكون 'SCHEDULED' (مجدولة) وقبل أن تبدأ.
    if db_auction.auction_status.status_name_key != "SCHEDULED":
        raise BadRequestException(detail=f"لا يمكن تحديث المزاد في حالته الحالية: {db_auction.auction_status.status_name_key}. يمكن تعديل المزادات المجدولة فقط.")
    
    # 3. التحقق من منطقية التواريخ والأسعار إذا تم تحديثها.
    if auction_in.start_timestamp is not None and auction_in.start_timestamp < datetime.now(timezone.utc):
        raise BadRequestException(detail="تاريخ بدء المزاد يجب أن يكون في المستقبل.")
    if auction_in.start_timestamp is not None and auction_in.end_timestamp is not None and auction_in.start_timestamp >= auction_in.end_timestamp:
        raise BadRequestException(detail="تاريخ بدء المزاد يجب أن يكون قبل تاريخ انتهائه.")
    
    # TODO: المزيد من التحقق للأسعار (reserve_price_per_unit, minimum_bid_increment).
    # TODO: التحقق من quantity_offered لا يتغير إذا كان هناك bids مسجلة.

    # 4. التحقق من وجود الحالة الجديدة إذا تم تحديث auction_status_id.
    if auction_in.auction_status_id and auction_in.auction_status_id != db_auction.auction_status_id:
        new_status = db.query(models_statuses.AuctionStatus).filter(models_statuses.AuctionStatus.auction_status_id == auction_in.auction_status_id).first()
        if not new_status:
            raise BadRequestException(detail=f"حالة المزاد بمعرف {auction_in.auction_status_id} غير موجودة.")
        # TODO: آلة حالة المزاد: التحقق من الانتقال المسموح به إلى الحالة الجديدة (مثلاً لا يمكن القفز من SCHEDULED إلى CLOSED).
        #       if new_status.status_name_key == "CANCELLED": # هذا يجب أن يتم عبر cancel_auction
        #           raise BadRequestException("يرجى استخدام نقطة نهاية الإلغاء لإلغاء المزاد.")

    return auctions_crud.update_auction(db=db, db_auction=db_auction, auction_in=auction_in)

def cancel_auction(db: Session, auction_id: UUID, current_user: User, reason: Optional[str] = None) -> models_auction.Auction:
    """
    خدمة لإلغاء مزاد (يعادل الحذف الناعم).
    تتضمن التحقق من الصلاحيات، ومراحل المزاد المسموح بها للإلغاء، وعكس العمليات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد المراد إلغاؤه.
        current_user (User): المستخدم الحالي.
        reason (Optional[str]): سبب الإلغاء.

    Returns:
        models_auction.Auction: كائن المزاد بعد تحديث حالته إلى "ملغى".

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بالإلغاء.
        BadRequestException: إذا كان المزاد في حالة لا تسمح بالإلغاء.
        ConflictException: إذا لم يتم العثور على حالة الإلغاء.
    """
    db_auction = get_auction_details(db, auction_id)

    # 1. التحقق من صلاحيات المستخدم: يجب أن يكون البائع المالك أو مسؤولاً.
    is_owner = db_auction.seller_user_id == current_user.user_id
    is_admin = any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions)

    if not (is_owner or is_admin):
        raise ForbiddenException(detail="غير مصرح لك بإلغاء هذا المزاد.")

    # 2. التحقق من المرحلة المسموح بها للإلغاء (آلة حالة المزاد).
    #    - عادةً، لا يمكن إلغاء المزادات النشطة التي بها مزايدات أو المزادات المنتهية.
    if db_auction.auction_status.status_name_key not in ["SCHEDULED", "PENDING_ARRIVAL"]: # حالات تسمح بالإلغاء
        raise BadRequestException(detail=f"لا يمكن إلغاء المزاد في حالته الحالية: {db_auction.auction_status.status_name_key}.")
    if db_auction.total_bids_count > 0:
        raise BadRequestException(detail="لا يمكن إلغاء المزاد بعد تلقي مزايدات.")

    # 3. جلب حالة الإلغاء
    canceled_status = db.query(models_statuses.AuctionStatus).filter(models_statuses.AuctionStatus.status_name_key == "CANCELED").first()
    if not canceled_status:
        raise ConflictException(detail="حالة الإلغاء 'CANCELED' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    # 4. تحديث حالة المزاد
    auctions_crud.update_auction_status(db=db, db_auction=db_auction, new_status_id=canceled_status.auction_status_id)

    # TODO: هـام: إعادة الكميات المحجوزة من المخزون إلى المخزون المتاح (inventory_service).
    #       إذا تم حجز الكمية عند إنشاء المزاد.

    # TODO: إخطار جميع المشاركين المسجلين في المزاد (AuctionParticipant) بأنه تم الإلغاء.
    # TODO: إخطار وحدة الإشعارات (Module 11) بأن المزاد قد تم إلغاؤه.

    return db_auction

# ==========================================================
# --- خدمات لوطات/دفعات المزاد (AuctionLot) ---
# ==========================================================

def create_auction_lot(db: Session, lot_in: schemas.AuctionLotCreate, current_user: User) -> models_auction.AuctionLot:
    """
    خدمة لإنشاء لوت مزاد جديد.
    تتضمن التحقق من وجود المزاد الأم، ملكية البائع، والتحقق من بنود اللوت.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_in (schemas.AuctionLotCreate): بيانات اللوت للإنشاء.
        current_user (User): المستخدم الحالي (البائع).

    Returns:
        models_auction.AuctionLot: كائن اللوت الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المزاد الأم.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
        BadRequestException: إذا كانت بيانات اللوت غير صالحة (مثلاً الكميات، أسعار البدء).
        ConflictException: إذا لم يتم العثور على حالة اللوت الافتراضية.
    """
    # 1. التحقق من وجود المزاد الأم وصلاحية المستخدم (البائع أو المسؤول)
    db_auction = get_auction_details(db, lot_in.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بإضافة لوط لهذا المزاد.")

    # 2. التحقق من أن المزاد في حالة تسمح بإضافة لوطات (عادةً 'SCHEDULED' وقبل بدء المزاد)
    if db_auction.auction_status.status_name_key != "SCHEDULED":
        raise BadRequestException(detail=f"لا يمكن إضافة لوطات لمزاد في حالته الحالية: {db_auction.auction_status.status_name_key}.")

    # 3. التحقق من بنود اللوت (LotProduct) وصوره (LotImage)
    if not lot_in.products_in_lot:
        raise BadRequestException(detail="يجب أن يحتوي اللوت على منتج واحد على الأقل.")
    
    total_products_in_lot_quantity = 0.0
    for product_in_lot in lot_in.products_in_lot:
        # TODO: التحقق من وجود ProductPackagingOptionId
        # get_packaging_option_details(db, product_in_lot.packaging_option_id)
        total_products_in_lot_quantity += product_in_lot.quantity_in_lot
    
    if lot_in.quantity_in_lot and lot_in.quantity_in_lot != total_products_in_lot_quantity:
        raise BadRequestException(detail="الكمية الإجمالية في اللوت لا تتطابق مع مجموع كميات المنتجات المحددة في اللوت.")
    
    # TODO: التحقق من وجود ImageId لكل LotImage
    # for image_in_lot in lot_in.images:
    #     image_service.get_image_details(db, image_in_lot.image_id)

    # 4. جلب حالة اللوت الأولية (يمكن أن تكون نفس حالة المزاد أو حالة خاصة باللوت)
    #    هنا نفترض أن اللوت يأخذ نفس حالة المزاد أو حالة افتراضية "جديدة"
    initial_lot_status = db_auction.auction_status_id # يمكن استخدام حالة المزاد كحالة افتراضية للوت
    if lot_in.lot_status_id: # إذا تم تحديد حالة للوت بشكل صريح
        get_auction_status_details(db, lot_in.lot_status_id) # التحقق من وجود الحالة
        initial_lot_status = lot_in.lot_status_id

    return auctions_crud.create_auction_lot(db=db, lot_in=lot_in)

def get_auction_lot_details(db: Session, lot_id: UUID) -> models_auction.AuctionLot:
    """
    خدمة لجلب تفاصيل لوت مزاد واحد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت المطلوب.

    Returns:
        models_auction.AuctionLot: كائن اللوت المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على اللوت.
    """
    lot = auctions_crud.get_auction_lot(db, lot_id=lot_id)
    if not lot:
        raise NotFoundException(detail=f"لوت المزاد بمعرف {lot_id} غير موجود.")
    return lot

def get_all_auction_lots_for_auction(db: Session, auction_id: UUID) -> List[models_auction.AuctionLot]:
    """
    خدمة لجلب جميع لوطات المزاد لمزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        auction_id (UUID): معرف المزاد الأب.

    Returns:
        List[models_auction.AuctionLot]: قائمة بكائنات اللوطات.
    """
    # 1. التحقق من وجود المزاد الأم
    # get_auction_details(db, auction_id) # ليس بالضرورة هنا، قد يتم التحقق في الراوتر

    return auctions_crud.get_all_auction_lots_for_auction(db, auction_id=auction_id)

def update_auction_lot(db: Session, lot_id: UUID, lot_in: schemas.AuctionLotUpdate, current_user: User) -> models_auction.AuctionLot:
    """
    خدمة لتحديث لوت مزاد موجود.
    تتضمن التحقق من ملكية البائع وصلاحياته، ومراحل المزاد المسموح بها للتحديث.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت المراد تحديثه.
        lot_in (schemas.AuctionLotUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_auction.AuctionLot: كائن اللوت المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على اللوت.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
        BadRequestException: إذا كانت البيانات غير صالحة، أو إذا كان المزاد في حالة لا تسمح بالتحديث.
    """
    db_lot = get_auction_lot_details(db, lot_id)

    # 1. التحقق من ملكية البائع للمزاد الأم وصلاحياته
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بتحديث لوت المزاد هذا.")

    # 2. التحقق من أن المزاد في حالة تسمح بالتعديل (عادةً 'SCHEDULED')
    if db_auction.auction_status.status_name_key != "SCHEDULED":
        raise BadRequestException(detail=f"لا يمكن تحديث اللوت في حالته الحالية: {db_auction.auction_status.status_name_key}. يمكن تعديل لوطات المزادات المجدولة فقط.")

    # 3. التحقق من منطقية الكميات والأسعار إذا تم تحديثها.
    if lot_in.quantity_in_lot is not None and lot_in.quantity_in_lot <= 0:
        raise BadRequestException(detail="كمية اللوت يجب أن تكون أكبر من صفر.")
    if lot_in.lot_starting_price is not None and lot_in.lot_starting_price <= 0:
        raise BadRequestException(detail="سعر بدء اللوت يجب أن يكون أكبر من صفر.")
    
    # 4. التحقق من حالة اللوت (lot_status_id)
    if lot_in.lot_status_id and lot_in.lot_status_id != db_lot.lot_status_id:
        get_auction_status_details(db, lot_in.lot_status_id) # التحقق من وجود الحالة
        # TODO: آلة حالة اللوت: التحقق من الانتقالات المسموح بها بين حالات اللوت.

    return auctions_crud.update_auction_lot(db=db, db_lot=db_lot, lot_in=lot_in)

def delete_auction_lot(db: Session, lot_id: UUID, current_user: User):
    """
    خدمة لحذف لوت مزاد (حذف صارم).
    تتضمن التحقق من ملكية البائع، وحالة المزاد، وعدم وجود مزايدات مرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت المراد حذفه.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على اللوت.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
        BadRequestException: إذا كان المزاد في حالة لا تسمح بالحذف، أو إذا كانت هناك مزايدات مسجلة.
    """
    db_lot = get_auction_lot_details(db, lot_id)

    # 1. التحقق من ملكية البائع للمزاد الأم وصلاحياته
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بحذف لوت المزاد هذا.")

    # 2. التحقق من أن المزاد في حالة تسمح بالحذف (عادةً 'SCHEDULED' وقبل بدء المزاد)
    if db_auction.auction_status.status_name_key != "SCHEDULED":
        raise BadRequestException(detail=f"لا يمكن حذف اللوت في حالته الحالية: {db_auction.auction_status.status_name_key}. يمكن حذف لوطات المزادات المجدولة فقط.")
    
    # 3. التحقق من عدم وجود مزايدات مرتبطة باللوت.
    # TODO: يتطلب استيراد خدمة المزايدات (bidding_service) للتحقق من وجود مزايدات.
    # if bidding_service.get_bids_for_lot(db, lot_id).count() > 0:
    #    raise BadRequestException(detail="لا يمكن حذف اللوت بعد تلقي مزايدات.")
    from src.auctions.crud.bidding_crud import get_all_bids_for_auction # استيراد مباشر للـ CRUD
    if get_all_bids_for_auction(db, auction_id=db_auction.auction_id): # التحقق من وجود مزايدات في المزاد ككل
        raise BadRequestException(detail="لا يمكن حذف اللوت بعد تلقي مزايدات على هذا المزاد.")


    auctions_crud.delete_auction_lot(db=db, db_lot=db_lot)
    return {"message": "تم حذف لوت المزاد بنجاح."}


# ==========================================================
# --- خدمات ترجمات لوطات المزاد (AuctionLotTranslation) ---
# ==========================================================

def create_auction_lot_translation(db: Session, lot_id: UUID, trans_in: schemas.AuctionLotTranslationCreate, current_user: User) -> models_auction.AuctionLotTranslation:
    """
    خدمة لإنشاء ترجمة جديدة للوت مزاد معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت الأم.
        trans_in (schemas.AuctionLotTranslationCreate): بيانات الترجمة للإنشاء.
        current_user (User): المستخدم الحالي.

    Returns:
        models_auction.AuctionLotTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على اللوت الأم.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    # 1. التحقق من وجود اللوت الأم وصلاحية المستخدم
    db_lot = get_auction_lot_details(db, lot_id)
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بإضافة ترجمة لهذا اللوت.")

    # 2. التحقق من عدم وجود ترجمة بنفس اللغة للوت
    if auctions_crud.get_auction_lot_translation(db, lot_id=lot_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة للوت بمعرف {lot_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return auctions_crud.create_auction_lot_translation(db=db, lot_id=lot_id, trans_in=trans_in)

def get_auction_lot_translation_details(db: Session, lot_id: UUID, language_code: str) -> models_auction.AuctionLotTranslation:
    """
    خدمة لجلب ترجمة لوت مزاد محددة بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت الأم.
        language_code (str): رمز اللغة.

    Returns:
        models_auction.AuctionLotTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = auctions_crud.get_auction_lot_translation(db, lot_id=lot_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للوت بمعرف {lot_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_auction_lot_translation(db: Session, lot_id: UUID, language_code: str, trans_in: schemas.AuctionLotTranslationUpdate, current_user: User) -> models_auction.AuctionLotTranslation:
    """
    خدمة لتحديث ترجمة لوت مزاد موجودة.
    تتضمن التحقق من ملكية المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.AuctionLotTranslationUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_auction.AuctionLotTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
    """
    db_translation = get_auction_lot_translation_details(db, lot_id, language_code)

    # التحقق من ملكية المستخدم للوت الأم
    db_lot = get_auction_lot_details(db, lot_id)
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بتحديث ترجمة هذا اللوت.")

    return auctions_crud.update_auction_lot_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_auction_lot_translation(db: Session, lot_id: UUID, language_code: str, current_user: User):
    """
    خدمة لحذف ترجمة لوت مزاد معينة (حذف صارم).
    تتضمن التحقق من ملكية المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت الأم.
        language_code (str): رمز اللغة للترجمة.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
    """
    db_translation = get_auction_lot_translation_details(db, lot_id, language_code)

    # التحقق من ملكية المستخدم للوت الأم
    db_lot = get_auction_lot_details(db, lot_id)
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بحذف ترجمة هذا اللوت.")

    auctions_crud.delete_auction_lot_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة لوت المزاد بنجاح."}


# ==========================================================
# --- خدمات منتجات اللوت (LotProduct) ---
# ==========================================================

def create_lot_product(db: Session, lot_product_in: schemas.LotProductCreate, current_user: User) -> models_auction.LotProduct:
    """
    خدمة لإنشاء سجل منتج لوت جديد.
    تتضمن التحقق من وجود اللوت الأم، ملكية البائع، ووجود خيار التعبئة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_product_in (schemas.LotProductCreate): بيانات منتج اللوت للإنشاء.
        current_user (User): المستخدم الحالي.

    Returns:
        models_auction.LotProduct: كائن منتج اللوت الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على اللوت الأم أو خيار التعبئة.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
        BadRequestException: إذا كانت الكمية غير صالحة.
    """
    # 1. التحقق من وجود اللوت الأم وصلاحية المستخدم
    db_lot = get_auction_lot_details(db, lot_product_in.lot_id)
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بإضافة منتج لهذا اللوت.")

    # 2. التحقق من وجود خيار التعبئة
    from src.products.services.packaging_service import get_packaging_option_details # استيراد خدمة خيار التعبئة
    get_packaging_option_details(db, lot_product_in.packaging_option_id)

    # 3. التحقق من الكمية
    if lot_product_in.quantity_in_lot <= 0:
        raise BadRequestException(detail="الكمية في اللوت يجب أن تكون أكبر من صفر.")

    return auctions_crud.create_lot_product(db=db, lot_product_in=lot_product_in)

def get_lot_product_details(db: Session, lot_product_id: int) -> models_auction.LotProduct:
    """
    خدمة لجلب سجل منتج لوت واحد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_product_id (int): معرف منتج اللوت المطلوب.

    Returns:
        models_auction.LotProduct: كائن منتج اللوت المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على منتج اللوت.
    """
    lot_product = auctions_crud.get_lot_product(db, lot_product_id=lot_product_id)
    if not lot_product:
        raise NotFoundException(detail=f"منتج اللوت بمعرف {lot_product_id} غير موجود.")
    return lot_product

def get_all_lot_products_for_lot(db: Session, lot_id: UUID) -> List[models_auction.LotProduct]:
    """
    خدمة لجلب جميع منتجات اللوت للوت مزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت الأم.

    Returns:
        List[models_auction.LotProduct]: قائمة بكائنات منتجات اللوت.
    """
    # التحقق من وجود اللوت الأم (اختياري هنا)
    # get_auction_lot_details(db, lot_id)
    return auctions_crud.get_all_lot_products_for_lot(db, lot_id=lot_id)

def update_lot_product(db: Session, lot_product_id: int, lot_product_in: schemas.LotProductUpdate, current_user: User) -> models_auction.LotProduct:
    """
    خدمة لتحديث سجل منتج لوت موجود.
    تتضمن التحقق من ملكية البائع.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_product_id (int): معرف منتج اللوت المراد تحديثه.
        lot_product_in (schemas.LotProductUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_auction.LotProduct: كائن منتج اللوت المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على منتج اللوت.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
        BadRequestException: إذا كانت الكمية غير صالحة.
    """
    db_lot_product = get_lot_product_details(db, lot_product_id)

    # التحقق من ملكية البائع للمزاد الأم
    db_lot = get_auction_lot_details(db, db_lot_product.lot_id)
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بتحديث منتج اللوت هذا.")

    # التحقق من الكمية
    if lot_product_in.quantity_in_lot is not None and lot_product_in.quantity_in_lot <= 0:
        raise BadRequestException(detail="الكمية في اللوت يجب أن تكون أكبر من صفر.")

    return auctions_crud.update_lot_product(db=db, db_lot_product=db_lot_product, lot_product_in=lot_product_in)

def delete_lot_product(db: Session, lot_product_id: int, current_user: User):
    """
    خدمة لحذف سجل منتج لوت معين (حذف صارم).
    تتضمن التحقق من ملكية البائع.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_product_id (int): معرف منتج اللوت المراد حذفه.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على منتج اللوت.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
    """
    db_lot_product = get_lot_product_details(db, lot_product_id)

    # التحقق من ملكية البائع للمزاد الأم
    db_lot = get_auction_lot_details(db, db_lot_product.lot_id)
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بحذف منتج اللوت هذا.")

    auctions_crud.delete_lot_product(db=db, db_lot_product=db_lot_product)
    return {"message": "تم حذف منتج اللوت بنجاح."}


# ==========================================================
# --- خدمات صور اللوت (LotImage) ---
# ==========================================================

def create_lot_image(db: Session, lot_image_in: schemas.LotImageCreate, current_user: User) -> models_auction.LotImage:
    """
    خدمة لإنشاء سجل صورة لوت جديد.
    تتضمن التحقق من وجود اللوت الأم، ملكية البائع، ووجود الصورة الأساسية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_image_in (schemas.LotImageCreate): بيانات صورة اللوت للإنشاء.
        current_user (User): المستخدم الحالي.

    Returns:
        models_auction.LotImage: كائن صورة اللوت الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على اللوت الأم أو الصورة الأساسية.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
    """
    # 1. التحقق من وجود اللوت الأم وصلاحية المستخدم
    db_lot = get_auction_lot_details(db, lot_image_in.lot_id)
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بإضافة صورة لهذا اللوت.")

    # 2. التحقق من وجود الصورة الأساسية (Image)
    from src.products.services.image_service import get_image_details # استيراد خدمة الصورة
    get_image_details(db, lot_image_in.image_id)

    return auctions_crud.create_lot_image(db=db, lot_image_in=lot_image_in)

def get_lot_image_details(db: Session, lot_image_id: int) -> models_auction.LotImage:
    """
    خدمة لجلب سجل صورة لوت واحد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_image_id (int): معرف صورة اللوت المطلوب.

    Returns:
        models_auction.LotImage: كائن صورة اللوت المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على صورة اللوت.
    """
    lot_image = auctions_crud.get_lot_image(db, lot_image_id=lot_image_id)
    if not lot_image:
        raise NotFoundException(detail=f"صورة اللوت بمعرف {lot_image_id} غير موجودة.")
    return lot_image

def get_all_lot_images_for_lot(db: Session, lot_id: UUID) -> List[models_auction.LotImage]:
    """
    خدمة لجلب جميع صور اللوت للوت مزاد معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_id (UUID): معرف اللوت الأم.

    Returns:
        List[models_auction.LotImage]: قائمة بكائنات صور اللوت.
    """
    # التحقق من وجود اللوت الأم (اختياري هنا)
    # get_auction_lot_details(db, lot_id)
    return auctions_crud.get_all_lot_images_for_lot(db, lot_id=lot_id)

def update_lot_image(db: Session, lot_image_id: int, lot_image_in: schemas.LotImageUpdate, current_user: User) -> models_auction.LotImage:
    """
    خدمة لتحديث سجل صورة لوت موجود.
    تتضمن التحقق من ملكية البائع.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_image_id (int): معرف صورة اللوت المراد تحديثه.
        lot_image_in (schemas.LotImageUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_auction.LotImage: كائن صورة اللوت المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على صورة اللوت.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
    """
    db_lot_image = get_lot_image_details(db, lot_image_id)

    # التحقق من ملكية البائع للمزاد الأم
    db_lot = get_auction_lot_details(db, db_lot_image.lot_id)
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بتحديث صورة اللوت هذه.")

    return auctions_crud.update_lot_image(db=db, db_lot_image=db_lot_image, lot_image_in=lot_image_in)

def delete_lot_image(db: Session, lot_image_id: int, current_user: User):
    """
    خدمة لحذف سجل صورة لوت معين (حذف صارم).
    تتضمن التحقق من ملكية البائع.

    Args:
        db (Session): جلسة قاعدة البيانات.
        lot_image_id (int): معرف صورة اللوت المراد حذفها.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على صورة اللوت.
        ForbiddenException: إذا لم يكن المستخدم يملك المزاد الأم أو غير مصرح له.
    """
    db_lot_image = get_lot_image_details(db, lot_image_id)

    # التحقق من ملكية البائع للمزاد الأم
    db_lot = get_auction_lot_details(db, db_lot_image.lot_id)
    db_auction = get_auction_details(db, db_lot.auction_id)
    if db_auction.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_AUCTION_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بحذف صورة اللوت هذه.")

    auctions_crud.delete_lot_image(db=db, db_lot_image=db_lot_image)
    # TODO: هنا يجب إضافة منطق لحذف الملف الفعلي للصورة من خدمة التخزين السحابي (مثل AWS S3)
    #       (ImageService.delete_image_file_by_id أو ما شابه)
    return {"message": "تم حذف صورة اللوت بنجاح."}