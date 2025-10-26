# backend\src\market\crud\rfqs_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز من Market
from src.market.models import rfqs_models as models_market # Rfq, RfqItem
# استيراد المودلز من Lookups (لجداول الحالات والترجمات)
from src.lookups.models import RfqStatus, RfqStatusTranslation # <-- من lookups.models.py
# استيراد الـ Schemas
from src.market.schemas import rfq_schemas as schemas
from src.lookups.schemas import lookups_schemas as schemas_lookups


# ==========================================================
# --- CRUD Functions for Rfq (طلبات عروض الأسعار) ---
# ==========================================================

def create_rfq(db: Session, rfq_in: schemas.RfqCreate, buyer_user_id: UUID, rfq_reference_number: Optional[str], initial_status_id: int) -> models_market.Rfq:
    """
    ينشئ سجلاً جديداً لطلب عرض أسعار (RFQ) في قاعدة البيانات، بما في ذلك بنوده المضمنة.
    تتم الحسابات المالية وتعيين المعرفات الأولية بواسطة طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_in (schemas.RfqCreate): بيانات الـ RFQ للإنشاء، بما في ذلك قائمة بنود الـ RFQ.
        buyer_user_id (UUID): معرف المشتري.
        rfq_reference_number (Optional[str]): رقم مرجعي فريد للـ RFQ (يُنشأ في الخدمة).
        initial_status_id (int): معرف الحالة الأولية للـ RFQ (يُحدد في الخدمة).

    Returns:
        models_market.Rfq: كائن الـ RFQ الذي تم إنشاؤه.
    """
    db_rfq = models_market.Rfq(
        buyer_user_id=buyer_user_id,
        rfq_reference_number=rfq_reference_number,
        title=rfq_in.title,
        description=rfq_in.description,
        submission_deadline=rfq_in.submission_deadline,
        delivery_deadline=rfq_in.delivery_deadline,
        delivery_address_id=rfq_in.delivery_address_id,
        payment_terms_preference=rfq_in.payment_terms_preference,
        rfq_status_id=initial_status_id
    )
    db.add(db_rfq)
    db.flush() # للحصول على rfq_id قبل حفظ البنود

    if rfq_in.items:
        for item_in in rfq_in.items:
            db_item = models_market.RfqItem(
                rfq_id=db_rfq.rfq_id,
                product_id=item_in.product_id,
                custom_product_description=item_in.custom_product_description,
                quantity_requested=item_in.quantity_requested,
                unit_of_measure_id=item_in.unit_of_measure_id,
                required_specifications=item_in.required_specifications,
                target_price_per_unit=item_in.target_price_per_unit,
                notes=item_in.notes
            )
            db.add(db_item)
            
    db.commit()
    db.refresh(db_rfq)
    return db_rfq

def get_rfq(db: Session, rfq_id: int) -> Optional[models_market.Rfq]:
    """
    يجلب سجل طلب عرض أسعار (RFQ) واحد بالـ ID الخاص به، بما في ذلك بنوده والكائنات المرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_id (int): معرف الـ RFQ المطلوب.

    Returns:
        Optional[models_market.Rfq]: كائن الـ RFQ أو None إذا لم يتم العثور عليه.
    """
    return db.query(models_market.Rfq).options(
        joinedload(models_market.Rfq.items), # بنود الـ RFQ
        joinedload(models_market.Rfq.buyer), # المشتري
        joinedload(models_market.Rfq.delivery_address), # عنوان التسليم
        joinedload(models_market.Rfq.rfq_status), # حالة الـ RFQ
        joinedload(models_market.Rfq.quotes) # عروض الأسعار المرتبطة
    ).filter(models_market.Rfq.rfq_id == rfq_id).first()

def get_all_rfqs(db: Session, buyer_user_id: Optional[UUID] = None, rfq_status_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models_market.Rfq]:
    """
    يجلب قائمة بجميع طلبات عروض الأسعار (RFQs)، مع خيارات للتصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        buyer_user_id (Optional[UUID]): تصفية حسب معرف المشتري.
        rfq_status_id (Optional[int]): تصفية حسب معرف حالة الـ RFQ.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models_market.Rfq]: قائمة بكائنات الـ RFQs.
    """
    query = db.query(models_market.Rfq).options(
        joinedload(models_market.Rfq.buyer),
        joinedload(models_market.Rfq.rfq_status)
    )
    if buyer_user_id:
        query = query.filter(models_market.Rfq.buyer_user_id == buyer_user_id)
    if rfq_status_id:
        query = query.filter(models_market.Rfq.rfq_status_id == rfq_status_id)
    
    return query.offset(skip).limit(limit).all()

def update_rfq(db: Session, db_rfq: models_market.Rfq, rfq_in: schemas.RfqUpdate) -> models_market.Rfq:
    """
    يحدث بيانات سجل طلب عرض أسعار (RFQ) موجود.
    لا يقوم بتحديث بنود الـ RFQ مباشرة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_rfq (models_market.Rfq): كائن الـ RFQ من قاعدة البيانات المراد تحديثه.
        rfq_in (schemas.RfqUpdate): البيانات المراد تحديثها.

    Returns:
        models_market.Rfq: كائن الـ RFQ المحدث.
    """
    update_data = rfq_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rfq, key, value)
    db.add(db_rfq)
    db.commit()
    db.refresh(db_rfq)
    return db_rfq

def update_rfq_status(db: Session, db_rfq: models_market.Rfq, new_status_id: int) -> models_market.Rfq:
    """
    يحدث حالة طلب عرض أسعار (RFQ).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_rfq (models_market.Rfq): كائن الـ RFQ من قاعدة البيانات.
        new_status_id (int): معرف الحالة الجديدة للـ RFQ.

    Returns:
        models_market.Rfq: كائن الـ RFQ بعد تحديث حالته.
    """
    db_rfq.rfq_status_id = new_status_id
    db.add(db_rfq)
    db.commit()
    db.refresh(db_rfq)
    return db_rfq

# لا يوجد delete_rfq مباشر، يتم إدارة الحالة عبر تحديث rfq_status_id


# ==========================================================
# --- CRUD Functions for RfqItem (بنود طلب عرض الأسعار) ---
# ==========================================================

def create_rfq_item(db: Session, item_in: schemas.RfqItemCreate, rfq_id: int) -> models_market.RfqItem:
    """
    ينشئ بند طلب عرض أسعار (RFQ Item) جديد في قاعدة البيانات.
    عادةً ما يتم استدعاؤه كجزء من عملية إنشاء الـ RFQ الأب.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_in (schemas.RfqItemCreate): بيانات بند الـ RFQ للإنشاء.
        rfq_id (int): معرف الـ RFQ الأب الذي ينتمي إليه هذا البند.

    Returns:
        models_market.RfqItem: كائن بند الـ RFQ الذي تم إنشاؤه.
    """
    db_item = models_market.RfqItem(
        rfq_id=rfq_id,
        product_id=item_in.product_id,
        custom_product_description=item_in.custom_product_description,
        quantity_requested=item_in.quantity_requested,
        unit_of_measure_id=item_in.unit_of_measure_id,
        required_specifications=item_in.required_specifications,
        target_price_per_unit=item_in.target_price_per_unit,
        notes=item_in.notes
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_rfq_item(db: Session, rfq_item_id: int) -> Optional[models_market.RfqItem]:
    """
    يجلب بند طلب عرض أسعار (RFQ Item) واحد بالـ ID الخاص به، مع الكائنات المرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_item_id (int): معرف بند الـ RFQ المطلوب.

    Returns:
        Optional[models_market.RfqItem]: كائن بند الـ RFQ أو None إذا لم يتم العثور عليه.
    """
    return db.query(models_market.RfqItem).options(
        joinedload(models_market.RfqItem.product),
        joinedload(models_market.RfqItem.unit_of_measure)
    ).filter(models_market.RfqItem.rfq_item_id == rfq_item_id).first()

def get_rfq_items_for_rfq(db: Session, rfq_id: int) -> List[models_market.RfqItem]:
    """
    يجلب جميع بنود طلب عرض أسعار (RFQ) لـ RFQ معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_id (int): معرف الـ RFQ الأب.

    Returns:
        List[models_market.RfqItem]: قائمة بكائنات بنود الـ RFQ.
    """
    return db.query(models_market.RfqItem).filter(models_market.RfqItem.rfq_id == rfq_id).all()

def update_rfq_item(db: Session, db_rfq_item: models_market.RfqItem, item_in: schemas.RfqItemUpdate) -> models_market.RfqItem:
    """
    يحدث بيانات بند طلب عرض أسعار (RFQ Item) موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_rfq_item (models_market.RfqItem): كائن بند الـ RFQ من قاعدة البيانات المراد تحديثه.
        item_in (schemas.RfqItemUpdate): البيانات المراد تحديثها.

    Returns:
        models_market.RfqItem: كائن بند الـ RFQ المحدث.
    """
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rfq_item, key, value)
    db.add(db_rfq_item)
    db.commit()
    db.refresh(db_rfq_item)
    return db_rfq_item

# لا يوجد delete_rfq_item مباشر، يتم إدارة الحذف عبر الـ RFQ الأب.


# ==========================================================
# --- CRUD Functions for RfqStatus (حالات طلب عرض الأسعار) ---
#    (تُستورد من src.lookups.models)
# ==========================================================

def create_rfq_status(db: Session, status_in: schemas_lookups.RfqStatusCreate) -> RfqStatus:
    """
    ينشئ حالة طلب عرض أسعار (RFQ Status) جديدة في قاعدة البيانات، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas_lookups.RfqStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        RfqStatus: كائن الحالة الذي تم إنشاؤه.
    """
    db_status = RfqStatus(status_name_key=status_in.status_name_key)
    db.add(db_status)
    db.flush()

    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = RfqStatusTranslation(
                rfq_status_id=db_status.rfq_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_rfq_status(db: Session, rfq_status_id: int) -> Optional[RfqStatus]:
    """
    يجلب حالة طلب عرض أسعار (RFQ Status) واحدة بالـ ID الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة المطلوب.

    Returns:
        Optional[RfqStatus]: كائن الحالة أو None.
    """
    return db.query(RfqStatus).options(
        joinedload(RfqStatus.translations)
    ).filter(RfqStatus.rfq_status_id == rfq_status_id).first()

def get_all_rfq_statuses(db: Session) -> List[RfqStatus]:
    """
    يجلب قائمة بجميع حالات طلبات عروض الأسعار (RFQ Statuses).

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[RfqStatus]: قائمة بكائنات الحالات.
    """
    return db.query(RfqStatus).options(
        joinedload(RfqStatus.translations)
    ).all()

def update_rfq_status_crud(db: Session, db_status: RfqStatus, status_in: schemas_lookups.RfqStatusUpdate) -> RfqStatus:
    """
    يحدث بيانات حالة طلب عرض أسعار (RFQ Status) موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (RfqStatus): كائن الحالة من قاعدة البيانات.
        status_in (schemas_lookups.RfqStatusUpdate): البيانات المراد تحديثها.

    Returns:
        RfqStatus: كائن الحالة المحدث.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_rfq_status(db: Session, db_status: RfqStatus):
    """
    يحذف حالة طلب عرض أسعار (RFQ Status) معينة (حذف صارم).
    TODO: التحقق من عدم وجود RFQs مرتبطة بهذه الحالة سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (RfqStatus): كائن الحالة من قاعدة البيانات.
    """
    db.delete(db_status)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for RfqStatusTranslation (ترجمات حالات طلب عرض الأسعار) ---
# ==========================================================

def create_rfq_status_translation(db: Session, rfq_status_id: int, trans_in: schemas_lookups.RfqStatusTranslationCreate) -> RfqStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة طلب عرض أسعار (RFQ Status) معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة الأم.
        trans_in (schemas_lookups.RfqStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        RfqStatusTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = RfqStatusTranslation(
        rfq_status_id=rfq_status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_rfq_status_translation(db: Session, rfq_status_id: int, language_code: str) -> Optional[RfqStatusTranslation]:
    """
    يجلب ترجمة حالة طلب عرض أسعار (RFQ Status) محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة.
        language_code (str): رمز اللغة.

    Returns:
        Optional[RfqStatusTranslation]: كائن الترجمة أو None.
    """
    return db.query(RfqStatusTranslation).filter(
        and_(
            RfqStatusTranslation.rfq_status_id == rfq_status_id,
            RfqStatusTranslation.language_code == language_code
        )
    ).first()

def update_rfq_status_translation(db: Session, db_translation: RfqStatusTranslation, trans_in: schemas_lookups.RfqStatusTranslationUpdate) -> RfqStatusTranslation:
    """
    يحدث ترجمة حالة طلب عرض أسعار (RFQ Status) موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (RfqStatusTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas_lookups.RfqStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        RfqStatusTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_rfq_status_translation(db: Session, db_translation: RfqStatusTranslation):
    """
    يحذف ترجمة حالة طلب عرض أسعار (RFQ Status) معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (RfqStatusTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return
