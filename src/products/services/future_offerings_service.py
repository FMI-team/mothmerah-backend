# backend\src\products\services\future_offerings_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز (للتعريفات والـ Type Hinting)
from src.products.models import offerings_models as models_offerings
from src.lookups.models import ExpectedCropStatus, ExpectedCropStatusTranslation # <-- تم التعديل هنا

from src.products.schemas import future_offerings_schemas as schemas
# استيراد دوال الـ CRUD
from src.products.crud import future_offerings_crud
# استيراد الخدمات الأخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.products.services.product_service import get_product_by_id_for_user # للتحقق من وجود المنتج الأب
from src.products.services.unit_of_measure_service import get_unit_of_measure_details # للتحقق من وحدة القياس
from src.products.services.packaging_service import get_packaging_option_details # لـ ProductPriceHistory
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

# ==========================================================
# --- خدمات المحاصيل المتوقعة (ExpectedCrop) ---
# ==========================================================

def create_new_expected_crop(db: Session, crop_in: schemas.ExpectedCropCreate, current_user: User) -> models_offerings.ExpectedCrop:
    """
    خدمة لإنشاء عرض محصول متوقع جديد بواسطة منتج (مزارع/أسرة منتجة).
    تتضمن التحقق من صحة البيانات، وجود الكيانات المرتبطة، وتعيين الحالة الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        crop_in (schemas.ExpectedCropCreate): بيانات المحصول المتوقع للإنشاء.
        current_user (User): المستخدم الحالي الذي ينشئ العرض (يفترض أنه منتج/مزارع).

    Returns:
        models_offerings.ExpectedCrop: كائن المحصول المتوقع الذي تم إنشاؤه.

    Raises:
        BadRequestException: إذا كانت بيانات المنتج غير صحيحة (product_id أو custom_product_name_key).
        NotFoundException: إذا لم يتم العثور على وحدة القياس أو المنتج المرتبط.
        ConflictException: إذا لم يتم العثور على الحالة الافتراضية.
    """
    # 1. منطق عمل: تأكد من أن المستخدم أدخل إما منتجًا موجودًا أو اسمًا مخصصًا، وليس كلاهما أو لا شيء.
    if not (crop_in.product_id or crop_in.custom_product_name_key):
        raise BadRequestException(detail="يجب توفير معرف المنتج (product_id) أو اسم مخصص للمنتج (custom_product_name_key)، وليس كلاهما أو لا شيء.")
    if crop_in.product_id and crop_in.custom_product_name_key:
        raise BadRequestException(detail="يجب توفير معرف المنتج (product_id) أو اسم مخصص للمنتج (custom_product_name_key)، وليس كلاهما.")

    # 2. التحقق من وجود وحدة القياس.
    get_unit_of_measure_details(db, crop_in.unit_of_measure_id)

    # 3. التحقق من وجود المنتج إذا تم تحديد product_id.
    if crop_in.product_id:
        # get_product_by_id_for_user يمكنها أيضًا التحقق من وجود المنتج وفعاليته
        # هنا لا نحتاج للتحقق من ملكيته لأن المنتج قد يكون عامًا، ولكن يجب أن يكون موجودًا.
        # TODO: تأكد أن دالة get_product_by_id_for_user يمكنها جلب منتج حتى لو لم يكن المستخدم مالكه (للعرض فقط).
        # أو استخدم دالة CRUD مباشرة مثل product_crud.get_product_by_id(db, product_id, show_inactive=True)
        try:
            get_product_by_id_for_user(db, product_id=crop_in.product_id, user=current_user)
        except NotFoundException:
            raise NotFoundException(detail=f"المنتج بمعرف {crop_in.product_id} غير موجود في الكتالوج.")

    # 4. جلب الحالة الافتراضية للعروض (عادةً 'متاح للحجز' أو 'معروض').
    default_status = db.query(ExpectedCropStatus).filter(ExpectedCropStatus.status_name_key == "AVAILABLE_FOR_BOOKING").first()
    if not default_status:
        raise ConflictException(detail="حالة المحصول الافتراضية 'AVAILABLE_FOR_BOOKING' غير موجودة في النظام. يرجى تهيئة البيانات المرجعية.")

    # 5. استدعاء دالة CRUD للإنشاء.
    return future_offerings_crud.create_expected_crop(
        db=db,
        crop_in=crop_in,
        producer_id=current_user.user_id,
        offering_status_id=default_status.status_id
    )

def get_expected_crop_details(db: Session, expected_crop_id: int) -> models_offerings.ExpectedCrop:
    """
    خدمة لجلب تفاصيل عرض محصول متوقع واحد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع.

    Returns:
        models_offerings.ExpectedCrop: كائن المحصول المتوقع المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على المحصول المتوقع.
    """
    crop = future_offerings_crud.get_expected_crop(db, expected_crop_id=expected_crop_id)
    if not crop:
        raise NotFoundException(detail=f"المحصول المتوقع بمعرف {expected_crop_id} غير موجود.")
    return crop

def get_all_expected_crops(db: Session, producer_id: Optional[UUID] = None, status_name_key: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models_offerings.ExpectedCrop]:
    """
    خدمة لجلب جميع المحاصيل المتوقعة، مع خيارات للتصفية حسب المنتج و/أو الحالة.
    يمكن للمشترين عرض المحاصيل المتاحة، ويمكن للمنتجين عرض محاصيلهم الخاصة (عبر producer_id).

    Args:
        db (Session): جلسة قاعدة البيانات.
        producer_id (Optional[UUID]): تصفية حسب معرف المنتج/المزارع (اختياري).
        status_name_key (Optional[str]): تصفية حسب مفتاح اسم الحالة (مثل 'AVAILABLE_FOR_BOOKING').
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models_offerings.ExpectedCrop]: قائمة بكائنات المحاصيل المتوقعة.
    """
    status_id = None
    if status_name_key:
        status_obj = db.query(ExpectedCropStatus).filter(ExpectedCropStatus.status_name_key == status_name_key).first()
        if not status_obj:
            raise BadRequestException(detail=f"حالة المحصول المتوقع '{status_name_key}' غير موجودة.")
        status_id = status_obj.status_id

    return future_offerings_crud.get_all_expected_crops(db, producer_id=producer_id, status_id=status_id, skip=skip, limit=limit)

def get_my_expected_crops(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[models_offerings.ExpectedCrop]:
    """
    خدمة لجلب المحاصيل المتوقعة الخاصة بالمنتج (المزارع) الحالي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي (المنتج/المزارع).
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models_offerings.ExpectedCrop]: قائمة بكائنات المحاصيل المتوقعة الخاصة بالبائع.
    """
    return future_offerings_crud.get_all_expected_crops(db, producer_id=current_user.user_id, skip=skip, limit=limit)

def update_expected_crop(db: Session, expected_crop_id: int, crop_in: schemas.ExpectedCropUpdate, current_user: User) -> models_offerings.ExpectedCrop:
    """
    خدمة لتحديث سجل محصول متوقع موجود.
    تتضمن التحقق من ملكية المستخدم، وجود الكيانات المرتبطة، ومنطق تحديث الحالة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع المراد تحديثه.
        crop_in (schemas.ExpectedCropUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي الذي يجري التحديث.

    Returns:
        models_offerings.ExpectedCrop: كائن المحصول المتوقع المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على المحصول المتوقع.
        ForbiddenException: إذا كان المستخدم لا يملك هذا المحصول.
        BadRequestException: إذا كانت بيانات التحديث غير صحيحة (product_id أو custom_product_name_key).
        ConflictException: إذا لم يتم العثور على حالة العرض الجديدة.
    """
    db_crop = get_expected_crop_details(db, expected_crop_id)

    # 1. التحقق من ملكية المستخدم
    if db_crop.producer_user_id != current_user.user_id:
        raise ForbiddenException(detail="غير مصرح لك بتحديث هذا المحصول المتوقع.")

    # 2. التحقق من منطق product_id و custom_product_name_key عند التحديث
    if crop_in.product_id is not None and crop_in.custom_product_name_key is not None:
        raise BadRequestException(detail="يجب توفير معرف المنتج (product_id) أو اسم مخصص للمنتج (custom_product_name_key)، وليس كلاهما.")
    if crop_in.product_id is not None and db_crop.product_id != crop_in.product_id:
        # التحقق من وجود المنتج الجديد إذا تم تحديده
        try:
            get_product_by_id_for_user(db, product_id=crop_in.product_id, user=current_user)
        except NotFoundException:
            raise NotFoundException(detail=f"المنتج بمعرف {crop_in.product_id} غير موجود في الكتالوج.")
    
    # 3. التحقق من وجود وحدة القياس إذا تم تحديثها
    if crop_in.unit_of_measure_id and crop_in.unit_of_measure_id != db_crop.unit_of_measure_id:
        get_unit_of_measure_details(db, crop_in.unit_of_measure_id)

    # 4. تحديث الحالة (الحذف الناعم)
    if crop_in.offering_status_id is not None and crop_in.offering_status_id != db_crop.offering_status_id:
        # التحقق من وجود الحالة الجديدة
        new_status_obj = db.query(ExpectedCropStatus).filter(ExpectedCropStatus.status_id == crop_in.offering_status_id).first()
        if not new_status_obj:
            raise BadRequestException(detail=f"حالة العرض بمعرف {crop_in.offering_status_id} غير موجودة.")
        
        # TODO: منطق عمل: إذا كانت الحالة الجديدة 'ملغاة' أو 'مكتملة'، تحقق من عدم وجود حجوزات نشطة
        # إذا كانت هناك حجوزات نشطة، قد تحتاج إلى إلغائها أو منع تغيير الحالة.

        return future_offerings_crud.update_expected_crop_status(db=db, db_crop=db_crop, new_status_id=crop_in.offering_status_id)
    
    # استدعاء دالة CRUD للتحديث (باستثناء حقل الحالة الذي تم التعامل معه بشكل منفصل)
    return future_offerings_crud.update_expected_crop(db=db, db_crop=db_crop, crop_in=crop_in)

def cancel_expected_crop(db: Session, expected_crop_id: int, current_user: User) -> models_offerings.ExpectedCrop:
    """
    خدمة لإلغاء عرض محصول متوقع (الحذف الناعم).
    تتضمن التحقق من الملكية وتحويل الحالة إلى 'ملغى'.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع المراد إلغاؤه.
        current_user (User): المستخدم الحالي.

    Returns:
        models_offerings.ExpectedCrop: كائن المحصول المتوقع بعد الإلغاء.

    Raises:
        NotFoundException: إذا لم يتم العثور على المحصول.
        ForbiddenException: إذا كان المستخدم لا يملك المحصول.
        BadRequestException: إذا كان المحصول في حالة لا تسمح بالإلغاء (مثل 'مكتمل').
        ConflictException: إذا لم يتم العثور على حالة الإلغاء في النظام.
    """
    db_crop = get_expected_crop_details(db, expected_crop_id)

    if db_crop.producer_user_id != current_user.user_id:
        raise ForbiddenException(detail="غير مصرح لك بإلغاء هذا المحصول المتوقع.")
    
    # TODO: منطق عمل: تحقق من أن الحالة الحالية تسمح بالإلغاء (مثلاً، لا يمكن إلغاء محصول تم تسليمه بالفعل).
    # TODO: تحقق من عدم وجود حجوزات نشطة للمحصول وإلغائها إذا لزم الأمر قبل تغيير الحالة إلى 'ملغى'.

    canceled_status = db.query(ExpectedCropStatus).filter(ExpectedCropStatus.status_name_key == "CANCELED").first()
    if not canceled_status:
        raise ConflictException(detail="حالة 'CANCELED' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    return future_offerings_crud.update_expected_crop_status(db=db, db_crop=db_crop, new_status_id=canceled_status.status_id)


# ==========================================================
# --- خدمات ترجمات المحاصيل المتوقعة (ExpectedCrop Translation) ---
# ==========================================================

def create_expected_crop_translation(db: Session, expected_crop_id: int, trans_in: schemas.ExpectedCropTranslationCreate, current_user: User) -> models_offerings.ExpectedCropTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لمحصول متوقع.
    تتضمن التحقق من وجود المحصول الأم وملكية المستخدم وعدم تكرار الترجمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع الأم.
        trans_in (schemas.ExpectedCropTranslationCreate): بيانات الترجمة للإنشاء.
        current_user (User): المستخدم الحالي.

    Returns:
        models_offerings.ExpectedCropTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المحصول الأم.
        ForbiddenException: إذا كان المستخدم لا يملك المحصول الأم.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    # منطق عمل: التحقق من وجود المحصول الأم وملكيته للمستخدم
    db_crop = get_expected_crop_details(db, expected_crop_id)
    if db_crop.producer_user_id != current_user.user_id:
        raise ForbiddenException(detail="غير مصرح لك بإضافة ترجمة لهذا المحصول المتوقع.")

    # منطق عمل: التحقق من عدم وجود ترجمة بنفس اللغة للمحصول
    existing_translation = future_offerings_crud.get_expected_crop_translation(db, expected_crop_id=expected_crop_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة للمحصول بمعرف {expected_crop_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return future_offerings_crud.create_expected_crop_translation(db=db, expected_crop_id=expected_crop_id, trans_in=trans_in)

def get_expected_crop_translation_details(db: Session, expected_crop_id: int, language_code: str) -> models_offerings.ExpectedCropTranslation:
    """
    خدمة لجلب ترجمة محددة لمحصول متوقع بلغة معينة، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع الأم.
        language_code (str): رمز اللغة.

    Returns:
        models_offerings.ExpectedCropTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = future_offerings_crud.get_expected_crop_translation(db, expected_crop_id=expected_crop_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للمحصول بمعرف {expected_crop_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_expected_crop_translation(db: Session, expected_crop_id: int, language_code: str, trans_in: schemas.ExpectedCropTranslationUpdate, current_user: User) -> models_offerings.ExpectedCropTranslation:
    """
    خدمة لتحديث ترجمة محصول متوقع موجودة.
    تتضمن التحقق من ملكية المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.ExpectedCropTranslationUpdate): البيانات المراد تحديثها للترجمة.
        current_user (User): المستخدم الحالي.

    Returns:
        models_offerings.ExpectedCropTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
        ForbiddenException: إذا كان المستخدم لا يملك المحصول الأم.
    """
    db_translation = get_expected_crop_translation_details(db, expected_crop_id, language_code)

    # التحقق من ملكية المستخدم للمحصول الأم
    db_crop = get_expected_crop_details(db, expected_crop_id)
    if db_crop.producer_user_id != current_user.user_id:
        raise ForbiddenException(detail="غير مصرح لك بتحديث ترجمة هذا المحصول المتوقع.")

    return future_offerings_crud.update_expected_crop_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_expected_crop_translation(db: Session, expected_crop_id: int, language_code: str, current_user: User):
    """
    خدمة لحذف ترجمة محصول متوقع معينة (حذف صارم).
    تتضمن التحقق من ملكية المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع الأم.
        language_code (str): رمز اللغة للترجمة.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
        ForbiddenException: إذا كان المستخدم لا يملك المحصول الأم.
    """
    db_translation = get_expected_crop_translation_details(db, expected_crop_id, language_code)

    # التحقق من ملكية المستخدم للمحصول الأم
    db_crop = get_expected_crop_details(db, expected_crop_id)
    if db_crop.producer_user_id != current_user.user_id:
        raise ForbiddenException(detail="غير مصرح لك بحذف ترجمة هذا المحصول المتوقع.")

    future_offerings_crud.delete_expected_crop_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة المحصول المتوقع بنجاح."}

# ==========================================================
# --- خدمات سجل أسعار المنتج (ProductPriceHistory) ---
# ==========================================================

def create_product_price_history_entry(db: Session, history_in: schemas.ProductPriceHistoryCreate, current_user: Optional[User] = None) -> models_offerings.ProductPriceHistory:
    """
    خدمة لإنشاء سجل جديد لتاريخ سعر المنتج.
    تُستخدم هذه الدالة لتسجيل كل تغيير في سعر خيار تعبئة.
    يمكن أن يكون التغيير آليًا (بدون user_id) أو يدويًا بواسطة بائع/مسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        history_in (schemas.ProductPriceHistoryCreate): بيانات سجل السعر للإنشاء.
        current_user (Optional[User]): المستخدم الحالي الذي أجرى التغيير (إذا كان يدويًا).

    Returns:
        models_offerings.ProductPriceHistory: كائن سجل السعر الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على خيار التعبئة المرتبط.
        ForbiddenException: إذا حاول المستخدم العادي تغيير سعر لا يملكه (يجب أن يتحقق من الملكية).
    """
    # 1. التحقق من وجود خيار التعبئة.
    # TODO: يجب استيراد get_packaging_option_details من packaging_service
    from src.products.services.packaging_service import get_packaging_option_details
    packaging_option = get_packaging_option_details(db, history_in.product_packaging_option_id)

    # 2. منطق الصلاحية: إذا كان المستخدم موجودًا، يجب أن يكون هو مالك المنتج أو مسؤولاً.
    #    - يُفترض أن هذه الدالة ستُستدعى داخليًا (مثلاً عند تحديث سعر في ProductService)
    #      أو بواسطة مسؤول. إذا كانت ستُستدعى من بائع مباشر، يجب إضافة تحقق من ملكيته.
    changed_by_user_id = current_user.user_id if current_user else None

    # TODO: منطق عمل: التأكد من أن السعر الجديد ليس هو نفس السعر القديم (لتجنب سجلات مكررة).
    #       يمكن جلب آخر سجل سعر ومقارنته.
    #       last_price_history = future_offerings_crud.get_latest_price_history_for_packaging_option(db, history_in.product_packaging_option_id)
    #       if last_price_history and last_price_history.new_price_per_unit == history_in.new_price_per_unit:
    #           raise BadRequestException(detail="السعر الجديد مطابق للسعر الحالي، لن يتم إنشاء سجل جديد.")

    return future_offerings_crud.create_product_price_history(db=db, history_in=history_in, changed_by_user_id=changed_by_user_id)

def get_product_price_history_entry(db: Session, price_history_id: int) -> models_offerings.ProductPriceHistory:
    """
    خدمة لجلب سجل تاريخ سعر منتج واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        price_history_id (int): معرف سجل السعر المطلوب.

    Returns:
        models_offerings.ProductPriceHistory: كائن سجل السعر المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على سجل السعر.
    """
    history_entry = future_offerings_crud.get_product_price_history(db, price_history_id=price_history_id)
    if not history_entry:
        raise NotFoundException(detail=f"سجل تاريخ السعر بمعرف {price_history_id} غير موجود.")
    return history_entry

def get_all_product_price_history_for_packaging_option(db: Session, packaging_option_id: int, skip: int = 0, limit: int = 100) -> List[models_offerings.ProductPriceHistory]:
    """
    خدمة لجلب جميع سجلات تاريخ الأسعار لخيار تعبئة معين.
    هذه الدالة توفر رؤية تاريخية لتقلبات أسعار خيار تعبئة محدد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        packaging_option_id (int): معرف خيار التعبئة.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models_offerings.ProductPriceHistory]: قائمة بكائنات سجلات الأسعار لخيار التعبئة هذا.
    """
    # التحقق من وجود خيار التعبئة (اختياري هنا، ولكن يفضل لضمان صحة الـ ID)
    # TODO: يجب استيراد get_packaging_option_details من packaging_service
    from src.products.services.packaging_service import get_packaging_option_details
    get_packaging_option_details(db, packaging_option_id)

    return future_offerings_crud.get_all_product_price_history_for_packaging_option(db, packaging_option_id=packaging_option_id, skip=skip, limit=limit)

# ==========================================================
# --- خدمات حالات المحاصيل المتوقعة (ExpectedCropStatus) ---
# ==========================================================

def create_new_expected_crop_status(db: Session, status_in: schemas.ExpectedCropStatusCreate) -> ExpectedCropStatus:
    """
    خدمة لإنشاء حالة جديدة للمحصول المتوقع مع ترجماتها.
    هذه الدالة مخصصة لإدارة الحالات المرجعية لعروض المحاصيل (عادةً بواسطة المسؤولين).

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas.ExpectedCropStatusCreate): بيانات الحالة الجديدة، بما في ذلك مفتاح الاسم والترجمات.

    Returns:
        ExpectedCropStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس مفتاح الاسم موجودة بالفعل.
    """
    # 1. منطق عمل: التحقق من عدم وجود حالة بنفس مفتاح الاسم.
    if db.query(ExpectedCropStatus).filter(ExpectedCropStatus.status_name_key == status_in.status_name_key).first():
        raise ConflictException(detail=f"حالة المحصول المتوقع بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    
    # 2. استدعاء دالة CRUD للإنشاء.
    return future_offerings_crud.create_expected_crop_status(db=db, status_in=status_in)

def get_expected_crop_status_by_id(db: Session, status_id: int) -> ExpectedCropStatus:
    """
    خدمة لجلب حالة محصول متوقع بالـ ID الخاص بها، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID الحالة المطلوبة.

    Returns:
        ExpectedCropStatus: كائن الحالة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة بالـ ID المحدد.
    """
    # 1. جلب الحالة باستخدام دالة CRUD.
    status_obj = future_offerings_crud.get_expected_crop_status(db, status_id=status_id)
    
    # 2. التحقق من وجود الحالة.
    if not status_obj:
        raise NotFoundException(detail=f"حالة المحصول المتوقع بمعرف {status_id} غير موجودة.")
    
    return status_obj

def get_all_expected_crop_statuses(db: Session) -> List[ExpectedCropStatus]:
    """
    خدمة لجلب جميع حالات المحاصيل المتوقعة المرجعية في النظام.

    Args:
        db (Session): جلسة قاعدة البيانات.

    Returns:
        List[ExpectedCropStatus]: قائمة بكائنات الحالات.
    """
    # تستدعي دالة CRUD لجلب جميع الحالات.
    return future_offerings_crud.get_all_expected_crop_statuses(db)

def update_expected_crop_status(db: Session, status_id: int, status_in: schemas.ExpectedCropStatusUpdate) -> ExpectedCropStatus:
    """
    خدمة لتحديث حالة محصول متوقع موجودة.
    تسمح هذه الدالة بتعديل مفتاح الاسم لحالة المحصول المتوقع.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID الحالة المراد تحديثها.
        status_in (schemas.ExpectedCropStatusUpdate): البيانات المراد تحديثها (مفتاح الاسم).

    Returns:
        ExpectedCropStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة بالـ ID المحدد.
        ConflictException: إذا كانت هناك محاولة لتغيير مفتاح الاسم إلى مفتاح موجود بالفعل لحالة أخرى.
    """
    # 1. جلب الحالة باستخدام دالة الخدمة (لضمان وجودها).
    db_status = get_expected_crop_status_by_id(db, status_id)
    
    # 2. منطق عمل: إذا تم تحديث مفتاح الاسم، تحقق من عدم التكرار.
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        if db.query(ExpectedCropStatus).filter(ExpectedCropStatus.status_name_key == status_in.status_name_key).first():
            raise ConflictException(detail=f"حالة المحصول المتوقع بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    
    # 3. استدعاء دالة CRUD للتحديث.
    return future_offerings_crud.update_expected_crop_status(db=db, db_status=db_status, status_in=status_in)

def delete_expected_crop_status(db: Session, status_id: int):
    """
    خدمة لحذف حالة محصول متوقع (حذف صارم).
    هذه الدالة مخصصة لإدارة الحالات المرجعية، وتتضمن تحققات صارمة لمنع حذف الحالات المستخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID الحالة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة بالـ ID المحدد.
        ForbiddenException: إذا كانت الحالة مستخدمة حاليًا بواسطة أي عروض محاصيل متوقعة (ExpectedCrop)، لمنع كسر العلاقات.
    """
    # 1. جلب الحالة باستخدام دالة الخدمة.
    db_status = get_expected_crop_status_by_id(db, status_id)
    
    # 2. منطق عمل: التحقق من عدم وجود عروض محاصيل (ExpectedCrop) تستخدم هذه الحالة.
    #    - هذا يضمن سلامة البيانات ويمنع حذف حالة ضرورية لعرض محاصيل نشطة.
    from src.products.models.offerings_models import ExpectedCrop # استيراد هنا لتجنب التبعية الدائرية
    if db.query(ExpectedCrop).filter(ExpectedCrop.offering_status_id == status_id).count() > 0:
        raise ForbiddenException(detail=f"لا يمكن حذف حالة المحصول المتوقع بمعرف {status_id} لأنها تستخدم من قبل عروض محاصيل موجودة.")
    
    # 3. استدعاء دالة CRUD للحذف الصارم.
    future_offerings_crud.delete_expected_crop_status(db=db, db_status=db_status)
    return {"message": "تم حذف حالة المحصول المتوقع بنجاح."}

# ==========================================================
# --- خدمات ترجمات حالات المحاصيل المتوقعة (ExpectedCropStatusTranslation) ---
# ==========================================================

def create_expected_crop_status_translation(db: Session, status_id: int, trans_in: schemas.ExpectedCropStatusTranslationCreate) -> ExpectedCropStatusTranslation:
    """
    إنشاء ترجمة جديدة لحالة محصول متوقع.
    هذه الدالة مخصصة لإضافة دعم لغوي لحالات المحاصيل المتوقعة المرجعية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID الحالة الأم التي سيتم إضافة الترجمة إليها.
        trans_in (schemas.ExpectedCropStatusTranslationCreate): بيانات الترجمة الجديدة،
            بما في ذلك كود اللغة، الاسم المترجم، والوصف المترجم.

    Returns:
        ExpectedCropStatusTranslation: كائن الترجمة التي تم إنشاؤها.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة الأم بالـ ID المحدد.
        ConflictException: إذا كانت هناك ترجمة بنفس اللغة موجودة بالفعل لنفس الحالة، مما يشير إلى تكرار غير مسموح به.
    """
    # 1. منطق عمل: التحقق من وجود الحالة الأم.
    #    - تستدعي دالة الخدمة get_expected_crop_status_by_id لضمان وجود الكائن الأم.
    get_expected_crop_status_by_id(db, status_id)

    # 2. منطق عمل: التحقق من عدم وجود ترجمة بنفس اللغة لنفس الحالة.
    if future_offerings_crud.get_expected_crop_status_translation(db, status_id=status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة للحالة بمعرف {status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")
    
    # 3. استدعاء دالة CRUD لإنشاء الترجمة.
    return future_offerings_crud.create_expected_crop_status_translation(db=db, status_id=status_id, trans_in=trans_in)

def get_expected_crop_status_translation_details(db: Session, status_id: int, language_code: str) -> ExpectedCropStatusTranslation:
    """
    جلب ترجمة محددة لحالة محصول متوقع بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID الحالة الأم.
        language_code (str): رمز اللغة (مثلاً 'ar', 'en').

    Returns:
        ExpectedCropStatusTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة المحددة.
    """
    # 1. جلب الترجمة باستخدام دالة CRUD.
    translation = future_offerings_crud.get_expected_crop_status_translation(db, status_id=status_id, language_code=language_code)
    
    # 2. التحقق من وجود الترجمة.
    if not translation:
        raise NotFoundException(detail=f"الترجمة للحالة بمعرف {status_id} باللغة '{language_code}' غير موجودة.")
    
    return translation

def update_expected_crop_status_translation(db: Session, status_id: int, language_code: str, trans_in: schemas.ExpectedCropStatusTranslationUpdate) -> ExpectedCropStatusTranslation:
    """
    تحديث ترجمة حالة محصول متوقع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID الحالة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.ExpectedCropStatusTranslationUpdate): البيانات المراد تحديثها للترجمة.

    Returns:
        ExpectedCropStatusTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة المحددة.
    """
    # 1. جلب الترجمة باستخدام دالة الخدمة (لضمان وجودها).
    db_translation = get_expected_crop_status_translation_details(db, status_id, language_code)
    
    # 2. استدعاء دالة CRUD للتحديث.
    return future_offerings_crud.update_expected_crop_status_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_expected_crop_status_translation(db: Session, status_id: int, language_code: str):
    """
    حذف ترجمة حالة محصول متوقع معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): ID الحالة الأم.
        language_code (str): رمز اللغة للترجمة.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة المحددة.
    """
    # 1. جلب الترجمة باستخدام دالة الخدمة (لضمان وجودها).
    db_translation = get_expected_crop_status_translation_details(db, status_id, language_code)
    
    # 2. استدعاء دالة CRUD للحذف الصارم.
    future_offerings_crud.delete_expected_crop_status_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة حالة المحصول المتوقع بنجاح."}