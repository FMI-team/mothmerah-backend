# backend\src\users\crud\security_crud.py

from sqlalchemy.orm import Session
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

# استيراد المودلز من Users (المجموعة 1)
from src.users.models import security_models as models # PasswordResetToken, PhoneChangeRequest, UserSession
# استيراد Schemas (إذا لزم الأمر لـ Type Hinting)
from src.users.schemas import security_schemas as schemas


# ==========================================================
# --- CRUD Functions for PasswordResetToken (رموز إعادة تعيين كلمة المرور) ---
# ==========================================================

def create_password_reset_token(db: Session, user_id: UUID, token_hash: str, expiry_timestamp: datetime) -> models.PasswordResetToken:
    """
    ينشئ سجل رمز إعادة تعيين كلمة مرور جديد في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم الذي ينتمي إليه الرمز.
        token_hash (str): النسخة المجزأة (hashed) من الرمز.
        expiry_timestamp (datetime): تاريخ ووقت انتهاء صلاحية الرمز.

    Returns:
        models.PasswordResetToken: كائن الرمز الذي تم إنشاؤه.
    """
    db_token = models.PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expiry_timestamp=expiry_timestamp,
        is_used=False # الافتراضي هو غير مستخدم عند الإنشاء
    )
    db.add(db_token)
    db.commit() # يتم الـ commit هنا لأن الرمز يجب أن يُحفظ فوراً
    db.refresh(db_token)
    return db_token

def get_password_reset_token_by_id(db: Session, token_id: int) -> Optional[models.PasswordResetToken]:
    """
    يجلب سجل رمز إعادة تعيين كلمة مرور واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        token_id (int): معرف الرمز المطلوب.

    Returns:
        Optional[models.PasswordResetToken]: كائن الرمز أو None.
    """
    return db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token_id == token_id).first()

def get_latest_password_reset_token_for_user(db: Session, user_id: UUID) -> Optional[models.PasswordResetToken]:
    """
    يجلب أحدث رمز إعادة تعيين كلمة مرور نشط وغير مستخدم لمستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.

    Returns:
        Optional[models.PasswordResetToken]: أحدث رمز أو None.
    """
    return db.query(models.PasswordResetToken).filter(
        and_(
            models.PasswordResetToken.user_id == user_id,
            models.PasswordResetToken.is_used == False,
            models.PasswordResetToken.expiry_timestamp > datetime.now(timezone.utc)
        )
    ).order_by(models.PasswordResetToken.created_at.desc()).first()

def mark_password_reset_token_as_used(db: Session, db_token: models.PasswordResetToken) -> models.PasswordResetToken:
    """
    يضع علامة على رمز إعادة تعيين كلمة المرور بأنه "مستخدم".

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_token (models.PasswordResetToken): كائن الرمز من قاعدة البيانات.

    Returns:
        models.PasswordResetToken: كائن الرمز المحدث.
    """
    db_token.is_used = True
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

# لا يوجد delete_password_reset_token مباشر، بل يتم الاعتماد على is_used وتاريخ الانتهاء لتنظيف دوري.


# ==========================================================
# --- CRUD Functions for PhoneChangeRequest (طلبات تغيير رقم الجوال) ---
# ==========================================================

def create_phone_change_request(db: Session, request_in: schemas.PhoneChangeRequestCreate, user_id: UUID, old_phone_number: str, old_phone_otp_hash: str, new_phone_otp_hash: Optional[str] = None, request_status: str = "PENDING_OLD_PHONE_VERIFICATION") -> models.PhoneChangeRequest:
    """
    ينشئ سجل طلب تغيير رقم جوال جديد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        request_in (schemas.PhoneChangeRequestCreate): البيانات الأساسية للطلب.
        user_id (UUID): معرف المستخدم صاحب الطلب.
        old_phone_number (str): رقم الجوال القديم للمستخدم.
        old_phone_otp_hash (str): تجزئة رمز OTP المرسل للرقم القديم.
        new_phone_otp_hash (Optional[str]): تجزئة رمز OTP المرسل للرقم الجديد (يتم تعيينه لاحقاً).
        request_status (str): الحالة الأولية للطلب.

    Returns:
        models.PhoneChangeRequest: كائن الطلب الذي تم إنشاؤه.
    """
    db_request = models.PhoneChangeRequest(
        user_id=user_id,
        old_phone_number=old_phone_number,
        new_phone_number=request_in.new_phone_number,
        old_phone_otp_code=old_phone_otp_hash,
        new_phone_otp_code=new_phone_otp_hash,
        request_status=request_status
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def get_phone_change_request(db: Session, request_id: int) -> Optional[models.PhoneChangeRequest]:
    """
    يجلب طلب تغيير رقم جوال واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        request_id (int): معرف الطلب المطلوب.

    Returns:
        Optional[models.PhoneChangeRequest]: كائن الطلب أو None.
    """
    return db.query(models.PhoneChangeRequest).filter(models.PhoneChangeRequest.request_id == request_id).first()

def update_phone_change_request(db: Session, db_request: models.PhoneChangeRequest, request_data_update: dict) -> models.PhoneChangeRequest:
    """
    يحدث بيانات طلب تغيير رقم جوال موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_request (models.PhoneChangeRequest): كائن الطلب من قاعدة البيانات.
        request_data_update (dict): قاموس بالبيانات المراد تحديثها.

    Returns:
        models.PhoneChangeRequest: كائن الطلب المحدث.
    """
    for key, value in request_data_update.items():
        setattr(db_request, key, value)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

# لا يوجد delete_phone_change_request مباشر، يتم إدارة الحالة عبر request_status.


# ==========================================================
# --- CRUD Functions for UserSession (جلسات المستخدمين) ---
# ==========================================================

def create_user_session(db: Session, user_id: UUID, expiry_timestamp: datetime, refresh_token_hash: str, ip_address: Optional[str] = None, device_identifier: Optional[str] = None, user_agent: Optional[str] = None) -> models.UserSession:
    """
    ينشئ سجل جلسة مستخدم جديدة في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم صاحب الجلسة.
        expiry_timestamp (datetime): تاريخ انتهاء صلاحية الجلسة.
        refresh_token_hash (str): النسخة المجزأة من الـ refresh token.
        ip_address (Optional[str]): عنوان IP الذي تم منه تسجيل الدخول.
        device_identifier (Optional[str]): معرف الجهاز/المتصفح.
        user_agent (Optional[str]): معلومات وكيل المستخدم.

    Returns:
        models.UserSession: كائن الجلسة الذي تم إنشاؤه.
    """
    db_session = models.UserSession(
        user_id=user_id,
        expiry_timestamp=expiry_timestamp,
        refresh_token_hash=refresh_token_hash,
        ip_address=ip_address,
        device_identifier=device_identifier,
        user_agent=user_agent,
        is_active=True, # افتراضيًا نشط عند الإنشاء
    )
    db.add(db_session)
    db.commit() # يتم الـ commit هنا لأن الجلسة يجب أن تُحفظ فوراً
    db.refresh(db_session)
    return db_session

def get_user_session_by_id(db: Session, session_id: UUID) -> Optional[models.UserSession]:
    """
    يجلب جلسة مستخدم عن طريق الـ ID الخاص بها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        session_id (UUID): معرف الجلسة الفريد.

    Returns:
        Optional[models.UserSession]: كائن الجلسة إن وجد، وإلا None.
    """
    return db.query(models.UserSession).filter(models.UserSession.session_id == session_id).first()

def get_user_session_by_refresh_token_hash(db: Session, refresh_token_hash: str) -> Optional[models.UserSession]:
    """
    يجلب جلسة مستخدم عن طريق تجزئة الـ Refresh Token.

    Args:
        db (Session): جلسة قاعدة البيانات.
        refresh_token_hash (str): تجزئة الـ Refresh Token.

    Returns:
        Optional[models.UserSession]: كائن الجلسة إن وجد، وإلا None.
    """
    return db.query(models.UserSession).filter(models.UserSession.refresh_token_hash == refresh_token_hash).first()


def get_active_sessions_for_user(db: Session, user_id: UUID) -> List[models.UserSession]:
    """
    جلب قائمة بجميع الجلسات النشطة لمستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.

    Returns:
        List[models.UserSession]: قائمة بالجلسات النشطة.
    """
    return db.query(models.UserSession).filter(
        models.UserSession.user_id == user_id,
        models.UserSession.is_active == True,
        models.UserSession.expiry_timestamp > datetime.now(timezone.utc)
    ).all()

def deactivate_user_session(db: Session, db_session: models.UserSession) -> models.UserSession:
    """
    يقوم بإلغاء تنشيط جلسة مستخدم (يستخدم عند تسجيل الخروج أو انتهاء الصلاحية).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_session (models.UserSession): كائن الجلسة المراد إلغاء تنشيطه.

    Returns:
        models.UserSession: كائن الجلسة بعد تحديثه.
    """
    db_session.is_active = False
    db_session.logout_timestamp = datetime.now(timezone.utc)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def deactivate_all_active_sessions_for_user(db: Session, user_id: UUID) -> int:
    """
    يقوم بإلغاء تنشيط كل الجلسات النشطة لمستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.

    Returns:
        int: عدد الجلسات التي تم إلغاؤها.
    """
    # عملية تحديث مجمعة وأكثر كفاءة من جلب كل الجلسات وتحديثها في حلقة
    num_deactivated = db.query(models.UserSession).filter(
        models.UserSession.user_id == user_id,
        models.UserSession.is_active == True
    ).update(
        {
            models.UserSession.is_active: False,
            models.UserSession.logout_timestamp: datetime.now(timezone.utc)
        },
        synchronize_session=False # ضروري للأداء في التحديث المجمع
    )
    db.commit()
    return num_deactivated

def deactivate_inactive_sessions_older_than(db: Session, inactive_before: datetime) -> int:
    """
    يقوم بإلغاء تنشيط الجلسات النشطة التي كان آخر نشاط لها قبل الوقت المحدد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        inactive_before (datetime): الطابع الزمني الذي تُعتبر الجلسات غير نشطة إذا كان آخر نشاط لها قبله.

    Returns:
        int: عدد الجلسات التي تم إلغاء تنشيطها.
    """
    num_deactivated = db.query(models.UserSession).filter(
        models.UserSession.is_active == True,
        models.UserSession.last_activity_timestamp < inactive_before
    ).update(
        {
            models.UserSession.is_active: False,
            models.UserSession.logout_timestamp: datetime.now(timezone.utc)
        },
        synchronize_session=False
    )
    db.commit()
    return num_deactivated