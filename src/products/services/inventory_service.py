# backend\src\products\services\inventory_service.py

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

# استيراد المودلز (للتعريفات والـ Type Hinting)
from src.products.models.inventory_models import InventoryItem, InventoryTransaction # InventoryItem, InventoryTransaction
# استيراد المودلز من Lookups
from src.lookups.models import ( # تم تصحيح مسار الاستيراد
    InventoryItemStatus,
    InventoryItemStatusTranslation,
    InventoryTransactionType,
    InventoryTransactionTypeTranslation
)
# استيراد الـ Schemas
from src.products.schemas import inventory_schemas
# استيراد دوال الـ CRUD من الملف الخاص بها
from src.products.crud import inventory_crud
# استيراد الخدمات الأخرى للتحقق من الوجود (مثل خدمة المنتج وخدمة خيارات التعبئة)
from src.products.services.packaging_service import get_packaging_option_details # للحصول على تفاصيل خيار التعبئة
from src.products.services.product_service import get_product_by_id_for_user # للتحقق من ملكية المنتج وخيار التعبئة
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

# ==========================================================
# --- خدمات عناصر المخزون (InventoryItem) ---
# ==========================================================

def adjust_stock_level(db: Session, adjustment: inventory_schemas.StockAdjustmentCreate, current_user: User) -> InventoryItem:
    """
    تعديل مستوى المخزون (زيادة/نقصان) لبند مخزون معين.
    هذه الدالة هي نقطة الدخول الرئيسية لعمليات تحديث المخزون التي تتم يدويًا أو عبر النظام (مثلاً، عند البيع أو الإرجاع).

    Args:
        db (Session): جلسة قاعدة البيانات.
        adjustment (inventory_schemas.StockAdjustmentCreate): بيانات التعديل المطلوبة، وتشمل:
            - product_packaging_option_id (int): ID خيار التعبئة الذي يتم تعديل مخزونه.
            - change_in_quantity (float): الكمية المراد إضافتها (موجبة) أو خصمها (سالبة).
            - reason_notes (Optional[str]): ملاحظات إضافية حول سبب التعديل.
        current_user (User): المستخدم الحالي الذي يقوم بإجراء التعديل (للتحقق من الصلاحيات والتسجيل في سجل الحركات).

    Returns:
        InventoryItem: كائن بند المخزون المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على خيار التعبئة المرتبط.
        ForbiddenException: إذا كان المستخدم لا يملك المنتج المرتبط بخيار التعبئة، أو لا يملك الصلاحية.
        BadRequestException: إذا كانت الكمية الناتجة عن التعديل سالبة.
        ConflictException: إذا لم يتم العثور على نوع حركة المخزون المناسب (مثلاً "MANUAL_ADJUSTMENT_IN").
    """
    # 1. التحقق من وجود خيار التعبئة وأن المستخدم يملكه (أو مسؤول)
    #    - تستخدم get_packaging_option_details لضمان وجود خيار التعبئة، وسترفع NotFoundException إن لم يوجد.
    packaging_option = get_packaging_option_details(db, adjustment.product_packaging_option_id)
    
    #    - تستخدم get_product_by_id_for_user للتحقق من ملكية المنتج المرتبط بخيار التعبئة للمستخدم الحالي.
    #      سترفع ForbiddenException إذا لم يكن المستخدم مصرحًا له.
    get_product_by_id_for_user(db, product_id=packaging_option.product_id, user=current_user)

    # 2. جلب أو إنشاء سجل المخزون الخاص بخيار التعبئة هذا والبائع.
    #    - إذا لم يكن سجل المخزون موجودًا، فسيتم إنشاؤه بكميات صفرية وحالة "OUT_OF_STOCK".
    inventory_item = inventory_crud.get_or_create_inventory_item(db, packaging_option_id=adjustment.product_packaging_option_id, seller_id=current_user.user_id)

    # 3. تحديث الكميات في بند المخزون.
    #    - يتم استخدام Decimal لضمان دقة الحسابات المالية وتجنب الأخطاء الشائعة في الفلوت (Floating Point).
    change_in_quantity_decimal = Decimal(str(adjustment.change_in_quantity))
    new_on_hand_quantity = Decimal(str(inventory_item.on_hand_quantity)) + change_in_quantity_decimal
    
    #    - تحقق لمنع الكمية السالبة بعد التعديل.
    if new_on_hand_quantity < 0:
        raise BadRequestException(detail="Stock quantity cannot be negative.")
        
    #    - تحديث الكميات الفعلية والمتاحة. الكمية المحجوزة (reserved_quantity) يتم التعامل معها في عمليات الطلبات.
    inventory_item.on_hand_quantity = float(new_on_hand_quantity)
    inventory_item.available_quantity = float(new_on_hand_quantity) - inventory_item.reserved_quantity

    # 4. تحديد نوع حركة المخزون وتسجيلها في جدول سجلات الحركات (InventoryTransaction).
    #    - يتم تحديد نوع الحركة بناءً على ما إذا كانت إضافة أو خصم.
    trans_type_key = "MANUAL_ADJUSTMENT_IN" if adjustment.change_in_quantity > 0 else "MANUAL_ADJUSTMENT_OUT"
    
    #    - جلب نوع الحركة من جدول lookup (InventoryTransactionType).
    trans_type = db.query(InventoryTransactionType).filter(InventoryTransactionType.transaction_type_name_key == trans_type_key).first()
    
    #    - إذا لم يتم العثور على نوع الحركة (مما يشير إلى مشكلة في بيانات الـ seeding)، يتم رفع ConflictException.
    if not trans_type:
        raise ConflictException(detail=f"Transaction type '{trans_type_key}' not found in the system. Please ensure lookup data is seeded.")

    #    - إنشاء كائن InventoryTransactionRead schema مؤقت لتمرير البيانات إلى دالة CRUD.
    transaction_read_schema = inventory_schemas.InventoryTransactionRead(
        transaction_type_id=trans_type.transaction_type_id,
        quantity_changed=adjustment.change_in_quantity,
        reason_notes=adjustment.reason_notes,
        created_by_user_id=current_user.user_id,
        # هذه الحقول ليست مطلوبة للإنشاء في CRUD ولكنها جزء من الـ schema وتُستخدم لتوحيد الواجهة
        transaction_id=0, # قيمة وهمية مؤقتة لأنها تُنشأ في DB
        inventory_item_id=inventory_item.inventory_item_id,
        balance_after_transaction=0, # سيتم تعيينها في دالة CRUD
        transaction_timestamp=datetime.now() # سيتم تعيينها في دالة CRUD
    )

    #    - استدعاء دالة CRUD لإنشاء سجل الحركة. هذه الدالة لا تقوم بعمل commit.
    inventory_crud.create_inventory_transaction(
        db, 
        inventory_item_id=inventory_item.inventory_item_id, 
        transaction_in=transaction_read_schema,
        current_balance=inventory_item.available_quantity # يتم تسجيل الرصيد المتاح بعد الحركة
    )
    
    # 5. حفظ كل التغييرات في قاعدة البيانات.
    #    - يتم إجراء commit واحد لضمان الذرية (Atomic Operation): إما أن تنجح عملية تحديث الكمية وتسجيل الحركة معًا، أو لا ينجح أي منهما.
    db.commit()
    
    #    - تحديث كائن بند المخزون من قاعدة البيانات ليعكس آخر التغييرات.
    db.refresh(inventory_item)
    
    return inventory_item

def get_inventory_item_by_id(db: Session, inventory_item_id: int, current_user: User) -> InventoryItem:
    """
    جلب تفاصيل بند مخزون واحد بالـ ID الخاص به، مع التحقق من صلاحيات المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        inventory_item_id (int): ID بند المخزون المطلوب.
        current_user (User): المستخدم الحالي الذي يحاول جلب التفاصيل.

    Returns:
        InventoryItem: كائن بند المخزون المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على بند المخزون.
        ForbiddenException: إذا كان المستخدم لا يملك هذا البند وليس لديه صلاحيات المسؤول.
    """
    # 1. جلب بند المخزون باستخدام دالة CRUD.
    inventory_item = inventory_crud.get_inventory_item(db, inventory_item_id=inventory_item_id)
    
    # 2. التحقق من وجود بند المخزون.
    if not inventory_item:
        raise NotFoundException(detail=f"Inventory item with ID {inventory_item_id} not found.")

    # 3. التحقق من صلاحيات المستخدم: يجب أن يكون المالك (البائع) أو مسؤولاً عاماً.
    #    - 'ADMIN_PRODUCT_VIEW_ANY' هي صلاحية افتراضية للمسؤول تسمح له برؤية أي منتج/مخزون.
    if inventory_item.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRODUCT_VIEW_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="Not authorized to view this inventory item.")
    
    return inventory_item

def get_my_inventory_items(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
    """
    جلب جميع بنود المخزون الخاصة بالبائع الحالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي (البائع) الذي يطلب بنود مخزونه.
        skip (int): عدد السجلات لتخطيها (للترقيم).
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها (للترقيم).

    Returns:
        List[InventoryItem]: قائمة بكائنات بنود المخزون الخاصة بالبائع.
    """
    # تستدعي دالة CRUD لجلب بنود المخزون المفلترة حسب معرف البائع.
    return inventory_crud.get_all_inventory_items(db, seller_id=current_user.user_id, skip=skip, limit=limit)

def get_all_inventory_items_for_admin(db: Session, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
    """
    جلب جميع بنود المخزون في النظام (خاصة بالمسؤولين).

    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[InventoryItem]: قائمة بجميع بنود المخزون في النظام.
    """
    # تستدعي دالة CRUD لجلب جميع بنود المخزون دون تصفية حسب البائع.
    return inventory_crud.get_all_inventory_items(db, skip=skip, limit=limit)

def update_inventory_item_by_admin(db: Session, inventory_item_id: int, item_in: inventory_schemas.InventoryItemUpdate) -> InventoryItem:
    """
    تحديث بند مخزون مباشرة بواسطة مسؤول النظام.
    تسمح هذه الدالة بتعديل أي حقل في بند المخزون، بما في ذلك الكميات والحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        inventory_item_id (int): ID بند المخزون المراد تحديثه.
        item_in (inventory_schemas.InventoryItemUpdate): البيانات المراد تحديثها.

    Returns:
        InventoryItem: كائن بند المخزون المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على بند المخزون.
        BadRequestException: إذا كانت الحالة الجديدة غير موجودة.
    """
    # 1. جلب بند المخزون.
    #    - هنا، لا يتم التحقق من المستخدم لأنه يفترض أن هذه الدالة تُستدعى فقط في سياق يمتلك فيه المستخدم صلاحيات المسؤول (عبر الراوتر).
    db_item = inventory_crud.get_inventory_item(db, inventory_item_id=inventory_item_id)
    if not db_item:
        raise NotFoundException(detail=f"Inventory item with ID {inventory_item_id} not found.")
    
    # 2. التحقق من وجود حالة المخزون الجديدة إذا تم تحديثها.
    if item_in.inventory_item_status_id:
        status_exists = db.query(InventoryItemStatus).filter(InventoryItemStatus.inventory_item_status_id == item_in.inventory_item_status_id).first()
        if not status_exists:
            raise BadRequestException(detail=f"Inventory item status with ID {item_in.inventory_item_status_id} not found.")

    # 3. استدعاء دالة CRUD للتحديث.
    return inventory_crud.update_inventory_item(db=db, db_inventory_item=db_item, item_in=item_in)

# ==========================================================
# --- خدمات عناصر المخزون (InventoryItem) ---
# ==========================================================

def adjust_stock_level(db: Session, adjustment: inventory_schemas.StockAdjustmentCreate, current_user: User) -> InventoryItem:
    """
    تعديل مستوى المخزون (زيادة/نقصان) لبند مخزون معين.
    هذه الدالة هي نقطة الدخول الرئيسية لعمليات تحديث المخزون التي تتم يدويًا أو عبر النظام (مثلاً، عند البيع أو الإرجاع).

    Args:
        db (Session): جلسة قاعدة البيانات.
        adjustment (inventory_schemas.StockAdjustmentCreate): بيانات التعديل المطلوبة، وتشمل:
            - product_packaging_option_id (int): ID خيار التعبئة الذي يتم تعديل مخزونه.
            - change_in_quantity (float): الكمية المراد إضافتها (موجبة) أو خصمها (سالبة).
            - reason_notes (Optional[str]): ملاحظات إضافية حول سبب التعديل.
        current_user (User): المستخدم الحالي الذي يقوم بإجراء التعديل (للتحقق من الصلاحيات والتسجيل في سجل الحركات).

    Returns:
        InventoryItem: كائن بند المخزون المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على خيار التعبئة المرتبط.
        ForbiddenException: إذا كان المستخدم لا يملك المنتج المرتبط بخيار التعبئة، أو لا يملك الصلاحية.
        BadRequestException: إذا كانت الكمية الناتجة عن التعديل سالبة.
        ConflictException: إذا لم يتم العثور على نوع حركة المخزون المناسب (مثلاً "MANUAL_ADJUSTMENT_IN").
    """
    # 1. التحقق من وجود خيار التعبئة وأن المستخدم يملكه (أو مسؤول)
    #    - تستخدم get_packaging_option_details لضمان وجود خيار التعبئة، وسترفع NotFoundException إن لم يوجد.
    packaging_option = get_packaging_option_details(db, adjustment.product_packaging_option_id)
    
    #    - تستخدم get_product_by_id_for_user للتحقق من ملكية المنتج المرتبط بخيار التعبئة للمستخدم الحالي.
    #      سترفع ForbiddenException إذا لم يكن المستخدم مصرحًا له.
    get_product_by_id_for_user(db, product_id=packaging_option.product_id, user=current_user)

    # 2. جلب أو إنشاء سجل المخزون الخاص بخيار التعبئة هذا والبائع.
    #    - إذا لم يكن سجل المخزون موجودًا، فسيتم إنشاؤه بكميات صفرية وحالة "OUT_OF_STOCK".
    inventory_item = inventory_crud.get_or_create_inventory_item(db, packaging_option_id=adjustment.product_packaging_option_id, seller_id=current_user.user_id)

    # 3. تحديث الكميات في بند المخزون.
    #    - يتم استخدام Decimal لضمان دقة الحسابات المالية وتجنب الأخطاء الشائعة في الفلوت (Floating Point).
    change_in_quantity_decimal = Decimal(str(adjustment.change_in_quantity))
    new_on_hand_quantity = Decimal(str(inventory_item.on_hand_quantity)) + change_in_quantity_decimal
    
    #    - تحقق لمنع الكمية السالبة بعد التعديل.
    if new_on_hand_quantity < 0:
        raise BadRequestException(detail="Stock quantity cannot be negative.")
        
    #    - تحديث الكميات الفعلية والمتاحة. الكمية المحجوزة (reserved_quantity) يتم التعامل معها في عمليات الطلبات.
    inventory_item.on_hand_quantity = float(new_on_hand_quantity)
    inventory_item.available_quantity = float(new_on_hand_quantity) - inventory_item.reserved_quantity

    # 4. تحديد نوع حركة المخزون وتسجيلها في جدول سجلات الحركات (InventoryTransaction).
    #    - يتم تحديد نوع الحركة بناءً على ما إذا كانت إضافة أو خصم.
    trans_type_key = "MANUAL_ADJUSTMENT_IN" if adjustment.change_in_quantity > 0 else "MANUAL_ADJUSTMENT_OUT"
    
    #    - جلب نوع الحركة من جدول lookup (InventoryTransactionType).
    trans_type = db.query(InventoryTransactionType).filter(InventoryTransactionType.transaction_type_name_key == trans_type_key).first()
    
    #    - إذا لم يتم العثور على نوع الحركة (مما يشير إلى مشكلة في بيانات الـ seeding)، يتم رفع ConflictException.
    if not trans_type:
        raise ConflictException(detail=f"Transaction type '{trans_type_key}' not found in the system. Please ensure lookup data is seeded.")

    #    - إنشاء كائن InventoryTransactionRead schema مؤقت لتمرير البيانات إلى دالة CRUD.
    transaction_read_schema = inventory_schemas.InventoryTransactionRead(
        transaction_type_id=trans_type.transaction_type_id,
        quantity_changed=adjustment.change_in_quantity,
        reason_notes=adjustment.reason_notes,
        created_by_user_id=current_user.user_id,
        # هذه الحقول ليست مطلوبة للإنشاء في CRUD ولكنها جزء من الـ schema وتُستخدم لتوحيد الواجهة
        transaction_id=0, # قيمة وهمية مؤقتة لأنها تُنشأ في DB
        inventory_item_id=inventory_item.inventory_item_id,
        balance_after_transaction=0, # سيتم تعيينها في دالة CRUD
        transaction_timestamp=datetime.now() # سيتم تعيينها في دالة CRUD
    )

    #    - استدعاء دالة CRUD لإنشاء سجل الحركة. هذه الدالة لا تقوم بعمل commit.
    inventory_crud.create_inventory_transaction(
        db, 
        inventory_item_id=inventory_item.inventory_item_id, 
        transaction_in=transaction_read_schema,
        current_balance=inventory_item.available_quantity # يتم تسجيل الرصيد المتاح بعد الحركة
    )
    
    # 5. حفظ كل التغييرات في قاعدة البيانات.
    #    - يتم إجراء commit واحد لضمان الذرية (Atomic Operation): إما أن تنجح عملية تحديث الكمية وتسجيل الحركة معًا، أو لا ينجح أي منهما.
    db.commit()
    
    #    - تحديث كائن بند المخزون من قاعدة البيانات ليعكس آخر التغييرات.
    db.refresh(inventory_item)
    
    return inventory_item

def get_inventory_item_by_id(db: Session, inventory_item_id: int, current_user: User) -> InventoryItem:
    """
    جلب تفاصيل بند مخزون واحد بالـ ID الخاص به، مع التحقق من صلاحيات المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        inventory_item_id (int): ID بند المخزون المطلوب.
        current_user (User): المستخدم الحالي الذي يحاول جلب التفاصيل.

    Returns:
        InventoryItem: كائن بند المخزون المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على بند المخزون.
        ForbiddenException: إذا كان المستخدم لا يملك هذا البند وليس لديه صلاحيات المسؤول.
    """
    # 1. جلب بند المخزون باستخدام دالة CRUD.
    inventory_item = inventory_crud.get_inventory_item(db, inventory_item_id=inventory_item_id)
    
    # 2. التحقق من وجود بند المخزون.
    if not inventory_item:
        raise NotFoundException(detail=f"Inventory item with ID {inventory_item_id} not found.")

    # 3. التحقق من صلاحيات المستخدم: يجب أن يكون المالك (البائع) أو مسؤولاً عاماً.
    #    - 'ADMIN_PRODUCT_VIEW_ANY' هي صلاحية افتراضية للمسؤول تسمح له برؤية أي منتج/مخزون.
    if inventory_item.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRODUCT_VIEW_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="Not authorized to view this inventory item.")
    
    return inventory_item

def get_my_inventory_items(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
    """
    جلب جميع بنود المخزون الخاصة بالبائع الحالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي (البائع) الذي يطلب بنود مخزونه.
        skip (int): عدد السجلات لتخطيها (للترقيم).
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها (للترقيم).

    Returns:
        List[InventoryItem]: قائمة بكائنات بنود المخزون الخاصة بالبائع.
    """
    # تستدعي دالة CRUD لجلب بنود المخزون المفلترة حسب معرف البائع.
    return inventory_crud.get_all_inventory_items(db, seller_id=current_user.user_id, skip=skip, limit=limit)

def get_all_inventory_items_for_admin(db: Session, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
    """
    جلب جميع بنود المخزون في النظام (خاصة بالمسؤولين).

    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[InventoryItem]: قائمة بجميع بنود المخزون في النظام.
    """
    # تستدعي دالة CRUD لجلب جميع بنود المخزون دون تصفية حسب البائع.
    return inventory_crud.get_all_inventory_items(db, skip=skip, limit=limit)

def update_inventory_item_by_admin(db: Session, inventory_item_id: int, item_in: inventory_schemas.InventoryItemUpdate) -> InventoryItem:
    """
    تحديث بند مخزون مباشرة بواسطة مسؤول النظام.
    تسمح هذه الدالة بتعديل أي حقل في بند المخزون، بما في ذلك الكميات والحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        inventory_item_id (int): ID بند المخزون المراد تحديثه.
        item_in (inventory_schemas.InventoryItemUpdate): البيانات المراد تحديثها.

    Returns:
        InventoryItem: كائن بند المخزون المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على بند المخزون.
        BadRequestException: إذا كانت الحالة الجديدة غير موجودة.
    """
    # 1. جلب بند المخزون.
    #    - هنا، لا يتم التحقق من المستخدم لأنه يفترض أن هذه الدالة تُستدعى فقط في سياق يمتلك فيه المستخدم صلاحيات المسؤول (عبر الراوتر).
    db_item = inventory_crud.get_inventory_item(db, inventory_item_id=inventory_item_id)
    if not db_item:
        raise NotFoundException(detail=f"Inventory item with ID {inventory_item_id} not found.")
    
    # 2. التحقق من وجود حالة المخزون الجديدة إذا تم تحديثها.
    if item_in.inventory_item_status_id:
        status_exists = db.query(InventoryItemStatus).filter(InventoryItemStatus.inventory_item_status_id == item_in.inventory_item_status_id).first()
        if not status_exists:
            raise BadRequestException(detail=f"Inventory item status with ID {item_in.inventory_item_status_id} not found.")

    # 3. استدعاء دالة CRUD للتحديث.
    return inventory_crud.update_inventory_item(db=db, db_inventory_item=db_item, item_in=item_in)

# ==========================================================
# --- خدمات ترجمات حالات عناصر المخزون (InventoryItemStatusTranslation) ---
# ==========================================================

def create_inventory_item_status_translation(db: Session, status_id: int, trans_in: inventory_schemas.InventoryItemStatusTranslationCreate) -> InventoryItemStatusTranslation:
    """
    إنشاء ترجمة جديدة لحالة بند مخزون.
    هذه الدالة مخصصة لإضافة دعم لغوي لحالات بنود المخزون المرجعية، مثل ترجمة "متاح" إلى لغات مختلفة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID حالة بند المخزون الأم الذي سيتم إضافة الترجمة إليه.
        trans_in (inventory_schemas.InventoryItemStatusTranslationCreate): بيانات الترجمة الجديدة،
            بما في ذلك كود اللغة (language_code)، الاسم المترجم (translated_name)، والوصف المترجم (translated_description).

    Returns:
        InventoryItemStatusTranslation: كائن الترجمة التي تم إنشاؤها.

    Raises:
        NotFoundException: إذا لم يتم العثور على حالة بند المخزون الأم بالـ ID المحدد.
        ConflictException: إذا كانت هناك ترجمة بنفس اللغة موجودة بالفعل لنفس الحالة، مما يضمن تفرد الترجمات لكل لغة.
    """
    # 1. منطق عمل: التحقق من وجود حالة بند المخزون الأم.
    #    - تستدعي دالة الخدمة get_inventory_item_status_by_id لضمان وجود الكائن الأم.
    #      إذا لم يوجد، سترفع NotFoundException.
    get_inventory_item_status_by_id(db, status_id)

    # 2. منطق عمل: التحقق من عدم وجود ترجمة بنفس اللغة لنفس حالة بند المخزون.
    #    - تستخدم دالة CRUD للتحقق من وجود ترجمة مكررة لنفس اللغة.
    if inventory_crud.get_inventory_item_status_translation(db, status_id=status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"Translation for status ID {status_id} with language '{trans_in.language_code}' already exists.")
    
    # 3. استدعاء دالة CRUD لإنشاء الترجمة.
    return inventory_crud.create_inventory_item_status_translation(db=db, status_id=status_id, trans_in=trans_in)

def get_inventory_item_status_translation_by_id_and_lang(db: Session, status_id: int, language_code: str) -> InventoryItemStatusTranslation:
    """
    جلب ترجمة محددة لحالة بند مخزون بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID حالة بند المخزون الأم.
        language_code (str): رمز اللغة (مثل 'ar', 'en').

    Returns:
        InventoryItemStatusTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة المحددة بالـ ID ورمز اللغة.
    """
    # 1. جلب الترجمة باستخدام دالة CRUD.
    translation = inventory_crud.get_inventory_item_status_translation(db, status_id=status_id, language_code=language_code)
    
    # 2. التحقق من وجود الترجمة.
    if not translation:
        raise NotFoundException(detail=f"Translation for status ID {status_id} in language '{language_code}' not found.")
    
    return translation

def update_inventory_item_status_translation(db: Session, status_id: int, language_code: str, trans_in: inventory_schemas.InventoryItemStatusTranslationUpdate) -> InventoryItemStatusTranslation:
    """
    تحديث ترجمة حالة بند مخزون موجودة.
    تسمح هذه الدالة بتعديل الاسم والوصف المترجمين لحالة معينة بلغة محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID حالة بند المخزون الأم.
        language_code (str): رمز اللغة للترجمة المراد تحديثها.
        trans_in (inventory_schemas.InventoryItemStatusTranslationUpdate): البيانات المراد تحديثها للترجمة.

    Returns:
        InventoryItemStatusTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة المحددة بالـ ID ورمز اللغة.
    """
    # 1. جلب الترجمة باستخدام دالة الخدمة (لضمان وجودها ومعالجة NotFoundException).
    db_translation = get_inventory_item_status_translation_by_id_and_lang(db, status_id, language_code)
    
    # 2. استدعاء دالة CRUD للتحديث.
    return inventory_crud.update_inventory_item_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_inventory_item_status_translation(db: Session, status_id: int, language_code: str):
    """
    حذف ترجمة حالة بند مخزون معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID حالة بند المخزون الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة المحددة بالـ ID ورمز اللغة.
    """
    # 1. جلب الترجمة باستخدام دالة الخدمة (لضمان وجودها).
    db_translation = get_inventory_item_status_translation_by_id_and_lang(db, status_id, language_code)
    
    # 2. استدعاء دالة CRUD للحذف الصارم.
    inventory_crud.delete_inventory_item_status_translation(db=db, db_translation=db_translation)
    return {"message": "Inventory item status translation deleted successfully."}

# ==========================================================
# --- خدمات أنواع حركات المخزون (InventoryTransactionType) ---
# ==========================================================

def create_new_inventory_transaction_type(db: Session, type_in: inventory_schemas.InventoryTransactionTypeCreate) -> InventoryTransactionType:
    """
    إنشاء نوع حركة مخزون جديد مع ترجماته.
    هذه الدالة مخصصة لإدارة أنواع الحركات المرجعية في النظام (عادةً بواسطة المسؤولين)،
    مثل "استلام بضاعة"، "خصم بيع"، "تلف"، "تعديل يدوي".

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (inventory_schemas.InventoryTransactionTypeCreate): بيانات نوع الحركة الجديدة،
            بما في ذلك مفتاح الاسم (transaction_type_name_key) والترجمات الاختيارية.

    Returns:
        InventoryTransactionType: كائن نوع الحركة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك محاولة لإنشاء نوع حركة بنفس مفتاح الاسم موجود بالفعل،
            مما يضمن تفرد أنواع الحركات.
    """
    # 1. منطق عمل: التحقق من عدم وجود نوع حركة بنفس مفتاح الاسم لتجنب التكرار.
    if db.query(InventoryTransactionType).filter(InventoryTransactionType.transaction_type_name_key == type_in.transaction_type_name_key).first():
        raise ConflictException(detail=f"Inventory transaction type with key '{type_in.transaction_type_name_key}' already exists.")
    
    # 2. استدعاء دالة CRUD لإنشاء نوع الحركة.
    #    - تتولى دالة CRUD مسؤولية حفظ الكائن الرئيسي وترجماته المضمنة في عملية واحدة.
    return inventory_crud.create_inventory_transaction_type(db=db, type_in=type_in)

def get_inventory_transaction_type_by_id(db: Session, type_id: int) -> InventoryTransactionType:
    """
    جلب نوع حركة مخزون بالـ ID الخاص بها، مع معالجة عدم الوجود.
    هذه الدالة مفيدة لجلب تفاصيل نوع حركة معين أو للتحقق من وجوده قبل إجراء عمليات أخرى.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): ID نوع الحركة المطلوبة.

    Returns:
        InventoryTransactionType: كائن نوع الحركة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على نوع الحركة بالـ ID المحدد.
    """
    # 1. جلب نوع الحركة باستخدام دالة CRUD.
    type_obj = inventory_crud.get_inventory_transaction_type(db, type_id=type_id)
    
    # 2. التحقق من وجود نوع الحركة.
    if not type_obj:
        raise NotFoundException(detail=f"Inventory transaction type with ID {type_id} not found.")
    
    return type_obj

def get_all_inventory_transaction_types(db: Session) -> List[InventoryTransactionType]:
    """
    جلب جميع أنواع حركات المخزون المرجعية في النظام.
    هذه الدالة توفر قائمة كاملة بأنواع الحركات الممكنة في سجل المخزون.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[InventoryTransactionType]: قائمة بكائنات أنواع الحركات المرجعية.
    """
    # تستدعي دالة CRUD لجلب جميع أنواع الحركات.
    return inventory_crud.get_all_inventory_transaction_types(db)

def update_inventory_transaction_type(db: Session, type_id: int, type_in: inventory_schemas.InventoryTransactionTypeUpdate) -> InventoryTransactionType:
    """
    تحديث نوع حركة مخزون موجودة.
    تسمح هذه الدالة بتعديل مفتاح الاسم لنوع حركة المخزون.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): ID نوع الحركة المراد تحديثها.
        type_in (inventory_schemas.InventoryTransactionTypeUpdate): البيانات المراد تحديثها (مفتاح الاسم).

    Returns:
        InventoryTransactionType: كائن نوع الحركة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على نوع الحركة بالـ ID المحدد.
        ConflictException: إذا كانت هناك محاولة لتغيير مفتاح الاسم إلى مفتاح موجود بالفعل لنوع حركة آخر، مما يؤدي إلى تكرار.
    """
    # 1. جلب نوع الحركة باستخدام دالة الخدمة (لضمان وجودها ومعالجة NotFoundException).
    db_type = get_inventory_transaction_type_by_id(db, type_id)
    
    # 2. منطق عمل: إذا تم تحديث مفتاح الاسم (transaction_type_name_key)، تحقق من عدم التكرار.
    #    - يتم التحقق من أن المفتاح الجديد لا يتعارض مع مفتاح موجود لنوع حركة آخر (غير النوع الذي يتم تحديثه).
    if type_in.transaction_type_name_key and type_in.transaction_type_name_key != db_type.transaction_type_name_key:
        if db.query(InventoryTransactionType).filter(InventoryTransactionType.transaction_type_name_key == type_in.transaction_type_name_key).first():
            raise ConflictException(detail=f"Inventory transaction type with key '{type_in.transaction_type_name_key}' already exists.")
    
    # 3. استدعاء دالة CRUD للتحديث.
    return inventory_crud.update_inventory_transaction_type(db=db, db_type=db_type, type_in=type_in)

def delete_inventory_transaction_type(db: Session, type_id: int):
    """
    حذف نوع حركة مخزون (حذف صارم).
    هذه الدالة مخصصة لإدارة أنواع الحركات المرجعية في النظام، وتتضمن تحققات صارمة لمنع حذف الأنواع المستخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): ID نوع الحركة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على نوع الحركة بالـ ID المحدد.
        ForbiddenException: إذا كانت نوع الحركة مستخدمة حاليًا بواسطة أي حركات مخزون مسجلة (InventoryTransaction)،
            لمنع كسر سجلات الحركات التاريخية.
    """
    # 1. جلب نوع الحركة باستخدام دالة الخدمة (لضمان وجودها).
    db_type = get_inventory_transaction_type_by_id(db, type_id)
    
    # 2. منطق عمل: التحقق من عدم وجود حركات مخزون تستخدم هذا النوع.
    #    - هذا يضمن سلامة البيانات التاريخية في جدول InventoryTransaction، حيث لا يجب حذف نوع حركة إذا كانت هناك سجلات تعتمد عليه.
    if db.query(InventoryTransaction).filter(InventoryTransaction.transaction_type_id == type_id).count() > 0:
        raise ForbiddenException(detail=f"Cannot delete inventory transaction type ID {type_id} because it is used by existing inventory transactions.")
    
    # 3. استدعاء دالة CRUD للحذف الصارم.
    inventory_crud.delete_inventory_transaction_type(db=db, db_type=db_type)
    return {"message": "Inventory transaction type deleted successfully."}

# ==========================================================
# --- خدمات ترجمات أنواع حركات المخزون (InventoryTransactionTypeTranslation) ---
# ==========================================================

def create_inventory_transaction_type_translation(db: Session, type_id: int, trans_in: inventory_schemas.InventoryTransactionTypeTranslationCreate) -> InventoryTransactionTypeTranslation:
    """
    إنشاء ترجمة جديدة لنوع حركة مخزون.
    هذه الدالة مخصصة لإضافة دعم لغوي لأنواع حركات المخزون المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): ID نوع حركة المخزون الأم الذي سيتم إضافة الترجمة إليه.
        trans_in (inventory_schemas.InventoryTransactionTypeTranslationCreate): بيانات الترجمة الجديدة،
            بما في ذلك كود اللغة، الاسم المترجم، والوصف المترجم.

    Returns:
        InventoryTransactionTypeTranslation: كائن الترجمة التي تم إنشاؤها.

    Raises:
        NotFoundException: إذا لم يتم العثور على نوع حركة المخزون الأم بالـ ID المحدد.
        ConflictException: إذا كانت هناك ترجمة بنفس اللغة موجودة بالفعل لنفس نوع الحركة، مما يشير إلى تكرار غير مسموح به.
    """
    # 1. منطق عمل: التحقق من وجود نوع حركة المخزون الأم.
    #    - تستدعي دالة الخدمة get_inventory_transaction_type_by_id لضمان وجود الكائن الأم.
    #      إذا لم يوجد، سترفع NotFoundException.
    get_inventory_transaction_type_by_id(db, type_id)

    # 2. منطق عمل: التحقق من عدم وجود ترجمة بنفس اللغة لنفس نوع حركة المخزون.
    #    - تستخدم دالة CRUD للتحقق من وجود ترجمة مكررة لنفس اللغة.
    if inventory_crud.get_inventory_transaction_type_translation(db, type_id=type_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"Translation for type ID {type_id} with language '{trans_in.language_code}' already exists.")
    
    # 3. استدعاء دالة CRUD لإنشاء الترجمة.
    return inventory_crud.create_inventory_transaction_type_translation(db=db, type_id=type_id, trans_in=trans_in)

def get_inventory_transaction_type_translation_by_id_and_lang(db: Session, type_id: int, language_code: str) -> InventoryTransactionTypeTranslation:
    """
    جلب ترجمة محددة لنوع حركة مخزون بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): ID نوع حركة المخزون الأم.
        language_code (str): رمز اللغة (مثل 'ar', 'en').

    Returns:
        InventoryTransactionTypeTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة المحددة.
    """
    # 1. جلب الترجمة باستخدام دالة CRUD.
    translation = inventory_crud.get_inventory_transaction_type_translation(db, type_id=type_id, language_code=language_code)
    
    # 2. التحقق من وجود الترجمة.
    if not translation:
        raise NotFoundException(detail=f"Translation for type ID {type_id} in language '{language_code}' not found.")
    
    return translation

def update_inventory_transaction_type_translation(db: Session, type_id: int, language_code: str, trans_in: inventory_schemas.InventoryTransactionTypeTranslationUpdate) -> InventoryTransactionTypeTranslation:
    """
    تحديث ترجمة نوع حركة مخزون موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): ID نوع حركة المخزون الأم.
        language_code (str): رمز اللغة للترجمة المراد تحديثها.
        trans_in (inventory_schemas.InventoryTransactionTypeTranslationUpdate): البيانات المراد تحديثها للترجمة.

    Returns:
        InventoryTransactionTypeTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة المحددة.
    """
    # 1. جلب الترجمة باستخدام دالة الخدمة (لضمان وجودها ومعالجة NotFoundException).
    db_translation = get_inventory_transaction_type_translation_by_id_and_lang(db, type_id, language_code)
    
    # 2. استدعاء دالة CRUD للتحديث.
    return inventory_crud.update_inventory_transaction_type_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_inventory_transaction_type_translation(db: Session, type_id: int, language_code: str):
    """
    حذف ترجمة نوع حركة مخزون معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): ID نوع حركة المخزون الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة المحددة.
    """
    # 1. جلب الترجمة باستخدام دالة الخدمة (لضمان وجودها).
    db_translation = get_inventory_transaction_type_translation_by_id_and_lang(db, type_id, language_code)
    
    # 2. استدعاء دالة CRUD للحذف الصارم.
    inventory_crud.delete_inventory_transaction_type_translation(db=db, db_translation=db_translation)
    return {"message": "Inventory transaction type translation deleted successfully."}
