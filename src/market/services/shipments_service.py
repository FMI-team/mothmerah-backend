# backend\src\market\services\shipments_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, timezone # لاستخدام التواريخ والأوقات

# استيراد المودلز
from src.market.models import shipments_models as models_market
# استيراد المودلز من Lookups
from src.lookups.models import ShipmentStatus, ShipmentStatusTranslation, Currency # من lookups.models.py
from src.users.models.addresses_models import  Address

# استيراد Schemas
from src.market.schemas import shipment_schemas as schemas
# استيراد دوال الـ CRUD
from src.market.crud import shipments_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات
from src.lookups.schemas import lookups_schemas as schemas_lookups

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.market.services.orders_service import (
    get_order_details, # للتحقق من وجود الطلب الأب
    get_order_item_details_service  # للتحقق من وجود بند الطلب
    )
from src.users.services.core_service import get_user_profile # للتحقق من وجود المستخدم (شاحن)
from src.users.services.address_service import get_address_by_id # للتحقق من وجود عنوان الشحن
from sqlalchemy.dialects.postgresql import UUID
# TODO: وحدة الإشعارات - (Module 11) لإرسال الإشعارات.


# ==========================================================
# --- خدمات الشحنات (Shipment) ---
# ==========================================================

def create_new_shipment(db: Session, shipment_in: schemas.ShipmentCreate, current_user: User) -> models_market.Shipment:
    """
    خدمة لإنشاء سجل شحنة جديد.
    تتضمن التحقق من وجود الطلب الأب، عناوين الشحن، وتعيين الحالة الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_in (schemas.ShipmentCreate): بيانات الشحنة للإنشاء، بما في ذلك بنود الشحنة.
        current_user (User): المستخدم الحالي (البائع أو المسؤول عن الشحن).

    Returns:
        models_market.Shipment: كائن الشحنة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على الطلب الأب، العنوان، العملة، أو حالة الشحن الأولية.
        ForbiddenException: إذا كان المستخدم غير مصرح له بإنشاء شحنة لهذا الطلب.
        BadRequestException: إذا كانت البيانات غير صالحة (مثلاً الكميات، التواريخ).
        ConflictException: إذا لم يتم العثور على حالة الشحن الأولية.
    """
    # 1. التحقق من وجود الطلب الأب وملكية البائع له
    db_order = get_order_details(db, order_id=shipment_in.order_id, current_user=current_user)
    # TODO: منطق عمل: التحقق من أن المستخدم هو البائع (db_order.seller_user_id) أو مسؤول الشحن
    #       (if db_order.seller_user_id != current_user.user_id and not is_admin_or_shipper_manager)
    #       get_order_details لديها بالفعل تحقق، لكن قد لا يكون كافياً لكل حالات الشحن.

    # 2. التحقق من وجود عنوان الشحن
    if shipment_in.shipping_address_id:
        get_address_by_id(db, shipment_in.shipping_address_id)

    # 3. التحقق من العملة (لتكلفة الشحن)
    currency_exists = db.query(Currency).filter(Currency.currency_code == shipment_in.currency_code).first()
    if not currency_exists:
        raise NotFoundException(detail=f"رمز العملة '{shipment_in.currency_code}' غير صالح.")

    # 4. جلب الحالة الأولية للشحنة
    initial_shipment_status = db.query(ShipmentStatus).filter(ShipmentStatus.status_name_key == "PENDING").first()
    if not initial_shipment_status:
        raise ConflictException(detail="حالة الشحن الأولية 'PENDING' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    # 5. التحقق من بنود الشحنة (Shipment Items)
    if not shipment_in.items:
        raise BadRequestException(detail="يجب أن تحتوي الشحنة على بند واحد على الأقل.")
    
    for item_in in shipment_in.items:
        db_order_item = get_order_item_details_service(db, item_in.order_item_id)
        if not db_order_item or db_order_item.order_id != db_order.order_id:
            raise BadRequestException(detail=f"بند الطلب بمعرف {item_in.order_item_id} غير موجود أو لا ينتمي إلى الطلب الأب.")
        # TODO: منطق عمل: التحقق من أن الكمية المشحونة لا تتجاوز الكمية المطلوبة في بند الطلب الأب
        #       وأنه لا يوجد تجاوز للكمية الإجمالية التي تم شحنها لهذا البند سابقاً.

    # 6. توليد رقم مرجعي فريد للشحنة
    shipment_reference_number = f"SHP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{UUID(bytes=os.urandom(8)).hex[:8].upper()}"
    # TODO: يجب أن يكون هناك آلية أكثر قوة لتوليد أرقام مرجعية فريدة.

    # 7. استدعاء CRUD لإنشاء الشحنة وبنودها
    db_shipment = shipments_crud.create_shipment(
        db=db,
        shipment_in=shipment_in,
        shipment_reference_number=shipment_reference_number,
        initial_status_id=initial_shipment_status.shipment_status_id
    )

    db.commit()
    db.refresh(db_shipment)

    # TODO: إخطار المشتري بأن الشحنة قد تم إنشاؤها (وحدة الإشعارات).
    # TODO: تحديث حالة الطلب الأب (Order) إلى "قيد الشحن" أو ما شابه (خدمة orders_service).

    return db_shipment

def get_shipment_details(db: Session, shipment_id: int, current_user: User) -> models_market.Shipment:
    """
    خدمة لجلب تفاصيل شحنة واحدة بالـ ID، مع التحقق من صلاحيات المشتري أو البائع أو المسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_id (int): معرف الشحنة المطلوب.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.Shipment: كائن الشحنة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الشحنة.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية الشحنة.
    """
    db_shipment = shipments_crud.get_shipment(db, shipment_id=shipment_id)
    if not db_shipment:
        raise NotFoundException(detail=f"الشحنة بمعرف {shipment_id} غير موجودة.")

    # التحقق من الصلاحيات: المشتري (صاحب الطلب)، أو البائع (الشاحن/بائع الطلب)، أو المسؤول
    is_buyer = db_shipment.order.buyer_user_id == current_user.user_id
    is_seller = db_shipment.order.seller_user_id == current_user.user_id # إذا كان الطلب لبائع واحد
    is_admin = any(p.permission_name_key == "ADMIN_ORDER_VIEW_ANY" for p in current_user.default_role.permissions) # TODO: صلاحية view shipments

    # TODO: قد تحتاج إلى منطق أكثر تعقيدًا إذا كان الطلب متعدد البائعين.
    #       مثلاً، البائع يرى الشحنة إذا كانت تخص أحد بنوده.
    # is_seller_of_any_item = any(item.seller_user_id == current_user.user_id for item in db_shipment.order.items)

    if not (is_buyer or is_seller or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل هذه الشحنة.")
    
    return db_shipment

def get_all_shipments_for_order(db: Session, order_id: UUID, current_user: User, skip: int = 0, limit: int = 100) -> List[models_market.Shipment]:
    """
    خدمة لجلب جميع الشحنات المتعلقة بطلب معين، مع التحقق من صلاحيات المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        order_id (UUID): معرف الطلب الأب.
        current_user (User): المستخدم الحالي.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_market.Shipment]: قائمة بكائنات الشحنات.

    Raises:
        NotFoundException: إذا لم يتم العثور على الطلب.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية الطلب/الشحنات.
    """
    # 1. التحقق من وجود الطلب وصلاحية المستخدم لرؤيته (باستخدام orders_service)
    # TODO: يجب استيراد get_order_details من orders_service
    from src.market.services.orders_service import get_order_details
    get_order_details(db, order_id, current_user) # هذه الدالة تتحقق من صلاحية المستخدم للطلب

    return shipments_crud.get_all_shipments(db, order_id=order_id, skip=skip, limit=limit)

def get_my_shipments(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[models_market.Shipment]:
    """
    خدمة لجلب جميع الشحنات التي قام بها المستخدم (كبائع/شاحن) أو التي تخص طلبات هو المشتري فيها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_market.Shipment]: قائمة بكائنات الشحنات.
    """
    # TODO: هذا يتطلب منطق بحث أكثر تعقيدًا في CRUD
    #       للبحث عن الشحنات التي:
    #       1. shipped_by_user_id = current_user.user_id
    #       2. order.buyer_user_id = current_user.user_id
    #       3. order.items.seller_user_id = current_user.user_id
    #       حالياً، get_all_shipments لا تدعم هذه التصفية المعقدة مباشرة.
    #       يجب تحسين دالة CRUD أو بناء استعلام مباشر هنا.

    return shipments_crud.get_all_shipments(db, skip=skip, limit=limit) # حالياً تجلب الكل دون تصفية

def update_shipment(db: Session, shipment_id: int, shipment_in: schemas.ShipmentUpdate, current_user: User) -> models_market.Shipment:
    """
    خدمة لتحديث سجل شحنة موجود.
    تتضمن التحقق من الصلاحيات (البائع أو المسؤول عن الشحن) ومراحل دورة حياة الشحنة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_id (int): معرف الشحنة المراد تحديثها.
        shipment_in (schemas.ShipmentUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.Shipment: كائن الشحنة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الشحنة.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بتحديث الشحنة.
        BadRequestException: إذا كانت البيانات غير صالحة (مثل الحالة الجديدة غير موجودة، أو التواريخ غير منطقية).
    """
    db_shipment = get_shipment_details(db, shipment_id, current_user) # يتحقق من الوجود والصلاحية

    # التحقق من وجود الحالة الجديدة إذا تم تحديثها
    if shipment_in.shipment_status_id:
        new_status = db.query(ShipmentStatus).filter(ShipmentStatus.shipment_status_id == shipment_in.shipment_status_id).first()
        if not new_status:
            raise BadRequestException(detail=f"حالة الشحنة بمعرف {shipment_in.shipment_status_id} غير موجودة.")
        # TODO: منطق عمل: آلة حالة (State Machine) للشحنة: التحقق من الانتقالات المسموح بها.
        #       مثلاً، لا يمكن الانتقال من "تم التسليم" إلى "قيد التجهيز".

    # التحقق من منطقية التواريخ
    if shipment_in.estimated_shipping_date and shipment_in.actual_shipping_date and shipment_in.actual_shipping_date < shipment_in.estimated_shipping_date:
        raise BadRequestException(detail="تاريخ الشحن الفعلي يجب أن يكون بعد أو يساوي تاريخ الشحن المقدر.")
    # TODO: المزيد من التحقق لتواريخ التسليم.

    return shipments_crud.update_shipment(db=db, db_shipment=db_shipment, shipment_in=shipment_in)

def update_shipment_status(db: Session, shipment_id: int, new_status_id: int, current_user: User, notes: Optional[str] = None) -> models_market.Shipment:
    """
    خدمة لتحديث حالة الشحنة مباشرة بواسطة البائع أو المسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_id (int): معرف الشحنة المراد تحديث حالتها.
        new_status_id (int): معرف الحالة الجديدة.
        current_user (User): المستخدم الحالي.
        notes (Optional[str]): ملاحظات على تغيير الحالة.

    Returns:
        models_market.Shipment: كائن الشحنة بعد تحديث حالتها.

    Raises:
        NotFoundException: إذا لم يتم العثور على الشحنة أو الحالة الجديدة.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له.
        BadRequestException: إذا كانت الحالة الجديدة غير موجودة أو الانتقال غير مسموح به.
    """
    db_shipment = get_shipment_details(db, shipment_id, current_user) # يتحقق من الوجود والصلاحية

    # التحقق من وجود الحالة الجديدة
    new_status = db.query(ShipmentStatus).filter(ShipmentStatus.shipment_status_id == new_status_id).first()
    if not new_status:
        raise BadRequestException(detail=f"حالة الشحنة بمعرف {new_status_id} غير موجودة.")
    
    # TODO: منطق عمل: آلة حالة (State Machine) للشحنة: التحقق من الانتقالات المسموح بها.
    #       مثلًا، لا يمكن الانتقال من "تم التسليم" إلى "تم الشحن".

    return shipments_crud.update_shipment_status(db=db, db_shipment=db_shipment, new_status_id=new_status_id)

def cancel_shipment(db: Session, shipment_id: int, current_user: User, reason: Optional[str] = None) -> models_market.Shipment:
    """
    خدمة لإلغاء الشحنة (الحذف الناعم).
    تتضمن التحقق من الصلاحيات وتغيير حالتها إلى "ملغاة".

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_id (int): معرف الشحنة المراد إلغاؤها.
        current_user (User): المستخدم الحالي.
        reason (Optional[str]): سبب الإلغاء.

    Returns:
        models_market.Shipment: كائن الشحنة بعد الإلغاء.

    Raises:
        NotFoundException: إذا لم يتم العثور على الشحنة.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له.
        BadRequestException: إذا كانت الشحنة في حالة لا تسمح بالإلغاء.
        ConflictException: إذا لم يتم العثور على حالة الإلغاء.
    """
    db_shipment = get_shipment_details(db, shipment_id, current_user)

    # TODO: التحقق من الصلاحيات والإذن بالإلغاء بناءً على دور المستخدم وحالة الشحنة.
    #       مثلاً، لا يمكن إلغاء شحنة تم تسليمها.

    canceled_status = db.query(ShipmentStatus).filter(ShipmentStatus.status_name_key == "CANCELED").first()
    if not canceled_status:
        raise ConflictException(detail="حالة الإلغاء 'CANCELED' غير موجودة. يرجى تهيئة البيانات المرجعية.")
    
    return shipments_crud.update_shipment_status(db=db, db_shipment=db_shipment, new_status_id=canceled_status.shipment_status_id)


# ==========================================================
# --- خدمات حالات الشحن (ShipmentStatus) ---
# ==========================================================

def create_shipment_status_service(db: Session, status_in: schemas_lookups.ShipmentStatusCreate) -> ShipmentStatus:
    """
    خدمة لإنشاء حالة شحن جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas_lookups.ShipmentStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        ShipmentStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    if db.query(ShipmentStatus).filter(ShipmentStatus.status_name_key == status_in.status_name_key).first():
        raise ConflictException(detail=f"حالة الشحن بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return shipments_crud.create_shipment_status(db=db, status_in=status_in)

def get_shipment_status_details_service(db: Session, shipment_status_id: int) -> ShipmentStatus:
    """
    خدمة لجلب حالة شحن بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة.

    Returns:
        ShipmentStatus: كائن الحالة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
    """
    status_obj = shipments_crud.get_shipment_status(db, shipment_status_id=shipment_status_id)
    if not status_obj:
        raise NotFoundException(detail=f"حالة الشحن بمعرف {shipment_status_id} غير موجودة.")
    return status_obj

def get_all_shipment_statuses_service(db: Session) -> List[ShipmentStatus]:
    """
    خدمة لجلب جميع حالات الشحن المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[ShipmentStatus]: قائمة بكائنات الحالات.
    """
    return shipments_crud.get_all_shipment_statuses(db)

def update_shipment_status_service(db: Session, shipment_status_id: int, status_in: schemas_lookups.ShipmentStatusUpdate) -> ShipmentStatus:
    """
    خدمة لتحديث حالة شحن موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas_lookups.ShipmentStatusUpdate): البيانات المراد تحديثها.

    Returns:
        ShipmentStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_shipment_status_details_service(db, shipment_status_id)
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        if db.query(ShipmentStatus).filter(ShipmentStatus.status_name_key == status_in.status_name_key).first():
            raise ConflictException(detail=f"حالة الشحن بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return shipments_crud.update_shipment_status_crud(db=db, db_status=db_status, status_in=status_in)

def delete_shipment_status_service(db: Session, shipment_status_id: int):
    """
    خدمة لحذف حالة شحن (حذف صارم).
    تتضمن التحقق من عدم وجود شحنات مرتبطة بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ForbiddenException: إذا كانت الحالة مستخدمة حاليًا بواسطة أي شحنات.
    """
    db_status = get_shipment_status_details_service(db, shipment_status_id)
    # TODO: التحقق من عدم وجود Shipment تستخدم shipment_status_id هذا
    # from src.market.models.shipments_models import Shipment
    # if db.query(Shipment).filter(Shipment.shipment_status_id == shipment_status_id).count() > 0:
    #     raise ForbiddenException(detail=f"لا يمكن حذف حالة الشحن بمعرف {shipment_status_id} لأنها تستخدم من قبل شحنات موجودة.")
    shipments_crud.delete_shipment_status(db=db, db_status=db_status)
    return {"message": "تم حذف حالة الشحن بنجاح."}


# ==========================================================
# --- خدمات ترجمات حالات الشحن (ShipmentStatusTranslation) ---
# ==========================================================

def create_shipment_status_translation_service(db: Session, shipment_status_id: int, trans_in: schemas_lookups.ShipmentStatusTranslationCreate) -> ShipmentStatusTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لحالة شحن معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة الأم.
        trans_in (schemas_lookups.ShipmentStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        ShipmentStatusTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة الأم.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    get_shipment_status_details_service(db, shipment_status_id)
    if shipments_crud.get_shipment_status_translation(db, shipment_status_id=shipment_status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة لحالة الشحن بمعرف {shipment_status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")
    return shipments_crud.create_shipment_status_translation(db=db, shipment_status_id=shipment_status_id, trans_in=trans_in)

def get_shipment_status_translation_details_service(db: Session, shipment_status_id: int, language_code: str) -> ShipmentStatusTranslation:
    """
    خدمة لجلب ترجمة حالة شحن محددة بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة.

    Returns:
        ShipmentStatusTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = shipments_crud.get_shipment_status_translation(db, shipment_status_id=shipment_status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة الشحن بمعرف {shipment_status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_shipment_status_translation_service(db: Session, shipment_status_id: int, language_code: str, trans_in: schemas_lookups.ShipmentStatusTranslationUpdate) -> ShipmentStatusTranslation:
    """
    خدمة لتحديث ترجمة حالة شحن موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas_lookups.ShipmentStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        ShipmentStatusTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_shipment_status_translation_details_service(db, shipment_status_id, language_code)
    return shipments_crud.update_shipment_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_shipment_status_translation_service(db: Session, shipment_status_id: int, language_code: str):
    """
    خدمة لحذف ترجمة حالة شحن معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        shipment_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_shipment_status_translation_details_service(db, shipment_status_id, language_code)
    shipments_crud.delete_shipment_status_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة حالة الشحن بنجاح."}
