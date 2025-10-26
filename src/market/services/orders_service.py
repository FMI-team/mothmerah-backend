# backend\src\market\services\orders_service.py

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from datetime import datetime,  timezone # استخدام timezone لجعل التواريخ aware

# استيراد المودلز
from src.market.models import orders_models as models_market
# استيراد المودلز من Lookups
from src.lookups.models import (
    OrderStatus, OrderStatusTranslation,
    PaymentStatus, PaymentStatusTranslation,
    OrderItemStatus, OrderItemStatusTranslation,
    Currency#, Address # لاستخدامها في التحقق من وجود FKs
)
# استيراد Schemas
from src.market.schemas import order_schemas as schemas
# استيراد دوال الـ CRUD
from src.market.crud import orders_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

from src.lookups.schemas import lookups_schemas as schemas_lookups

# استيراد الخدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.products.services.packaging_service import get_packaging_option_details # للتحقق من خيار التعبئة
from src.products.services.product_service import get_product_by_id_for_user # للتحقق من ملكية المنتج
from src.pricing.services.pricing_service import get_active_price # لحساب السعر الفعال
from src.users.services.core_service import (get_address_by_id, # للتحقق من وجود العناوين
    get_user_profile) # للتحقق من وجود البائع في Order

# TODO: استيراد خدمة المخزون
from src.products.services.inventory_service import adjust_stock_level # <-- أضف هذا الاستيراد

# TODO: هـام (REQ-FUN-077): حفظ محتويات سلة التسوق للمستخدم المسجل ليتمكن من العودة إليها لاحقًا.
# هذا يتطلب إضافة جدول/مودل جديد لسلة التسوق الدائمة (مثلاً 'shopping_carts' و 'shopping_cart_items').
# سيشمل ذلك CRUD وخدمة منفصلة لإدارة السلة،
# ومن ثم يمكن لـ create_new_order استهلاك بيانات من هذه السلة الدائمة بدلاً من استقبالها مباشرة كـ OrderCreate.



# ==========================================================
# --- خدمات الطلبات (Order) ---
# ==========================================================

def calculate_order_amounts(items_in: List[schemas.OrderItemCreate]) -> dict:
    """
    يحسب المبالغ المالية الإجمالية للطلب بناءً على بنود الطلب المقدمة.
    Args:
        items_in (List[schemas.OrderItemCreate]): قائمة ببنود الطلب التي يطلبها المشتري.
    Returns:
        dict: قاموس يحتوي على total_amount_before_discount, discount_amount,
              total_amount_after_discount, vat_amount, final_total_amount.
    """
    total_before_discount = Decimal(0)
    total_discount = Decimal(0)

    for item in items_in:
        item_total = Decimal(str(item.quantity_ordered)) * Decimal(str(item.unit_price_at_purchase))
        # TODO: إذا كان هناك discount_amount على مستوى البند، يجب إدراجه هنا
        total_before_discount += item_total
        # TODO: يتم حساب الخصم الفعلي على مستوى السلة أو الطلب بعد تجميع البنود
        #       هنا نفترض أن unit_price_at_purchase قد جاء بعد تطبيق خصومات الكمية
        #       إذا كان هناك خصم عام على الطلب، فيجب حساب discount_amount بناءً عليه.

    total_amount_after_discount = total_before_discount - total_discount
    
    # TODO: حساب VAT (ضريبة القيمة المضافة) بناءً على قواعد العمل (مثلاً 15% في السعودية)
    #       أو إذا كان VAT مضمناً في السعر بالفعل.
    vat_rate = Decimal('0.15') # مثال: 15%
    vat_amount = total_amount_after_discount * vat_rate
    
    final_total_amount = total_amount_after_discount + vat_amount

    return {
        'total_amount_before_discount': float(total_before_discount),
        'discount_amount': float(total_discount),
        'total_amount_after_discount': float(total_amount_after_discount),
        'vat_amount': float(vat_amount),
        'final_total_amount': float(final_total_amount)
    }

def create_new_order(db: Session, order_in: schemas.OrderCreate, current_user: User) -> models_market.Order:
    """
    خدمة لإنشاء طلب شراء مباشر جديد.
    تتضمن التحقق من المخزون، حساب الأسعار، وتعيين الحالة الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_in (schemas.OrderCreate): بيانات الطلب للإنشاء، بما في ذلك بنود الطلب.
        current_user (User): المستخدم الحالي (المشتري).

    Returns:
        models_market.Order: كائن الطلب الذي تم إنشاؤه.

    Raises:
        BadRequestException: إذا كانت البيانات غير صالحة (مثلاً كميات صفرية).
        NotFoundException: إذا لم يتم العثور على منتج أو عنوان أو عملة أو بائع.
        ForbiddenException: إذا كانت الكمية المطلوبة أكبر من المتاح في المخزون.
        ConflictException: إذا لم يتم العثور على حالة الطلب الأولية أو حالة بنود الطلب.
    """
    # 1. التحقق من وجود العناوين
    if order_in.shipping_address_id:
        get_address_by_id(db, order_in.shipping_address_id)
    if order_in.billing_address_id:
        get_address_by_id(db, order_in.billing_address_id)

    # 2. التحقق من العملة
    currency_exists = db.query(Currency).filter(Currency.currency_code == order_in.currency_code).first()
    if not currency_exists:
        raise NotFoundException(detail=f"رمز العملة '{order_in.currency_code}' غير صالح.")

    # 3. التحقق من البائع في كل بند وحساب الأسعار وتوفر المخزون
    initial_order_items_data = []
    total_amount_before_discount_calc = Decimal(0)
    total_discount_calc = Decimal(0) # TODO: حساب الخصم العام للطلب (إذا كان موجوداً)

    # جلب حالة بند الطلب الافتراضية
    default_item_status = db.query(OrderItemStatus).filter(OrderItemStatus.status_name_key == "NEW").first()
    if not default_item_status:
        raise ConflictException(detail="حالة بند الطلب الافتراضية 'NEW' غير موجودة.")

    for item_in in order_in.items:
        # أ. التحقق من وجود خيار التعبئة والبائع
        packaging_option = get_packaging_option_details(db, item_in.product_packaging_option_id)
        seller_for_item = get_user_profile(db, item_in.seller_user_id) # البائع لهذا البند
        if not seller_for_item:
            raise NotFoundException(detail=f"البائع بمعرف {item_in.seller_user_id} لبند المنتج غير موجود.")

        # ب. التحقق من توفر المخزون وحجزه
        # هذا التحقق تم مسبقاً، هنا نقوم بخصم الكمية
        from src.products.crud.inventory_crud import get_or_create_inventory_item # استيراد مباشر لـ CRUD فقط للتحقق الأولي
        inventory_item = get_or_create_inventory_item(db, item_in.product_packaging_option_id, item_in.seller_user_id)
        if inventory_item.available_quantity < item_in.quantity_ordered:
            raise ForbiddenException(detail=f"الكمية المطلوبة من المنتج '{packaging_option.packaging_option_name_key}' ({item_in.quantity_ordered}) أكبر من الكمية المتاحة في المخزون ({inventory_item.available_quantity}).")
        
        # ج. حساب السعر الفعلي للبند (باستخدام خدمة الأسعار الديناميكية)
        effective_unit_price = get_active_price(db, item_in.product_packaging_option_id, item_in.quantity_ordered)
        item_total_price = effective_unit_price * item_in.quantity_ordered

        initial_order_items_data.append(schemas.OrderItemCreate(
            product_packaging_option_id=item_in.product_packaging_option_id,
            seller_user_id=item_in.seller_user_id,
            quantity_ordered=item_in.quantity_ordered,
            unit_price_at_purchase=effective_unit_price,
            total_price_for_item=item_total_price,
            item_status_id=default_item_status.item_status_id,
            notes=item_in.notes
        ))
        total_amount_before_discount_calc += Decimal(str(item_total_price)) # يتم تجميع الإجمالي قبل أي خصومات عامة

    # 4. حساب المبالغ النهائية للطلب
    calculated_amounts = calculate_order_amounts(initial_order_items_data)

    # 5. جلب الحالة الأولية للطلب
    initial_order_status = db.query(OrderStatus).filter(OrderStatus.status_name_key == "NEW").first()
    if not initial_order_status:
        raise ConflictException(detail="حالة الطلب الأولية 'NEW' غير موجودة.")

    # 6. توليد رقم مرجعي فريد للطلب
    order_reference_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{UUID(bytes=os.urandom(8)).hex[:8].upper()}"
    # TODO: يجب أن يكون هناك آلية أكثر قوة لتوليد أرقام مرجعية فريدة وتجنب التكرار المحتمل على المدى الطويل

    # 7. استدعاء CRUD لإنشاء الطلب وبنوده.
    db_order = orders_crud.create_order(
        db=db,
        order_in=order_in,
        buyer_user_id=current_user.user_id,
        order_reference_number=order_reference_number,
        initial_status_id=initial_order_status.order_status_id,
        calculated_amounts=calculated_amounts
    )

    # 8. تسجيل أول حركة في سجل حالة الطلب
    orders_crud.create_order_status_history(
        db=db,
        order_id=db_order.order_id,
        old_status_id=None, # لا يوجد حالة سابقة
        new_status_id=initial_order_status.order_status_id,
        changed_by_user_id=current_user.user_id,
        notes="الطلب تم إنشاؤه."
    )
    
    # 9. خصم الكميات من المخزون بعد تأكيد الطلب ونجاح الإنشاء (REQ-FUN-090).
    #    - يتم استدعاء adjust_stock_level لكل بند في الطلب.
    for item in db_order.items:
        # إنشاء schema تعديل المخزون (بكمية سالبة)
        stock_adjustment = inventory_schemas.StockAdjustmentCreate(
            product_packaging_option_id=item.product_packaging_option_id,
            change_in_quantity=-float(item.quantity_ordered), # الكمية بالسالب لخصمها
            reason_notes=f"خصم بسبب الطلب رقم: {db_order.order_reference_number}"
        )
        # استدعاء خدمة تعديل المخزون
        # يجب تمرير المستخدم الذي يقوم بالخصم (نظام أو البائع في هذه الحالة)
        # TODO: يمكن تحسين هذه الدالة في inventory_service.adjust_stock_level لتقبل SystemUser بدلاً من CurrentUser.
        adjust_stock_level(db, stock_adjustment, current_user) # <-- تم تنفيذ هذا الـ TODO

    db.commit() # تأكيد العملية بالكامل
    db.refresh(db_order)

    # TODO: هـام (REQ-FUN-082): التكامل الفعلي مع وحدة الدفع والمحفظة (Module 8).
    # يتطلب هذا بناء خدمات وحدة الدفع نفسها للتعامل مع بوابات الدفع الخارجية.
    # هنا يجب أن تبدأ عملية الدفع بناءً على طريقة الدفع المختارة،
    # وتنتظر التأكيد قبل تحديث حالة الطلب إلى "تم الدفع" أو "قيد التجهيز".
    # مثال: payment_service.initiate_payment(db, db_order.order_id, db_order.final_total_amount, order_in.payment_method_id, current_user)

    # TODO: هـام (REQ-FUN-103): إخطار وحدة الإشعارات (Module 11) بوجود طلب جديد.

    return db_order

def get_order_details(db: Session, order_id: UUID, current_user: User) -> models_market.Order:
    """
    خدمة لجلب تفاصيل طلب واحد بالـ ID، مع التحقق من صلاحيات المشتري أو البائع أو المسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_id (UUID): معرف الطلب المطلوب.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.Order: كائن الطلب المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الطلب.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية الطلب.
    """
    db_order = orders_crud.get_order(db, order_id=order_id)
    if not db_order:
        raise NotFoundException(detail=f"الطلب بمعرف {order_id} غير موجود.")

    # التحقق من الصلاحيات: المشتري أو البائع أو المسؤول
    is_buyer = db_order.buyer_user_id == current_user.user_id
    is_seller_of_any_item = any(item.seller_user_id == current_user.user_id for item in db_order.items)
    is_admin = any(p.permission_name_key == "ADMIN_ORDER_VIEW_ANY" for p in current_user.default_role.permissions)

    if not (is_buyer or is_seller_of_any_item or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل هذا الطلب.")
    
    return db_order

def get_my_orders(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[models_market.Order]:
    """
    خدمة لجلب جميع الطلبات التي يكون المستخدم الحالي طرفًا فيها (كمشتري أو بائع).

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_market.Order]: قائمة بكائنات الطلبات.
    """
    # جلب الطلبات التي هو المشتري فيها
    orders_as_buyer = orders_crud.get_all_orders(db, buyer_user_id=current_user.user_id, skip=skip, limit=limit)
    
    # جلب الطلبات التي هو بائع لبنود فيها (حتى لو لم يكن هو البائع الرئيسي في جدول الطلبات)
    # TODO: هذا يتطلب استعلامًا أكثر تعقيدًا لضم جدول OrderItem
    #       أو دالة CRUD منفصلة لجلب الطلبات التي يكون فيها المستخدم بائعاً لبنود معينة.
    #       لأغراض MVP، يمكن دمج القوائم بعد جلبها بشكل منفصل.
    
    # حالياً، get_all_orders تقوم بالتصفية على seller_user_id في الطلب الرئيسي
    # وهذا لا يلتقط الطلبات التي تحتوي على بنود من بائعين متعددين.
    # يجب تحسين get_all_orders في CRUD لتدعم البحث عن seller_user_id في order_items
    orders_as_seller = orders_crud.get_all_orders(db, seller_user_id=current_user.user_id, skip=skip, limit=limit)

    # دمج القوائم وإزالة التكرارات
    all_orders = {order.order_id: order for order in orders_as_buyer}
    all_orders.update({order.order_id: order for order in orders_as_seller})

    # TODO: يجب أن تكون تصفية الترقيم والحد (skip, limit) مطبقة بعد الدمج.
    #       لتحسين الأداء، يجب أن يتم الاستعلام في CRUD ليعيد الطلبات التي يكون المستخدم فيها مشترياً أو بائعاً لبند.

    return list(all_orders.values())

def get_all_orders_for_admin(db: Session, skip: int = 0, limit: int = 100) -> List[models_market.Order]:
    """
    خدمة [للمسؤول] لجلب جميع الطلبات في النظام.

    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_market.Order]: قائمة بكائنات الطلبات.
    """
    return orders_crud.get_all_orders(db, skip=skip, limit=limit)

def update_order(db: Session, order_id: UUID, order_in: schemas.OrderUpdate, current_user: User) -> models_market.Order:
    """
    خدمة لتحديث طلب موجود.
    تتضمن التحقق من الصلاحيات (مالك أو مسؤول).

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_id (UUID): معرف الطلب المراد تحديثه.
        order_in (schemas.OrderUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.Order: كائن الطلب المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الطلب.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بتحديث الطلب.
        BadRequestException: إذا كانت الحالة الجديدة غير موجودة.
    """
    db_order = get_order_details(db, order_id, current_user) # يتحقق من الوجود والصلاحية

    # التحقق من وجود الحالة الجديدة إذا تم تحديثها
    if order_in.order_status_id:
        new_status = orders_crud.get_order_status(db, order_in.order_status_id)
        if not new_status:
            raise BadRequestException(detail=f"حالة الطلب بمعرف {order_in.order_status_id} غير موجودة.")
        
        # TODO: منطق عمل: التحقق من الانتقالات المسموح بها بين حالات الطلب (Order State Machine).
        #       مثلاً، لا يمكن الانتقال من "ملغى" إلى "تم الشحن".
        #       يمكن تعريف آلة حالة في مكان مركزي.

    updated_order = orders_crud.update_order(db=db, db_order=db_order, order_in=order_in)

    # إذا تم تحديث الحالة، سجل ذلك في تاريخ الحالة
    if order_in.order_status_id and order_in.order_status_id != db_order.order_status_id:
        orders_crud.create_order_status_history(
            db=db,
            order_id=db_order.order_id,
            old_status_id=db_order.order_status_id,
            new_status_id=order_in.order_status_id,
            changed_by_user_id=current_user.user_id,
            notes=f"تغيير الحالة بواسطة المستخدم ({current_user.user_id})"
        )
        # TODO: إرسال إشعار (وحدة الإشعارات) حول تغيير حالة الطلب

    return updated_order

def cancel_order(db: Session, order_id: UUID, current_user: User, reason: Optional[str] = None) -> models_market.Order:
    """
    خدمة لإلغاء الطلب (من قبل المشتري أو البائع/المسؤول).
    تتضمن التحقق من الصلاحيات، المرحلة المسموح بها للإلغاء، وعكس العمليات (المخزون/المدفوعات).

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_id (UUID): معرف الطلب المراد إلغاؤه.
        current_user (User): المستخدم الحالي.
        reason (Optional[str]): سبب الإلغاء.

    Returns:
        models_market.Order: كائن الطلب بعد تحديث حالته إلى "ملغى".

    Raises:
        NotFoundException: إذا لم يتم العثور على الطلب.
        ForbiddenException: إذا كان المستخدم غير مصرح له بالإلغاء أو كانت الحالة لا تسمح بالإلغاء.
        ConflictException: إذا لم يتم العثور على حالة الإلغاء.
    """
    db_order = get_order_details(db, order_id, current_user)

    # 1. التحقق من صلاحية المستخدم للإلغاء (مالك الطلب أو بائع لأحد البنود أو مسؤول)
    is_buyer = db_order.buyer_user_id == current_user.user_id
    is_seller_of_any_item = any(item.seller_user_id == current_user.user_id for item in db_order.items)
    is_admin = any(p.permission_name_key == "ADMIN_ORDER_MANAGE_ANY" for p in current_user.default_role.permissions) # صلاحية إلغاء الطلب كمسؤول

    if not (is_buyer or is_seller_of_any_item or is_admin):
        raise ForbiddenException(detail="غير مصرح لك بإلغاء هذا الطلب.")

    # 2. التحقق من المرحلة المسموح بها للإلغاء (Order State Machine)
    # TODO: تحديد الحالات التي لا يُسمح فيها بالإلغاء (مثلاً بعد الشحن).
    # current_status_key = db_order.status.status_name_key # يجب أن تكون محملة
    # if current_status_key in ["SHIPPED", "DELIVERED", "COMPLETED"]:
    #     raise BadRequestException(detail="لا يمكن إلغاء الطلب في حالته الحالية.")

    # 3. جلب حالة الإلغاء المناسبة (مثلاً 'CANCELED_BY_BUYER', 'CANCELED_BY_SELLER', 'CANCELED_BY_ADMIN')
    canceled_status_key = "CANCELED" # افتراضيًا
    if is_buyer: canceled_status_key = "CANCELED_BY_BUYER"
    elif is_seller_of_any_item: canceled_status_key = "CANCELED_BY_SELLER"
    elif is_admin: canceled_status_key = "CANCELED_BY_ADMIN"

    canceled_status = db.query(OrderStatus).filter(OrderStatus.status_name_key == canceled_status_key).first()
    if not canceled_status:
        raise ConflictException(detail=f"حالة الإلغاء '{canceled_status_key}' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    # 4. تحديث حالة الطلب
    orders_crud.update_order_status(db=db, db_order=db_order, new_status_id=canceled_status.order_status_id)

    # 5. عكس العمليات: إعادة المخزون واسترداد المدفوعات
    for item in db_order.items:
        # TODO: استعادة الكميات إلى المخزون (InventoryService)
        #       مثلاً: inventory_service.adjust_stock_level(db, item.product_packaging_option_id, item.quantity_ordered, ...)
        pass
    
    # TODO: بدء عملية استرداد المدفوعات (PaymentService)
    #       مثلاً: payment_service.initiate_refund(db, db_order.order_id, db_order.final_total_amount, ...)

    # 6. تسجيل التغيير في تاريخ الحالة
    orders_crud.create_order_status_history(
        db=db,
        order_id=db_order.order_id,
        old_status_id=db_order.order_status_id, # الحالة قبل الإلغاء
        new_status_id=canceled_status.order_status_id,
        changed_by_user_id=current_user.user_id,
        notes=reason or f"الطلب تم إلغاؤه بواسطة {current_user.user_id}"
    )

    # TODO: إرسال إشعارات (وحدة الإشعارات) للطرف الآخر بأن الطلب تم إلغاؤه

    return db_order

def get_order_item_details_service(db: Session, order_item_id: int, current_user: Optional[User] = None) -> models_market.OrderItem:
    """
    خدمة لجلب تفاصيل بند طلب واحد بالـ ID، مع التحقق من صلاحيات المستخدم.
    المستخدم يجب أن يكون المشتري (لصاحب الطلب الأم) أو البائع (لصاحب البند) أو مسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_item_id (int): معرف بند الطلب المطلوب.
        current_user (Optional[User]): المستخدم الحالي.

    Returns:
        models_market.OrderItem: كائن بند الطلب المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على بند الطلب.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية بند الطلب.
    """
    db_item = orders_crud.get_order_item(db, order_item_id=order_item_id)
    if not db_item:
        raise NotFoundException(detail=f"بند الطلب بمعرف {order_item_id} غير موجود.")

    # التحقق من الصلاحيات: المشتري (صاحب الطلب الأم) أو البائع (صاحب البند) أو مسؤول
    # يجب تحميل الطلب الأم هنا للتحقق من buyer_user_id
    db_order_parent = orders_crud.get_order(db, order_id=db_item.order_id)
    if not db_order_parent: # هذا لا ينبغي أن يحدث في نظام سليم
        raise NotFoundException(detail=f"الطلب الأم لبند الطلب بمعرف {order_item_id} غير موجود.")

    is_buyer_of_order = db_order_parent.buyer_user_id == current_user.user_id if current_user else False
    is_seller_of_item = db_item.seller_user_id == current_user.user_id if current_user else False
    is_admin = False
    if current_user:
        is_admin = any(p.permission_name_key == "ADMIN_ORDER_VIEW_ANY" for p in current_user.default_role.permissions)

    if not (is_buyer_of_order or is_seller_of_item or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل بند الطلب هذا.")
    
    return db_item


# ==========================================================
# --- خدمات حالات الطلب (OrderStatus) ---
# ==========================================================

def create_order_status_service(db: Session, status_in: schemas_lookups.OrderStatusCreate) -> OrderStatus:
    """
    خدمة لإنشاء حالة طلب جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas_lookups.OrderStatusCreate): بيانات الحالة للإنشاء.
 
    Returns:
        OrderStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    if db.query(OrderStatus).filter(OrderStatus.status_name_key == status_in.status_name_key).first():
        raise ConflictException(detail=f"حالة الطلب بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return orders_crud.create_order_status(db=db, status_in=status_in)

def get_order_status_details(db: Session, order_status_id: int) -> OrderStatus:
    """
    خدمة لجلب حالة طلب بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة.

    Returns:
        OrderStatus: كائن الحالة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
    """
    status_obj = orders_crud.get_order_status(db, order_status_id=order_status_id)
    if not status_obj:
        raise NotFoundException(detail=f"حالة الطلب بمعرف {order_status_id} غير موجودة.")
    return status_obj

def get_all_order_statuses_service(db: Session) -> List[OrderStatus]:
    """
    خدمة لجلب جميع حالات الطلب المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[OrderStatus]: قائمة بكائنات الحالات.
    """
    return orders_crud.get_all_order_statuses(db)

def update_order_status_service(db: Session, order_status_id: int, status_in: schemas_lookups.OrderStatusUpdate) -> OrderStatus:
    """
    خدمة لتحديث حالة طلب موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas_lookups.OrderStatusUpdate): البيانات المراد تحديثها.

    Returns:
        OrderStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_order_status_details(db, order_status_id)
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        if db.query(OrderStatus).filter(OrderStatus.status_name_key == status_in.status_name_key).first():
            raise ConflictException(detail=f"حالة الطلب بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return orders_crud.update_order_status(db=db, db_status=db_status, status_in=status_in)

def delete_order_status_service(db: Session, order_status_id: int):
    """
    خدمة لحذف حالة طلب (حذف صارم).
    تتضمن التحقق من عدم وجود طلبات مرتبطة بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ForbiddenException: إذا كانت الحالة مستخدمة حاليًا بواسطة أي طلبات.
    """
    db_status = get_order_status_details(db, order_status_id)
    if db.query(models_market.Order).filter(models_market.Order.order_status_id == order_status_id).count() > 0:
        raise ForbiddenException(detail=f"لا يمكن حذف حالة الطلب بمعرف {order_status_id} لأنها تستخدم من قبل طلبات موجودة.")
    orders_crud.delete_order_status(db=db, db_status=db_status)
    return {"message": "تم حذف حالة الطلب بنجاح."}


# ==========================================================
# --- خدمات ترجمات حالات الطلب (OrderStatusTranslation) ---
# ==========================================================

def create_order_status_translation_service(db: Session, order_status_id: int, trans_in: schemas_lookups.OrderStatusTranslationCreate) -> OrderStatusTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لحالة طلب معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة الأم.
        trans_in (schemas.OrderStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        OrderStatusTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة الأم.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    get_order_status_details(db, order_status_id)
    if orders_crud.get_order_status_translation(db, order_status_id=order_status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة لحالة الطلب بمعرف {order_status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")
    return orders_crud.create_order_status_translation(db=db, order_status_id=order_status_id, trans_in=trans_in)

def get_order_status_translation_details(db: Session, order_status_id: int, language_code: str) -> OrderStatusTranslation:
    """
    خدمة لجلب ترجمة حالة طلب محددة بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة.

    Returns:
        OrderStatusTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = orders_crud.get_order_status_translation(db, order_status_id=order_status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة الطلب بمعرف {order_status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_order_status_translation_service(db: Session, order_status_id: int, language_code: str, trans_in: schemas_lookups.OrderStatusTranslationUpdate) -> OrderStatusTranslation:
    """
    خدمة لتحديث ترجمة حالة طلب موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas_lookups.OrderStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        OrderStatusTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_order_status_translation_details(db, order_status_id, language_code)
    return orders_crud.update_order_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_order_status_translation_service(db: Session, order_status_id: int, language_code: str):
    """
    خدمة لحذف ترجمة حالة طلب معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_order_status_translation_details(db, order_status_id, language_code)
    orders_crud.delete_order_status_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة حالة الطلب بنجاح."}


# ==========================================================
# --- خدمات حالات الدفع (PaymentStatus) ---
# ==========================================================

def create_payment_status_service(db: Session, status_in: schemas_lookups.PaymentStatusCreate) -> PaymentStatus:
    """
    خدمة لإنشاء حالة دفع جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas_lookups.PaymentStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        PaymentStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    if db.query(PaymentStatus).filter(PaymentStatus.status_name_key == status_in.status_name_key).first():
        raise ConflictException(detail=f"حالة الدفع بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return orders_crud.create_payment_status(db=db, status_in=status_in)

def get_payment_status_details(db: Session, payment_status_id: int) -> PaymentStatus:
    """
    خدمة لجلب حالة دفع بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة.

    Returns:
        PaymentStatus: كائن الحالة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
    """
    status_obj = orders_crud.get_payment_status(db, payment_status_id=payment_status_id)
    if not status_obj:
        raise NotFoundException(detail=f"حالة الدفع بمعرف {payment_status_id} غير موجودة.")
    return status_obj

def get_all_payment_statuses_service(db: Session) -> List[PaymentStatus]:
    """
    خدمة لجلب جميع حالات الدفع المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[PaymentStatus]: قائمة بكائنات الحالات.
    """
    return orders_crud.get_all_payment_statuses(db)

def update_payment_status_service(db: Session, payment_status_id: int, status_in: schemas_lookups.PaymentStatusUpdate) -> PaymentStatus:
    """
    خدمة لتحديث حالة دفع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas_lookups.PaymentStatusUpdate): البيانات المراد تحديثها.

    Returns:
        PaymentStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_payment_status_details(db, payment_status_id)
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        if db.query(PaymentStatus).filter(PaymentStatus.status_name_key == status_in.status_name_key).first():
            raise ConflictException(detail=f"حالة الدفع بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return orders_crud.update_payment_status(db=db, db_status=db_status, status_in=status_in)

def delete_payment_status_service(db: Session, payment_status_id: int):
    """
    خدمة لحذف حالة دفع (حذف صارم).
    تتضمن التحقق من عدم وجود طلبات مرتبطة بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ForbiddenException: إذا كانت الحالة مستخدمة حاليًا بواسطة أي طلبات.
    """
    db_status = get_payment_status_details(db, payment_status_id)
    # TODO: التحقق من عدم وجود طلبات (Order) تستخدم payment_status_id هذا
    #       هذا يتطلب استيراد Order model
    # from src.market.models.orders_models import Order
    # if db.query(Order).filter(Order.payment_status_id == payment_status_id).count() > 0:
    #     raise ForbiddenException(detail=f"لا يمكن حذف حالة الدفع بمعرف {payment_status_id} لأنها تستخدم من قبل طلبات موجودة.")
    orders_crud.delete_payment_status(db=db, db_status=db_status)
    return {"message": "تم حذف حالة الدفع بنجاح."}


# ==========================================================
# --- خدمات ترجمات حالات الدفع (PaymentStatusTranslation) ---
# ==========================================================

def create_payment_status_translation_service(db: Session, payment_status_id: int, trans_in: schemas_lookups.PaymentStatusTranslationCreate) -> PaymentStatusTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لحالة دفع معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة الأم.
        trans_in (schemas_lookups.PaymentStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        PaymentStatusTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة الأم.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    get_payment_status_details(db, payment_status_id)
    if orders_crud.get_payment_status_translation(db, payment_status_id=payment_status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة لحالة الدفع بمعرف {payment_status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")
    return orders_crud.create_payment_status_translation(db=db, payment_status_id=payment_status_id, trans_in=trans_in)

def get_payment_status_translation_details(db: Session, payment_status_id: int, language_code: str) -> PaymentStatusTranslation:
    """
    خدمة لجلب ترجمة حالة دفع محددة بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة.

    Returns:
        PaymentStatusTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = orders_crud.get_payment_status_translation(db, payment_status_id=payment_status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة الدفع بمعرف {payment_status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_payment_status_translation_service(db: Session, payment_status_id: int, language_code: str, trans_in: schemas_lookups.PaymentStatusTranslationUpdate) -> PaymentStatusTranslation:
    """
    خدمة لتحديث ترجمة حالة دفع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas_lookups.PaymentStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        PaymentStatusTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_payment_status_translation_details(db, payment_status_id, language_code)
    return orders_crud.update_payment_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_payment_status_translation_service(db: Session, payment_status_id: int, language_code: str):
    """
    خدمة لحذف ترجمة حالة دفع معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        payment_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_payment_status_translation_details(db, payment_status_id, language_code)
    orders_crud.delete_payment_status_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة حالة الدفع بنجاح."}


# ==========================================================
# --- خدمات حالات بنود الطلب (OrderItemStatus) ---
# ==========================================================

def create_order_item_status_service(db: Session, status_in: schemas_lookups.OrderItemStatusCreate) -> OrderItemStatus:
    """
    خدمة لإنشاء حالة بند طلب جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas_lookups.OrderItemStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        OrderItemStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    if db.query(OrderItemStatus).filter(OrderItemStatus.status_name_key == status_in.status_name_key).first():
        raise ConflictException(detail=f"حالة بند الطلب بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return orders_crud.create_order_item_status(db=db, status_in=status_in)

def get_order_item_status_details(db: Session, item_status_id: int) -> OrderItemStatus:
    """
    خدمة لجلب حالة بند طلب بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_status_id (int): معرف الحالة.

    Returns:
        OrderItemStatus: كائن الحالة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
    """
    status_obj = orders_crud.get_order_item_status(db, item_status_id=item_status_id)
    if not status_obj:
        raise NotFoundException(detail=f"حالة بند الطلب بمعرف {item_status_id} غير موجودة.")
    return status_obj

def get_all_order_item_statuses_service(db: Session) -> List[OrderItemStatus]:
    """
    خدمة لجلب جميع حالات بنود الطلب المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[OrderItemStatus]: قائمة بكائنات الحالات.
    """
    return orders_crud.get_all_order_item_statuses(db)

def update_order_item_status_service(db: Session, item_status_id: int, status_in: schemas_lookups.OrderItemStatusUpdate) -> OrderItemStatus:
    """
    خدمة لتحديث حالة بند طلب موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas_lookups.OrderItemStatusUpdate): البيانات المراد تحديثها.

    Returns:
        OrderItemStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_order_item_status_details(db, item_status_id)
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        if db.query(OrderItemStatus).filter(OrderItemStatus.status_name_key == status_in.status_name_key).first():
            raise ConflictException(detail=f"حالة بند الطلب بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return orders_crud.update_order_item_status(db=db, db_status=db_status, status_in=status_in)

def delete_order_item_status_service(db: Session, item_status_id: int):
    """
    خدمة لحذف حالة بند طلب (حذف صارم).
    تتضمن التحقق من عدم وجود بنود طلبات مرتبطة بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        item_status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ForbiddenException: إذا كانت الحالة مستخدمة حاليًا بواسطة أي بنود طلبات.
    """
    db_status = get_order_item_status_details(db, item_status_id)
    # TODO: التحقق من عدم وجود OrderItem تستخدم item_status_id هذا
    # from src.market.models.orders_models import OrderItem
    # if db.query(OrderItem).filter(OrderItem.item_status_id == item_status_id).count() > 0:
    #     raise ForbiddenException(detail=f"لا يمكن حذف حالة بند الطلب بمعرف {item_status_id} لأنها تستخدم من قبل بنود طلبات موجودة.")
    orders_crud.delete_order_item_status(db=db, db_status=db_status)
    return {"message": "تم حذف حالة بند الطلب بنجاح."}

    