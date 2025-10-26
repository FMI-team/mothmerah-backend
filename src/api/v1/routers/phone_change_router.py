# backend\src\api\v1\routers\phone_change_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from uuid import UUID # لمعالجة معرفات المستخدمين
from typing import List, Optional, Dict # لتعريف أنواع البيانات في Python

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User as UserModel # مودل المستخدم، لضمان User type hint

# استيراد Schemas (هياكل البيانات)
from src.users.schemas import security_schemas as schemas # PhoneChangeRequestCreate, PhoneChangeVerify, PhoneChangeRequestRead

# استيراد الخدمات (منطق العمل)
from src.users.services import phone_change_service # لـ initiate_phone_change, verify_old_phone_and_send_new_otp, finalize_phone_change, cancel_phone_change_request


# تعريف الراوتر الرئيسي لتغيير رقم الجوال.
router = APIRouter(
    prefix="/users/phone-change", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر
    tags=["Users - Profile & Management"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.get_current_active_user)] # جميع نقاط الوصول هنا تتطلب مستخدمًا مصادقًا ونشطًا
)

# ================================================================
# --- نقاط الوصول لتغيير رقم الجوال (Phone Change) ---
# ================================================================

@router.post(
    "/initiate",
    response_model=schemas.PhoneChangeRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Authenticated User] بدء عملية تغيير رقم الجوال",
    description="""
    يسمح للمستخدم المصادق عليه ببدء عملية تغيير رقم جواله.
    يتم إرسال رمز تحقق (OTP) إلى رقم الجوال الحالي للمستخدم للمصادقة الأولية.
    (REQ-FUN-004)
    """,
)
async def initiate_phone_change_endpoint(
    request_in: schemas.PhoneChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لبدء عملية تغيير رقم الجوال للمستخدم الحالي."""
    return phone_change_service.initiate_phone_change(db=db, user=current_user, request_in=request_in)

@router.post(
    "/verify-old-phone",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="[Authenticated User] التحقق من رقم الجوال القديم وإرسال رمز جديد",
    description="""
    يسمح للمستخدم بالتحقق من رقم جواله القديم باستخدام رمز OTP.
    عند النجاح، يتم إرسال رمز OTP جديد إلى رقم الجوال الجديد للتحقق النهائي.
    (REQ-FUN-004)
    """,
)
async def verify_old_phone_and_send_new_otp_endpoint(
    verification_in: schemas.PhoneChangeVerify,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول للتحقق من الرقم القديم وإرسال OTP للرقم الجديد."""
    return phone_change_service.verify_old_phone_and_send_new_otp(db=db, user=current_user, verification_in=verification_in)

@router.post(
    "/finalize",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="[Authenticated User] إنهاء عملية تغيير رقم الجوال",
    description="""
    يسمح للمستخدم بتأكيد رقم الجوال الجديد باستخدام رمز OTP الذي تم إرساله إليه.
    عند النجاح، يتم تحديث رقم الجوال الأساسي للمستخدم في ملفه الشخصي.
    (REQ-FUN-004)
    """,
)
async def finalize_phone_change_endpoint(
    verification_in: schemas.PhoneChangeVerify,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لإنهاء عملية تغيير رقم الجوال."""
    return phone_change_service.finalize_phone_change(db=db, user=current_user, verification_in=verification_in)

@router.post(
    "/{request_id}/cancel",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="[Authenticated User] إلغاء طلب تغيير رقم الجوال",
    description="""
    يسمح للمستخدم بإلغاء طلب تغيير رقم الجوال المعلق.
    """,
)
async def cancel_phone_change_request_endpoint(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لإلغاء طلب تغيير رقم الجوال."""
    return phone_change_service.cancel_phone_change_request(db=db, request_id=request_id, current_user=current_user)