# backend\src\api\v1\routers\auth_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from fastapi.security import OAuth2PasswordRequestForm # لنموذج تسجيل الدخول OAuth2
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين
from pydantic import BaseModel, Field

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي (للتسجيل/تغيير كلمة المرور)
from src.users.models.core_models import User as UserModel # مودل المستخدم، للتحقق من الصلاحيات (يُعاد تسميته لتجنب التضارب)

# استيراد Schemas (هياكل البيانات) الخاصة بالمستخدمين والمصادقة
from src.users.schemas import core_schemas as schemas # UserCreate, UserRead, UserChangePassword, Token
from src.users.schemas import security_schemas as security_schemas # PasswordResetRequestSchema, PasswordResetConfirmSchema, PhoneChangeRequestRead

# استيراد الخدمات (منطق العمل) المتعلقة بالمستخدمين والمصادقة
from src.users.services import core_service # لـ register_new_user, authenticate_user, update_user_profile, change_user_password, soft_delete_user_account
from src.users.services import security_service # لـ request_password_reset, confirm_password_reset, refresh_access_token, logout_user_session, logout_from_all_devices
from src.users.services import phone_change_service # لـ initiate_phone_change, verify_old_phone_and_send_new_otp, finalize_phone_change


# تعريف الراوتر الرئيسي للمصادقة.
router = APIRouter(
    prefix="/auth", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/auth)
    tags=["Authentication"] # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
)

# ================================================================
# --- نقاط الوصول لتسجيل المستخدمين (Registration) ---
# ================================================================

@router.post(
    "/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Public] تسجيل مستخدم جديد",
    description="""
    يسمح للمستخدمين الجدد بإنشاء حساب في المنصة.
    يتضمن جمع البيانات الأساسية، اختيار الدور، وتجزئة كلمة المرور.
    (REQ-FUN-001, REQ-FUN-002, REQ-FUN-003, REQ-FUN-005, REQ-FUN-006, REQ-FUN-012)
    """,
)
async def register_user_endpoint(
    user_in: schemas.UserCreate, # الآن user_type_key و default_role_key جزء من هذا الـ Schema
    db: Session = Depends(get_db)
):
    """نقطة وصول لتسجيل مستخدم جديد."""
    # تمرير user_type_key و default_role_key مباشرة من user_in
    return core_service.register_new_user(
        db=db,
        user_in=user_in,
        user_type_key=user_in.user_type_key, # <-- تم التعديل هنا
        default_role_key=user_in.default_role_key # <-- تم التعديل هنا
    )


# ================================================================
# --- نماذج البيانات ---
# ================================================================

class LoginRequest(BaseModel):
    """نموذج طلب تسجيل الدخول - نفس schema الـ register."""
    phone_number: str = Field(..., description="رقم الجوال للمستخدم")
    password: str = Field(..., min_length=8, description="كلمة المرور")

    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+966500000000",
                "password": "admin_password_123"
            }
        }

# ================================================================
# --- نقاط الوصول لتسجيل الدخول (Login) ---
# ================================================================

@router.post(
    "/login",
    response_model=schemas.Token,
    status_code=status.HTTP_200_OK,
    summary="[Public] تسجيل الدخول",
    description="""
    يسمح للمستخدمين بتسجيل الدخول باستخدام رقم الجوال وكلمة المرور.
    يعيد توكن الوصول (access token) للاستخدام في الطلبات اللاحقة.
    (REQ-FUN-013, REQ-FUN-014, REQ-FUN-015, REQ-FUN-016, REQ-FUN-017, REQ-FUN-018, REQ-FUN-019, REQ-FUN-037)
    """,
)
async def login_endpoint(
    user_in: LoginRequest,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتسجيل الدخول."""
    return core_service.authenticate_user(
        db=db,
        phone_number=user_in.phone_number,
        password=user_in.password
    )
