# backend\src\market\crud\orders_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز من Market
from src.market.models import orders_models as models_market # Order, OrderItem, OrderStatusHistory
# استيراد المودلز من Lookups (لجداول الحالات والترجمات)
from src.lookups.models.lookups_models import ( # <-- تم التعديل هنا: استيراد مباشر من lookups_models.py
    OrderStatus, OrderStatusTranslation,
    PaymentStatus, PaymentStatusTranslation,
    OrderItemStatus, OrderItemStatusTranslation,
    Language # Language for translations if needed by translations crud functions
)
# استيراد الـ Schemas
from src.market.schemas import order_schemas as schemas
# استيراد Schemas للحالات والترجمات من Lookups العامة
from src.lookups.schemas import ( # <-- تم التعديل هنا: استيراد مباشر للـ Schemas من lookups.schemas
    OrderStatusCreate, OrderStatusUpdate,
    OrderStatusTranslationCreate, OrderStatusTranslationUpdate, # تأكد من أن الترتيب صحيح هنا إذا كنت تستورد Base و Create و Update
    PaymentStatusCreate, PaymentStatusUpdate,
    PaymentStatusTranslationCreate, PaymentStatusTranslationUpdate,
    OrderItemStatusCreate, OrderItemStatusUpdate,
    OrderItemStatusTranslationCreate, OrderItemStatusTranslationUpdate,
    LanguageRead # إذا كانت هناك دوال CRUD للترجمة تحتاج LanguageRead
)

# ==========================================================
# --- CRUD Functions for Order (الطلبات) ---
# ==========================================================

def create_order(db: Session, order_in: schemas.OrderCreate, buyer_user_id: UUID, order_reference_number: str, initial_status_id: int, calculated_amounts: dict) -> models_market.Order:
    """
    ينشئ سجلاً جديداً للطلب في قاعدة البيانات، بما في ذلك بنوده المضمنة (Order Items).
    تتم الحسابات المالية وتعيين المعرفات الأولية بواسطة طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_in (schemas.OrderCreate): بيانات الطلب للإنشاء، بما في ذلك قائمة بنود الطلب.
        buyer_user_id (UUID): معرف المشتري.
        order_reference_number (str): رقم مرجعي فريد للطلب (يُنشأ في الخدمة).
        initial_status_id (int): معرف الحالة الأولية للطلب (يُحدد في الخدمة).
        calculated_amounts (dict): قاموس يحتوي على المبالغ المحسوبة (مثل الإجمالي قبل/بعد، VAT، النهائي).

    Returns:
        models_market.Order: كائن الطلب الذي تم إنشاؤه.
    """
    db_order = models_market.Order(
        buyer_user_id=buyer_user_id,
        seller_user_id=order_in.seller_user_id,
        order_reference_number=order_reference_number,
        order_status_id=initial_status_id,
        total_amount_before_discount=calculated_amounts['total_amount_before_discount'],
        discount_amount=calculated_amounts['discount_amount'],
        total_amount_after_discount=calculated_amounts['total_amount_after_discount'],
        vat_amount=calculated_amounts['vat_amount'],
        final_total_amount=calculated_amounts['final_total_amount'],
        currency_code=order_in.currency_code,
        shipping_address_id=order_in.shipping_address_id,
        billing_address_id=order_in.billing_address_id,
        payment_method_id=order_in.payment_method_id,
        payment_status_id=order_in.payment_status_id,
        source_of_order=order_in.source_of_order,
        related_quote_id=order_in.related_quote_id,
        related_auction_settlement_id=order_in.related_auction_settlement_id,
        notes_from_buyer=order_in.notes_from_buyer,
        notes_from_seller=order_in.notes_from_seller
    )
    db.add(db_order)
    db.flush() # للحصول على order_id قبل حفظ البنود وتاريخ الحالة

    if order_in.items:
        for item_in in order_in.items:
            db_item = models_market.OrderItem(
                order_id=db_order.order_id,
                product_packaging_option_id=item_in.product_packaging_option_id,
                seller_user_id=item_in.seller_user_id,
                quantity_ordered=item_in.quantity_ordered,
                unit_price_at_purchase=item_in.unit_price_at_purchase,
                total_price_for_item=item_in.total_price_for_item,
                item_status_id=item_in.item_status_id,
                notes=item_in.notes
            )
            db.add(db_item)
            
    db.commit()
    db.refresh(db_order)
    return db_order

def get_order(db: Session, order_id: UUID) -> Optional[models_market.Order]:
    """
    يجلب سجل طلب واحد بالـ ID الخاص به، بما في ذلك بنوده وتاريخ حالته والكائنات المرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_id (UUID): معرف الطلب المطلوب.

    Returns:
        Optional[models_market.Order]: كائن الطلب أو None إذا لم يتم العثور عليه.
    """
    return db.query(models_market.Order).options(
        joinedload(models_market.Order.items).joinedload(models_market.OrderItem.packaging_option), # بنود الطلب وخيارات التعبئة
        joinedload(models_market.Order.status), # حالة الطلب
        joinedload(models_market.Order.history), # سجل تاريخ الحالة
        joinedload(models_market.Order.buyer), # المشتري
        joinedload(models_market.Order.seller), # البائع
        joinedload(models_market.Order.currency), # العملة
        joinedload(models_market.Order.shipping_address), # عنوان الشحن
        joinedload(models_market.Order.billing_address), # عنوان الفوترة
        joinedload(models_market.Order.payment_status), # حالة الدفع
        joinedload(models_market.Order.related_quote) # عرض السعر المرتبط
        # TODO: joinedload(models_market.Order.related_auction_settlement) # تسوية المزاد المرتبطة
    ).filter(models_market.Order.order_id == order_id).first()

def get_all_orders(db: Session, buyer_user_id: Optional[UUID] = None, seller_user_id: Optional[UUID] = None, order_status_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models_market.Order]:
    """
    يجلب قائمة بجميع الطلبات، مع خيارات للتصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        buyer_user_id (Optional[UUID]): تصفية حسب معرف المشتري.
        seller_user_id (Optional[UUID]): تصفية حسب معرف البائع (للطلبات التي يحدد فيها بائع واحد).
        order_status_id (Optional[int]): تصفية حسب معرف حالة الطلب.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models_market.Order]: قائمة بكائنات الطلبات.
    """
    query = db.query(models_market.Order).options(
        joinedload(models_market.Order.status),
        joinedload(models_market.Order.buyer),
        joinedload(models_market.Order.seller)
    )
    if buyer_user_id:
        query = query.filter(models_market.Order.buyer_user_id == buyer_user_id)
    if seller_user_id:
        # إذا كان الطلب كله لبائع واحد
        query = query.filter(models_market.Order.seller_user_id == seller_user_id)
    if order_status_id:
        query = query.filter(models_market.Order.order_status_id == order_status_id)
        
    # TODO: إذا كان الطلب يمكن أن يكون من بائعين متعددين (null seller_user_id في الطلب الرئيسي)
    #       سنحتاج إلى تصفية بناءً على OrderItem.seller_user_id في Join.

    return query.offset(skip).limit(limit).all()

def update_order(db: Session, db_order: models_market.Order, order_in: schemas.OrderUpdate) -> models_market.Order:
    """
    يحدث بيانات سجل طلب موجود.
    لا يقوم بتحديث بنود الطلب مباشرة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_order (models_market.Order): كائن الطلب من قاعدة البيانات المراد تحديثه.
        order_in (schemas.OrderUpdate): البيانات المراد تحديثها.

    Returns:
        models_market.Order: كائن الطلب المحدث.
    """
    update_data = order_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_status(db: Session, db_order: models_market.Order, new_status_id: int) -> models_market.Order:
    """
    يحدث حالة الطلب (للحذف الناعم أو تغيير الحالة في دورة حياة الطلب).
    يجب أن يتم تسجيل هذا التغيير في OrderStatusHistory في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_order (models_market.Order): كائن الطلب من قاعدة البيانات.
        new_status_id (int): معرف الحالة الجديدة للطلب.

    Returns:
        models_market.Order: كائن الطلب بعد تحديث حالته.
    """
    db_order.order_status_id = new_status_id
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

# لا يوجد delete_order مباشر، يتم إدارة الحالة عبر تحديث order_status_id


# ==========================================================
# --- CRUD Functions for OrderItem (بنود الطلب) ---
# ==========================================================

def create_order_item(db: Session, item_in: schemas.OrderItemCreate, order_id: UUID) -> models_market.OrderItem:
    """
    ينشئ بند طلب جديد في قاعدة البيانات.
    عادةً ما يتم استدعاؤه كجزء من عملية إنشاء الطلب الأب.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_in (schemas.OrderItemCreate): بيانات بند الطلب للإنشاء.
        order_id (UUID): معرف الطلب الأب الذي ينتمي إليه هذا البند.

    Returns:
        models_market.OrderItem: كائن بند الطلب الذي تم إنشاؤه.
    """
    db_item = models_market.OrderItem(
        order_id=order_id,
        product_packaging_option_id=item_in.product_packaging_option_id,
        seller_user_id=item_in.seller_user_id,
        quantity_ordered=item_in.quantity_ordered,
        unit_price_at_purchase=item_in.unit_price_at_purchase,
        total_price_for_item=item_in.total_price_for_item,
        item_status_id=item_in.item_status_id,
        notes=item_in.notes
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_order_item(db: Session, order_item_id: int) -> Optional[models_market.OrderItem]:
    """
    يجلب بند طلب واحد بالـ ID الخاص به، مع الكائنات المرتبطة (مثل خيار التعبئة).

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_item_id (int): معرف بند الطلب المطلوب.

    Returns:
        Optional[models_market.OrderItem]: كائن بند الطلب أو None إذا لم يتم العثور عليه.
    """
    return db.query(models_market.OrderItem).options(
        joinedload(models_market.OrderItem.packaging_option),
        joinedload(models_market.OrderItem.seller),
        joinedload(models_market.OrderItem.item_status)
    ).filter(models_market.OrderItem.order_item_id == order_item_id).first()

def get_order_items_for_order(db: Session, order_id: UUID) -> List[models_market.OrderItem]:
    """
    يجلب جميع بنود الطلب لطلب معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_id (UUID): معرف الطلب الأب.

    Returns:
        List[models_market.OrderItem]: قائمة بكائنات بنود الطلب.
    """
    return db.query(models_market.OrderItem).filter(models_market.OrderItem.order_id == order_id).all()

def update_order_item(db: Session, db_order_item: models_market.OrderItem, item_in: schemas.OrderItemUpdate) -> models_market.OrderItem:
    """
    يحدث بيانات بند طلب موجود.
    عادةً ما يتم تحديث الحالة أو الملاحظات هنا.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_order_item (models_market.OrderItem): كائن بند الطلب من قاعدة البيانات المراد تحديثه.
        item_in (schemas.OrderItemUpdate): البيانات المراد تحديثها.

    Returns:
        models_market.OrderItem: كائن بند الطلب المحدث.
    """
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order_item, key, value)
    db.add(db_order_item)
    db.commit()
    db.refresh(db_order_item)
    return db_order_item

# لا يوجد delete_order_item مباشر، يتم إدارة الحذف عبر الطلب الأب.


# ==========================================================
# --- CRUD Functions for OrderStatusHistory (سجل تغييرات حالة الطلب) ---
# ==========================================================

def create_order_status_history(db: Session, order_id: UUID, old_status_id: Optional[int], new_status_id: int, changed_by_user_id: Optional[UUID] = None, notes: Optional[str] = None) -> models_market.OrderStatusHistory:
    """
    ينشئ سجلاً جديداً لتاريخ تغيير حالة الطلب.
    هذه الدالة تُستخدم لتوثيق كل تغيير في حالة الطلب.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_id (UUID): معرف الطلب الذي حدث فيه التغيير.
        old_status_id (Optional[int]): معرف الحالة القديمة للطلب.
        new_status_id (int): معرف الحالة الجديدة للطلب.
        changed_by_user_id (Optional[UUID]): معرف المستخدم الذي أجرى التغيير (NULL إذا كان النظام).
        notes (Optional[str]): ملاحظات إضافية حول سبب التغيير.

    Returns:
        models_market.OrderStatusHistory: كائن سجل التاريخ الذي تم إنشاؤه.
    """
    db_history = models_market.OrderStatusHistory(
        order_id=order_id,
        old_status_id=old_status_id,
        new_status_id=new_status_id,
        changed_by_user_id=changed_by_user_id,
        notes=notes
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history

def get_order_status_history_for_order(db: Session, order_id: UUID) -> List[models_market.OrderStatusHistory]:
    """
    يجلب جميع سجلات تاريخ حالة الطلب لطلب معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_id (UUID): معرف الطلب.

    Returns:
        List[models_market.OrderStatusHistory]: قائمة بسجلات تاريخ حالة الطلب.
    """
    return db.query(models_market.OrderStatusHistory).filter(models_market.OrderStatusHistory.order_id == order_id).order_by(models_market.OrderStatusHistory.change_timestamp).all()

# لا يوجد تحديث أو حذف لـ OrderStatusHistory لأنه جدول سجلات تاريخية (immutable).


# ==========================================================
# --- CRUD Functions for OrderStatus (حالات الطلب) ---
#    (تُستورد من src.lookups.models)
# ==========================================================

def create_order_status(db: Session, status_in: OrderStatusCreate) -> OrderStatus:
    """
    ينشئ حالة طلب جديدة في قاعدة البيانات، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (OrderStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        OrderStatus: كائن الحالة الذي تم إنشاؤه.
    """
    db_status = OrderStatus(
        status_name_key=status_in.status_name_key,
        status_description_key=status_in.status_description_key,
        is_active=status_in.is_active
    )
    db.add(db_status)
    db.flush()

    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = OrderStatusTranslation(
                order_status_id=db_status.order_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name,
                translated_status_description=trans_in.translated_status_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_order_status(db: Session, order_status_id: int) -> Optional[OrderStatus]:
    """
    يجلب حالة طلب واحدة بالـ ID الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة المطلوب.

    Returns:
        Optional[OrderStatus]: كائن الحالة أو None إذا لم يتم العثور عليه.
    """
    return db.query(OrderStatus).options(
        joinedload(OrderStatus.translations)
    ).filter(OrderStatus.order_status_id == order_status_id).first()

def get_all_order_statuses(db: Session) -> List[OrderStatus]:
    """
    يجلب قائمة بجميع حالات الطلب.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[OrderStatus]: قائمة بكائنات الحالات.
    """
    return db.query(OrderStatus).options(
        joinedload(OrderStatus.translations)
    ).all()

def update_order_status(db: Session, db_status: OrderStatus, status_in: OrderStatusUpdate) -> OrderStatus:
    """
    يحدث بيانات حالة طلب موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (OrderStatus): كائن الحالة من قاعدة البيانات.
        status_in (OrderStatusUpdate): البيانات المراد تحديثها.

    Returns:
        OrderStatus: كائن الحالة المحدث.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_order_status(db: Session, db_status: OrderStatus):
    """
    يحذف حالة طلب معينة (حذف صارم).
    TODO: التحقق من عدم وجود طلبات مرتبطة بهذه الحالة سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (OrderStatus): كائن الحالة من قاعدة البيانات.
    """
    db.delete(db_status)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for OrderStatusTranslation (ترجمات حالات الطلب) ---
# ==========================================================

def create_order_status_translation(db: Session, order_status_id: int, trans_in: OrderStatusTranslationCreate) -> OrderStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة طلب معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة الأم.
        trans_in (OrderStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        OrderStatusTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = OrderStatusTranslation(
        order_status_id=order_status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_status_description=trans_in.translated_status_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_order_status_translation(db: Session, order_status_id: int, language_code: str) -> Optional[OrderStatusTranslation]:
    """
    يجلب ترجمة حالة طلب محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة.
        language_code (str): رمز اللغة.

    Returns:
        Optional[OrderStatusTranslation]: كائن الترجمة أو None.
    """
    return db.query(OrderStatusTranslation).filter(
        and_(
            OrderStatusTranslation.order_status_id == order_status_id,
            OrderStatusTranslation.language_code == language_code
        )
    ).first()

def update_order_status_translation(db: Session, db_translation: OrderStatusTranslation, trans_in: OrderStatusTranslationUpdate) -> OrderStatusTranslation:
    """
    يحدث ترجمة حالة طلب موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (OrderStatusTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (OrderStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        OrderStatusTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_order_status_translation(db: Session, db_translation: OrderStatusTranslation):
    """
    يحذف ترجمة حالة طلب معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (OrderStatusTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for PaymentStatus (حالات الدفع) ---
#    (تُستورد من src.lookups.models)
# ==========================================================

def create_payment_status(db: Session, status_in: PaymentStatusCreate) -> PaymentStatus:
    """
    ينشئ حالة دفع جديدة في قاعدة البيانات، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (PaymentStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        PaymentStatus: كائن الحالة الذي تم إنشاؤه.
    """
    db_status = PaymentStatus(status_name_key=status_in.status_name_key)
    db.add(db_status)
    db.flush()

    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = PaymentStatusTranslation(
                payment_status_id=db_status.payment_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_payment_status(db: Session, payment_status_id: int) -> Optional[PaymentStatus]:
    """
    يجلب حالة دفع واحدة بالـ ID الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة المطلوب.

    Returns:
        Optional[PaymentStatus]: كائن الحالة أو None.
    """
    return db.query(PaymentStatus).options(
        joinedload(PaymentStatus.translations)
    ).filter(PaymentStatus.payment_status_id == payment_status_id).first()

def get_all_payment_statuses(db: Session) -> List[PaymentStatus]:
    """
    يجلب قائمة بجميع حالات الدفع.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[PaymentStatus]: قائمة بكائنات الحالات.
    """
    return db.query(PaymentStatus).options(
        joinedload(PaymentStatus.translations)
    ).all()

def update_payment_status(db: Session, db_status: PaymentStatus, status_in: PaymentStatusUpdate) -> PaymentStatus:
    """
    يحدث بيانات حالة دفع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (PaymentStatus): كائن الحالة من قاعدة البيانات.
        status_in (PaymentStatusUpdate): البيانات المراد تحديثها.

    Returns:
        PaymentStatus: كائن الحالة المحدث.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_payment_status(db: Session, db_status: PaymentStatus):
    """
    يحذف حالة دفع معينة (حذف صارم).
    TODO: التحقق من عدم وجود طلبات مرتبطة بهذه الحالة سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (PaymentStatus): كائن الحالة من قاعدة البيانات.
    """
    db.delete(db_status)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for PaymentStatusTranslation (ترجمات حالات الدفع) ---
# ==========================================================

def create_payment_status_translation(db: Session, payment_status_id: int, trans_in: PaymentStatusTranslationCreate) -> PaymentStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة دفع معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة الأم.
        trans_in (PaymentStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        PaymentStatusTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = PaymentStatusTranslation(
        payment_status_id=payment_status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_payment_status_translation(db: Session, payment_status_id: int, language_code: str) -> Optional[PaymentStatusTranslation]:
    """
    يجلب ترجمة حالة دفع محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة.
        language_code (str): رمز اللغة.

    Returns:
        Optional[PaymentStatusTranslation]: كائن الترجمة أو None.
    """
    return db.query(PaymentStatusTranslation).filter(
        and_(
            PaymentStatusTranslation.payment_status_id == payment_status_id,
            PaymentStatusTranslation.language_code == language_code
        )
    ).first()

def update_payment_status_translation(db: Session, db_translation: PaymentStatusTranslation, trans_in: PaymentStatusTranslationUpdate) -> PaymentStatusTranslation:
    """
    يحدث ترجمة حالة دفع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (PaymentStatusTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (PaymentStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        PaymentStatusTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_payment_status_translation(db: Session, db_translation: PaymentStatusTranslation):
    """
    يحذف ترجمة حالة دفع معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (PaymentStatusTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for OrderItemStatus (حالات بنود الطلب) ---
#    (تُستورد من src.lookups.models)
# ==========================================================

def create_order_item_status(db: Session, status_in: OrderItemStatusCreate) -> OrderItemStatus:
    """
    ينشئ حالة بند طلب جديدة في قاعدة البيانات، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (OrderItemStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        OrderItemStatus: كائن الحالة الذي تم إنشاؤه.
    """
    db_status = OrderItemStatus(status_name_key=status_in.status_name_key)
    db.add(db_status)
    db.flush()

    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = OrderItemStatusTranslation(
                item_status_id=db_status.item_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_order_item_status(db: Session, item_status_id: int) -> Optional[OrderItemStatus]:
    """
    يجلب حالة بند طلب واحدة بالـ ID الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_status_id (int): معرف الحالة المطلوب.

    Returns:
        Optional[OrderItemStatus]: كائن الحالة أو None.
    """
    return db.query(OrderItemStatus).options(
        joinedload(OrderItemStatus.translations)
    ).filter(OrderItemStatus.item_status_id == item_status_id).first()

def get_all_order_item_statuses(db: Session) -> List[OrderItemStatus]:
    """
    يجلب قائمة بجميع حالات بنود الطلب.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[OrderItemStatus]: قائمة بكائنات الحالات.
    """
    return db.query(OrderItemStatus).options(
        joinedload(OrderItemStatus.translations)
    ).all()

def update_order_item_status(db: Session, db_status: OrderItemStatus, status_in: OrderItemStatusUpdate) -> OrderItemStatus:
    """
    يحدث بيانات حالة بند طلب موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (OrderItemStatus): كائن الحالة من قاعدة البيانات.
        status_in (OrderItemStatusUpdate): البيانات المراد تحديثها.

    Returns:
        OrderItemStatus: كائن الحالة المحدث.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_order_item_status(db: Session, db_status: OrderItemStatus):
    """
    يحذف حالة بند طلب معينة (حذف صارم).
    TODO: التحقق من عدم وجود بنود طلبات مرتبطة بهذه الحالة سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (OrderItemStatus): كائن الحالة من قاعدة البيانات.
    """
    db.delete(db_status)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for OrderItemStatusTranslation (ترجمات حالات بنود الطلب) ---
# ==========================================================

def create_order_item_status_translation(db: Session, item_status_id: int, trans_in: OrderItemStatusTranslationCreate) -> OrderItemStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة بند طلب معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_status_id (int): معرف الحالة الأم.
        trans_in (OrderItemStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        OrderItemStatusTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = OrderItemStatusTranslation(
        item_status_id=item_status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_order_item_status_translation(db: Session, item_status_id: int, language_code: str) -> Optional[OrderItemStatusTranslation]:
    """
    يجلب ترجمة حالة بند طلب محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_status_id (int): معرف الحالة.
        language_code (str): رمز اللغة.

    Returns:
        Optional[OrderItemStatusTranslation]: كائن الترجمة أو None.
    """
    return db.query(OrderItemStatusTranslation).filter(
        and_(
            OrderItemStatusTranslation.item_status_id == item_status_id,
            OrderItemStatusTranslation.language_code == language_code
        )
    ).first()

def update_order_item_status_translation(db: Session, db_translation: OrderItemStatusTranslation, trans_in: OrderItemStatusTranslationUpdate) -> OrderItemStatusTranslation:
    """
    يحدث ترجمة حالة بند طلب موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (OrderItemStatusTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (OrderItemStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        OrderItemStatusTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_order_item_status_translation(db: Session, db_translation: OrderItemStatusTranslation):
    """
    يحذف ترجمة حالة بند طلب معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (OrderItemStatusTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return