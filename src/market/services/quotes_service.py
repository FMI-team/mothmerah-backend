# backend\src\market\services\quotes_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone # لاستخدام التواريخ والأوقات

# استيراد المودلز
from src.market.models import quotes_models as models_market
# استيراد المودلز من Lookups
from src.lookups.models import QuoteStatus, QuoteStatusTranslation, RfqStatus
# استيراد Schemas
from src.market.schemas import quote_schemas as schemas
# استيراد دوال الـ CRUD
from src.market.crud import quotes_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات
from src.lookups.schemas import lookups_schemas as schemas_lookups

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.users.services.core_service import get_user_profile # للتحقق من وجود المشتري/البائع
from src.market.services.rfqs_service import get_rfq_details, get_rfq_item_details_service # للتحقق من وجود طلب RFQ
# from src.market.services.rfqs_service import get_rfq_item_details # للتحقق من وجود بند RFQ
# TODO: وحدة الإشعارات - (Module 11) لإرسال الإشعارات.
# TODO: وحدة إدارة الطلبات (orders_service) لإنشاء الطلب عند قبول عرض سعر.
from src.market.services.orders_service import create_new_order # <-- أضف هذا الاستيراد
from src.market.schemas import order_schemas # <-- أضف هذا الاستيراد للوصول لـ OrderCreate/OrderItemCreate

# ==========================================================
# --- خدمات عروض الأسعار (Quote) ---
# ==========================================================

def create_new_quote(db: Session, quote_in: schemas.QuoteCreate, current_user: User) -> models_market.Quote:
    """
    خدمة لإنشاء عرض سعر جديد بواسطة بائع استجابة لطلب RFQ.
    تتضمن التحقق من صحة البيانات، وجود الكيانات المرتبطة، وتعيين الحالة الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_in (schemas.QuoteCreate): بيانات عرض السعر للإنشاء، بما في ذلك بنود العرض.
        current_user (User): المستخدم الحالي (البائع مقدم العرض).

    Returns:
        models_market.Quote: كائن عرض السعر الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على طلب RFQ أو بند RFQ.
        ForbiddenException: إذا كان المستخدم غير مصرح له بتقديم عرض على هذا الـ RFQ (مثلاً ليس البائع المستهدف).
        BadRequestException: إذا كانت البيانات غير صالحة (مثلاً صلاحية العرض في الماضي، أو لا يوجد بنود).
        ConflictException: إذا لم يتم العثور على حالة عرض السعر الأولية.
    """
    # 1. التحقق من وجود طلب RFQ
    db_rfq = get_rfq_details(db, rfq_id=quote_in.rfq_id, current_user=current_user)
    # TODO: منطق عمل: التحقق من أن الـ RFQ لا يزال مفتوحًا لاستقبال العروض
    # if db_rfq.rfq_status.status_name_key != "OPEN":
    #     raise BadRequestException(detail="لا يمكن تقديم عرض سعر لطلب RFQ ليس في حالة مفتوحة.")

    # TODO: منطق عمل: التحقق من أن البائع مصرح له بتقديم عرض على هذا الـ RFQ (خاص/عام)
    #       (سيتطلب الوصول إلى تفاصيل توجيه الـ RFQ)

    # 2. التحقق من الموعد النهائي لتقديم العروض (يجب أن يكون RFQ_submission_deadline في المستقبل)
    if datetime.now(timezone.utc) > db_rfq.submission_deadline:
        raise BadRequestException(detail="لقد انتهى الموعد النهائي لتقديم عروض الأسعار لهذا الطلب.")

    # 3. التحقق من وجود بنود لعرض السعر
    if not quote_in.items:
        raise BadRequestException(detail="يجب أن يحتوي عرض السعر على بند واحد على الأقل.")

    # 4. التحقق من كل بند في العرض (rfq_item_id)
    for item_in in quote_in.items:
        rfq_item = get_rfq_item_details(db, rfq_item_id=item_in.rfq_item_id)
        # TODO: منطق عمل: التأكد من أن rfq_item_id ينتمي إلى الـ RFQ الصحيح (db_rfq.rfq_id == rfq_item.rfq_id)
        if rfq_item.rfq_id != db_rfq.rfq_id:
            raise BadRequestException(detail=f"بند الـ RFQ بمعرف {item_in.rfq_item_id} لا ينتمي إلى طلب RFQ هذا.")
        # TODO: منطق عمل: التأكد من أن جميع بنود الـ RFQ المطلوبة قد تم تسعيرها في العرض (اختياري، بناءً على قواعد العمل)

    # 5. حساب تاريخ انتهاء صلاحية العرض (expiry_timestamp) إذا تم تحديد validity_period_days
    if quote_in.validity_period_days:
        quote_in.expiry_timestamp = datetime.now(timezone.utc) + timedelta(days=quote_in.validity_period_days)
    elif not quote_in.expiry_timestamp: # إذا لم يتم تحديد أيام الصلاحية ولا تاريخ الانتهاء
        # TODO: يمكن تعيين صلاحية افتراضية هنا
        pass

    # 6. جلب الحالة الأولية لعرض السعر
    initial_quote_status = db.query(QuoteStatus).filter(QuoteStatus.status_name_key == "SUBMITTED").first()
    if not initial_quote_status:
        raise ConflictException(detail="حالة عرض السعر الأولية 'SUBMITTED' غير موجودة.")

    # 7. استدعاء CRUD لإنشاء عرض السعر وبنوده
    db_quote = quotes_crud.create_quote(
        db=db,
        quote_in=quote_in,
        seller_user_id=current_user.user_id,
        initial_status_id=initial_quote_status.quote_status_id
    )

    db.commit()
    db.refresh(db_quote)

    # TODO: إخطار المشتري (صاحب الـ RFQ) بوجود عرض سعر جديد (وحدة الإشعارات - Module 11)

    return db_quote

def get_quote_details(db: Session, quote_id: int, current_user: User) -> models_market.Quote:
    """
    خدمة لجلب تفاصيل عرض سعر واحد بالـ ID، مع التحقق من صلاحيات البائع مقدم العرض أو المشتري صاحب الـ RFQ أو المسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_id (int): معرف عرض السعر المطلوب.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.Quote: كائن عرض السعر المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على عرض السعر.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية عرض السعر.
    """
    db_quote = quotes_crud.get_quote(db, quote_id=quote_id)
    if not db_quote:
        raise NotFoundException(detail=f"عرض السعر بمعرف {quote_id} غير موجود.")

    # التحقق من الصلاحيات: البائع مقدم العرض، أو المشتري صاحب الـ RFQ، أو المسؤول
    is_seller = db_quote.seller_user_id == current_user.user_id
    is_rfq_buyer = db_quote.rfq.buyer_user_id == current_user.user_id # يتطلب تحميل rfq في العلاقة
    is_admin = any(p.permission_name_key == "ADMIN_QUOTE_VIEW_ANY" for p in current_user.default_role.permissions)

    if not (is_seller or is_rfq_buyer or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل عرض السعر هذا.")
    
    return db_quote

def get_quotes_for_my_rfq(db: Session, rfq_id: int, current_user: User, skip: int = 0, limit: int = 100) -> List[models_market.Quote]:
    """
    خدمة لجلب جميع عروض الأسعار المستلمة لطلب RFQ يخص المشتري الحالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_id (int): معرف طلب RFQ.
        current_user (User): المستخدم الحالي (المشتري صاحب الـ RFQ).
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_market.Quote]: قائمة بكائنات عروض الأسعار.

    Raises:
        NotFoundException: إذا لم يتم العثور على الـ RFQ.
        ForbiddenException: إذا لم يكن المستخدم هو مشتري الـ RFQ.
    """
    # 1. التحقق من وجود الـ RFQ وملكيته للمشتري
    db_rfq = get_rfq_details(db, rfq_id, current_user) # get_rfq_details تتحقق من ملكية المشتري للـ RFQ

    # 2. جلب عروض الأسعار لهذا الـ RFQ
    return quotes_crud.get_all_quotes(db, rfq_id=rfq_id, skip=skip, limit=limit)

def get_my_submitted_quotes(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[models_market.Quote]:
    """
    خدمة لجلب جميع عروض الأسعار التي قدمها البائع الحالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي (البائع مقدم العرض).
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_market.Quote]: قائمة بكائنات عروض الأسعار.
    """
    return quotes_crud.get_all_quotes(db, seller_user_id=current_user.user_id, skip=skip, limit=limit)

def update_quote(db: Session, quote_id: int, quote_in: schemas.QuoteUpdate, current_user: User) -> models_market.Quote:
    """
    خدمة لتحديث عرض سعر موجود.
    تتضمن التحقق من الصلاحيات (البائع مقدم العرض، المشتري صاحب الـ RFQ، أو المسؤول)
    ومراحل دورة حياة عرض السعر.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_id (int): معرف عرض السعر المراد تحديثه.
        quote_in (schemas.QuoteUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.Quote: كائن عرض السعر المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على عرض السعر.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بتحديث عرض السعر.
        BadRequestException: إذا كانت البيانات غير صالحة (مثلاً صلاحية العرض في الماضي، أو انتقال حالة غير مسموح به).
        ConflictException: إذا لم يتم العثور على حالة العرض الجديدة.
    """
    db_quote = get_quote_details(db, quote_id, current_user)

    # التحقق من أن عرض السعر لا يزال في حالة تسمح بالتعديل (مثلاً 'SUBMITTED')
    # TODO: آلة حالة (State Machine) لـ Quote: تحديد الانتقالات المسموح بها.
    #       لا يمكن تحديث عرض سعر تم قبوله أو رفضه.
    # if db_quote.quote_status.status_name_key not in ["SUBMITTED", "PENDING_REVIEW"]:
    #     raise BadRequestException(detail="لا يمكن تحديث عرض السعر هذا في حالته الحالية.")

    # التحقق من أن تاريخ الصلاحية الجديد لا يزال في المستقبل إذا تم تحديثه
    if quote_in.expiry_timestamp and quote_in.expiry_timestamp <= datetime.now(timezone.utc):
        raise BadRequestException(detail="تاريخ انتهاء صلاحية العرض يجب أن يكون في المستقبل.")

    # التحقق من وجود الحالة الجديدة إذا تم تحديثها
    if quote_in.quote_status_id:
        new_status = db.query(QuoteStatus).filter(QuoteStatus.quote_status_id == quote_in.quote_status_id).first()
        if not new_status:
            raise BadRequestException(detail=f"حالة عرض السعر بمعرف {quote_in.quote_status_id} غير موجودة.")
        # TODO: آلة حالة (State Machine) لـ Quote: التحقق من الانتقال المسموح به إلى الحالة الجديدة.

    return quotes_crud.update_quote(db=db, db_quote=db_quote, quote_in=quote_in)

def accept_quote(db: Session, quote_id: int, current_user: User) -> models_market.Quote:
    """
    خدمة لقبول عرض سعر (Quote) بواسطة المشتري.
    يؤدي القبول إلى إنشاء طلب شراء جديد وتحديث حالات الـ RFQ والعروض الأخرى.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_id (int): معرف عرض السعر المراد قبوله.
        current_user (User): المستخدم الحالي (يجب أن يكون مشتري الـ RFQ).

    Returns:
        models_market.Quote: كائن عرض السعر الذي تم قبوله.

    Raises:
        NotFoundException: إذا لم يتم العثور على عرض السعر.
        ForbiddenException: إذا لم يكن المستخدم مشتري الـ RFQ أو غير مصرح له.
        BadRequestException: إذا كان عرض السعر منتهي الصلاحية أو ليس في حالة تسمح بالقبول.
        ConflictException: إذا لم يتم العثور على حالات الدفع/الطلب/عرض السعر المطلوبة.
    """
    db_quote = get_quote_details(db, quote_id, current_user)

    # 1. التحقق من صلاحية المستخدم (يجب أن يكون مشتري الـ RFQ أو مسؤول)
    if db_quote.rfq.buyer_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_QUOTE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بقبول عرض السعر هذا.")

    # 2. التحقق من أن عرض السعر لا يزال صالحًا وفي حالة تسمح بالقبول
    if db_quote.expiry_timestamp and db_quote.expiry_timestamp < datetime.now(timezone.utc):
        raise BadRequestException(detail="عرض السعر هذا منتهي الصلاحية ولا يمكن قبوله.")
    # TODO: آلة حالة (State Machine) لـ Quote: يجب أن يكون في حالة 'مقدم' أو 'قيد المراجعة'.
    # if db_quote.quote_status.status_name_key != "SUBMITTED":
    #     raise BadRequestException(detail="لا يمكن قبول عرض السعر هذا في حالته الحالية.")

    # 3. جلب الحالات المطلوبة
    accepted_status = db.query(QuoteStatus).filter(QuoteStatus.status_name_key == "ACCEPTED").first()
    rejected_status = db.query(QuoteStatus).filter(QuoteStatus.status_name_key == "REJECTED").first()
    rfq_closed_status = db.query(RfqStatus).filter(RfqStatus.status_name_key == "CLOSED_AWARDED").first() # حالة الـ RFQ بعد القبول
    
    if not all([accepted_status, rejected_status, rfq_closed_status]):
        raise ConflictException(detail="حالات النظام المطلوبة (ACCEPTED/REJECTED/CLOSED_AWARDED) غير موجودة. يرجى تهيئة البيانات المرجعية.")

    # 4. تحديث حالة عرض السعر المختار إلى 'مقبول'
    quotes_crud.update_quote_status(db=db, db_quote=db_quote, new_status_id=accepted_status.quote_status_id)

    # 5. تحديث حالة جميع عروض الأسعار الأخرى لنفس الـ RFQ إلى 'مرفوض'
    other_quotes = db.query(models_market.Quote).filter(
        models_market.Quote.rfq_id == db_quote.rfq_id,
        models_market.Quote.quote_id != quote_id
    ).all()
    for other_quote in other_quotes:
        quotes_crud.update_quote_status(db=db, db_quote=other_quote, new_status_id=rejected_status.quote_status_id)
        # TODO: إخطار البائعين الآخرين بأن عروضهم قد تم رفضها (وحدة الإشعارات).

    # 6. تحديث حالة الـ RFQ إلى 'مغلق - تم اختيار عرض'
    rfqs_crud.update_rfq_status(db=db, db_rfq=db_quote.rfq, new_status_id=rfq_closed_status.rfq_status_id)

    # 7. إنشاء طلب شراء جديد (Order) بناءً على تفاصيل عرض السعر المقبول (REQ-FUN-097).
    order_items_create = []
    for quote_item in db_quote.items:
        # TODO: التعامل مع custom_product_description في RFQ، حالياً نفترض المنتج موجود في الكتالوج.
        #       هنا، يجب أن نتحقق من أن بند RFQ_item_id له product_id صالح أو نتعامل مع Custom Product.
        #       if quote_item.rfq_item.product_id:
        #           product_packaging_option_id = ... # جلب خيار التعبئة الافتراضي للمنتج
        #       else:
        #           # التعامل مع منتج مخصص
        
        # for simplicity, assuming product_packaging_option_id can be derived or is always available from rfq_item
        # TODO: تأكد أن rfq_item.product_id و rfq_item.unit_of_measure_id يكفيان لتحديد ProductPackagingOption
        #       الأكثر دقة هو أن QuoteItem يجب أن يشير إلى ProductPackagingOption_id مباشرة إذا كان المنتج من الكتالوج.

        # هنا سنفترض أن rfq_item.product_id و rfq_item.unit_of_measure_id
        # كافيان لتحديد ProductPackagingOption أو أننا نتعامل مع Custom Product.
        # في نظام متكامل، قد تحتاج إلى دالة خدمة هنا تجلب ProductPackagingOptionId
        # بناءً على ProductId و UnitOfMeasureId والمواصفات (إذا كانت موجودة).
        
        # لغرض هذا الـ TODO، سنفترض أننا نستطيع الحصول على packaging_option_id
        # من rfq_item المرتبط أو من معلومات أخرى في QuoteItem.
        # إذا كان RfqItem يشير إلى product_id، يجب جلب خيار تعبئة مناسب لهذا المنتج.
        # هذا الجزء معقد ويتطلب منطقًا إضافيًا لربط QuoteItem بـ ProductPackagingOption.
        # حالياً، RfqItem لديه product_id (nullable) و unit_of_measure_id.
        # لإنشاء OrderItemCreate، نحتاج product_packaging_option_id.
        
        # Temporary placeholder for product_packaging_option_id
        temp_packaging_option_id = None
        if quote_item.rfq_item.product_id:
            # TODO: جلب ProductPackagingOption_id من ProductId و UnitOfMeasureId
            #       هذا يتطلب منطقًا في product_service أو packaging_service
            #       للعثور على خيار التعبئة الافتراضي أو الأنسب.
            #       For now, let's assume a default/example packaging option exists or is derived.
            temp_packaging_option_id = 1 # Placeholder value. MUST BE REPLACED WITH ACTUAL LOGIC.
        elif quote_item.offered_product_description:
            # TODO: التعامل مع المنتجات المخصصة غير الموجودة في الكتالوج
            #       هذه البنود لن يكون لها product_packaging_option_id
            #       وتتطلب آلية مختلفة لإنشاء OrderItem (ربما حقل description مباشرة).
            pass
        
        if temp_packaging_option_id: # فقط إذا تمكنا من تحديد خيار تعبئة
            order_items_create.append(order_schemas.OrderItemCreate(
                product_packaging_option_id=temp_packaging_option_id, # <-- هذا يجب أن يتم حسابه بدقة
                seller_user_id=db_quote.seller_user_id,
                quantity_ordered=quote_item.offered_quantity,
                unit_price_at_purchase=quote_item.unit_price_offered,
                total_price_for_item=quote_item.total_item_price,
                item_status_id=None, # يمكن تعيين حالة أولية هنا
                notes=quote_item.item_notes
            ))

    # إنشاء OrderCreate schema من بيانات عرض السعر
    order_create_schema = order_schemas.OrderCreate(
        buyer_user_id=db_quote.rfq.buyer_user_id, # المشتري هو صاحب الـ RFQ
        seller_user_id=db_quote.seller_user_id, # البائع هو مقدم العرض الفائز
        order_reference_number=None, # سيتم إنشاؤه في create_new_order
        order_date=datetime.now(timezone.utc),
        order_status_id=None, # سيتم تعيينه في create_new_order
        total_amount_before_discount=float(db_quote.total_quote_amount), # افترض أن هذا هو الإجمالي قبل الخصم
        discount_amount=0.0, # TODO: حساب أي خصومات إضافية على مستوى الطلب
        total_amount_after_discount=float(db_quote.total_quote_amount),
        vat_amount=0.0, # TODO: حساب VAT
        final_total_amount=float(db_quote.total_quote_amount), # TODO: حساب الإجمالي النهائي
        currency_code="SAR", # TODO: يجب أن تكون العملة من الـ RFQ أو القواعد
        shipping_address_id=db_quote.rfq.delivery_address_id, # عنوان التسليم من الـ RFQ
        billing_address_id=db_quote.rfq.buyer.billing_address_id if db_quote.rfq.buyer.billing_address_id else None, # TODO: جلب العنوان الفعلي من المشتري
        payment_method_id=None, # TODO: تحديد طريقة الدفع (يمكن أن تكون جزءًا من شروط العرض)
        payment_status_id=None, # TODO: تحديد حالة الدفع الأولية
        source_of_order="FROM_QUOTE",
        related_quote_id=db_quote.quote_id,
        items=order_items_create,
        notes_from_buyer=db_quote.rfq.notes, # TODO: يمكن نقل ملاحظات المشتري من الـ RFQ
        notes_from_seller=db_quote.seller_notes # ملاحظات البائع من العرض
    )

    # استدعاء خدمة إنشاء الطلب (orders_service)
    # create_new_order ستعالج تفاصيل إنشاء الطلب، تسجيل التاريخ، وخصم المخزون
    created_order = create_new_order(db, order_create_schema, db_quote.rfq.buyer) # المشتري هو current_user في هذا السياق
    # TODO: هنا، المستخدم الحالي هو البائع، لكن create_new_order تتوقع المشتري.
    #       يجب تمرير db_quote.rfq.buyer كـ current_user لـ create_new_order
    #       ويمكن تسجيل changed_by_user_id في OrderStatusHistory كـ current_user (البائع الذي قبل العرض).
    #       أو، الأفضل، أن create_new_order تأخذ BuyerUser و ChangedByUser بشكل منفصل.

    # TODO: إخطار البائع الفائز بوجود طلب جديد (وحدة الإشعارات).
    # TODO: إخطار المشتري بأن عرضه قد تم قبوله وتم إنشاء الطلب (وحدة الإشعارات).

    return db_quote

def reject_quote(db: Session, quote_id: int, current_user: User) -> models_market.Quote:
    """
    خدمة لرفض عرض سعر (Quote) بواسطة المشتري.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_id (int): معرف عرض السعر المراد رفضه.
        current_user (User): المستخدم الحالي (يجب أن يكون مشتري الـ RFQ).

    Returns:
        models_market.Quote: كائن عرض السعر الذي تم رفضه.

    Raises:
        NotFoundException: إذا لم يتم العثور على عرض السعر.
        ForbiddenException: إذا لم يكن المستخدم مشتري الـ RFQ أو غير مصرح له.
        BadRequestException: إذا كان عرض السعر ليس في حالة تسمح بالرفض.
        ConflictException: إذا لم يتم العثور على حالات الدفع/الطلب/عرض السعر المطلوبة.
    """
    db_quote = get_quote_details(db, quote_id, current_user)

    # التحقق من صلاحية المستخدم (يجب أن يكون مشتري الـ RFQ أو مسؤول)
    if db_quote.rfq.buyer_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_QUOTE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك برفض عرض السعر هذا.")

    # TODO: آلة حالة (State Machine) لـ Quote: يجب أن يكون في حالة 'مقدم' أو 'قيد المراجعة'.
    # if db_quote.quote_status.status_name_key not in ["SUBMITTED", "PENDING_REVIEW"]:
    #     raise BadRequestException(detail="لا يمكن رفض عرض السعر هذا في حالته الحالية.")

    rejected_status = db.query(QuoteStatus).filter(QuoteStatus.status_name_key == "REJECTED").first()
    if not rejected_status:
        raise ConflictException(detail="حالة 'REJECTED' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    quotes_crud.update_quote_status(db=db, db_quote=db_quote, new_status_id=rejected_status.quote_status_id)

    # TODO: إخطار البائع بأن عرضه قد تم رفضه.
    # TODO: التحقق من جميع العروض الأخرى لنفس الـ RFQ. إذا تم رفض آخر عرض، يجب تحديث حالة الـ RFQ إلى "مغلق - لم يتم الاختيار".

    return db_quote

# ==========================================================
# --- خدمات حالات عرض السعر (QuoteStatus) ---
# ==========================================================

def create_quote_status_service(db: Session, status_in: schemas_lookups.QuoteStatusCreate) -> QuoteStatus:
    """
    خدمة لإنشاء حالة عرض سعر (Quote Status) جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas_lookups.QuoteStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        QuoteStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    if db.query(QuoteStatus).filter(QuoteStatus.status_name_key == status_in.status_name_key).first():
        raise ConflictException(detail=f"حالة عرض السعر بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return quotes_crud.create_quote_status(db=db, status_in=status_in)

def get_quote_status_details_service(db: Session, quote_status_id: int) -> QuoteStatus:
    """
    خدمة لجلب حالة عرض سعر (Quote Status) بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة.

    Returns:
        QuoteStatus: كائن الحالة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
    """
    status_obj = quotes_crud.get_quote_status(db, quote_status_id=quote_status_id)
    if not status_obj:
        raise NotFoundException(detail=f"حالة عرض السعر بمعرف {quote_status_id} غير موجودة.")
    return status_obj

def get_all_quote_statuses_service(db: Session) -> List[QuoteStatus]:
    """
    خدمة لجلب جميع حالات عرض السعر المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[QuoteStatus]: قائمة بكائنات الحالات.
    """
    return quotes_crud.get_all_quote_statuses(db)

def update_quote_status_service(db: Session, quote_status_id: int, status_in: schemas_lookups.QuoteStatusUpdate) -> QuoteStatus:
    """
    خدمة لتحديث حالة عرض سعر (Quote Status) موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas_lookups.QuoteStatusUpdate): البيانات المراد تحديثها.

    Returns:
        QuoteStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_quote_status_details_service(db, quote_status_id)
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        if db.query(QuoteStatus).filter(QuoteStatus.status_name_key == status_in.status_name_key).first():
            raise ConflictException(detail=f"حالة عرض السعر بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return quotes_crud.update_quote_status_crud(db=db, db_status=db_status, status_in=status_in)

def delete_quote_status_service(db: Session, quote_status_id: int):
    """
    خدمة لحذف حالة عرض سعر (Quote Status) (حذف صارم).
    تتضمن التحقق من عدم وجود عروض أسعار مرتبطة بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ForbiddenException: إذا كانت الحالة مستخدمة حاليًا بواسطة أي عروض أسعار.
    """
    db_status = get_quote_status_details_service(db, quote_status_id)
    # TODO: التحقق من عدم وجود Quote تستخدم quote_status_id هذا
    # from src.market.models.quotes_models import Quote
    # if db.query(Quote).filter(Quote.quote_status_id == quote_status_id).count() > 0:
    #     raise ForbiddenException(detail=f"لا يمكن حذف حالة عرض السعر بمعرف {quote_status_id} لأنها تستخدم من قبل عروض أسعار موجودة.")
    quotes_crud.delete_quote_status(db=db, db_status=db_status)
    return {"message": "تم حذف حالة عرض السعر بنجاح."}


# ==========================================================
# --- خدمات ترجمات حالات عرض السعر (QuoteStatusTranslation) ---
# ==========================================================

def create_quote_status_translation_service(db: Session, quote_status_id: int, trans_in: schemas_lookups.QuoteStatusTranslationCreate) -> QuoteStatusTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لحالة عرض سعر (Quote Status) معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة الأم.
        trans_in (schemas_lookups.QuoteStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        QuoteStatusTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة الأم.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    get_quote_status_details_service(db, quote_status_id)
    if quotes_crud.get_quote_status_translation(db, quote_status_id=quote_status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة لحالة عرض السعر بمعرف {quote_status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")
    return quotes_crud.create_quote_status_translation(db=db, quote_status_id=quote_status_id, trans_in=trans_in)

def get_quote_status_translation_details_service(db: Session, quote_status_id: int, language_code: str) -> QuoteStatusTranslation:
    """
    خدمة لجلب ترجمة حالة عرض سعر (Quote Status) محددة بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة.

    Returns:
        QuoteStatusTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = quotes_crud.get_quote_status_translation(db, quote_status_id=quote_status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة عرض السعر بمعرف {quote_status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_quote_status_translation_service(db: Session, quote_status_id: int, language_code: str, trans_in: schemas_lookups.QuoteStatusTranslationUpdate) -> QuoteStatusTranslation:
    """
    خدمة لتحديث ترجمة حالة عرض سعر (Quote Status) موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas_lookups.QuoteStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        QuoteStatusTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_quote_status_translation_details_service(db, quote_status_id, language_code)
    return quotes_crud.update_quote_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_quote_status_translation_service(db: Session, quote_status_id: int, language_code: str):
    """
    خدمة لحذف ترجمة حالة عرض سعر (Quote Status) معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        quote_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_quote_status_translation_details_service(db, quote_status_id, language_code)
    quotes_crud.delete_quote_status_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة حالة عرض السعر بنجاح."}

