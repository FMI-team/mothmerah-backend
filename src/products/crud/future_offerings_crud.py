# backend\src\products\crud\future_offerings_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز (تفترض أنها موجودة في هذه المسارات)
from src.products.models import offerings_models as models # ExpectedCrop, ExpectedCropTranslation, ProductPriceHistory
# from src.products.models import statuses_models # ExpectedCropStatus, ExpectedCropStatusTranslation
from src.lookups.models import ExpectedCropStatus, ExpectedCropStatusTranslation # <-- تم التعديل هنا
from src.products.schemas import future_offerings_schemas as schemas

# ==========================================================
# --- CRUD Functions for ExpectedCrop (المحاصيل المتوقعة) ---
# ==========================================================

def create_expected_crop(db: Session, crop_in: schemas.ExpectedCropCreate, producer_id: UUID, offering_status_id: int) -> models.ExpectedCrop:
    """
    ينشئ سجلاً جديداً لمحصول متوقع في قاعدة البيانات.
    يقوم أيضًا بإنشاء الترجمات المضمنة في الـ schema.

    Args:
        db (Session): جلسة قاعدة البيانات.
        crop_in (schemas.ExpectedCropCreate): بيانات المحصول المتوقع للإنشاء، بما في ذلك الترجمات.
        producer_id (UUID): معرف المستخدم (المنتج/المزارع) الذي ينشئ المحصول.
        offering_status_id (int): معرف الحالة الأولية للمحصول (يُحدد بواسطة طبقة الخدمة).

    Returns:
        models.ExpectedCrop: كائن المحصول المتوقع الذي تم إنشاؤه.
    """
    db_crop = models.ExpectedCrop(
        producer_user_id=producer_id,
        product_id=crop_in.product_id,
        custom_product_name_key=crop_in.custom_product_name_key,
        expected_quantity=crop_in.expected_quantity,
        unit_of_measure_id=crop_in.unit_of_measure_id,
        expected_harvest_start_date=crop_in.expected_harvest_start_date,
        expected_harvest_end_date=crop_in.expected_harvest_end_date,
        offering_status_id=offering_status_id,
        cultivation_notes_key=crop_in.cultivation_notes_key,
        asking_price_per_unit=crop_in.asking_price_per_unit,
        is_organic=crop_in.is_organic
    )
    db.add(db_crop)
    db.flush() # للحصول على expected_crop_id قبل حفظ الترجمات

    if crop_in.translations:
        for trans_in in crop_in.translations:
            db_translation = models.ExpectedCropTranslation(
                expected_crop_id=db_crop.expected_crop_id,
                language_code=trans_in.language_code,
                translated_product_name=trans_in.translated_product_name,
                translated_cultivation_notes=trans_in.translated_cultivation_notes
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_crop)
    return db_crop

def get_expected_crop(db: Session, expected_crop_id: int) -> Optional[models.ExpectedCrop]:
    """
    يجلب سجل محصول متوقع واحد بالـ ID الخاص به، بما في ذلك ترجماته وحالته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع المطلوب.

    Returns:
        Optional[models.ExpectedCrop]: كائن المحصول المتوقع أو None إذا لم يتم العثور عليه.
    """
    return db.query(models.ExpectedCrop).options(
        joinedload(models.ExpectedCrop.translations),
        joinedload(models.ExpectedCrop.status) # تحميل حالة العرض (ExpectedCropStatus)
    ).filter(models.ExpectedCrop.expected_crop_id == expected_crop_id).first()

def get_all_expected_crops(db: Session, producer_id: Optional[UUID] = None, status_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models.ExpectedCrop]:
    """
    يجلب قائمة بجميع المحاصيل المتوقعة، مع خيارات للتصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        producer_id (Optional[UUID]): تصفية حسب معرف المنتج/المزارع (اختياري).
        status_id (Optional[int]): تصفية حسب معرف حالة العرض (اختياري).
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.ExpectedCrop]: قائمة بكائنات المحاصيل المتوقعة.
    """
    query = db.query(models.ExpectedCrop).options(
        joinedload(models.ExpectedCrop.translations),
        joinedload(models.ExpectedCrop.status)
    )
    if producer_id:
        query = query.filter(models.ExpectedCrop.producer_user_id == producer_id)
    if status_id:
        query = query.filter(models.ExpectedCrop.offering_status_id == status_id)
    return query.offset(skip).limit(limit).all()

def update_expected_crop(db: Session, db_crop: models.ExpectedCrop, crop_in: schemas.ExpectedCropUpdate) -> models.ExpectedCrop:
    """
    يحدث بيانات سجل محصول متوقع موجود.
    لا يقوم بتحديث الحالة هنا بشكل مباشر، بل يتم ذلك عبر دالة `update_expected_crop_status`.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_crop (models.ExpectedCrop): كائن المحصول المتوقع من قاعدة البيانات.
        crop_in (schemas.ExpectedCropUpdate): البيانات المراد تحديثها.

    Returns:
        models.ExpectedCrop: كائن المحصول المتوقع المحدث.
    """
    update_data = crop_in.model_dump(exclude_unset=True, exclude={"offering_status_id"}) # لا نحدث الحالة هنا
    for key, value in update_data.items():
        setattr(db_crop, key, value)
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)
    return db_crop

def update_expected_crop_status(db: Session, db_crop: models.ExpectedCrop, new_status_id: int) -> models.ExpectedCrop:
    """
    يحدث حالة المحصول المتوقع. تُستخدم هذه الدالة لتطبيق "الحذف الناعم"
    أو لتغيير حالة المحصول في دورة حياته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_crop (models.ExpectedCrop): كائن المحصول المتوقع من قاعدة البيانات.
        new_status_id (int): معرف الحالة الجديدة للمحصول.

    Returns:
        models.ExpectedCrop: كائن المحصول المتوقع بعد تحديث حالته.
    """
    db_crop.offering_status_id = new_status_id
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)
    return db_crop

# TODO: لا يوجد delete_expected_crop مباشر لأن الحذف يكون ناعمًا بتغيير الحالة.

# ==========================================================
# --- CRUD Functions for ExpectedCropTranslation (ترجمات المحاصيل المتوقعة) ---
# ==========================================================

def create_expected_crop_translation(db: Session, expected_crop_id: int, trans_in: schemas.ExpectedCropTranslationCreate) -> models.ExpectedCropTranslation:
    """
    ينشئ ترجمة جديدة لسجل محصول متوقع معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع الأم.
        trans_in (schemas.ExpectedCropTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.ExpectedCropTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models.ExpectedCropTranslation(
        expected_crop_id=expected_crop_id,
        language_code=trans_in.language_code,
        translated_product_name=trans_in.translated_product_name,
        translated_cultivation_notes=trans_in.translated_cultivation_notes
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_expected_crop_translation(db: Session, expected_crop_id: int, language_code: str) -> Optional[models.ExpectedCropTranslation]:
    """
    يجلب ترجمة محصول متوقع محددة بالـ ID الخاص بالمحصول ورمز اللغة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        expected_crop_id (int): معرف المحصول المتوقع.
        language_code (str): رمز اللغة (مثلاً: 'ar', 'en').

    Returns:
        Optional[models.ExpectedCropTranslation]: كائن الترجمة أو None إذا لم يتم العثور عليها.
    """
    return db.query(models.ExpectedCropTranslation).filter(
        and_(
            models.ExpectedCropTranslation.expected_crop_id == expected_crop_id,
            models.ExpectedCropTranslation.language_code == language_code
        )
    ).first()

def update_expected_crop_translation(db: Session, db_translation: models.ExpectedCropTranslation, trans_in: schemas.ExpectedCropTranslationUpdate) -> models.ExpectedCropTranslation:
    """
    يحدث ترجمة محصول متوقع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.ExpectedCropTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.ExpectedCropTranslationUpdate): البيانات المراد تحديثها للترجمة.

    Returns:
        models.ExpectedCropTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_expected_crop_translation(db: Session, db_translation: models.ExpectedCropTranslation):
    """
    يحذف ترجمة محصول متوقع معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.ExpectedCropTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for ProductPriceHistory (سجل أسعار المنتج) ---
#    ملاحظة: هذا الجدول للسجلات التاريخية فقط (immutable)، لذا لا توجد دوال تحديث أو حذف.
# ==========================================================

def create_product_price_history(db: Session, history_in: schemas.ProductPriceHistoryCreate, changed_by_user_id: Optional[UUID] = None) -> models.ProductPriceHistory:
    """
    ينشئ سجلاً جديداً لتاريخ سعر المنتج في قاعدة البيانات.
    هذه الدالة تُستخدم لتسجيل كل تغيير في سعر خيار تعبئة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        history_in (schemas.ProductPriceHistoryCreate): بيانات سجل السعر للإنشاء.
        changed_by_user_id (Optional[UUID]): معرف المستخدم الذي أجرى التغيير (إذا كان يدويًا أو مسؤولاً).
                                              يُترك None إذا كان التغيير آليًا.

    Returns:
        models.ProductPriceHistory: كائن سجل السعر الذي تم إنشاؤه.
    """
    db_history = models.ProductPriceHistory(
        product_packaging_option_id=history_in.product_packaging_option_id,
        old_price_per_unit=history_in.old_price_per_unit,
        new_price_per_unit=history_in.new_price_per_unit,
        change_reason=history_in.change_reason,
        changed_by_user_id=changed_by_user_id
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history

def get_product_price_history(db: Session, price_history_id: int) -> Optional[models.ProductPriceHistory]:
    """
    يجلب سجل تاريخ سعر منتج واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        price_history_id (int): معرف سجل السعر المطلوب.

    Returns:
        Optional[models.ProductPriceHistory]: كائن سجل السعر أو None إذا لم يتم العثور عليه.
    """
    return db.query(models.ProductPriceHistory).filter(models.ProductPriceHistory.price_history_id == price_history_id).first()

def get_all_product_price_history_for_packaging_option(db: Session, packaging_option_id: int, skip: int = 0, limit: int = 100) -> List[models.ProductPriceHistory]:
    """
    يجلب جميع سجلات تاريخ الأسعار لخيار تعبئة معين.
    يتم ترتيب السجلات حسب الطابع الزمني بترتيب تنازلي (الأحدث أولاً).

    Args:
        db (Session): جلسة قاعدة البيانات.
        packaging_option_id (int): معرف خيار التعبئة الذي ترتبط به سجلات الأسعار.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.ProductPriceHistory]: قائمة بكائنات سجلات الأسعار.
    """
    return db.query(models.ProductPriceHistory).filter(
        models.ProductPriceHistory.product_packaging_option_id == packaging_option_id
    ).order_by(models.ProductPriceHistory.price_change_timestamp.desc()).offset(skip).limit(limit).all()

# TODO: لا يوجد تحديث أو حذف لـ ProductPriceHistory لأنه جدول سجلات تاريخية (immutable).

# ==========================================================
# --- CRUD Functions for ExpectedCropStatus (حالات المحاصيل المتوقعة) ---
# ==========================================================

def create_expected_crop_status(db: Session, status_in: schemas.ExpectedCropStatusCreate) -> ExpectedCropStatus:
    """
    ينشئ حالة جديدة للمحصول المتوقع في قاعدة البيانات، مع ترجماتها المضمنة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas.ExpectedCropStatusCreate): بيانات الحالة للإنشاء، بما في ذلك الترجمات.

    Returns:
        ExpectedCropStatus: كائن الحالة الذي تم إنشاؤه.
    """
    db_status = ExpectedCropStatus(status_name_key=status_in.status_name_key)
    db.add(db_status)
    db.flush() # للحصول على status_id قبل حفظ الترجمات

    if status_in.translations:
        for trans_in in status_in.translations:
            db_translation = ExpectedCropStatusTranslation(
                status_id=db_status.status_id,
                language_code=trans_in.language_code,
                translated_status_name=trans_in.translated_status_name,
                translated_description=trans_in.translated_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_expected_crop_status(db: Session, status_id: int) -> Optional[ExpectedCropStatus]:
    """
    يجلب حالة محصول متوقع واحدة بالـ ID الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): معرف الحالة المطلوب.

    Returns:
        Optional[ExpectedCropStatus]: كائن الحالة أو None إذا لم يتم العثور عليه.
    """
    return db.query(ExpectedCropStatus).options(
        joinedload(ExpectedCropStatus.translations)
    ).filter(ExpectedCropStatus.status_id == status_id).first()

def get_all_expected_crop_statuses(db: Session, skip: int = 0, limit: int = 100) -> List[ExpectedCropStatus]:
    """
    يجلب قائمة بجميع حالات المحاصيل المتوقعة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[ExpectedCropStatus]: قائمة بكائنات الحالات.
    """
    return db.query(ExpectedCropStatus).options(
        joinedload(ExpectedCropStatus.translations)
    ).offset(skip).limit(limit).all()

def update_expected_crop_status(db: Session, db_status: ExpectedCropStatus, status_in: schemas.ExpectedCropStatusUpdate) -> ExpectedCropStatus:
    """
    يحدث بيانات حالة محصول متوقع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (ExpectedCropStatus): كائن الحالة من قاعدة البيانات.
        status_in (schemas.ExpectedCropStatusUpdate): البيانات المراد تحديثها للحالة.

    Returns:
        ExpectedCropStatus: كائن الحالة المحدث.
    """
    update_data = status_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_status, key, value)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def delete_expected_crop_status(db: Session, db_status: ExpectedCropStatus):
    """
    يحذف حالة محصول متوقع معينة (حذف صارم).
    TODO: قبل الحذف، يجب التحقق في طبقة الخدمة من عدم وجود أي ExpectedCrop يستخدم هذه الحالة.
          إذا كانت هناك ارتباطات، يجب منع الحذف أو مطالبة المستخدم بنقل المحاصيل المرتبطة إلى حالة أخرى.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_status (ExpectedCropStatus): كائن الحالة من قاعدة البيانات.
    """
    db.delete(db_status)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for ExpectedCropStatusTranslation (ترجمات حالات المحاصيل المتوقعة) ---
# ==========================================================

def create_expected_crop_status_translation(db: Session, status_id: int, trans_in: schemas.ExpectedCropStatusTranslationCreate) -> ExpectedCropStatusTranslation:
    """
    ينشئ ترجمة جديدة لحالة محصول متوقع.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): معرف الحالة الأم.
        trans_in (schemas.ExpectedCropStatusTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        ExpectedCropStatusTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = ExpectedCropStatusTranslation(
        status_id=status_id,
        language_code=trans_in.language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_description=trans_in.translated_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_expected_crop_status_translation(db: Session, status_id: int, language_code: str) -> Optional[ExpectedCropStatusTranslation]:
    """
    يجلب ترجمة حالة محصول متوقع محددة بالـ ID الخاص بالحالة ورمز اللغة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_id (int): معرف الحالة.
        language_code (str): رمز اللغة (مثلاً: 'ar', 'en').

    Returns:
        Optional[ExpectedCropStatusTranslation]: كائن الترجمة أو None إذا لم يتم العثور عليها.
    """
    return db.query(ExpectedCropStatusTranslation).filter(
        and_(
            ExpectedCropStatusTranslation.status_id == status_id,
            ExpectedCropStatusTranslation.language_code == language_code
        )
    ).first()

def update_expected_crop_status_translation(db: Session, db_translation: ExpectedCropStatusTranslation, trans_in: schemas.ExpectedCropStatusTranslationUpdate) -> ExpectedCropStatusTranslation:
    """
    يحدث ترجمة حالة محصول متوقع موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (ExpectedCropStatusTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.ExpectedCropStatusTranslationUpdate): البيانات المراد تحديثها للترجمة.

    Returns:
        ExpectedCropStatusTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_expected_crop_status_translation(db: Session, db_translation: ExpectedCropStatusTranslation):
    """
    يحذف ترجمة حالة محصول متوقع معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (ExpectedCropStatusTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return
