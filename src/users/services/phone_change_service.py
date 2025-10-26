# backend/src/users/services/phone_change_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets
import string
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

# استيراد المودلز
from src.users import models # لـ models.User, models.PhoneChangeRequest
# استيراد الـ CRUD
from src.users.crud import security_crud # لـ PhoneChangeRequest CRUDs
from src.users.crud import core_crud # لـ User CRUDs
# استيراد Schemas
from src.users.schemas import security_schemas as schemas # PhoneChangeRequest Schemas
from src.users.schemas import core_schemas as user_schemas # لـ UserRead

# استيراد أدوات الأمان
from src.core.security import get_password_hash, verify_password
from src.core.config import settings # لإعدادات OTP (مدة الصلاحية، عدد المحاولات)

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User

# TODO: استيراد خدمة الإشعارات (Module 11) لإرسال رسائل SMS.


# Helper function to generate a random OTP
def _generate_otp(length: int = 6) -> str:
    """يولد رمز تحقق عشوائي (OTP) مكون من أرقام فقط."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def initiate_phone_change(db: Session, user: models.User, request_in: schemas.PhoneChangeRequestCreate) -> models.PhoneChangeRequest:
    """
    خدمة لبدء طلب تغيير رقم الجوال للمستخدم.
    [REQ-FUN-001, REQ-FUN-004]: التحقق من صحة رقم الجوال عبر OTP.
    تتضمن التحقق من عدم استخدام الرقم الجديد، وإرسال رمز OTP للرقم القديم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user (models.User): كائن المستخدم الحالي الذي يطلب تغيير رقمه.
        request_in (schemas.PhoneChangeRequestCreate): البيانات التي تتضمن الرقم الجديد.

    Returns:
        models.PhoneChangeRequest: كائن طلب تغيير رقم الجوال الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان الرقم الجديد مسجلاً بالفعل.
        BadRequestException: إذا كان المستخدم لديه طلب تغيير جوال معلق بالفعل.
    """
    # 1. التحقق من أن الرقم الجديد غير مستخدم من قبل مستخدم آخر
    existing_user_with_new_phone = core_crud.get_user_by_phone_number(db, phone_number=request_in.new_phone_number)
    if existing_user_with_new_phone:
        raise ConflictException(detail="رقم الجوال الجديد هذا مسجل بالفعل لحساب آخر.")

    # 2. التحقق من عدم وجود طلب تغيير جوال معلق للمستخدم الحالي
    # TODO: يجب إضافة دالة CRUD لـ get_latest_pending_phone_change_request_for_user في security_crud
    #       أو التحقق من db.query(models.PhoneChangeRequest).filter(...).first()
    #       حاليا، يمكننا التحقق من أي طلب معلق.
    pending_request = db.query(models.PhoneChangeRequest).filter(
        models.PhoneChangeRequest.user_id == user.user_id,
        models.PhoneChangeRequest.request_status.in_(['PENDING_OLD_PHONE_VERIFICATION', 'PENDING_NEW_PHONE_VERIFICATION'])
    ).first()
    if pending_request:
        raise BadRequestException(detail=f"لديك بالفعل طلب تغيير رقم جوال معلق بحالة '{pending_request.request_status}'.")


    # 3. توليد رمز OTP للرقم القديم وتجزئته
    old_phone_otp = _generate_otp()
    old_phone_otp_hash = get_password_hash(old_phone_otp)

    # 4. تجهيز بيانات الطلب
    request_data = {
        "user_id": user.user_id,
        "old_phone_number": user.phone_number,
        "new_phone_number": request_in.new_phone_number,
        "old_phone_otp_code": old_phone_otp_hash,
        "request_status": "PENDING_OLD_PHONE_VERIFICATION", # الحالة الأولية
        # new_phone_otp_code سيكون None في هذه المرحلة
    }

    # 5. استدعاء CRUD لإنشاء الطلب
    db_request = security_crud.create_phone_change_request(db, request_data=request_data)

    # 6. محاكاة إرسال OTP إلى الرقم القديم (REQ-FUN-004)
    print(f"--- MOCK SMS to OLD number {user.phone_number} ---")
    print(f"رمز التحقق لتغيير رقم الجوال هو: {old_phone_otp}")
    print(f"-----------------------------------------")
    # TODO: هـام (REQ-FUN-103): استدعاء خدمة SMS من وحدة الإشعارات (Module 11) لإرسال الرمز.

    return db_request

def verify_old_phone_and_send_new_otp(db: Session, user: models.User, verification_in: schemas.PhoneChangeVerify) -> dict:
    """
    خدمة للتحقق من الرمز المرسل للرقم القديم، وإذا نجح، يتم إرسال رمز جديد إلى الرقم الجديد.
    [REQ-FUN-004]: التحقق من صحة رقم الجوال عبر OTP.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user (models.User): كائن المستخدم الحالي.
        verification_in (schemas.PhoneChangeVerify): بيانات التحقق (معرف الطلب، رمز OTP).

    Returns:
        dict: رسالة تأكيد.

    Raises:
        NotFoundException: إذا لم يتم العثور على الطلب.
        BadRequestException: إذا كانت الحالة غير صحيحة، أو الرمز غير صحيح.
    """
    req = security_crud.get_phone_change_request(db, verification_in.request_id)

    # 1. التحقق من وجود الطلب وملكيته للمستخدم
    if not req or req.user_id != user.user_id:
        raise NotFoundException(detail="طلب تغيير رقم الجوال غير موجود.")
    
    # 2. التحقق من حالة الطلب
    if req.request_status != 'PENDING_OLD_PHONE_VERIFICATION':
        raise BadRequestException(detail="حالة طلب تغيير رقم الجوال غير صالحة للتحقق من الرقم القديم.")

    # 3. التحقق من رمز OTP القديم
    if not verify_password(verification_in.otp_code, req.old_phone_otp_code):
        # TODO: يمكن إضافة منطق لعد المحاولات الفاشلة هنا قبل قفل الطلب مؤقتاً.
        req.verification_attempts += 1
        req.last_attempt_timestamp = datetime.now(timezone.utc)
        security_crud.update_phone_change_request(db, req, {"verification_attempts": req.verification_attempts, "last_attempt_timestamp": req.last_attempt_timestamp})
        raise BadRequestException(detail="رمز التحقق غير صحيح. الرجاء المحاولة مرة أخرى.")

    # 4. توليد رمز OTP للرقم الجديد وتجزئته
    new_otp = _generate_otp()
    new_otp_hash = get_password_hash(new_otp)

    # 5. تحديث حالة الطلب وإضافة الرمز الجديد
    security_crud.update_phone_change_request(db, req, {
        "new_phone_otp_code": new_otp_hash,
        "request_status": 'PENDING_NEW_PHONE_VERIFICATION',
        "verification_attempts": 0 # إعادة تعيين العداد
    })
    
    # 6. محاكاة إرسال OTP إلى الرقم الجديد
    print(f"--- MOCK SMS to NEW number {req.new_phone_number} ---")
    print(f"رمز التحقق النهائي لتغيير رقم الجوال هو: {new_otp}")
    print(f"----------------------------------------")
    # TODO: هـام (REQ-FUN-103): استدعاء خدمة SMS من وحدة الإشعارات (Module 11) لإرسال الرمز.

    return {"message": "تم التحقق من الرقم القديم بنجاح. تم إرسال رمز تحقق جديد إلى رقم جوالك الجديد."}

def finalize_phone_change(db: Session, user: models.User, verification_in: schemas.PhoneChangeVerify) -> dict:
    """
    خدمة للتحقق النهائي من الرمز المرسل للرقم الجديد وتغيير رقم المستخدم.
    [REQ-FUN-004]: التحقق من صحة رقم الجوال عبر OTP.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user (models.User): كائن المستخدم الحالي.
        verification_in (schemas.PhoneChangeVerify): بيانات التحقق (معرف الطلب، رمز OTP).

    Returns:
        dict: رسالة تأكيد.

    Raises:
        NotFoundException: إذا لم يتم العثور على الطلب.
        BadRequestException: إذا كانت الحالة غير صحيحة، أو الرمز غير صحيح.
        ConflictException: إذا كان الرقم الجديد قد أصبح مستخدماً من قبل مستخدم آخر في هذه الأثناء.
    """
    req = security_crud.get_phone_change_request(db, verification_in.request_id)

    # 1. التحقق من وجود الطلب وملكيته للمستخدم
    if not req or req.user_id != user.user_id:
        raise NotFoundException(detail="طلب تغيير رقم الجوال غير موجود.")
    
    # 2. التحقق من حالة الطلب
    if req.request_status != 'PENDING_NEW_PHONE_VERIFICATION':
        raise BadRequestException(detail="حالة طلب تغيير رقم الجوال غير صالحة للتحقق النهائي.")
        
    # 3. التحقق من رمز OTP الجديد
    if not verify_password(verification_in.otp_code, req.new_phone_otp_code):
        # TODO: يمكن إضافة منطق لعد المحاولات الفاشلة هنا.
        req.verification_attempts += 1
        req.last_attempt_timestamp = datetime.now(timezone.utc)
        security_crud.update_phone_change_request(db, req, {"verification_attempts": req.verification_attempts, "last_attempt_timestamp": req.last_attempt_timestamp})
        raise BadRequestException(detail="رمز التحقق غير صحيح.")

    # 4. التحقق من أن الرقم الجديد لم يصبح مستخدمًا في هذه الأثناء
    existing_user_with_new_phone = core_crud.get_user_by_phone_number(db, phone_number=req.new_phone_number)
    if existing_user_with_new_phone and existing_user_with_new_phone.user_id != user.user_id:
        raise ConflictException(detail="رقم الجوال الجديد هذا مسجل بالفعل لحساب آخر أثناء عملية التغيير.")

    # 5. تحديث رقم جوال المستخدم
    user.phone_number = req.new_phone_number
    user.phone_verified_at = datetime.now(timezone.utc) # يعتبر موثقاً
    db.add(user)

    # 6. تحديث حالة الطلب إلى 'COMPLETED'
    security_crud.update_phone_change_request(db, req, {"request_status": 'COMPLETED'})
    
    db.commit()

    # TODO: إخطار المستخدم بأن رقم جواله قد تغير بنجاح (Module 11).
    # TODO: تسجيل تغيير رقم الجوال في سجل التدقيق (Audit Log - Module 13).

    return {"message": "رقم الجوال قد تم تغييره بنجاح."}

def cancel_phone_change_request(db: Session, request_id: int, current_user: User) -> dict:
    """
    خدمة لإلغاء طلب تغيير رقم الجوال.
    """
    req = security_crud.get_phone_change_request(db, request_id)

    if not req or req.user_id != current_user.user_id:
        raise NotFoundException(detail="طلب تغيير رقم الجوال غير موجود.")

    if req.request_status == 'COMPLETED':
        raise BadRequestException(detail="لا يمكن إلغاء طلب تم إكماله بالفعل.")

    security_crud.update_phone_change_request(db, req, {"request_status": 'CANCELLED'})
    db.commit()
    return {"message": "تم إلغاء طلب تغيير رقم الجوال بنجاح."}