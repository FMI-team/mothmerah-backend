# backend\src\users\services\license_service.py

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from typing import List, Optional
from uuid import UUID, uuid4 # لـ user_id, uuid4() لتوليد مفاتيح الملفات
from datetime import datetime, date, timezone # لـ Date و DateTime

# استيراد المودلز
from src.users.models import verification_models as models # License
# استيراد الـ CRUD
from src.users.crud import license_crud # لـ License CRUDs
from src.users.crud import user_lookups_crud # لـ LicenseVerificationStatus CRUDs

# استيراد Schemas
from src.users.schemas import license_schemas as schemas # License Schemas
from src.users.schemas import verification_lookups_schemas as schemas_lookups # لـ LicenseVerificationStatus, LicenseType, IssuingAuthority Schemas

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.users.services.core_service import get_user_profile # للتحقق من وجود المستخدم
from src.products.services.image_service import get_image_details # للتحقق من وجود الصور المرفوعة (إذا كانت تُعالج كصور عامة)
# TODO: خدمة التخزين السحابي (Cloud Storage Service) لرفع وحذف الملفات.
# TODO: خدمة التكامل مع APIs الجهات الحكومية (مثل منصة العمل الحر).
# TODO: خدمة الإشعارات (notifications_service) من Module 11 لإرسال التنبيهات.

from src.users.models.core_models import User


# ==========================================================
# --- خدمات التراخيص والوثائق الفعلية للمستخدمين (License) ---
# ==========================================================

def upload_new_license(
    db: Session,
    user_id: UUID,
    license_in: schemas.LicenseCreate,
    file: UploadFile # ملف الوثيقة الفعلي
) -> models.License:
    """
    خدمة لرفع وإنشاء سجل ترخيص جديد لمستخدم.
    [REQ-FUN-030]: السماح للمستخدم برفع وتحديث صور وثائقه الرسمية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم صاحب الترخيص.
        license_in (schemas.LicenseCreate): بيانات الترخيص.
        file (UploadFile): الملف الفعلي للوثيقة.

    Returns:
        models.License: كائن الترخيص الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم أو نوع الترخيص أو الجهة المصدرة.
        BadRequestException: إذا كانت بيانات الترخيص غير صالحة (مثلاً صيغة الملف، حجم الملف، تواريخ).
        ConflictException: إذا لم يتم العثور على حالة التحقق الافتراضية.
    """
    # 1. التحقق من وجود المستخدم
    # get_user_profile(db, user_id) # تم حذف هذا التحقق بناءً على تعليقات المستخدم السابقة. يمكن إعادته إذا كان ضرورياً.

    # 2. التحقق من وجود نوع الترخيص
    license_type = user_lookups_crud.get_license_type(db, license_in.license_type_id)
    if not license_type:
        raise NotFoundException(detail=f"نوع الترخيص بمعرف {license_in.license_type_id} غير موجود.")

    # 3. التحقق من وجود الجهة المصدرة (إذا تم تحديدها)
    if license_in.issuing_authority_id:
        issuing_authority = user_lookups_crud.get_issuing_authority(db, license_in.issuing_authority_id)
        if not issuing_authority:
            raise NotFoundException(detail=f"الجهة المصدرة بمعرف {license_in.issuing_authority_id} غير موجودة.")
    
    # 4. منطق رفع الملف إلى خدمة التخزين السحابي
    # TODO: هـام: التكامل مع خدمة التخزين السحابي (مثلاً AWS S3) لرفع الملفات (Module 2.ج - ImageService).
    #       يجب أن تستدعي خدمة هنا تقوم برفع الملف وتُعيد المفتاح.
    #       for now, just generate a unique key.
    file_extension = file.filename.split(".")[-1] if file.filename else "dat"
    file_storage_key = f"licenses/{user_id}/{uuid4()}.{file_extension}"
    # try:
    #     uploaded_url = cloud_storage_service.upload_file(file.file, file_storage_key, file.content_type)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"فشل في رفع الملف: {e}")

    # 5. جلب الحالة الافتراضية للتحقق
    default_verification_status = user_lookups_crud.get_license_verification_status_by_key(db, key="PENDING_REVIEW")
    if not default_verification_status:
        raise ConflictException(detail="حالة التحقق الافتراضية 'PENDING_REVIEW' غير موجودة. يرجى تهيئة البيانات المرجعية.")

    # 6. التحقق من تواريخ الصلاحية (REQ-FUN-023)
    if license_in.issue_date and license_in.expiry_date and license_in.issue_date >= license_in.expiry_date:
        raise BadRequestException(detail="تاريخ الإصدار يجب أن يكون قبل تاريخ الانتهاء.")
    if license_in.expiry_date and license_in.expiry_date < date.today():
        raise BadRequestException(detail="تاريخ انتهاء الصلاحية يجب أن يكون في المستقبل.")


    db_license = license_crud.create_license(
        db=db,
        license_in=license_in,
        user_id=user_id,
        file_storage_key=file_storage_key, # استخدام المفتاح من عملية الرفع
        verification_status_id=default_verification_status.license_verification_status_id
    )

    # TODO: هـام: بدء عملية التحقق من الترخيص (REQ-FUN-010, REQ-FUN-011).
    #       استدعاء خدمة التحقق الآلي (integration_service.verify_license_with_government_api)
    #       أو إرسال إشعار للمسؤولين لمراجعتها يدوياً.

    # TODO: تحديث حالة التحقق العامة للمستخدم (User.user_verification_status_id)
    #       orders_service.update_user_verification_status (من core_service).

    return db_license

def get_licenses_for_user(db: Session, user_id: UUID, current_user: User) -> List[models.License]:
    """
    خدمة لجلب قائمة بجميع تراخيص المستخدم (الخاصة به أو كمسؤول).
    [REQ-FUN-029]: عرض حالة التحقق من الوثائق الرسمية للمستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم صاحب التراخيص.
        current_user (User): المستخدم الذي يطلب البيانات.

    Returns:
        List[models.License]: قائمة بالتراخيص.

    Raises:
        ForbiddenException: إذا كان المستخدم غير مصرح له.
        NotFoundException: إذا لم يتم العثور على المستخدم صاحب التراخيص.
    """
    # التحقق من الصلاحيات: المستخدم نفسه أو مسؤول
    if user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_VIEW_USER_LICENSES" for p in current_user.default_role.permissions): # TODO: صلاحية ADMIN_VIEW_USER_LICENSES
        raise ForbiddenException(detail="غير مصرح لك برؤية تراخيص هذا المستخدم.")

    # التحقق من وجود المستخدم (يمكن جلب المستخدم هنا أو في الراوتر)
    # get_user_profile(db, user_id)

    return license_crud.get_licenses_for_user(db=db, user_id=user_id)

def get_license_details(db: Session, license_id: int, current_user: User) -> models.License:
    """
    خدمة لجلب تفاصيل ترخيص واحد بالـ ID، مع التحقق من ملكية المستخدم أو صلاحيات المسؤول.

    Args:
        db (Session): جلسة قاعدة البيانات.
        license_id (int): معرف الترخيص المطلوب.
        current_user (User): المستخدم الحالي.

    Returns:
        models.License: كائن الترخيص المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترخيص.
        ForbiddenException: إذا كان المستخدم غير مالك وليس مسؤولاً.
    """
    db_license = license_crud.get_license_by_id(db, license_id=license_id)
    if not db_license:
        raise NotFoundException(detail=f"الترخيص بمعرف {license_id} غير موجود.")

    # التحقق من الملكية
    if db_license.user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_VIEW_USER_LICENSES" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل هذا الترخيص.")
    
    return db_license

def update_license_by_user(
    db: Session,
    license_id: int,
    license_in: schemas.LicenseUpdate,
    current_user: User
) -> models.License:
    """
    خدمة لتحديث ترخيص من قبل المستخدم.
    [REQ-FUN-030]: السماح للمستخدم برفع وتحديث صور وثائقه الرسمية.
    تتضمن التحقق من الملكية، وتغيير حالة التحقق بعد التحديث.

    Args:
        db (Session): جلسة قاعدة البيانات.
        license_id (int): معرف الترخيص.
        license_in (schemas.LicenseUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models.License: كائن الترخيص المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترخيص.
        ForbiddenException: إذا لم يكن المستخدم يملك الترخيص أو غير مصرح له.
        BadRequestException: إذا حاول المستخدم تحديث حقول غير مسموح بها.
        ConflictException: إذا لم يتم العثور على حالة التحقق الافتراضية.
    """
    db_license = get_license_details(db, license_id, current_user) # التحقق من الوجود والملكية

    # 1. منع المستخدم من تحديث حالة التحقق بنفسه
    if license_in.verification_status_id is not None and db_license.verification_status_id != license_in.verification_status_id:
        raise BadRequestException(detail="لا يمكنك تغيير حالة التحقق للترخيص مباشرة.")
    
    # 2. التحقق من وجود نوع الترخيص أو الجهة المصدرة إذا تم تحديثها
    if license_in.license_type_id and license_in.license_type_id != db_license.license_type_id:
        license_type = user_lookups_crud.get_license_type(db, license_in.license_type_id)
        if not license_type:
            raise NotFoundException(detail=f"نوع الترخيص بمعرف {license_in.license_type_id} غير موجود.")
    
    if license_in.issuing_authority_id and license_in.issuing_authority_id != db_license.issuing_authority_id:
        issuing_authority = user_lookups_crud.get_issuing_authority(db, license_in.issuing_authority_id)
        if not issuing_authority:
            raise NotFoundException(detail=f"الجهة المصدرة بمعرف {license_in.issuing_authority_id} غير موجودة.")
    
    # 3. التحقق من تواريخ الصلاحية (REQ-FUN-023)
    if license_in.issue_date and license_in.expiry_date and license_in.issue_date >= license_in.expiry_date:
        raise BadRequestException(detail="تاريخ الإصدار يجب أن يكون قبل تاريخ الانتهاء.")
    if license_in.expiry_date and license_in.expiry_date < date.today():
        raise BadRequestException(detail="تاريخ انتهاء الصلاحية يجب أن يكون في المستقبل.")

    # 4. تحديث الترخيص
    updated_license = license_crud.update_license(db=db, db_license=db_license, license_in=license_in)

    # 5. إعادة تفعيل عملية التحقق تلقائيًا (REQ-FUN-031)
    #    - بعد أي تحديث من المستخدم، تعود حالة التحقق إلى "قيد المراجعة".
    pending_review_status = user_lookups_crud.get_license_verification_status_by_key(db, key="PENDING_REVIEW")
    if not pending_review_status:
        raise ConflictException(detail="'PENDING_REVIEW' status for license verification not found.")
    
    license_crud.update_license_verification_status(db, db_license=updated_license, new_verification_status_id=pending_review_status.license_verification_status_id)

    # TODO: إخطار مسؤولي النظام (Module 11) بوجود ترخيص تم تحديثه ويحتاج مراجعة.

    return updated_license

def delete_license_by_user(db: Session, license_id: int, current_user: User):
    """
    خدمة لحذف ترخيص من قبل المستخدم.
    تتضمن التحقق من الملكية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        license_id (int): معرف الترخيص المراد حذفه.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترخيص.
        ForbiddenException: إذا لم يكن المستخدم يملك الترخيص أو غير مصرح له.
    """
    db_license = get_license_details(db, license_id, current_user) # التحقق من الوجود والملكية

    # TODO: منطق عمل: التحقق من عدم وجود ارتباطات حيوية (مثلاً إذا كان الترخيص مطلوبًا لدور نشط).
    #       يمكن أن يكون هذا التحقق ضمن verify_license_as_admin أو هنا.

    license_crud.delete_license(db=db, db_license=db_license)
    # TODO: هنا يجب إضافة منطق لحذف الملف الفعلي للصورة من خدمة التخزين السحابي (مثل AWS S3) (REQ-FUN-030).
    return {"message": "تم حذف الترخيص بنجاح."}


def get_all_licenses_as_admin(db: Session, skip: int = 0, limit: int = 100) -> List[models.License]:
    """
    [للمسؤول] خدمة لجلب قائمة بكل التراخيص في النظام.

    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات لتخطيها.
        limit (int): الحد الأقصى لعدد السجلات.

    Returns:
        List[models.License]: قائمة بكائنات التراخيص.
    """
    return license_crud.get_all_licenses(db=db, skip=skip, limit=limit)

def verify_license_as_admin(
    db: Session,
    license_id: int,
    new_status_key: str, # نستخدم key بدلاً من ID ليكون أكثر وضوحاً
    admin_user: User
) -> models.License:
    """
    [للمسؤول] خدمة لتغيير حالة التحقق لترخيص معين.
    [REQ-FUN-029]: عرض حالة التحقق من وثائقه الرسمية (يتم تحديث الحالة هنا).

    Args:
        db (Session): جلسة قاعدة البيانات.
        license_id (int): معرف الترخيص المراد تحديث حالته.
        new_status_key (str): مفتاح الحالة الجديدة (مثلاً 'APPROVED', 'REJECTED', 'EXPIRED').
        admin_user (User): المستخدم المسؤول الذي يقوم بالتحقق.

    Returns:
        models.License: كائن الترخيص المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترخيص أو الحالة الجديدة.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له (ليس مسؤولاً).
        BadRequestException: إذا كانت الحالة الجديدة غير صالحة.
    """
    db_license = license_crud.get_license_by_id(db, license_id=license_id)
    if not db_license:
        raise NotFoundException(detail=f"الترخيص بمعرف {license_id} غير موجود.")
    
    # 1. التحقق من صلاحية المسؤول (يتم التحقق في الراوتر أيضاً، لكن هنا لضمان منطق الخدمة)
    if not any(p.permission_name_key == "ADMIN_MANAGE_LICENSES" for p in admin_user.default_role.permissions): # TODO: صلاحية ADMIN_MANAGE_LICENSES
        raise ForbiddenException(detail="غير مصرح لك بتغيير حالة التحقق لهذا الترخيص.")

    # 2. جلب الحالة الجديدة
    new_status = user_lookups_crud.get_license_verification_status_by_key(db, key=new_status_key)
    if not new_status:
        raise BadRequestException(detail=f"حالة التحقق '{new_status_key}' غير موجودة. يرجى تهيئة البيانات المرجعية.")
    
    # 3. التحقق من الانتقالات المسموح بها لحالة التحقق (آلة الحالة)
    # TODO: يمكن إضافة منطق آلة الحالة هنا، مثلاً لا يمكن الانتقال من 'APPROVED' إلى 'PENDING_REVIEW' مباشرة.
    # old_status_key = db_license.verification_status.status_name_key

    # 4. تحديث حالة التحقق للترخيص
    updated_license = license_crud.update_license_verification_status(db=db, db_license=db_license, new_verification_status_id=new_status.license_verification_status_id)

    # 5. تسجيل التغيير في تاريخ التحقق للمستخدم (UserVerificationHistory)
    # TODO: يجب استدعاء create_user_verification_history_record من verification_history_log_crud
    # from src.users.crud import verification_history_log_crud
    # verification_history_log_crud.create_user_verification_history_record(db, record_data={
    #     "user_id": db_license.user_id,
    #     "old_user_verification_status_id": db_license.verification_status_id, # الحالة قبل التحديث
    #     "new_user_verification_status_id": new_status.license_verification_status_id,
    #     "changed_by_user_id": admin_user.user_id,
    #     "notes": f"تغيير حالة ترخيص بمعرف {db_license.license_id} إلى {new_status_key}"
    # })

    # 6. تحديث الحالة العامة لـ user_verification_status_id في User (REQ-FUN-029)
    #    - يجب أن يعكس هذا الحالة الأكثر تقييدًا لجميع تراخيص المستخدم، أو الحالة العامة للتحقق.
    #    - هذا يتطلب منطقًا معقدًا لحساب حالة التحقق الإجمالية للمستخدم.
    # TODO: استدعاء دالة في core_service لتحديث User.user_verification_status_id بناءً على حالة جميع التراخيص.
    
    # TODO: إخطار المستخدم (Module 11) بأن حالة ترخيصه قد تغيرت.

    return updated_license