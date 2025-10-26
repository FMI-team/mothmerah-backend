# backend\src\market\services\rfqs_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone # لاستخدام التواريخ والأوقات

# استيراد المودلز
from src.market.models import rfqs_models as models_market
# استيراد المودلز من Lookups
from src.lookups.models import RfqStatus, RfqStatusTranslation, Language  # TODO: تأكد من استيراد هذه المودلز من lookups
# استيراد Schemas
from src.market.schemas import rfq_schemas as schemas
# استيراد دوال الـ CRUD
from src.market.crud import rfqs_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
# استيراد المودلات الأخرى المستخدمة
from src.products.models import Product, UnitOfMeasure
from src.users.models.addresses_models import  Address
# from src.users.models.addresses_models import Address # <-- تم تصحيح المسار
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

# استيراد Schemas
from src.market.schemas import rfq_schemas as schemas
from src.lookups.schemas import lookups_schemas as schemas_lookups # <-- تأكد من هذا الاستيراد إذا كنت تستخدمه

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.users.services.core_service import get_user_profile # للتحقق من وجود المشتري/البائع
from src.users.services.address_service import get_address_by_id # للتحقق من وجود عنوان التسليم
from src.products.services.product_service import get_product_by_id_for_user # للتحقق من وجود المنتج
from src.products.services.unit_of_measure_service import get_unit_of_measure_details # للتحقق من وحدة القياس

# TODO: وحدة الإشعارات - (Module 11) لإرسال الإشعارات.


# ==========================================================
# --- خدمات طلبات عروض الأسعار (Rfq) ---
# ==========================================================

def create_new_rfq(db: Session, rfq_in: schemas.RfqCreate, current_user: User) -> models_market.Rfq:
    """
    خدمة لإنشاء طلب عرض أسعار (RFQ) جديد بواسطة مشتري تجاري.
    تتضمن التحقق من صحة البيانات، وجود الكيانات المرتبطة، وتعيين الحالة الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_in (schemas.RfqCreate): بيانات الـ RFQ للإنشاء، بما في ذلك بنود الـ RFQ.
        current_user (User): المستخدم الحالي (المشتري التجاري).

    Returns:
        models_market.Rfq: كائن الـ RFQ الذي تم إنشاؤه.

    Raises:
        BadRequestException: إذا كانت البيانات غير صالحة (مثلاً موعد نهائي في الماضي، أو لا يوجد بنود).
        NotFoundException: إذا لم يتم العثور على عنوان التسليم، المنتج، أو وحدة القياس.
        ConflictException: إذا لم يتم العثور على حالة الـ RFQ الأولية.
    """
    # 1. التحقق من وجود عنوان التسليم
    if rfq_in.delivery_address_id:
        get_address_by_id(db, rfq_in.delivery_address_id)

    # 2. التحقق من الموعد النهائي لتقديم العروض (يجب أن يكون في المستقبل)
    if rfq_in.submission_deadline <= datetime.now(timezone.utc):
        raise BadRequestException(detail="الموعد النهائي لتقديم العروض يجب أن يكون في المستقبل.")

    # 3. التحقق من وجود بنود للـ RFQ
    if not rfq_in.items:
        raise BadRequestException(detail="يجب أن يحتوي طلب عرض الأسعار على بند واحد على الأقل.")

    # 4. التحقق من كل بند في الـ RFQ (product_id, unit_of_measure_id)
    for item_in in rfq_in.items:
        if item_in.product_id:
            # TODO: يجب التأكد أن get_product_by_id_for_user يمكنها جلب المنتج حتى لو لم يكن المستخدم مالكه
            # أو استخدام دالة CRUD مباشرة مثل product_crud.get_product_by_id(db, product_id, show_inactive=True)
            # لأن المشتري لا يملك المنتج، فقط يستعرضه
            try:
                get_product_by_id_for_user(db, product_id=item_in.product_id, user=current_user)
            except NotFoundException:
                raise NotFoundException(detail=f"المنتج بمعرف {item_in.product_id} في بند الـ RFQ غير موجود.")
        
        get_unit_of_measure_details(db, item_in.unit_of_measure_id)

    # 5. جلب الحالة الأولية للـ RFQ
    initial_rfq_status = db.query(RfqStatus).filter(RfqStatus.status_name_key == "OPEN").first()
    if not initial_rfq_status:
        raise ConflictException(detail="حالة الـ RFQ الأولية 'OPEN' غير موجودة.")

    # 6. توليد رقم مرجعي فريد للـ RFQ
    rfq_reference_number = f"RFQ-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{UUID(bytes=os.urandom(8)).hex[:8].upper()}"
    # TODO: يجب أن يكون هناك آلية أكثر قوة لتوليد أرقام مرجعية فريدة وتجنب التكرار المحتمل على المدى الطويل

    # 7. استدعاء CRUD لإنشاء الـ RFQ وبنوده
    db_rfq = rfqs_crud.create_rfq(
        db=db,
        rfq_in=rfq_in,
        buyer_user_id=current_user.user_id,
        rfq_reference_number=rfq_reference_number,
        initial_status_id=initial_rfq_status.rfq_status_id
    )

    db.commit()
    db.refresh(db_rfq)

    # TODO: هـام (REQ-FUN-093): توجيه الـ RFQ لبائعين محددين/مؤهلين.
    # يتطلب هذا إضافة جدول جديد (مثلاً 'rfq_target_sellers') لربط الـ RFQ بالبائعين المستهدفين.
    # ومنطق في هذه الخدمة لتسجيل هذا التوجيه (خاص/عام) بناءً على مدخلات RFQ.
    # ثم يتم استخدام هذا لتصفية الـ RFQs المتاحة للبائعين.

    # TODO: هـام (REQ-FUN-094): إخطار البائعين المعنيين بوجود RFQ جديد.
    # يتطلب التكامل مع وحدة الإشعارات (Module 11). يجب استدعاء خدمة من هناك لإرسال التنبيهات.

    return db_rfq

def get_rfq_details(db: Session, rfq_id: int, current_user: User) -> models_market.Rfq:
    """
    خدمة لجلب تفاصيل طلب عرض أسعار (RFQ) واحد بالـ ID، مع التحقق من صلاحيات المشتري أو المسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_id (int): معرف الـ RFQ المطلوب.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.Rfq: كائن الـ RFQ المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الـ RFQ.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية الـ RFQ.
    """
    db_rfq = rfqs_crud.get_rfq(db, rfq_id=rfq_id)
    if not db_rfq:
        raise NotFoundException(detail=f"طلب عرض الأسعار (RFQ) بمعرف {rfq_id} غير موجود.")

    # التحقق من الصلاحيات: المشتري أو المسؤول
    is_buyer = db_rfq.buyer_user_id == current_user.user_id
    is_admin = any(p.permission_name_key == "ADMIN_RFQ_VIEW_ANY" for p in current_user.default_role.permissions)

    # TODO: قد تحتاج إضافة منطق للبائعين هنا: هل يمكن للبائع رؤية هذا RFQ (إذا كان موجهًا إليه)؟
    #       هذا سيتطلب معرفة البائعين المستهدفين للـ RFQ.

    if not (is_buyer or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل طلب عرض الأسعار هذا.")
    
    return db_rfq

def get_my_rfqs(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[models_market.Rfq]:
    """
    خدمة لجلب جميع طلبات عروض الأسعار (RFQs) التي أنشأها المشتري الحالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي (المشتري).
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_market.Rfq]: قائمة بكائنات الـ RFQs.
    """
    return rfqs_crud.get_all_rfqs(db, buyer_user_id=current_user.user_id, skip=skip, limit=limit)

def get_rfqs_available_for_seller(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[models_market.Rfq]:
    """
    خدمة لجلب طلبات عروض الأسعار (RFQs) المتاحة للبائع الحالي للرد عليها.
    تتضمن الـ RFQs التي تم توجيهها إليه بشكل خاص أو العامة التي يمكنه رؤيتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي (البائع).
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models_market.Rfq]: قائمة بكائنات الـ RFQs المتاحة.
    """
    # TODO: هذا يتطلب منطق عمل أكثر تعقيدًا.
    #       إذا كان هناك جدول rfq_target_sellers لربط الـ RFQ ببائعين محددين، فيجب استخدام هذا الجدول.
    #       وإلا، يجب جلب الـ RFQs العامة التي يمكن لأي بائع مؤهل رؤيتها.
    #       لأغراض MVP، يمكن أن يعرض جميع الـ RFQs المفتوحة.
    return rfqs_crud.get_all_rfqs(db, rfq_status_id=db.query(RfqStatus).filter(RfqStatus.status_name_key == "OPEN").first().rfq_status_id, skip=skip, limit=limit)


def update_rfq(db: Session, rfq_id: int, rfq_in: schemas.RfqUpdate, current_user: User) -> models_market.Rfq:
    """
    خدمة لتحديث طلب عرض أسعار (RFQ) موجود.
    تتضمن التحقق من الصلاحيات (مالك أو مسؤول) ومراحل دورة حياة الـ RFQ.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_id (int): معرف الـ RFQ المراد تحديثه.
        rfq_in (schemas.RfqUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.Rfq: كائن الـ RFQ المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الـ RFQ.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بتحديث الـ RFQ.
        BadRequestException: إذا كانت البيانات غير صالحة (مثل موعد نهائي في الماضي).
        ConflictException: إذا كانت الحالة الجديدة غير موجودة أو الانتقال غير مسموح به.
    """
    db_rfq = get_rfq_details(db, rfq_id, current_user) # يتحقق من الوجود والصلاحية

    # التحقق من أن الـ RFQ لا يزال في حالة تسمح بالتعديل (مثلاً 'OPEN')
    # TODO: آلة حالة (State Machine) لـ RFQ: تحديد الانتقالات المسموح بها.
    #       مثلاً، لا يمكن تعديل RFQ بعد إغلاقه أو اختيار عرض فيه.
    # if db_rfq.rfq_status.status_name_key != "OPEN":
    #     raise BadRequestException(detail="لا يمكن تحديث طلب عرض الأسعار هذا في حالته الحالية.")

    # التحقق من أن الموعد النهائي لا يزال في المستقبل إذا تم تحديثه
    if rfq_in.submission_deadline and rfq_in.submission_deadline <= datetime.now(timezone.utc):
        raise BadRequestException(detail="الموعد النهائي لتقديم العروض يجب أن يكون في المستقبل.")

    # التحقق من وجود الحالة الجديدة إذا تم تحديثها
    if rfq_in.rfq_status_id:
        new_status = db.query(RfqStatus).filter(RfqStatus.rfq_status_id == rfq_in.rfq_status_id).first()
        if not new_status:
            raise BadRequestException(detail=f"حالة الـ RFQ بمعرف {rfq_in.rfq_status_id} غير موجودة.")
        # TODO: آلة حالة (State Machine) لـ RFQ: التحقق من الانتقال المسموح به إلى الحالة الجديدة.

    return rfqs_crud.update_rfq(db=db, db_rfq=db_rfq, rfq_in=rfq_in)

def cancel_rfq(db: Session, rfq_id: int, current_user: User) -> models_market.Rfq:
    """
    خدمة لإلغاء طلب عرض أسعار (RFQ).
    تتضمن التحقق من الصلاحيات، ومراحل دورة حياة الـ RFQ، وتغيير حالته إلى "ملغى".

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_id (int): معرف الـ RFQ المراد إلغاؤه.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.Rfq: كائن الـ RFQ بعد تحديث حالته إلى "ملغى".

    Raises:
        NotFoundException: إذا لم يتم العثور على الـ RFQ.
        ForbiddenException: إذا كان المستخدم غير مصرح له بالإلغاء.
        BadRequestException: إذا كان الـ RFQ في حالة لا تسمح بالإلغاء.
        ConflictException: إذا لم يتم العثور على حالة الإلغاء.
    """
    db_rfq = get_rfq_details(db, rfq_id, current_user)

    # التحقق من أن المستخدم هو المشتري أو مسؤول
    is_buyer = db_rfq.buyer_user_id == current_user.user_id
    is_admin = any(p.permission_name_key == "ADMIN_RFQ_MANAGE_ANY" for p in current_user.default_role.permissions)

    if not (is_buyer or is_admin):
        raise ForbiddenException(detail="غير مصرح لك بإلغاء طلب عرض الأسعار هذا.")

    # التحقق من المرحلة المسموح بها للإلغاء
    # TODO: آلة حالة (State Machine) لـ RFQ: لا يمكن إلغاء RFQ بعد اختيار عرض أو بعد إغلاقه لسبب آخر.
    # if db_rfq.rfq_status.status_name_key not in ["OPEN", "PENDING_QUOTES"]:
    #     raise BadRequestException(detail="لا يمكن إلغاء طلب عرض الأسعار في حالته الحالية.")

    canceled_status = db.query(RfqStatus).filter(RfqStatus.status_name_key == "CANCELED").first()
    if not canceled_status:
        raise ConflictException(detail="حالة الإلغاء 'CANCELED' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    # تحديث حالة الـ RFQ
    rfqs_crud.update_rfq_status(db=db, db_rfq=db_rfq, new_status_id=canceled_status.rfq_status_id)

    # TODO: إخطار البائعين الذين قدموا عروضاً بأن الـ RFQ قد ألغي.
    # TODO: تحديث حالة جميع عروض الأسعار المرتبطة (quotes) إلى "ملغاة" أو "مرفوضة بسبب الإلغاء".

    return db_rfq


# ==========================================================
# --- خدمات حالات طلب عروض الأسعار (RfqStatus) ---
# ==========================================================

def create_rfq_status_service(db: Session, status_in: schemas_lookups.RfqStatusCreate) -> RfqStatus:
    """
    خدمة لإنشاء حالة طلب عرض أسعار (RFQ Status) جديدة مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas_lookups.RfqStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        RfqStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    if db.query(RfqStatus).filter(RfqStatus.status_name_key == status_in.status_name_key).first():
        raise ConflictException(detail=f"حالة طلب عرض الأسعار بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return rfqs_crud.create_rfq_status(db=db, status_in=status_in)

def get_rfq_status_details(db: Session, rfq_status_id: int) -> RfqStatus:
    """
    خدمة لجلب حالة طلب عرض أسعار (RFQ Status) بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة.

    Returns:
        RfqStatus: كائن الحالة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
    """
    status_obj = rfqs_crud.get_rfq_status(db, rfq_status_id=rfq_status_id)
    if not status_obj:
        raise NotFoundException(detail=f"حالة طلب عرض الأسعار بمعرف {rfq_status_id} غير موجودة.")
    return status_obj

def get_all_rfq_statuses_service(db: Session) -> List[RfqStatus]:
    """
    خدمة لجلب جميع حالات طلبات عروض الأسعار (RFQ Statuses) المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[RfqStatus]: قائمة بكائنات الحالات.
    """
    return rfqs_crud.get_all_rfq_statuses(db)

def update_rfq_status_service(db: Session, rfq_status_id: int, status_in: schemas_lookups.RfqStatusUpdate) -> RfqStatus:
    """
    خدمة لتحديث حالة طلب عرض أسعار (RFQ Status) موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas_lookups.RfqStatusUpdate): البيانات المراد تحديثها.

    Returns:
        RfqStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_rfq_status_details(db, rfq_status_id)
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        if db.query(RfqStatus).filter(RfqStatus.status_name_key == status_in.status_name_key).first():
            raise ConflictException(detail=f"حالة طلب عرض الأسعار بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    return rfqs_crud.update_rfq_status_crud(db=db, db_status=db_status, status_in=status_in)

def delete_rfq_status_service(db: Session, rfq_status_id: int):
    """
    خدمة لحذف حالة طلب عرض أسعار (RFQ Status) (حذف صارم).
    تتضمن التحقق من عدم وجود طلبات عروض أسعار (RFQs) مرتبطة بهذه الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ForbiddenException: إذا كانت الحالة مستخدمة حاليًا بواسطة أي RFQs.
    """
    db_status = get_rfq_status_details(db, rfq_status_id)
    # TODO: التحقق من عدم وجود Rfq تستخدم rfq_status_id هذا
    # from src.market.models.rfqs_models import Rfq
    # if db.query(Rfq).filter(Rfq.rfq_status_id == rfq_status_id).count() > 0:
    #     raise ForbiddenException(detail=f"لا يمكن حذف حالة طلب عرض الأسعار بمعرف {rfq_status_id} لأنها تستخدم من قبل طلبات عروض أسعار موجودة.")
    rfqs_crud.delete_rfq_status(db=db, db_status=db_status)
    return {"message": "تم حذف حالة طلب عرض الأسعار بنجاح."}


# ==========================================================
# --- خدمات ترجمات حالات طلب عروض الأسعار (RfqStatusTranslation) ---
# ==========================================================

def create_rfq_status_translation_service(db: Session, rfq_status_id: int, trans_in: schemas_lookups.RfqStatusTranslationCreate) -> RfqStatusTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لحالة طلب عرض أسعار (RFQ Status) معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة الأم.
        trans_in (schemas_lookups.RfqStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        RfqStatusTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة الأم.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    get_rfq_status_details(db, rfq_status_id)
    if rfqs_crud.get_rfq_status_translation(db, rfq_status_id=rfq_status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة لحالة طلب عرض الأسعار بمعرف {rfq_status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")
    return rfqs_crud.create_rfq_status_translation(db=db, rfq_status_id=rfq_status_id, trans_in=trans_in)

def get_rfq_status_translation_details(db: Session, rfq_status_id: int, language_code: str) -> RfqStatusTranslation:
    """
    خدمة لجلب ترجمة حالة طلب عرض أسعار (RFQ Status) محددة بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة.

    Returns:
        RfqStatusTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = rfqs_crud.get_rfq_status_translation(db, rfq_status_id=rfq_status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة طلب عرض الأسعار بمعرف {rfq_status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_rfq_status_translation_service(db: Session, rfq_status_id: int, language_code: str, trans_in: schemas_lookups.RfqStatusTranslationUpdate) -> RfqStatusTranslation:
    """
    خدمة لتحديث ترجمة حالة طلب عرض أسعار (RFQ Status) موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas_lookups.RfqStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        RfqStatusTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_rfq_status_translation_details(db, rfq_status_id, language_code)
    return rfqs_crud.update_rfq_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_rfq_status_translation_service(db: Session, rfq_status_id: int, language_code: str):
    """
    خدمة لحذف ترجمة حالة طلب عرض أسعار (RFQ Status) معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_rfq_status_translation_details(db, rfq_status_id, language_code)
    rfqs_crud.delete_rfq_status_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة حالة طلب عرض الأسعار بنجاح."}


# ==========================================================
# --- خدمات بنود طلب عروض الأسعار (RfqItem) ---
# ==========================================================

def get_rfq_item_details_service(db: Session, rfq_item_id: int, current_user: User) -> models_market.RfqItem:
    """
    خدمة لجلب تفاصيل بند طلب عرض أسعار (RFQ Item) واحد بالـ ID، مع التحقق من صلاحيات المستخدم.
    المستخدم يجب أن يكون المشتري (صاحب الـ RFQ الأم) أو مسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_item_id (int): معرف بند الـ RFQ المطلوب.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.RfqItem: كائن بند الـ RFQ المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على بند الـ RFQ.
        ForbiddenException: إذا كان المستخدم غير مصرح له برؤية بند الـ RFQ.
    """
    db_item = rfqs_crud.get_rfq_item(db, rfq_item_id=rfq_item_id)
    if not db_item:
        raise NotFoundException(detail=f"بند طلب عرض الأسعار بمعرف {rfq_item_id} غير موجود.")

    # التحقق من الصلاحيات: المشتري (صاحب الـ RFQ) أو مسؤول
    # TODO: يجب أن يتم تحميل الـ RFQ الأم في دالة CRUD get_rfq_item لتحقيق الكفاءة
    db_rfq_parent = rfqs_crud.get_rfq(db, rfq_id=db_item.rfq_id)
    if not db_rfq_parent: # يجب أن لا يحدث هذا إذا كان الربط صحيحاً
        raise NotFoundException(detail="الـ RFQ الأم لبند الـ RFQ غير موجود.")

    is_buyer = db_rfq_parent.buyer_user_id == current_user.user_id
    is_admin = any(p.permission_name_key == "ADMIN_RFQ_VIEW_ANY" for p in current_user.default_role.permissions)

    if not (is_buyer or is_admin):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل بند طلب عرض الأسعار هذا.")
    
    return db_item


def update_rfq_item(db: Session, rfq_item_id: int, item_in: schemas.RfqItemUpdate, current_user: User) -> models_market.RfqItem:
    """
    خدمة لتحديث بند طلب عرض أسعار (RFQ Item) موجود.
    تتضمن التحقق من الصلاحيات (المشتري/المسؤول) ومراحل دورة حياة الـ RFQ.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_item_id (int): معرف بند الـ RFQ المراد تحديثه.
        item_in (schemas.RfqItemUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models_market.RfqItem: كائن بند الـ RFQ المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على بند الـ RFQ.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بتحديث بند الـ RFQ.
        BadRequestException: إذا كانت البيانات غير صالحة.
    """
    db_item = get_rfq_item_details_service(db, rfq_item_id, current_user) # يتحقق من الوجود والصلاحية

    # التحقق من أن الـ RFQ الأم لا يزال في حالة تسمح بالتعديل (مثلاً 'OPEN')
    # TODO: آلة حالة (State Machine) لـ RFQ الأم.
    # if db_item.rfq.rfq_status.status_name_key != "OPEN": # إذا كان rfq محمل
    #    raise BadRequestException(detail="لا يمكن تحديث بند طلب عرض الأسعار هذا في حالة الـ RFQ الأم الحالية.")

    # TODO: التحقق من وجود product_id, unit_of_measure_id إذا تم تحديثهما
    #       (على الرغم من أن التعديل لا يسمح بتحديث هذه الحقول حالياً).

    return rfqs_crud.update_rfq_item(db=db, db_rfq_item=db_item, item_in=item_in)


def delete_rfq_item_service(db: Session, rfq_item_id: int, current_user: User):
    """
    خدمة لحذف بند طلب عرض أسعار (RFQ Item) موجود.
    تتضمن التحقق من الصلاحيات (المشتري/المسؤول) ومراحل دورة حياة الـ RFQ.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rfq_item_id (int): معرف بند الـ RFQ المراد حذفه.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على بند الـ RFQ.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بحذف بند الـ RFQ.
        BadRequestException: إذا كان الـ RFQ في حالة لا تسمح بحذف البند.
    """
    db_item = get_rfq_item_details_service(db, rfq_item_id, current_user) # يتحقق من الوجود والصلاحية

    # TODO: التحقق من أن الـ RFQ الأم لا يزال في حالة تسمح بحذف البند (مثلاً 'OPEN')
    #       لا يمكن حذف بند إذا كان قد تم قبول عرض سعر له أو تم إغلاق الـ RFQ.

    # TODO: يجب التأكد من أن حذف البند لا يجعل الـ RFQ فارغاً بدون بنود.
    # if len(db_item.rfq.items) == 1:
    #     raise BadRequestException(detail="لا يمكن حذف البند الوحيد في طلب عرض الأسعار.")

    rfqs_crud.delete_rfq_item(db=db, db_rfq_item=db_item)
    db.commit()
    return {"message": "تم حذف بند طلب عرض الأسعار بنجاح."}







