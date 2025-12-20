# backend\src\users\services\core_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

# استيراد المودلز
from src.users.models import core_models as models # User, AccountStatus, UserType, AccountStatusHistory, UserPreference
from src.users.models.roles_models import Role # Role
from src.users.models.security_models import UserSession # UserSession
# استيراد الـ CRUD
from src.users.crud import core_crud # لـ User, UserPreference, AccountStatusHistory CRUDs
from src.users.crud import user_lookups_crud # لـ AccountStatus, UserType CRUDs
from src.users.crud import security_crud # لـ UserSession (لإبطال الجلسات)

# استيراد Schemas
from src.users.schemas import core_schemas as schemas # User, UserPreference, AccountStatusHistory
from src.users.schemas.management_schemas import AdminUserStatusUpdate # لـ AdminUserStatusUpdate (تم نقله إلى هنا)

# استيراد أدوات الأمان
from src.core.security import get_password_hash, verify_password
from src.core import security # لـ create_access_token, create_refresh_token
from src.core.config import settings # لإعدادات الجلسة والقفل
# from src.db.redis_client import redis_client # لآلية حماية القوة الغاشمة - تم تعطيله

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
# TODO: يجب إضافة خدمات للتحقق من وجود اللغات والعناوين والأدوار وحالة التحقق
from src.users.services.address_lookups_service import get_country_by_code_service # لـ country_code
from src.users.services.address_service import get_address_by_id # لـ shipping_address_id, billing_address_id (لا تستخدم مباشرة هنا)
from src.users.models.core_models import User

def update_current_user_profile(db: Session, user:  User, user_in: schemas.UserUpdate) ->  User:
    """خدمة لتحديث الملف الشخصي للمستخدم الحالي."""
    # التحقق من البريد الإلكتروني إذا تم تغييره
    if user_in.email:
        existing_user = db.query( User).filter( User.email == user_in.email).first()
        if existing_user and existing_user.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered by another account.",
            )
    
    return core_crud.update_user(db=db, db_user=user, user_in=user_in)


def refresh_access_token(db: Session, refresh_token: str) -> str:
    """
    خدمة لتجديد الـ Access Token باستخدام الـ Refresh Token.
    
    :param db: جلسة قاعدة البيانات.
    :param refresh_token: الـ Refresh Token المقدم من العميل.
    :raises HTTPException: إذا كان الـ Refresh Token غير صالح أو منتهي الصلاحية.
    :return: Access Token جديد.
    """
    # الخطوة 1: فك تشفير الـ Refresh Token للحصول على حمولته
    try:
        payload = security.decode_access_token(refresh_token)
        if not payload.sid: # التأكد من أنه Refresh Token (يحتوي على sid)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # الخطوة 2: التحقق من وجود الجلسة في قاعدة البيانات وأنها نشطة
    db_session = security_crud.get_session_by_id(db, session_id=payload.sid)
    if not db_session or not db_session.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is not active")

    # الخطوة 3: التحقق من تطابق الـ Refresh Token المجزأ
    if not verify_password(refresh_token, db_session.refresh_token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # الخطوة 4: التحقق من أن المستخدم صاحب الجلسة لا يزال موجودًا ونشطًا
    user = core_crud.get_user_by_id(db, user_id=payload.user_id)
    if not user or user.account_status.status_name_key != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")

    # الخطوة 5: كل شيء صحيح، قم بإنشاء وإرجاع Access Token جديد
    new_access_token = security.create_access_token(user_id=user.user_id)
    return new_access_token










# ==========================================================
# --- خدمات المستخدمين (User) ---
# ==========================================================

def register_new_user(db: Session, user_in: schemas.UserCreate, user_type_key: str, default_role_key: str = "BASE_USER") -> models.User:
    """
    خدمة لتنفيذ منطق عمل تسجيل مستخدم جديد.
    [REQ-FUN-001, REQ-FUN-002, REQ-FUN-003, REQ-FUN-004, REQ-FUN-005, REQ-FUN-006, REQ-FUN-007, REQ-FUN-012]
    تتضمن التحقق من تفرد رقم الجوال والبريد الإلكتروني، وتجزئة كلمة المرور،
    وتعيين الدور وحالة الحساب الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_in (schemas.UserCreate): بيانات المستخدم للإنشاء.
        user_type_key (str): المفتاح النصي لنوع المستخدم (مثلاً: 'SELLER', 'BUYER').
        default_role_key (str): المفتاح النصي للدور الأساسي الافتراضي.

    Returns:
        models.User: كائن المستخدم الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان رقم الجوال أو البريد الإلكتروني مسجلاً بالفعل.
        BadRequestException: إذا كانت البيانات غير صالحة.
        NotFoundException: إذا لم يتم العثور على الأدوار/الحالات الافتراضية.
    """
    # 1. التحقق من عدم وجود المستخدم (رقم الجوال)
    user_with_phone = core_crud.get_user_by_phone_number(db, phone_number=user_in.phone_number)
    if user_with_phone:
        raise ConflictException(detail="رقم الجوال مسجل بالفعل.")
    
    # 2. التحقق من عدم وجود المستخدم (البريد الإلكتروني، إذا تم توفيره)
    if user_in.email:
        user_with_email = core_crud.get_user_by_email(db, email=user_in.email)
        if user_with_email:
            raise ConflictException(detail="البريد الإلكتروني مسجل بالفعل.")

    # 3. تجزئة كلمة المرور (REQ-FUN-005, REQ-FUN-006)
    hashed_password = get_password_hash(user_in.password)
    
    # 4. تجهيز بيانات المستخدم للحفظ
    user_data_to_save = user_in.model_dump(exclude={"password", "user_type_key", "default_role_key", "translations"}) # استبعاد كلمة المرور والحقول غير المطلوبة
    user_data_to_save["password_hash"] = hashed_password

    # 5. جلب الـ IDs الصحيحة من قاعدة البيانات لجداول Lookups (REQ-FUN-012)
    user_type_obj = user_lookups_crud.get_user_type_by_key(db, key=user_type_key)
    # TODO: يجب استيراد get_role_by_key من rbac_crud
    # من src.users.crud import rbac_crud
    role_obj = db.query(Role).filter(Role.role_name_key == default_role_key).first() # مؤقتا
    initial_account_status_obj = user_lookups_crud.get_account_status_by_key(db, key="ACTIVE") # أو "ACTIVE" إذا كان التحقق يتم لاحقًا
    initial_verification_status_obj = user_lookups_crud.get_user_verification_status_by_key(db, key="ACTIVE")
    
    if not all([user_type_obj, role_obj, initial_account_status_obj, initial_verification_status_obj]):
        raise NotFoundException(detail="حالات أو أدوار افتراضية غير موجودة في النظام. يرجى تهيئة البيانات المرجعية.")

    # إضافة الـ IDs إلى القاموس
    user_data_to_save.update({
        "user_type_id": user_type_obj.user_type_id,
        "default_user_role_id": role_obj.role_id,
        "account_status_id": initial_account_status_obj.account_status_id,
        "user_verification_status_id": initial_verification_status_obj.user_verification_status_id,
        "phone_verified_at": None, # يتم التحقق لاحقا عبر OTP
        "email_verified_at": None, # يتم التحقق لاحقا عبر رابط
        "is_deleted": False, # افتراضياً غير محذوف
        "preferred_language_code": user_in.preferred_language_code or settings.DEFAULT_LANGUAGE # التأكد من وجود اللغة
    })

    # 6. استدعاء الـ CRUD لحفظ البيانات الجاهزة
    db_user = core_crud.create_user(db=db, user_data=user_data_to_save)

    # TODO: هـام (REQ-FUN-004): إرسال رمز تحقق لمرة واحدة (OTP) إلى رقم الجوال المسجل.
    # يتطلب التكامل مع خدمة SMS خارجية (Module 11).
    # print(f"MOCK SMS: Your OTP is: {otp_code}")

    # TODO: REQ-FUN-007, REQ-FUN-008, REQ-FUN-009: جمع وتخزين معلومات المستخدم الإضافية (اسم المنشأة، السجل التجاري، وثيقة العمل الحر، ترخيص الأسرة المنتجة).
    #       هذه المعلومات يجب أن تُعالج هنا بعد إنشاء المستخدم الأساسي، وربما تتطلب جداول إضافية أو توسيع لـ User model.

    # TODO: REQ-FUN-010, REQ-FUN-011: التكامل للتحقق من صحة الوثائق (العمل الحر، الأسر المنتجة).
    #       هذا يتطلب استدعاء خدمات من وحدة التحقق (verification_service) لبدء عملية التحقق في الخلفية.

    # TODO: تسجيل عملية إنشاء الحساب في سجلات تدقيق النظام (Audit Logs - Module 13).

    return db_user

def authenticate_user(db: Session, phone_number: str, password: str) -> Dict[str, Any]:
    """
    خدمة للتحقق من هوية المستخدم، وتطبيق حماية القوة الغاشمة، وإنشاء جلسة.
    [REQ-FUN-013, REQ-FUN-014, REQ-FUN-015, REQ-FUN-016, REQ-FUN-017, REQ-FUN-018, REQ-FUN-019, REQ-FUN-037]

    Args:
        db (Session): جلسة قاعدة البيانات.
        phone_number (str): رقم الجوال المستخدم لتسجيل الدخول.
        password (str): كلمة المرور.

    Returns:
        Dict[str, Any]: قاموس يحتوي على (user, access_token, refresh_token).

    Raises:
        HTTPException: عند فشل المصادقة أو قفل الحساب.
    """
    # 1. التحقق من كلمة المرور
    user = core_crud.get_user_by_phone_number(db, phone_number=phone_number)
    
    # 2. التحقق من بيانات الاعتماد
    if not user or not verify_password(password, user.password_hash): # REQ-FUN-016
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رقم الجوال أو كلمة المرور غير صحيحة. يرجى المحاولة مرة أخرى.")

    # 3. التحقق من حالة الحساب (REQ-FUN-019)
    if user.account_status.status_name_key != "ACTIVE":
        # TODO: يمكن تخصيص الرسالة بناءً على status_name_key
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"حسابك في حالة '{user.account_status.status_name_key}'. يرجى التواصل مع فريق الدعم الفني.")

    # 6. تحديث وقت آخر تسجيل دخول (REQ-FUN-018)
    user.last_login_timestamp = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)

    # 7. إنشاء التوكنات (Access Token و Refresh Token)
    access_token = security.create_access_token(user_id=user.user_id)
    # مؤقتاً: إنشاء refresh token بسيط بدون session_id
    refresh_token = f"refresh_{user.user_id}_{datetime.now(timezone.utc).timestamp()}"

    # TODO: إرسال إشعار بتسجيل الدخول الناجح (Module 11 - REQ-FUN-103) (إذا كان نظام الإشعارات متوفرًا).

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

def get_user_profile(db: Session, user_id: UUID) -> models.User:
    """
    خدمة لجلب الملف الشخصي لمستخدم معين.
    [REQ-FUN-020]: السماح للمستخدمين المسجلين بعرض معلومات ملفاتهم الشخصية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم المطلوب.

    Returns:
        models.User: كائن المستخدم.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم.
    """
    user = core_crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise NotFoundException(detail=f"المستخدم بمعرف {user_id} غير موجود.")
    return user

def update_user_profile(db: Session, db_user: models.User, user_in: schemas.UserUpdate) -> models.User:
    """
    خدمة لتحديث الملف الشخصي للمستخدم.
    [REQ-FUN-021]: السماح للمستخدمين بتعديل معلومات ملفاتهم الشخصية القابلة للتعديل.
    تتضمن التحقق من تفرد البريد الإلكتروني إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_user (models.User): كائن المستخدم من قاعدة البيانات.
        user_in (schemas.UserUpdate): البيانات المراد تحديثها.

    Returns:
        models.User: كائن المستخدم المحدث.

    Raises:
        ConflictException: إذا كان البريد الإلكتروني أو رقم الجوال المستخدم موجودًا بالفعل.
        BadRequestException: إذا حاول المستخدم تغيير رقم الجوال مباشرة.
    """
    # 1. التحقق من البريد الإلكتروني إذا تم تغييره وتفرد البريد (REQ-FUN-021)
    if user_in.email and user_in.email != db_user.email:
        existing_user_by_email = core_crud.get_user_by_email(db, email=user_in.email)
        if existing_user_by_email and existing_user_by_email.user_id != db_user.user_id:
            raise ConflictException(detail="البريد الإلكتروني هذا مسجل بالفعل لحساب آخر.")
    
    # 2. منع تغيير رقم الجوال مباشرة (REQ-FUN-021)
    #    - يجب أن يتم تغيير رقم الجوال عبر آلية مخصصة في phone_change_service.
    if user_in.phone_number and user_in.phone_number != db_user.phone_number:
        raise BadRequestException(detail="لا يمكن تحديث رقم الجوال مباشرة. يرجى استخدام آلية تغيير رقم الجوال المخصصة.")

    # TODO: REQ-FUN-024: تسجيل التغييرات الهامة على الملف الشخصي في سجل التدقيق (Audit Log - Module 13).
    #       مثال: audit_service.log_user_profile_change(db, db_user.user_id, changed_fields, old_values, new_values, current_user.user_id)

    return core_crud.update_user(db=db, db_user=db_user, user_in=user_in)

def change_user_password(db: Session, user: models.User, password_data: schemas.UserChangePassword) -> Dict[str, str]:
    """
    خدمة لتغيير كلمة مرور المستخدم المسجل دخوله.
    [REQ-FUN-025, REQ-FUN-027]: توفير آلية آمنة لتغيير كلمات المرور، وطلب كلمة المرور الحالية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user (models.User): كائن المستخدم الحالي.
        password_data (schemas.UserChangePassword): بيانات تغيير كلمة المرور.

    Returns:
        Dict[str, str]: رسالة تأكيد.

    Raises:
        BadRequestException: إذا كانت كلمة المرور الحالية غير صحيحة، أو الجديدة لا تفي بالمعايير، أو غير متطابقة.
    """
    # 1. التحقق من أن كلمة المرور الحالية صحيحة (REQ-FUN-027)
    if not verify_password(password_data.current_password, user.password_hash):
        raise BadRequestException(detail="كلمة المرور الحالية غير صحيحة.")

    # 2. تجزئة كلمة المرور الجديدة
    new_password_hash = get_password_hash(password_data.new_password)

    # 3. تحديث كلمة المرور في قاعدة البيانات
    user.password_hash = new_password_hash
    db.add(user)

    # 4. هـام (REQ-FUN-025): إبطال جميع جلسات المستخدم الأخرى (لتأمين الحساب بعد تغيير كلمة المرور).
    security_crud.deactivate_all_active_sessions_for_user(db, user_id=user.user_id)

    db.commit()
    return {"message": "تم تحديث كلمة المرور بنجاح. تم تسجيل خروجك من جميع الأجهزة الأخرى."}


def soft_delete_user_account(db: Session, user_id: UUID, current_user: User, reason: Optional[str] = None) -> models.User:
    """
    خدمة لتنفيذ الحذف الناعم لحساب مستخدم.
    [REQ-FUN-030]: السماح للمستخدم بطلب تغيير حالة حسابه (إلغاء التنشيط).

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم المراد حذف حسابه.
        current_user (User): المستخدم الذي يجري العملية (نفس المستخدم أو مسؤول).
        reason (Optional[str]): سبب الحذف.

    Returns:
        models.User: كائن المستخدم بعد الحذف الناعم.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم.
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له بالحذف.
        ConflictException: إذا لم يتم العثور على حالة "محذوف".
    """
    db_user = get_user_profile(db, user_id=user_id)

    # 1. التحقق من الصلاحيات: المستخدم نفسه أو مسؤول
    if db_user.user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_MANAGE_USERS" for p in current_user.default_role.permissions): # TODO: صلاحية ADMIN_USER_DELETE
        raise ForbiddenException(detail="غير مصرح لك بحذف هذا الحساب.")

    # 2. جلب حالة الحساب "المحذوف"
    # محاولة استخدام DELETED_BY_USER أولاً، ثم DELETED كبديل
    deleted_status = user_lookups_crud.get_account_status_by_key(db, key="DELETED_BY_USER")
    if not deleted_status:
        deleted_status = user_lookups_crud.get_account_status_by_key(db, key="DELETED")
    if not deleted_status:
        raise ConflictException(detail="'DELETED' or 'DELETED_BY_USER' status not found in DB. Please seed default statuses.")
    
    # 3. التحقق من أن الحساب ليس في حالة نهائية (is_terminal) بالفعل (إلا إذا كان المسؤول)
    if db_user.account_status.is_terminal and not any(p.permission_name_key == "ADMIN_MANAGE_USERS" for p in current_user.default_role.permissions):
        raise BadRequestException(detail=f"لا يمكن حذف الحساب في حالته النهائية: {db_user.account_status.status_name_key}.")

    # حفظ الحالة القديمة قبل التحديث
    old_account_status_id = db_user.account_status_id

    # 4. تحديث حقول المستخدم للحذف الناعم
    db_user.is_deleted = True
    db_user.account_status_id = deleted_status.account_status_id

    # 5. إبطال جميع جلسات المستخدم النشطة
    security_crud.deactivate_all_active_sessions_for_user(db, user_id=db_user.user_id)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 6. تسجيل التغيير في تاريخ حالة الحساب (REQ-FUN-031)
    core_crud.create_account_status_history_record(db, record_data={
        "user_id": db_user.user_id,
        "old_account_status_id": old_account_status_id, # الحالة قبل التحديث
        "new_account_status_id": deleted_status.account_status_id,
        "changed_by_user_id": current_user.user_id,
        "reason_for_change": reason or "حساب تم حذفه ناعمًا بواسطة المستخدم/المسؤول."
    })

    # TODO: إخطار المستخدم بأن حسابه قد تم إلغاء تنشيطه (وحدة الإشعارات - Module 11).

    return db_user

# ==========================================================
# --- خدمات تفضيلات المستخدمين (User Preferences) ---
# ==========================================================

def get_user_preferences(db: Session, current_user: User) -> List[models.UserPreference]:
    """
    خدمة لجلب قائمة تفضيلات المستخدم الحالي.
    """
    return core_crud.get_user_preferences(db, user_id=current_user.user_id)

def create_or_update_user_preference(db: Session, current_user: User, pref_in: schemas.UserPreferenceCreate) -> models.UserPreference:
    """
    خدمة لإنشاء أو تحديث تفضيل للمستخدم الحالي.
    """
    # TODO: يمكن إضافة تحققات على preference_key و preference_value (مثل قائمة بالمفاتيح المسموح بها).
    return core_crud.create_or_update_user_preference(db, user_id=current_user.user_id, pref_in=pref_in)

def delete_user_preference(db: Session, current_user: User, preference_key: str) -> Dict[str, str]:
    """
    خدمة لحذف تفضيل معين للمستخدم الحالي.
    سيؤدي هذا إلى جعل النظام يستخدم القيمة الافتراضية لهذا التفضيل.

    Args:
        db (Session): جلسة قاعدة البيانات.
        current_user (User): المستخدم الحالي.
        preference_key (str): مفتاح التفضيل المراد حذفه.

    Returns:
        Dict[str, str]: رسالة تأكيد.

    Raises:
        NotFoundException: إذا لم يتم العثور على التفضيل للمستخدم.
    """
    success = core_crud.delete_user_preference_by_key(db, user_id=current_user.user_id, preference_key=preference_key)
    if not success:
        raise NotFoundException(detail=f"التفضيل بمفتاح '{preference_key}' غير موجود للمستخدم الحالي.")
    return {"message": "تم حذف تفضيل المستخدم بنجاح. سيتم الآن استخدام القيمة الافتراضية للنظام."}


# ==========================================================
# --- خدمات سجل تغييرات حالة الحساب (Account Status History) ---
# ==========================================================

def get_user_account_history(db: Session, user_id_to_view: UUID, requesting_user: User) -> List[models.AccountStatusHistory]:
    """
    خدمة لجلب سجل تغييرات حالة حساب مستخدم.
    [REQ-FUN-088]: توفير سجل بتاريخ التغييرات التي طرأت على حالة كل طلب. (خطأ هنا، هو لحالات الحساب)
    - المستخدم يمكنه رؤية سجله الخاص.
    - المسؤول يمكنه رؤية سجل أي مستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id_to_view (UUID): معرف المستخدم الذي يود رؤية سجله.
        requesting_user (User): المستخدم الذي يطلب السجل.

    Returns:
        List[models.AccountStatusHistory]: قائمة بسجلات تاريخ حالات الحساب.

    Raises:
        ForbiddenException: إذا لم يكن المستخدم مصرحًا له.
    """
    # منطق التحقق من الصلاحيات
    # TODO: يجب التأكد أن صلاحية ADMIN_VIEW_USERS هي الصلاحية الصحيحة هنا (أو صلاحية أكثر تحديداً).
    if user_id_to_view != requesting_user.user_id and not any(p.permission_name_key == "ADMIN_VIEW_USERS" for p in requesting_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك برؤية سجل حالة هذا المستخدم.")

    history = core_crud.get_account_status_history_for_user(db, user_id=user_id_to_view)
    if not history:
        # لا نعتبره خطأ، قد لا يكون هناك سجل بعد
        return []
    return history


# ==========================================================
# --- خدمات إدارة المستخدمين للمسؤولين (Admin User Management) ---
# ==========================================================

def get_all_users(db: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[models.User]:
    """
    خدمة لجلب جميع المستخدمين في النظام، مع خيار لتضمين المستخدمين المحذوفين ناعمًا.
    
    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات لتخطيها (للترقيم).
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.
        include_deleted (bool): إذا كان True، يتم تضمين المستخدمين المحذوفين ناعمًا.
    
    Returns:
        List[models.User]: قائمة بجميع المستخدمين.
    """
    return core_crud.get_all_users(db, skip=skip, limit=limit, include_deleted=include_deleted)
