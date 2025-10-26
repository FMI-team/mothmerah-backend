# backend\src\users\services\security_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

# استيراد المودلز
from src.users.models import security_models as models # PasswordResetToken, UserSession, PhoneChangeRequest
from src.users.models.core_models import User # لـ User في العلاقات

# استيراد الـ CRUD
from src.users.crud import security_crud # لـ PasswordResetToken, UserSession, PhoneChangeRequest CRUDs
from src.users.crud import core_crud # لـ User CRUDs

# استيراد Schemas
from src.users.schemas import security_schemas as schemas # PasswordResetToken, PhoneChangeRequest, UserSession
from src.users.schemas import core_schemas as user_schemas # لـ UserChangePassword

# استيراد أدوات الأمان
from src.core.security import get_password_hash, verify_password
from src.core import security # لـ create_access_token, create_refresh_token, decode_access_token
from src.core.config import settings # لإعدادات الجلسة والقفل
# from src.db.redis_client import redis_client # لآلية حماية القوة الغاشمة - تم تعطيله

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- خدمات رموز إعادة تعيين كلمة المرور (PasswordResetToken) ---
# ==========================================================

def request_password_reset(db: Session, phone_number: str) -> dict:
    """
    خدمة لطلب إعادة تعيين كلمة المرور.
    [REQ-FUN-026]: توفير آلية "هل نسيت كلمة المرور؟".
    يرسل رمز OTP إلى رقم الجوال المسجل.

    Args:
        db (Session): جلسة قاعدة البيانات.
        phone_number (str): رقم الجوال للمستخدم.

    Returns:
        dict: رسالة تأكيد إرسال الرمز.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم.
        HTTPException: في حالة الفشل في إرسال الرمز (Mock).
    """
    user = core_crud.get_user_by_phone_number(db, phone_number=phone_number)
    if not user:
        # ملاحظة أمنية: لا نخبر المهاجم بأن الرقم غير موجود.
        print(f"Password reset requested for non-existent user: {phone_number}")
        return {"message": "إذا كان هناك حساب مرتبط برقم الجوال هذا، فقد تم إرسال رمز إعادة تعيين."}

    # 1. إنشاء رمز OTP عشوائي وآمن
    otp = ''.join(secrets.choice(string.digits) for _ in range(6))
    
    # 2. تجزئة الرمز قبل حفظه
    token_hash = get_password_hash(otp)
    
    # 3. تحديد تاريخ انتهاء الصلاحية (مثلاً 10 دقائق)
    expiry_date = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    
    # 4. حفظ الرمز المجزأ في قاعدة البيانات
    security_crud.create_password_reset_token(db, user_id=user.user_id, token_hash=token_hash, expiry_timestamp=expiry_date)
    
    # 5. محاكاة إرسال الرسالة النصية (في الإنتاج، ستكون هنا خدمة SMS من Module 11)
    print(f"--- MOCK SMS to {phone_number} ---")
    print(f"رمز إعادة تعيين كلمة المرور هو: {otp}")
    print(f"------------------------------------")
    
    # TODO: REQ-FUN-103: استدعاء خدمة الإشعارات لإرسال الـ OTP (Module 11).

    return {"message": "إذا كان هناك حساب مرتبط برقم الجوال هذا، فقد تم إرسال رمز إعادة تعيين."}

def confirm_password_reset(db: Session, phone_number: str, token: str, new_password: str) -> dict:
    """
    خدمة لتأكيد إعادة تعيين كلمة المرور باستخدام الرمز.
    [REQ-FUN-026, REQ-FUN-005]: التأكد من أن كلمة المرور الجديدة تفي بمعايير التعقيد المحددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        phone_number (str): رقم الجوال.
        token (str): الرمز (OTP).
        new_password (str): كلمة المرور الجديدة.

    Returns:
        dict: رسالة تأكيد.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم.
        BadRequestException: إذا كان الرمز غير صالح أو منتهي الصلاحية أو تم استخدامه، أو كلمة المرور ضعيفة.
    """
    user = core_crud.get_user_by_phone_number(db, phone_number=phone_number)
    if not user:
        raise NotFoundException(detail="المستخدم غير موجود.")

    db_token = security_crud.get_latest_password_reset_token_for_user(db, user_id=user.user_id)
    
    # 1. التحقق من صلاحية الرمز (REQ-FUN-026)
    if not db_token or db_token.is_used or datetime.now(timezone.utc) > db_token.expiry_timestamp:
        raise BadRequestException(detail="رمز إعادة التعيين غير صالح أو منتهي الصلاحية.")

    # 2. التحقق من تطابق الرمز
    if not verify_password(token, db_token.token_hash):
        # يمكن إضافة منطق لعد المحاولات الفاشلة هنا
        raise BadRequestException(detail="رمز إعادة التعيين غير صحيح.")

    # 3. التحقق من تعقيد كلمة المرور الجديدة (REQ-FUN-005)
    # هذا التحقق سيتم في الـ Schema (UserChangePassword)، ولكن يمكن تكراره هنا كتحقق إضافي.
    # if len(new_password) < 8: raise BadRequestException("كلمة المرور يجب أن لا تقل عن 8 أحرف.")
    # TODO: يجب التأكد من أن الـ validator في Schema UserChangePassword سيُطبق.

    # 4. تحديث كلمة المرور في قاعدة البيانات
    user.password_hash = get_password_hash(new_password)
    db.add(user)
    
    # 5. ضع علامة على أن الرمز قد استُخدم
    security_crud.mark_password_reset_token_as_used(db, db_token=db_token)
    
    # 6. إبطال جميع جلسات المستخدم الأخرى لأسباب أمنية (REQ-FUN-025)
    security_crud.deactivate_all_active_sessions_for_user(db, user_id=user.user_id)
    
    db.commit() # تأكيد العملية بالكامل

    # TODO: إخطار المستخدم بأن كلمة المرور قد تم تغييرها (Module 11).
    # TODO: تسجيل عملية إعادة تعيين كلمة المرور في سجل التدقيق (Module 13).

    return {"message": "كلمة المرور قد تم إعادة تعيينها بنجاح."}


def change_user_password(db: Session, user: User, password_data: user_schemas.UserChangePassword) -> dict:
    """
    خدمة لتغيير كلمة مرور المستخدم المسجل دخوله.
    [REQ-FUN-025, REQ-FUN-027]: توفير آلية آمنة لتغيير كلمات المرور، وطلب كلمة المرور الحالية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user (User): كائن المستخدم الحالي.
        password_data (schemas.UserChangePassword): بيانات تغيير كلمة المرور.

    Returns:
        dict: رسالة تأكيد.

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

    # TODO: إخطار المستخدم بأن كلمة المرور قد تغيرت (Module 11).
    # TODO: تسجيل حدث تغيير كلمة المرور في سجل التدقيق (Module 13).

    return {"message": "تم تحديث كلمة المرور بنجاح. تم تسجيل خروجك من جميع الأجهزة الأخرى."}


# ==========================================================
# --- خدمات إدارة جلسات المستخدمين (User Session Management) ---
# ==========================================================

def refresh_access_token(db: Session, refresh_token: str) -> str:
    """
    خدمة لتجديد الـ Access Token باستخدام الـ Refresh Token.
    [REQ-FUN-015, REQ-FUN-037]: استخدام JWTs لإدارة الجلسات، وتوفير آلية تجديد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        refresh_token (str): الـ Refresh Token المقدم من العميل.

    Returns:
        str: Access Token جديد.

    Raises:
        HTTPException: إذا كان الـ Refresh Token غير صالح أو منتهي الصلاحية، أو الجلسة غير نشطة.
    """
    # 1. فك تشفير الـ Refresh Token للحصول على حمولته
    try:
        payload = security.decode_access_token(refresh_token)
        if not payload.sid: # التأكد من أنه Refresh Token (يحتوي على session ID - sid)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    except HTTPException: # يُرمى إذا كان التوكن منتهي الصلاحية أو غير صالح
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رمز التحديث (Refresh Token) غير صالح أو منتهي الصلاحية.")

    # 2. التحقق من وجود الجلسة في قاعدة البيانات وأنها نشطة
    db_session = security_crud.get_user_session_by_id(db, session_id=payload.sid)
    if not db_session or not db_session.is_active or db_session.expiry_timestamp < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="الجلسة غير نشطة أو منتهية الصلاحية. يرجى تسجيل الدخول مرة أخرى.")

    # 3. التحقق من تطابق الـ Refresh Token المجزأ
    if not verify_password(refresh_token, db_session.refresh_token_hash):
        # TODO: يمكن إضافة منطق هنا لإبطال جميع جلسات المستخدم إذا تم اكتشاف محاولة استخدام Refresh Token خاطئ.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رمز التحديث (Refresh Token) غير صالح.")

    # 4. التحقق من أن المستخدم صاحب الجلسة لا يزال موجودًا ونشطًا
    user = core_crud.get_user_by_id(db, user_id=payload.user_id)
    if not user or user.account_status.status_name_key != "ACTIVE": # REQ-FUN-019
        # إذا تم تعطيل حساب المستخدم، حتى لو كان لديه Refresh Token صالح، يجب رفض التجديد.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="المستخدم غير نشط أو غير موجود.")

    # 5. كل شيء صحيح، قم بإنشاء وإرجاع Access Token جديد
    new_access_token = security.create_access_token(user_id=user.user_id)
    
    # 6. تحديث وقت آخر نشاط للجلسة (لأغراض انتهاء الصلاحية الآلي - REQ-FUN-039)
    db_session.last_activity_timestamp = datetime.now(timezone.utc)
    db.add(db_session)
    db.commit() # حفظ تحديث last_activity_timestamp
    db.refresh(db_session)

    # TODO: تسجيل عملية تجديد التوكن في سجلات التدقيق (Module 13).

    return new_access_token

def logout_user_session_by_id(db: Session, user_id: UUID, session_id_to_revoke: UUID) -> dict:
    """
    خدمة لتسجيل الخروج من جلسة مستخدم معينة (عبر ID الجلسة).
    تُستخدم هذه الدالة لإلغاء جلسة محددة، سواءً بواسطة المستخدم نفسه (على جهاز آخر)
    أو بواسطة مسؤول النظام.
    """
    db_session = security_crud.get_user_session_by_id(db, session_id=session_id_to_revoke)

    if not db_session:
        raise NotFoundException(detail="الجلسة المطلوبة غير موجودة.")

    # التحقق من أن الجلسة موجودة وتخص المستخدم المعني
    # هنا user_id هو المستخدم الذي يطلب الإجراء (current_user)،
    # إذا كانت الجلسة ليست له، فيجب أن يكون مسؤولاً.
    if db_session.user_id != user_id:
        # TODO: يمكن إضافة تحقق صلاحية المسؤول هنا ADMIN_USER_MANAGE_ANY
        raise ForbiddenException(detail="غير مصرح لك بتسجيل الخروج من هذه الجلسة.")

    if not db_session.is_active:
        raise BadRequestException(detail="الجلسة غير نشطة بالفعل.")

    security_crud.deactivate_user_session(db, db_session=db_session)
    # TODO: تسجيل حدث تسجيل الخروج في سجل التدقيق (Module 13).
    return {"message": "تم إنهاء الجلسة بنجاح."}


def logout_user_session(db: Session, refresh_token: str):
    """
    خدمة لتسجيل خروج المستخدم من جلسته الحالية أو من جلسة محددة.
    [REQ-FUN-038]: السماح للمستخدم بتسجيل الخروج من جلسته الحالية بشكل آمن.

    Args:
        db (Session): جلسة قاعدة البيانات.
        refresh_token (str): الـ Refresh Token المرتبط بالجلسة المراد إغلاقها.

    Returns:
        dict: رسالة تأكيد.

    Raises:
        HTTPException: إذا كان الرمز غير صالح (لا نرفعها عادة للمستخدم).
    """
    # try:
    #     payload = security.decode_access_token(refresh_token)
    #     if not payload.sid:
    #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")
    # except HTTPException:
    #     # حتى لو كان التوكن منتهي الصلاحية أو غير صالح، لا نبلغ المستخدم، فقط لا نفعل شيئًا من جانب الخادم
    #     # لأن الهدف هو إزالة الجلسة، والخطأ يعني أنها غير موجودة أصلاً أو غير صالحة.
    #     return {"message": "تم تسجيل خروجك بنجاح."}

    # db_session = security_crud.get_user_session_by_id(db, session_id=payload.sid)
    # if db_session and db_session.is_active:
    #     # التحقق من تطابق الـ Refresh Token المجزأ قبل إلغاء التنشيط (أمان إضافي)
    #     if verify_password(refresh_token, db_session.refresh_token_hash):
    #         security_crud.deactivate_user_session(db, db_session=db_session)
    #         # TODO: تسجيل حدث تسجيل الخروج في سجل التدقيق (Module 13).
    #     else:
    #         # إذا لم يتطابق الرمز، قد يكون هذا محاولة اختراق، يجب إبطال جميع جلسات المستخدم.
    #         security_crud.deactivate_all_active_sessions_for_user(db, user_id=db_session.user_id)
    #         # TODO: إخطار المستخدم بوجود نشاط مشبوه (Module 11).

    # return {"message": "تم تسجيل خروجك بنجاح."}

    try:
        payload = security.decode_access_token(refresh_token)
        # إذا لم يكن هناك sid، هذا ليس refresh token صالحًا لإدارة الجلسات
        if not payload.sid:
            raise BadRequestException(detail="رمز التحديث (Refresh Token) غير صالح. لا يحتوي على معرف الجلسة.")
    except HTTPException: # يُرمى إذا كان التوكن منتهي الصلاحية أو غير صالح
        # حتى لو كان التوكن منتهي الصلاحية أو غير صالح، لا نبلغ المستخدم، فقط لا نفعل شيئًا
        # لأن الهدف هو إزالة الجلسة، والخطأ يعني أنها غير موجودة أصلاً أو غير صالحة.
        return {"message": "تم تسجيل خروجك بنجاح."} # رسالة عامة للأمان

    # نستخدم الدالة الجديدة المخصصة لتسجيل الخروج بواسطة ID الجلسة (JTI)
    # user_id هنا سيكون هو صاحب الجلسة
    return logout_user_session_by_id(db, user_id=payload.user_id, session_id_to_revoke=payload.sid)



def logout_from_all_devices(db: Session, user: User) -> dict:
    """
    خدمة لتسجيل خروج المستخدم من جميع الجلسات النشطة على جميع الأجهزة.
    [REQ-FUN-040]: السماح للمستخدم بعرض قائمة بجلساته النشطة ... مع إمكانية تسجيل الخروج منها عن بعد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد.
    """
    num_revoked = security_crud.deactivate_all_active_sessions_for_user(db, user_id=user.user_id)

    # TODO: إخطار المستخدم بأن جميع جلساته قد تم إغلاقها (Module 11).
    # TODO: تسجيل هذا الإجراء في سجل التدقيق (Module 13).

    return {"message": f"تم تسجيل خروجك بنجاح من {num_revoked} جلسة أخرى."}

def get_active_sessions_for_user(db: Session, user: User) -> List[models.UserSession]:
    """
    خدمة لجلب قائمة بالجلسات النشطة للمستخدم الحالي.
    [REQ-FUN-040]: السماح للمستخدم بعرض قائمة بجلساته النشطة على مختلف الأجهزة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user (User): المستخدم الحالي.

    Returns:
        List[models.UserSession]: قائمة بالجلسات النشطة للمستخدم.
    """
    return security_crud.get_active_sessions_for_user(db, user_id=user.user_id)


# TODO: يمكن إضافة دالة مجدولة لتنظيف الجلسات المنتهية الصلاحية وغير النشطة (REQ-FUN-039)
#       هذه الدالة ستُستدعى بواسطة Celery Beat.
# def cleanup_inactive_sessions_scheduled(db: Session):
#     inactive_threshold = datetime.now(timezone.utc) - timedelta(minutes=settings.INACTIVE_SESSION_MINUTES)
#     num_deactivated = security_crud.deactivate_inactive_sessions_older_than(db, inactive_before=inactive_threshold)
#     print(f"[{datetime.now(timezone.utc)}] Inactive session cleanup: Deactivated {num_deactivated} sessions.")
#     return {"message": f"Deactivated {num_deactivated} inactive sessions."}

# def change_password_for_logged_in_user(
#     db: Session,
#     *,
#     user: User,
#     password_data: user_schemas.UserChangePassword
# ):
#     """
#     خدمة لتغيير كلمة مرور المستخدم المسجل دخوله.
#     """
#     # الخطوة أ: التحقق من أن كلمة المرور الحالية صحيحة
#     if not verify_password(password_data.current_password, user.password_hash):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Incorrect current password."
#         )

#     # الخطوة ب: تجزئة كلمة المرور الجديدة
#     new_password_hash = get_password_hash(password_data.new_password)
#     user.password_hash = new_password_hash
#     db.add(user)

#     # الخطوة ج (مهم جدًا للأمان): إبطال جميع جلسات المستخدم الأخرى
#     # هذا يضمن أنه إذا تم اختراق الحساب، فإن تغيير كلمة المرور 
#     # يسجل خروج المهاجم من أي جهاز آخر.
#     security_crud.revoke_all_active_sessions_for_user(db, user_id=user.user_id)

#     db.commit()

#     return {"message": "Password updated successfully. You have been logged out from all other devices."}


# def logout_from_specific_session_by_jti(db: Session, user: models.User, session_jti_to_revoke: UUID):
#     """
#     [دالة مساعدة] خدمة لتسجيل الخروج من جلسة معينة باستخدام JTI الخاص بها.
#     تُستخدم عادةً داخليًا بعد فك تشفير Refresh Token.
#     """
#     db_session = security_crud.get_user_session_by_id(db, session_id=session_jti_to_revoke) # افتراض أن get_user_session_by_id تعمل بـ JTI

#     if not db_session or db_session.user_id != user.user_id:
#         raise NotFoundException(detail="Session not found for this user.") # استخدام NotFoundException المخصص

#     security_crud.deactivate_user_session(db, db_session=db_session)
#     # TODO: تسجيل حدث تسجيل الخروج في سجل التدقيق (Module 13).
#     return {"message": "Session has been successfully revoked."}

