# backend\src\products\crud\inventory_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from uuid import UUID
from typing import List, Optional

from src.products.models import inventory_models as models # استيراد المودلز الخاصة بـ InventoryItem و InventoryTransaction
# تصحيح الاستيرادات: جداول الحالات والأنواع موجودة في lookups.models.py
from src.lookups.models import ( # <-- تم تصحيح هذا المسار
    InventoryItemStatus,
    InventoryItemStatusTranslation,
    InventoryTransactionType,
    InventoryTransactionTypeTranslation
)
from src.products.schemas import inventory_schemas as schemas # استيراد الـ Schemas

# ==========================================================
# --- CRUD Functions for InventoryItem ---
# ==========================================================

def get_or_create_inventory_item(db: Session, packaging_option_id: int, seller_id: UUID) -> models.InventoryItem:
    """
    يبحث عن بند مخزون، وإذا لم يجده، يقوم بإنشاء واحد جديد بكمية صفر.
    محدثة لتعكس الهيكل الجديد.
    """
    db_item = db.query(models.InventoryItem).filter(
        and_(
            models.InventoryItem.product_packaging_option_id == packaging_option_id,
            models.InventoryItem.seller_user_id == seller_id
        )
    ).first()

    if not db_item:
        # جلب الحالة الافتراضية "OUT_OF_STOCK"
        default_status = db.query(InventoryItemStatus).filter(InventoryItemStatus.status_name_key == "OUT_OF_STOCK").first()
        
        new_item_data = {
            "product_packaging_option_id": packaging_option_id,
            "seller_user_id": seller_id,
            "available_quantity": 0,
            "reserved_quantity": 0,
            "on_hand_quantity": 0,
            "inventory_item_status_id": default_status.inventory_item_status_id if default_status else None # Fallback إذا لم يتم العثور على الحالة الافتراضية
        }
        db_item = models.InventoryItem(**new_item_data)
        db.add(db_item)
        db.flush() # استخدم flush للحصول على ID قبل الـ commit
        
    return db_item

def get_inventory_item(db: Session, inventory_item_id: int) -> Optional[models.InventoryItem]:
    """
    يجلب بند مخزون واحد بالـ ID الخاص به، مع الحالة والحركات.
    """
    return db.query(models.InventoryItem).options(
        joinedload(models.InventoryItem.status),
        joinedload(models.InventoryItem.transactions)
    ).filter(models.InventoryItem.inventory_item_id == inventory_item_id).first()

def get_all_inventory_items(db: Session, seller_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[models.InventoryItem]:
    """
    يجلب قائمة بجميع بنود المخزون، مع خيار التصفية حسب البائع.
    """
    query = db.query(models.InventoryItem).options(
        joinedload(models.InventoryItem.status)
    )
    if seller_id:
        query = query.filter(models.InventoryItem.seller_user_id == seller_id)
    return query.offset(skip).limit(limit).all()

def update_inventory_item(db: Session, db_inventory_item: models.InventoryItem, item_in: schemas.InventoryItemUpdate) -> models.InventoryItem:
    """
    يحدث بيانات بند مخزون موجود.
    """
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_inventory_item, key, value)
    db.add(db_inventory_item)
    db.commit()
    db.refresh(db_inventory_item)
    return db_inventory_item

# لا يوجد delete_inventory_item مباشر، يتم إدارة الحالة عبر تحديث inventory_item_status_id

# ==========================================================
# --- CRUD Functions for InventoryTransaction ---
# ==========================================================

def create_inventory_transaction(db: Session, inventory_item_id: int, transaction_in: schemas.InventoryTransactionRead, current_balance: float) -> models.InventoryTransaction:
    """
    ينشئ سجل حركة جديد في المخزون.
    ملاحظة: هذا ليس لإنشاء حركة من API مباشرة، بل يتم استدعاؤه داخليًا بواسطة خدمة تعديل المخزون.
    """
    db_transaction = models.InventoryTransaction(
        inventory_item_id=inventory_item_id,
        transaction_type_id=transaction_in.transaction_type_id,
        quantity_changed=transaction_in.quantity_changed,
        balance_after_transaction=current_balance, # الرصيد بعد هذه الحركة
        reason_notes=transaction_in.reason_notes,
        created_by_user_id=transaction_in.created_by_user_id
    )
    db.add(db_transaction)
    # لا نقوم بعمل commit هنا، ليتم التحكم به من طبقة الخدمة التي تستدعي هذه الدالة
    db.flush() # استخدم flush للحصول على ID إذا لزم الأمر
    return db_transaction

def get_inventory_transaction(db: Session, transaction_id: int) -> Optional[models.InventoryTransaction]:
    """
    يجلب سجل حركة مخزون واحد بالـ ID الخاص به.
    """
    return db.query(models.InventoryTransaction).filter(models.InventoryTransaction.transaction_id == transaction_id).first()

def get_transactions_for_inventory_item(db: Session, inventory_item_id: int, skip: int = 0, limit: int = 100) -> List[models.InventoryTransaction]:
    """
    يجلب جميع حركات المخزون لبند مخزون معين.
    """
    return db.query(models.InventoryTransaction).filter(models.InventoryTransaction.inventory_item_id == inventory_item_id).offset(skip).limit(limit).all()

# لا يوجد تحديث أو حذف لـ InventoryTransaction لأنه جدول سجلات (immutable)

# ==========================================================
# --- CRUD Functions for InventoryItemStatus ---
# ==========================================================

def create_inventory_item_status(db: Session, status_in: schemas.InventoryItemStatusCreate) -> InventoryItemStatus:
    """
    ينشئ حالة بند مخزون جديدة.
    """
    db_status = InventoryItemStatus(status_name_key=status_in.status_name_key)
    db.add(db_status)
    db.flush()
    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = InventoryItemStatusTranslation(
                inventory_item_status_id=db_status.inventory_item_status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name,
                translated_status_description=trans_in.translated_status_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_inventory_item_status(db: Session, status_id: int) -> Optional[InventoryItemStatus]:
    """
    يجلب حالة بند مخزون واحدة بالـ ID.
    """
    return db.query(InventoryItemStatus).options(joinedload(InventoryItemStatus.translations)).filter(InventoryItemStatus.inventory_item_status_id == status_id).first()

def get_all_inventory_item_statuses(db: Session, skip: int = 0, limit: int = 100) -> List[InventoryItemStatus]:
    """
    يجلب جميع حالات بنود المخزون.
    """
    return db.query(InventoryItemStatus).options(joinedload(InventoryItemStatus.translations)).offset(skip).limit(limit).all()

def update_inventory_item_status(db: Session, db_status: InventoryItemStatus, status_in: schemas.InventoryItemStatusUpdate) -> InventoryItemStatus:
    """
    يحدث حالة بند مخزون موجودة.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_inventory_item_status(db: Session, db_status: InventoryItemStatus):
    """
    يحذف حالة بند مخزون (حذف صارم).
    """
    db.delete(db_status)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for InventoryItemStatusTranslation ---
# ==========================================================

def create_inventory_item_status_translation(db: Session, status_id: int, trans_in: schemas.InventoryItemStatusTranslationCreate) -> InventoryItemStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة بند مخزون.
    """
    db_translation = InventoryItemStatusTranslation(
        inventory_item_status_id=status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_status_description=trans_in.translated_status_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_inventory_item_status_translation(db: Session, status_id: int, language_code: str) -> Optional[InventoryItemStatusTranslation]:
    """
    يجلب ترجمة حالة بند مخزون.
    """
    return db.query(InventoryItemStatusTranslation).filter(
        and_(
            InventoryItemStatusTranslation.inventory_item_status_id == status_id,
            InventoryItemStatusTranslation.language_code == language_code
        )
    ).first()

def update_inventory_item_status_translation(db: Session, db_translation: InventoryItemStatusTranslation, trans_in: schemas.InventoryItemStatusTranslationUpdate) -> InventoryItemStatusTranslation:
    """
    يحدث ترجمة حالة بند مخزون.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_inventory_item_status_translation(db: Session, db_translation: InventoryItemStatusTranslation):
    """
    يحذف ترجمة حالة بند مخزون (حذف صارم).
    """
    db.delete(db_translation)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for InventoryTransactionType ---
# ==========================================================

def create_inventory_transaction_type(db: Session, type_in: schemas.InventoryTransactionTypeCreate) -> InventoryTransactionType:
    """
    ينشئ نوع حركة مخزون جديدة.
    """
    db_type = InventoryTransactionType(transaction_type_name_key=type_in.transaction_type_name_key)
    db.add(db_type)
    db.flush()
    if type_in.translations:
        for trans_in in type_in.translations:
            db_translation = InventoryTransactionTypeTranslation(
                transaction_type_id=db_type.transaction_type_id,
                language_code=trans_in.language_code,
                translated_transaction_type_name=trans_in.translated_transaction_type_name,
                translated_transaction_description=trans_in.translated_transaction_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_type)
    return db_type

def get_inventory_transaction_type(db: Session, type_id: int) -> Optional[InventoryTransactionType]:
    """
    يجلب نوع حركة مخزون واحدة بالـ ID.
    """
    return db.query(InventoryTransactionType).options(joinedload(InventoryTransactionType.translations)).filter(InventoryTransactionType.transaction_type_id == type_id).first()

def get_all_inventory_transaction_types(db: Session, skip: int = 0, limit: int = 100) -> List[InventoryTransactionType]:
    """
    يجلب جميع أنواع حركات المخزون.
    """
    return db.query(InventoryTransactionType).options(joinedload(InventoryTransactionType.translations)).offset(skip).limit(limit).all()

def update_inventory_transaction_type(db: Session, db_type: InventoryTransactionType, type_in: schemas.InventoryTransactionTypeUpdate) -> InventoryTransactionType:
    """
    يحدث نوع حركة مخزون موجودة.
    """
    update_data = type_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_type, key, value)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def delete_inventory_transaction_type(db: Session, db_type: InventoryTransactionType):
    """
    يحذف نوع حركة مخزون (حذف صارم).
    """
    db.delete(db_type)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for InventoryTransactionTypeTranslation ---
# ==========================================================

def create_inventory_transaction_type_translation(db: Session, type_id: int, trans_in: schemas.InventoryTransactionTypeTranslationCreate) -> InventoryTransactionTypeTranslation:
    """
    ينشئ ترجمة جديدة لنوع حركة مخزون.
    """
    db_translation = InventoryTransactionTypeTranslation(
        transaction_type_id=type_id,
        language_code=trans_in.language_code,
        translated_transaction_type_name=trans_in.translated_transaction_type_name,
        translated_transaction_description=trans_in.translated_transaction_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_inventory_transaction_type_translation(db: Session, type_id: int, language_code: str) -> Optional[InventoryTransactionTypeTranslation]:
    """
    يجلب ترجمة نوع حركة مخزون.
    """
    return db.query(InventoryTransactionTypeTranslation).filter(
        and_(
            InventoryTransactionTypeTranslation.transaction_type_id == type_id,
            InventoryTransactionTypeTranslation.language_code == language_code
        )
    ).first()

def update_inventory_transaction_type_translation(db: Session, db_translation: InventoryTransactionTypeTranslation, trans_in: schemas.InventoryTransactionTypeTranslationUpdate) -> InventoryTransactionTypeTranslation:
    """
    يحدث ترجمة نوع حركة مخزون.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_inventory_transaction_type_translation(db: Session, db_translation: InventoryTransactionTypeTranslation):
    """
    يحذف ترجمة نوع حركة مخزون (حذف صارم).
    """
    db.delete(db_translation)
    db.commit()
    return