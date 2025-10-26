# backend\src\market\crud\quotes_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز من Market
from src.market.models import quotes_models as models_market # Quote, QuoteItem
# استيراد المودلز من Lookups (لجداول الحالات والترجمات)
from src.lookups.models import QuoteStatus, QuoteStatusTranslation # <-- من lookups.models.py
# استيراد الـ Schemas
from src.market.schemas import quote_schemas as schemas
from src.lookups.schemas import lookups_schemas as schemas_lookups


# ==========================================================
# --- CRUD Functions for Quote (عروض الأسعار) ---
# ==========================================================

def create_quote(db: Session, quote_in: schemas.QuoteCreate, seller_user_id: UUID, initial_status_id: int) -> models_market.Quote:
    """
    ينشئ سجلاً جديداً لعرض السعر في قاعدة البيانات، بما في ذلك بنوده المضمنة.
    تتم الحسابات المالية وتعيين المعرفات الأولية بواسطة طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_in (schemas.QuoteCreate): بيانات عرض السعر للإنشاء، بما في ذلك قائمة بنود العرض.
        seller_user_id (UUID): معرف البائع مقدم العرض.
        initial_status_id (int): معرف الحالة الأولية لعرض السعر (يُحدد في الخدمة).

    Returns:
        models_market.Quote: كائن عرض السعر الذي تم إنشاؤه.
    """
    db_quote = models_market.Quote(
        rfq_id=quote_in.rfq_id,
        seller_user_id=seller_user_id,
        submission_timestamp=quote_in.submission_timestamp,
        total_quote_amount=quote_in.total_quote_amount,
        payment_terms_key=quote_in.payment_terms_key,
        delivery_terms_key=quote_in.delivery_terms_key,
        validity_period_days=quote_in.validity_period_days,
        expiry_timestamp=quote_in.expiry_timestamp,
        quote_status_id=initial_status_id,
        seller_notes=quote_in.seller_notes
    )
    db.add(db_quote)
    db.flush() # للحصول على quote_id قبل حفظ البنود

    if quote_in.items:
        for item_in in quote_in.items:
            db_item = models_market.QuoteItem(
                quote_id=db_quote.quote_id,
                rfq_item_id=item_in.rfq_item_id,
                offered_product_description=item_in.offered_product_description,
                offered_quantity=item_in.offered_quantity,
                unit_price_offered=item_in.unit_price_offered,
                total_item_price=item_in.total_item_price,
                item_notes=item_in.item_notes
            )
            db.add(db_item)
            
    db.commit()
    db.refresh(db_quote)
    return db_quote

def get_quote(db: Session, quote_id: int) -> Optional[models_market.Quote]:
    """
    يجلب سجل عرض سعر واحد بالـ ID الخاص به، بما في ذلك بنوده والكائنات المرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_id (int): معرف عرض السعر المطلوب.

    Returns:
        Optional[models_market.Quote]: كائن عرض السعر أو None إذا لم يتم العثور عليه.
    """
    return db.query(models_market.Quote).options(
        joinedload(models_market.Quote.items), # بنود عرض السعر
        joinedload(models_market.Quote.rfq), # طلب عرض الأسعار المرتبط
        joinedload(models_market.Quote.seller), # البائع مقدم العرض
        joinedload(models_market.Quote.quote_status) # حالة عرض السعر
    ).filter(models_market.Quote.quote_id == quote_id).first()

def get_all_quotes(db: Session, rfq_id: Optional[int] = None, seller_user_id: Optional[UUID] = None, quote_status_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models_market.Quote]:
    """
    يجلب قائمة بجميع عروض الأسعار، مع خيارات للتصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_id (Optional[int]): تصفية حسب معرف طلب عرض الأسعار (RFQ).
        seller_user_id (Optional[UUID]): تصفية حسب معرف البائع مقدم العرض.
        quote_status_id (Optional[int]): تصفية حسب معرف حالة عرض السعر.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models_market.Quote]: قائمة بكائنات عروض الأسعار.
    """
    query = db.query(models_market.Quote).options(
        joinedload(models_market.Quote.rfq),
        joinedload(models_market.Quote.seller),
        joinedload(models_market.Quote.quote_status)
    )
    if rfq_id:
        query = query.filter(models_market.Quote.rfq_id == rfq_id)
    if seller_user_id:
        query = query.filter(models_market.Quote.seller_user_id == seller_user_id)
    if quote_status_id:
        query = query.filter(models_market.Quote.quote_status_id == quote_status_id)
    
    return query.offset(skip).limit(limit).all()

def update_quote(db: Session, db_quote: models_market.Quote, quote_in: schemas.QuoteUpdate) -> models_market.Quote:
    """
    يحدث بيانات سجل عرض سعر موجود.
    لا يقوم بتحديث بنود عرض السعر مباشرة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_quote (models_market.Quote): كائن عرض السعر من قاعدة البيانات المراد تحديثه.
        quote_in (schemas.QuoteUpdate): البيانات المراد تحديثها.

    Returns:
        models_market.Quote: كائن عرض السعر المحدث.
    """
    update_data = quote_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_quote, key, value)
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote

def update_quote_status(db: Session, db_quote: models_market.Quote, new_status_id: int) -> models_market.Quote:
    """
    يحدث حالة عرض السعر.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_quote (models_market.Quote): كائن عرض السعر من قاعدة البيانات.
        new_status_id (int): معرف الحالة الجديدة لعرض السعر.

    Returns:
        models_market.Quote: كائن عرض السعر بعد تحديث حالته.
    """
    db_quote.quote_status_id = new_status_id
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote

# لا يوجد delete_quote مباشر، يتم إدارة الحالة عبر تحديث quote_status_id


# ==========================================================
# --- CRUD Functions for QuoteItem (بنود عرض السعر) ---
# ==========================================================

def create_quote_item(db: Session, item_in: schemas.QuoteItemCreate, quote_id: int) -> models_market.QuoteItem:
    """
    ينشئ بند عرض سعر (Quote Item) جديد في قاعدة البيانات.
    عادةً ما يتم استدعاؤه كجزء من عملية إنشاء عرض السعر الأب.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_in (schemas.QuoteItemCreate): بيانات بند العرض للإنشاء.
        quote_id (int): معرف عرض السعر الأب الذي ينتمي إليه هذا البند.

    Returns:
        models_market.QuoteItem: كائن بند العرض الذي تم إنشاؤه.
    """
    db_item = models_market.QuoteItem(
        quote_id=quote_id,
        rfq_item_id=item_in.rfq_item_id,
        offered_product_description=item_in.offered_product_description,
        offered_quantity=item_in.offered_quantity,
        unit_price_offered=item_in.unit_price_offered,
        total_item_price=item_in.total_item_price,
        item_notes=item_in.item_notes
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_quote_item(db: Session, quote_item_id: int) -> Optional[models_market.QuoteItem]:
    """
    يجلب بند عرض سعر واحد بالـ ID الخاص به، مع الكائنات المرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_item_id (int): معرف بند العرض المطلوب.

    Returns:
        Optional[models_market.QuoteItem]: كائن بند العرض أو None.
    """
    return db.query(models_market.QuoteItem).options(
        joinedload(models_market.QuoteItem.rfq_item) # بند طلب RFQ المرتبط
    ).filter(models_market.QuoteItem.quote_item_id == quote_item_id).first()

def get_quote_items_for_quote(db: Session, quote_id: int) -> List[models_market.QuoteItem]:
    """
    يجلب جميع بنود عرض السعر لعرض سعر معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_id (int): معرف عرض السعر الأب.

    Returns:
        List[models_market.QuoteItem]: قائمة بكائنات بنود العرض.
    """
    return db.query(models_market.QuoteItem).filter(models_market.QuoteItem.quote_id == quote_id).all()

def update_quote_item(db: Session, db_quote_item: models_market.QuoteItem, item_in: schemas.QuoteItemUpdate) -> models_market.QuoteItem:
    """
    يحدث بيانات بند عرض سعر موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_quote_item (models_market.QuoteItem): كائن بند العرض من قاعدة البيانات المراد تحديثه.
        item_in (schemas.QuoteItemUpdate): البيانات المراد تحديثها.

    Returns:
        models_market.QuoteItem: كائن بند العرض المحدث.
    """
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_quote_item, key, value)
    db.add(db_quote_item)
    db.commit()
    db.refresh(db_quote_item)
    return db_quote_item

# لا يوجد delete_quote_item مباشر، يتم إدارة الحذف عبر عرض السعر الأب.


# ==========================================================
# --- CRUD Functions for QuoteStatus (حالات عرض السعر) ---
#    (تُستورد من src.lookups.models)
# ==========================================================

def create_quote_status(db: Session, status_in: schemas_lookups.QuoteStatusCreate) -> QuoteStatus:
    """
    ينشئ حالة عرض سعر جديدة في قاعدة البيانات، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas.QuoteStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        QuoteStatus: كائن الحالة الذي تم إنشاؤه.
    """
    db_status = QuoteStatus(
        status_name_key=status_in.status_name_key,
        status_description_key=status_in.status_description_key # Assuming it exists in lookups/models
    )
    db.add(db_status)
    db.flush()

    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = QuoteStatusTranslation(
                quote_status_id=db_status.quote_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name,
                translated_description=trans_in.translated_description # Assuming it exists in lookups/models
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_quote_status(db: Session, quote_status_id: int) -> Optional[QuoteStatus]:
    """
    يجلب حالة عرض سعر واحدة بالـ ID الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة المطلوب.

    Returns:
        Optional[QuoteStatus]: كائن الحالة أو None.
    """
    return db.query(QuoteStatus).options(
        joinedload(QuoteStatus.translations)
    ).filter(QuoteStatus.quote_status_id == quote_status_id).first()

def get_all_quote_statuses(db: Session) -> List[QuoteStatus]:
    """
    يجلب قائمة بجميع حالات عرض السعر.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[QuoteStatus]: قائمة بكائنات الحالات.
    """
    return db.query(QuoteStatus).options(
        joinedload(QuoteStatus.translations)
    ).all()

def update_quote_status_crud(db: Session, db_status: QuoteStatus, status_in: schemas_lookups.QuoteStatusUpdate) -> QuoteStatus:
    """
    يحدث بيانات حالة عرض سعر موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (QuoteStatus): كائن الحالة من قاعدة البيانات.
        status_in (schemas.QuoteStatusUpdate): البيانات المراد تحديثها.

    Returns:
        QuoteStatus: كائن الحالة المحدث.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_quote_status(db: Session, db_status: QuoteStatus):
    """
    يحذف حالة عرض سعر معينة (حذف صارم).
    TODO: التحقق من عدم وجود عروض أسعار مرتبطة بهذه الحالة سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (QuoteStatus): كائن الحالة من قاعدة البيانات.
    """
    db.delete(db_status)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for QuoteStatusTranslation (ترجمات حالات عرض السعر) ---
# ==========================================================

def create_quote_status_translation(db: Session, quote_status_id: int, trans_in: schemas_lookups.QuoteStatusTranslationCreate) -> QuoteStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة عرض سعر معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة الأم.
        trans_in (schemas.QuoteStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        QuoteStatusTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = QuoteStatusTranslation(
        quote_status_id=quote_status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_description=trans_in.translated_description # Assuming it exists in lookups/models
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_quote_status_translation(db: Session, quote_status_id: int, language_code: str) -> Optional[QuoteStatusTranslation]:
    """
    يجلب ترجمة حالة عرض سعر محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة.
        language_code (str): رمز اللغة.

    Returns:
        Optional[QuoteStatusTranslation]: كائن الترجمة أو None.
    """
    return db.query(QuoteStatusTranslation).filter(
        and_(
            QuoteStatusTranslation.quote_status_id == quote_status_id,
            QuoteStatusTranslation.language_code == language_code
        )
    ).first()

def update_quote_status_translation(db: Session, db_translation: QuoteStatusTranslation, trans_in: schemas_lookups.QuoteStatusTranslationUpdate) -> QuoteStatusTranslation:
    """
    يحدث ترجمة حالة عرض سعر موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (QuoteStatusTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.QuoteStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        QuoteStatusTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_quote_status_translation(db: Session, db_translation: QuoteStatusTranslation):
    """
    يحذف ترجمة حالة عرض سعر معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (QuoteStatusTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return
    