# backend\src\market\crud\shipments_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

# استيراد المودلز من Market
from src.market.models import shipments_models as models_market # Shipment, ShipmentItem
# استيراد المودلز من Lookups (لجداول الحالات والترجمات)
from src.lookups.models import ShipmentStatus, ShipmentStatusTranslation # <-- من lookups.models.py
# استيراد الـ Schemas
from src.market.schemas import shipment_schemas as schemas
from src.lookups.schemas import lookups_schemas as schemas_lookups


# ==========================================================
# --- CRUD Functions for Shipment (الشحنات) ---
# ==========================================================

def create_shipment(db: Session, shipment_in: schemas.ShipmentCreate, shipment_reference_number: str, initial_status_id: int) -> models_market.Shipment:
    """
    ينشئ سجلاً جديداً للشحنة في قاعدة البيانات، بما في ذلك بنودها المضمنة (Shipment Items).
    تتم الحسابات المالية وتعيين المعرفات الأولية بواسطة طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_in (schemas.ShipmentCreate): بيانات الشحنة للإنشاء، بما في ذلك قائمة بنود الشحنة.
        shipment_reference_number (str): رقم مرجعي فريد للشحنة (يُنشأ في الخدمة).
        initial_status_id (int): معرف الحالة الأولية للشحنة (يُحدد في الخدمة).

    Returns:
        models_market.Shipment: كائن الشحنة الذي تم إنشاؤه.
    """
    db_shipment = models_market.Shipment(
        order_id=shipment_in.order_id,
        shipment_reference_number=shipment_reference_number,
        shipping_carrier_name=shipment_in.shipping_carrier_name,
        tracking_number=shipment_in.tracking_number,
        shipment_status_id=initial_status_id,
        estimated_shipping_date=shipment_in.estimated_shipping_date,
        actual_shipping_date=shipment_in.actual_shipping_date,
        estimated_delivery_date=shipment_in.estimated_delivery_date,
        actual_delivery_date=shipment_in.actual_delivery_date,
        shipping_address_id=shipment_in.shipping_address_id,
        shipping_cost=shipment_in.shipping_cost,
        shipping_notes=shipment_in.shipping_notes,
        shipped_by_user_id=shipment_in.shipped_by_user_id
    )
    db.add(db_shipment)
    db.flush() # للحصول على shipment_id قبل حفظ البنود

    if shipment_in.items:
        for item_in in shipment_in.items:
            db_item = models_market.ShipmentItem(
                shipment_id=db_shipment.shipment_id,
                order_item_id=item_in.order_item_id,
                quantity_shipped=item_in.shipped_quantity,
                item_notes=item_in.item_notes
            )
            db.add(db_item)
            
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def get_shipment(db: Session, shipment_id: int) -> Optional[models_market.Shipment]:
    """
    يجلب سجل شحنة واحد بالـ ID الخاص به، بما في ذلك بنوده والكائنات المرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_id (int): معرف الشحنة المطلوب.

    Returns:
        Optional[models_market.Shipment]: كائن الشحنة أو None إذا لم يتم العثور عليها.
    """
    return db.query(models_market.Shipment).options(
        joinedload(models_market.Shipment.items), # بنود الشحنة
        joinedload(models_market.Shipment.order), # الطلب المرتبط
        joinedload(models_market.Shipment.shipment_status), # حالة الشحنة
        joinedload(models_market.Shipment.shipping_address), # عنوان الشحن
        joinedload(models_market.Shipment.shipped_by_user) # المستخدم الذي قام بالشحن
    ).filter(models_market.Shipment.shipment_id == shipment_id).first()

def get_all_shipments(db: Session, order_id: Optional[UUID] = None, shipment_status_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models_market.Shipment]:
    """
    يجلب قائمة بجميع الشحنات، مع خيارات للتصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_id (Optional[UUID]): تصفية حسب معرف الطلب.
        shipment_status_id (Optional[int]): تصفية حسب معرف حالة الشحنة.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models_market.Shipment]: قائمة بكائنات الشحنات.
    """
    query = db.query(models_market.Shipment).options(
        joinedload(models_market.Shipment.order),
        joinedload(models_market.Shipment.shipment_status)
    )
    if order_id:
        query = query.filter(models_market.Shipment.order_id == order_id)
    if shipment_status_id:
        query = query.filter(models_market.Shipment.shipment_status_id == shipment_status_id)
    
    return query.offset(skip).limit(limit).all()

def update_shipment(db: Session, db_shipment: models_market.Shipment, shipment_in: schemas.ShipmentUpdate) -> models_market.Shipment:
    """
    يحدث بيانات سجل شحنة موجود.
    لا يقوم بتحديث بنود الشحنة مباشرة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_shipment (models_market.Shipment): كائن الشحنة من قاعدة البيانات المراد تحديثه.
        shipment_in (schemas.ShipmentUpdate): البيانات المراد تحديثها.

    Returns:
        models_market.Shipment: كائن الشحنة المحدث.
    """
    update_data = shipment_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_shipment, key, value)
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def update_shipment_status(db: Session, db_shipment: models_market.Shipment, new_status_id: int) -> models_market.Shipment:
    """
    يحدث حالة الشحنة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_shipment (models_market.Shipment): كائن الشحنة من قاعدة البيانات.
        new_status_id (int): معرف الحالة الجديدة للشحنة.

    Returns:
        models_market.Shipment: كائن الشحنة بعد تحديث حالته.
    """
    db_shipment.shipment_status_id = new_status_id
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

# لا يوجد delete_shipment مباشر، يتم إدارة الحالة عبر تحديث shipment_status_id


# ==========================================================
# --- CRUD Functions for ShipmentItem (بنود الشحنة) ---
# ==========================================================

def create_shipment_item(db: Session, item_in: schemas.ShipmentItemCreate, shipment_id: int) -> models_market.ShipmentItem:
    """
    ينشئ بند شحنة جديد في قاعدة البيانات.
    عادةً ما يتم استدعاؤه كجزء من عملية إنشاء الشحنة الأب.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_in (schemas.ShipmentItemCreate): بيانات بند الشحنة للإنشاء.
        shipment_id (int): معرف الشحنة الأب الذي ينتمي إليه هذا البند.

    Returns:
        models_market.ShipmentItem: كائن بند الشحنة الذي تم إنشاؤه.
    """
    db_item = models_market.ShipmentItem(
        shipment_id=shipment_id,
        order_item_id=item_in.order_item_id,
        quantity_shipped=item_in.shipped_quantity,
        item_notes=item_in.item_notes
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_shipment_item(db: Session, shipment_item_id: int) -> Optional[models_market.ShipmentItem]:
    """
    يجلب بند شحنة واحد بالـ ID الخاص به، مع الكائنات المرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_item_id (int): معرف بند الشحنة المطلوب.

    Returns:
        Optional[models_market.ShipmentItem]: كائن بند الشحنة أو None.
    """
    return db.query(models_market.ShipmentItem).options(
        joinedload(models_market.ShipmentItem.order_item) # بند الطلب المرتبط
    ).filter(models_market.ShipmentItem.shipment_item_id == shipment_item_id).first()

def get_shipment_items_for_shipment(db: Session, shipment_id: int) -> List[models_market.ShipmentItem]:
    """
    يجلب جميع بنود الشحنة لشحنة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_id (int): معرف الشحنة الأب.

    Returns:
        List[models_market.ShipmentItem]: قائمة بكائنات بنود الشحنة.
    """
    return db.query(models_market.ShipmentItem).filter(models_market.ShipmentItem.shipment_id == shipment_id).all()

def update_shipment_item(db: Session, db_shipment_item: models_market.ShipmentItem, item_in: schemas.ShipmentItemUpdate) -> models_market.ShipmentItem:
    """
    يحدث بيانات بند شحنة موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_shipment_item (models_market.ShipmentItem): كائن بند الشحنة من قاعدة البيانات المراد تحديثه.
        item_in (schemas.ShipmentItemUpdate): البيانات المراد تحديثها.

    Returns:
        models_market.ShipmentItem: كائن بند الشحنة المحدث.
    """
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_shipment_item, key, value)
    db.add(db_shipment_item)
    db.commit()
    db.refresh(db_shipment_item)
    return db_shipment_item

# لا يوجد delete_shipment_item مباشر، يتم إدارة الحذف عبر الشحنة الأب.


# ==========================================================
# --- CRUD Functions for ShipmentStatus (حالات الشحن) ---
#    (تُستورد من src.lookups.models)
# ==========================================================

def create_shipment_status(db: Session, status_in: schemas_lookups.ShipmentStatusCreate) -> ShipmentStatus:
    """
    ينشئ حالة شحن جديدة في قاعدة البيانات، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas.ShipmentStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        ShipmentStatus: كائن الحالة الذي تم إنشاؤه.
    """
    db_status = ShipmentStatus(
        status_name_key=status_in.status_name_key,
        status_description_key=status_in.status_description_key # assuming it exists in lookups/models
    )
    db.add(db_status)
    db.flush()

    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = ShipmentStatusTranslation(
                shipment_status_id=db_status.shipment_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name,
                translated_description=trans_in.translated_description # assuming it exists in lookups/models
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_shipment_status(db: Session, shipment_status_id: int) -> Optional[ShipmentStatus]:
    """
    يجلب حالة شحن واحدة بالـ ID الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة المطلوب.

    Returns:
        Optional[ShipmentStatus]: كائن الحالة أو None.
    """
    return db.query(ShipmentStatus).options(
        joinedload(ShipmentStatus.translations)
    ).filter(ShipmentStatus.shipment_status_id == shipment_status_id).first()

def get_all_shipment_statuses(db: Session) -> List[ShipmentStatus]:
    """
    يجلب قائمة بجميع حالات الشحن.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[ShipmentStatus]: قائمة بكائنات الحالات.
    """
    return db.query(ShipmentStatus).options(
        joinedload(ShipmentStatus.translations)
    ).all()

def update_shipment_status_crud(db: Session, db_status: ShipmentStatus, status_in: schemas_lookups.ShipmentStatusUpdate) -> ShipmentStatus:
    """
    يحدث بيانات حالة شحن موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (ShipmentStatus): كائن الحالة من قاعدة البيانات.
        status_in (schemas.ShipmentStatusUpdate): البيانات المراد تحديثها.

    Returns:
        ShipmentStatus: كائن الحالة المحدث.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_shipment_status(db: Session, db_status: ShipmentStatus):
    """
    يحذف حالة شحن معينة (حذف صارم).
    TODO: التحقق من عدم وجود شحنات مرتبطة بهذه الحالة سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (ShipmentStatus): كائن الحالة من قاعدة البيانات.
    """
    db.delete(db_status)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for ShipmentStatusTranslation (ترجمات حالات الشحن) ---
# ==========================================================

def create_shipment_status_translation(db: Session, shipment_status_id: int, trans_in: schemas_lookups.ShipmentStatusTranslationCreate) -> ShipmentStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة شحن معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة الأم.
        trans_in (schemas.ShipmentStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        ShipmentStatusTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = ShipmentStatusTranslation(
        shipment_status_id=shipment_status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_description=trans_in.translated_description # assuming it exists in lookups/models
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_shipment_status_translation(db: Session, shipment_status_id: int, language_code: str) -> Optional[ShipmentStatusTranslation]:
    """
    يجلب ترجمة حالة شحن محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة.
        language_code (str): رمز اللغة.

    Returns:
        Optional[ShipmentStatusTranslation]: كائن الترجمة أو None.
    """
    return db.query(ShipmentStatusTranslation).filter(
        and_(
            ShipmentStatusTranslation.shipment_status_id == shipment_status_id,
            ShipmentStatusTranslation.language_code == language_code
        )
    ).first()

def update_shipment_status_translation(db: Session, db_translation: ShipmentStatusTranslation, trans_in: schemas_lookups.ShipmentStatusTranslationUpdate) -> ShipmentStatusTranslation:
    """
    يحدث ترجمة حالة شحن موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (ShipmentStatusTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.ShipmentStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        ShipmentStatusTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_shipment_status_translation(db: Session, db_translation: ShipmentStatusTranslation):
    """
    يحذف ترجمة حالة شحن معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (ShipmentStatusTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return