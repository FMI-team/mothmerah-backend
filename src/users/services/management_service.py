# backend\src\users\services\management_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID

# استيراد المودلز
from src.users.models import core_models as models # User, AccountStatus, UserType
from src.users.models import verification_models # LicenseType, IssuingAuthority, LicenseVerificationStatus, UserVerificationStatus
# استيراد الـ CRUD
from src.users.crud import core_crud # لـ User, AccountStatusHistory
from src.users.crud import user_lookups_crud # لـ UserType, AccountStatus, UserVerificationStatus (CRUDs)
from src.users.crud import verification_history_log_crud # لـ AccountStatusHistory

# استيراد Schemas
from src.users.schemas.management_schemas import AdminUserStatusUpdate # الـ Schema الرئيسي لهذا الملف

# استيراد Schemas الأخرى (لأنها قد تُستخدم في دوال هذا الملف)
from src.users.schemas import core_schemas as schemas_core # لـ UserTypeCreate/Update/Read, AccountStatusCreate/Update/Read
from src.users.schemas import verification_lookups_schemas as schemas_verification_lookups # لـ LicenseType, IssuingAuthority, UserVerificationStatus, LicenseVerificationStatus

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for Admin User Management (إدارة المستخدمين بواسطة المسؤول) ---
# ==========================================================

def change_user_status_by_admin(
    db: Session,
    target_user_id: UUID,
    status_data: AdminUserStatusUpdate,
    admin_user: models.User # المستخدم الذي يقوم بالإجراء (المسؤول)
) -> models.User:
    """
    [REQ-FUN-004]: خدمة لتغيير حالة حساب مستخدم بواسطة المسؤول وتوثيق هذا التغيير.
    تتضمن التحقق من وجود المستخدم والحالة الجديدة، وتسجيل التغيير في السجل التاريخي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        target_user_id (UUID): معرف المستخدم الذي سيتم تغيير حالته.
        status_data (AdminUserStatusUpdate): البيانات المطلوبة لتحديث الحالة.
        admin_user (models.User): المستخدم المسؤول الذي يقوم بالإجراء.

    Returns:
        models.User: كائن المستخدم بعد تحديث حالته.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم الهدف أو الحالة الجديدة.
        BadRequestException: إذا كانت الحالة الجديدة هي نفس الحالة الحالية أو غير صالحة.
        ForbiddenException: إذا كان المسؤول يحاول تعديل حسابه الخاص إلى حالة نهائية لا رجعة فيها (لمنع قفل المسؤول لنفسه)،
                            أو إذا كان لا يملك صلاحية كافية (التحقق يتم في الراوتر).
        ConflictException: إذا كانت هناك مشاكل في تهيئة حالات النظام.
    """
    target_user = core_crud.get_user_by_id(db, user_id=target_user_id)
    if not target_user:
        raise NotFoundException(detail="المستخدم الهدف غير موجود.")

    # 1. جلب الحالة الجديدة من قاعدة البيانات
    new_account_status = user_lookups_crud.get_account_status(db, status_id=status_data.new_status_id)
    if not new_account_status:
        raise NotFoundException(detail=f"حالة الحساب بمعرف {status_data.new_status_id} غير موجودة.")

    # 2. التحقق من أن الحالة الجديدة ليست هي الحالة الحالية (REQ-FUN-004)
    old_account_status_id = target_user.account_status_id
    if old_account_status_id == status_data.new_status_id:
        raise BadRequestException(detail="الحالة الجديدة هي نفس الحالة الحالية.")

    # 3. التحقق من منطق آلة الحالة (State Machine) للحالات
    #    - لا يمكن الانتقال من حالة نهائية (Terminal) إلى حالة أخرى إلا بواسطة مسؤولين بصلاحيات خاصة.
    #    - لا يمكن الانتقال إلى حالات معينة من حالات معينة.
    # TODO: منطق عمل: يجب تعريف آلة حالة (State Machine) واضحة لانتقال حالات الحساب.
    #       مثلاً: لا يمكن الانتقال من "BANNED" إلى "ACTIVE" مباشرة.
    #       يمكن أن يكون هناك جدول lookup يحدد الانتقالات المسموح بها.
    if target_user.account_status.is_terminal and not new_account_status.is_terminal:
        # إذا كان الحساب في حالة نهائية (مثل BANNED) ولا يحاول المسؤول نقله إلى حالة نهائية أخرى،
        # فيجب أن يكون هناك صلاحية خاصة لتجاوز الحالات النهائية.
        pass # هنا يمكن إضافة تحقق صلاحية إضافي للمسؤولين.
    
    # 4. منع المسؤول من حظر/إلغاء تنشيط حسابه الخاص بطريقة لا رجعة فيها (إلا بصلاحية أعلى)
    if target_user.user_id == admin_user.user_id and new_account_status.is_terminal:
        # TODO: يمكن إضافة استثناء للسوبر أدمن أو طلب تأكيد إضافي.
        pass

    # 5. إنشاء سجل في جدول تاريخ حالات الحساب (REQ-FUN-004, REQ-FUN-031)
    history_data = {
        "user_id": target_user.user_id,
        "old_account_status_id": old_account_status_id,
        "new_account_status_id": status_data.new_status_id,
        "changed_by_user_id": admin_user.user_id,
        "reason_for_change": status_data.reason_for_change
    }
    # TODO: يجب استدعاء create_account_status_history_record من user_lookups_crud أو core_crud أو verification_history_log_crud
    core_crud.create_account_status_history_record(db, record_data=history_data) # تم وضعها في core_crud


    # 6. تحديث حالة المستخدم الفعلية في جدول User
    target_user.account_status_id = status_data.new_status_id
    db.add(target_user)

    # 7. إلغاء تنشيط جلسات المستخدم إذا تم تعليقه أو حظره
    if new_account_status.status_name_key in ["SUSPENDED", "BANNED", "DEACTIVATED_BY_USER"]:
        security_crud.deactivate_all_active_sessions_for_user(db, user_id=target_user.user_id)

    db.commit() # تنفيذ كل التغييرات كوحدة واحدة (transaction)
    db.refresh(target_user)

    # TODO: إخطار المستخدم المتأثر بتغيير حالة حسابه (وحدة الإشعارات - Module 11).

    return target_user


# ==========================================================
# --- Services for UserType Management (إدارة أنواع المستخدمين) ---
#    (يمكن وضعها هنا لأنها تتعلق بإدارة المستخدمين)
# ==========================================================

def create_new_user_type(db: Session, type_in: schemas_core.UserTypeCreate) -> models.UserType:
    """
    خدمة لإنشاء نوع مستخدم جديد مع ترجماته الأولية.
    تتضمن التحقق من عدم تكرار المفتاح.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_in (schemas_core.UserTypeCreate): بيانات النوع للإنشاء.

    Returns:
        models.UserType: كائن النوع الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان نوع المستخدم بمفتاح معين موجوداً بالفعل.
    """
    # 1. التحقق من عدم وجود مفتاح بنفس الاسم
    existing_type = user_lookups_crud.get_user_type_by_key(db, key=type_in.user_type_name_key)
    if existing_type:
        raise ConflictException(detail=f"نوع المستخدم بمفتاح '{type_in.user_type_name_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود الترجمة الافتراضية (TODO)
    # TODO: منطق عمل: التأكد من أن translations تحتوي على ترجمة افتراضية (مثلاً العربية) عند الإنشاء.

    return user_lookups_crud.create_user_type(db, type_in=type_in)

def get_all_user_types_service(db: Session) -> List[models.UserType]:
    """خدمة لجلب كل أنواع المستخدمين مع ترجماتهم."""
    return user_lookups_crud.get_all_user_types(db)

def get_user_type_by_id_service(db: Session, type_id: int) -> models.UserType:
    """
    خدمة لجلب نوع مستخدم واحد بالـ ID، مع معالجة عدم الوجود.
    """
    db_type = user_lookups_crud.get_user_type(db, type_id=type_id)
    if not db_type:
        raise NotFoundException(detail=f"نوع المستخدم بمعرف {type_id} غير موجود.")
    return db_type

def update_user_type(db: Session, type_id: int, type_in: schemas_core.UserTypeUpdate) -> models.UserType:
    """
    خدمة لتحديث نوع مستخدم.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id (int): معرف النوع المراد تحديثه.
        type_in (schemas_core.UserTypeUpdate): البيانات المراد تحديثها.

    Returns:
        models.UserType: كائن النوع المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_type = get_user_type_by_id_service(db, type_id=type_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث user_type_name_key
    if type_in.user_type_name_key and type_in.user_type_name_key != db_type.user_type_name_key:
        existing_type_by_key = user_lookups_crud.get_user_type_by_key(db, key=type_in.user_type_name_key)
        if existing_type_by_key and existing_type_by_key.user_type_id != type_id:
            raise ConflictException(detail=f"نوع المستخدم بمفتاح '{type_in.user_type_name_key}' موجود بالفعل.")

    return user_lookups_crud.update_user_type(db, db_type=db_type, type_in=type_in)

def delete_user_type_by_id(db: Session, type_id_to_delete: int):
    """
    خدمة لحذف نوع مستخدم بشكل آمن.
    - إذا كان النوع مرتبطًا بمستخدمين، يتم نقلهم إلى النوع الافتراضي ثم يتم حذفه.
    - إذا لم يكن مرتبطًا، يتم حذفه مباشرة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        type_id_to_delete (int): معرف النوع المراد حذفه.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على النوع.
        BadRequestException: إذا حاول حذف النوع الافتراضي.
        ConflictException: إذا كانت هناك مشكلة في إعادة الإسناد.
    """
    # 1. جلب النوع المراد حذفه
    db_type_to_delete = get_user_type_by_id_service(db, type_id_to_delete)

    # 2. جلب النوع الافتراضي (هذا إعداد أساسي في النظام)
    DEFAULT_TYPE_KEY = "DEFAULT_USER"
    default_type = user_lookups_crud.get_user_type_by_key(db, key=DEFAULT_TYPE_KEY)
    if not default_type:
        raise ConflictException(detail=f"نوع المستخدم الافتراضي '{DEFAULT_TYPE_KEY}' غير موجود في النظام. يرجى تهيئة البيانات المرجعية.")

    # 3. منع حذف النوع الافتراضي نفسه
    if db_type_to_delete.user_type_id == default_type.user_type_id:
        raise BadRequestException(detail="لا يمكن حذف نوع المستخدم الافتراضي للنظام.")

    # 4. إعادة إسناد كل المستخدمين المرتبطين إلى النوع الافتراضي
    #    - هذا سيؤثر على المستخدمين الذين لديهم هذا النوع كـ user_type_id.
    users_count_with_type = user_lookups_crud.count_users_with_type(db, type_id=type_id_to_delete)
    if users_count_with_type > 0:
        user_lookups_crud.reassign_users_to_default_type(
            db=db,
            old_type_id=db_type_to_delete.user_type_id,
            default_type_id=default_type.user_type_id
        )
        # db.commit() # الـ commit سيتم في نهاية العملية
    
    # 5. الآن، بعد أن تم نقل كل المستخدمين، يمكننا حذف النوع بأمان
    user_lookups_crud.delete_user_type(db, db_type=db_type_to_delete)

    db.commit() # يجب عمل commit هنا لإتمام كل العمليات (إعادة الإسناد والحذف)

    return {"message": f"تم حذف نوع المستخدم '{db_type_to_delete.user_type_name_key}' وإعادة إسناد المستخدمين المرتبطين إلى النوع الافتراضي."}


# ==========================================================
# --- Services for AccountStatus Management (إدارة حالات الحساب) ---
#    (يمكن وضعها هنا لأنها تتعلق بإدارة المستخدمين)
# ==========================================================

def create_new_account_status(db: Session, status_in: schemas_core.AccountStatusCreate) -> models.AccountStatus:
    """
    خدمة لإنشاء حالة حساب جديدة مع ترجماتها الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        status_in (schemas_core.AccountStatusCreate): بيانات الحالة للإنشاء.

    Returns:
        models.AccountStatus: كائن الحالة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك حالة بنفس المفتاح موجودة بالفعل.
    """
    # 1. التحقق من عدم وجود حالة حساب بنفس المفتاح
    existing_status = user_lookups_crud.get_account_status_by_key(db, key=status_in.status_name_key)
    if existing_status:
        raise ConflictException(detail=f"حالة الحساب بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")
    
    # 2. التحقق من وجود الترجمة الافتراضية (TODO)
    # TODO: منطق عمل: التأكد من أن translations تحتوي على ترجمة افتراضية (مثلاً العربية) عند الإنشاء.

    return user_lookups_crud.create_account_status(db, status_in=status_in)

def get_all_account_statuses_service(db: Session) -> List[models.AccountStatus]:
    """خدمة لجلب كل حالات الحساب مع ترجماتها."""
    return user_lookups_crud.get_all_account_statuses(db)

def get_account_status_details_service(db: Session, account_status_id: int) -> models.AccountStatus:
    """
    خدمة لجلب حالة حساب واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    db_status = user_lookups_crud.get_account_status(db, account_status_id=account_status_id)
    if not db_status:
        raise NotFoundException(detail=f"حالة الحساب بمعرف {account_status_id} غير موجودة.")
    return db_status

def update_account_status(db: Session, account_status_id: int, status_in: schemas_core.AccountStatusUpdate) -> models.AccountStatus:
    """
    خدمة لتحديث حالة حساب موجودة.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        account_status_id (int): معرف الحالة المراد تحديثها.
        status_in (schemas_core.AccountStatusUpdate): البيانات المراد تحديثها.

    Returns:
        models.AccountStatus: كائن الحالة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_status = get_account_status_details_service(db, account_status_id=account_status_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث status_name_key
    if status_in.status_name_key and status_in.status_name_key != db_status.status_name_key:
        existing_status_by_key = user_lookups_crud.get_account_status_by_key(db, key=status_in.status_name_key)
        if existing_status_by_key and existing_status_by_key.account_status_id != account_status_id:
            raise ConflictException(detail=f"حالة الحساب بمفتاح '{status_in.status_name_key}' موجودة بالفعل.")

    return user_lookups_crud.update_account_status(db, db_status=db_status, status_in=status_in)

def delete_account_status_by_id(db: Session, account_status_id: int):
    """
    خدمة لحذف حالة حساب بشكل آمن.
    - إذا كان النوع مرتبطًا بمستخدمين، يتم نقلهم إلى النوع الافتراضي ثم يتم حذفه.
    - إذا لم يكن مرتبطًا، يتم حذفه مباشرة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        account_status_id (int): معرف الحالة المراد حذفه.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الحالة.
        BadRequestException: إذا حاول حذف حالة افتراضية أو نهائية.
        ConflictException: إذا كانت هناك مشكلة في إعادة الإسناد.
    """
    # 1. جلب الحالة المراد حذفها
    db_status_to_delete = get_account_status_details_service(db, account_status_id)

    # 2. جلب الحالة الافتراضية للحساب (مثلاً 'ACTIVE')
    DEFAULT_ACCOUNT_STATUS_KEY = "ACTIVE"
    default_status = user_lookups_crud.get_account_status_by_key(db, key=DEFAULT_ACCOUNT_STATUS_KEY)
    if not default_status:
        raise ConflictException(detail=f"حالة الحساب الافتراضية '{DEFAULT_ACCOUNT_STATUS_KEY}' غير موجودة في النظام. يرجى تهيئة البيانات المرجعية.")

    # 3. منع حذف الحالة الافتراضية أو الحالات النهائية
    if db_status_to_delete.account_status_id == default_status.account_status_id:
        raise BadRequestException(detail="لا يمكن حذف حالة الحساب الافتراضية.")
    if db_status_to_delete.is_terminal:
        raise BadRequestException(detail=f"لا يمكن حذف حالة الحساب النهائية '{db_status_to_delete.status_name_key}'.")

    # 4. إعادة إسناد كل المستخدمين المرتبطين إلى الحالة الافتراضية
    users_count_with_status = user_lookups_crud.count_users_with_account_status(db, status_id=account_status_id)
    if users_count_with_status > 0:
        user_lookups_crud.reassign_users_to_default_account_status(
            db=db,
            old_status_id=db_status_to_delete.account_status_id,
            default_status_id=default_status.account_status_id
        )
        # db.commit() # الـ commit سيتم في نهاية العملية
    
    # 5. الآن، بعد أن تم نقل كل المستخدمين، يمكننا حذف الحالة بأمان
    user_lookups_crud.delete_account_status(db, db_status=db_status_to_delete)

    db.commit() # يجب عمل commit هنا لإتمام كل العمليات (إعادة الإسناد والحذف)

    return {"message": f"تم حذف حالة الحساب '{db_status_to_delete.status_name_key}' وإعادة إسناد المستخدمين المرتبطين إلى الحالة الافتراضية."}

# --- خدمات ترجمات حالات الحساب (AccountStatusTranslation) ---

def create_account_status_translation(db: Session, account_status_id: int, trans_in: schemas_core.AccountStatusTranslationCreate) -> models.AccountStatus:
    """
    خدمة لإنشاء ترجمة جديدة لحالة حساب.
    تتضمن التحقق من وجود الحالة الأم وعدم تكرار الترجمة لنفس اللغة.
    """
    db_status = get_account_status_details_service(db, account_status_id) # التحقق من وجود الحالة الأم

    # التحقق من عدم وجود ترجمة بنفس اللغة
    if user_lookups_crud.get_account_status_translation(db, status_id=account_status_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة لحالة الحساب بمعرف {account_status_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    updated_status = user_lookups_crud.add_or_update_account_status_translation(db, status_id=account_status_id, trans_in=trans_in)
    db.commit() # الـ commit يتم داخل دالة CRUD
    return updated_status

def get_account_status_translation_details(db: Session, account_status_id: int, language_code: str) -> models.AccountStatusTranslation:
    """
    خدمة لجلب ترجمة حالة حساب محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        account_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة.

    Returns:
        models.AccountStatusTranslation: كائن الترجمة.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = user_lookups_crud.get_account_status_translation(db, account_status_id=account_status_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة لحالة الحساب بمعرف {account_status_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_account_status_translation(db: Session, account_status_id: int, language_code: str, trans_in: schemas_core.AccountStatusTranslationUpdate) -> models.AccountStatus:
    """
    خدمة لتحديث ترجمة حالة حساب موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        account_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas_core.AccountStatusTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.AccountStatus: كائن الحالة الأم المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_account_status_translation_details(db, account_status_id, language_code) # التحقق من وجود الترجمة
    updated_status = user_lookups_crud.add_or_update_account_status_translation(db, account_status_id=account_status_id, trans_in=schemas_core.AccountStatusTranslationCreate(
        language_code=language_code,
        translated_status_name=trans_in.translated_status_name,
        translated_status_description=trans_in.translated_status_description
    ))
    db.commit() # commit داخل الدالة crud
    return updated_status

def remove_account_status_translation(db: Session, account_status_id: int, language_code: str):
    """
    خدمة لحذف ترجمة حالة حساب معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        account_status_id (int): معرف الحالة الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_account_status_translation_details(db, account_status_id, language_code) # التحقق من وجود الترجمة
    user_lookups_crud.delete_account_status_translation(db, db_translation=db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة حالة الحساب بنجاح."}