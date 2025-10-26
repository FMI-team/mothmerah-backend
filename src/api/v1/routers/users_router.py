# backend\src\api\v1\routers\users_router.py

from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional,Dict # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User as UserModel # مودل المستخدم، لضمان User type hint

# استيراد Schemas (هياكل البيانات)
from src.users.schemas import core_schemas as schemas # UserRead, UserUpdate, UserChangePassword, UserPreferenceCreate, UserPreferenceRead
from src.users.schemas import address_schemas # AddressCreate, AddressUpdate, AddressRead

# استيراد الخدمات (منطق العمل)
from src.users.services import core_service # لـ get_user_profile, update_user_profile, change_user_password, soft_delete_user_account, get_user_preferences, create_or_update_user_preference, delete_user_preference
from src.users.services import address_service # لـ create_new_address, get_user_addresses, update_user_address, delete_user_address
from src.users.services import security_service # لـ logout_from_all_devices


# تعريف الراوتر الرئيسي لإدارة الملف الشخصي للمستخدم.
router = APIRouter(
    prefix="/users", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/users)
    tags=["Users - Profile & Management"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.get_current_active_user)] # جميع نقاط الوصول هنا تتطلب مستخدمًا مصادقًا ونشطًا
)

# ================================================================
# --- نقاط الوصول للملف الشخصي للمستخدم (User Profile) ---
# ================================================================

@router.get(
    "/me",
    response_model=schemas.UserRead,
    summary="[Authenticated User] جلب معلومات ملفي الشخصي",
    description="""
    يسمح للمستخدم المصادق عليه حاليًا بجلب معلومات ملفه الشخصي الكاملة.
    (REQ-FUN-020)
    """,
)
async def get_my_profile_endpoint(
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لجلب الملف الشخصي للمستخدم الحالي."""
    return current_user # يمكن إرجاع كائن المستخدم مباشرة لأنه يطابق UserRead


@router.patch(
    "/me",
    response_model=schemas.UserRead,
    summary="[Authenticated User] تحديث معلومات ملفي الشخصي",
    description="""
    يسمح للمستخدم المصادق عليه بتعديل معلومات ملفه الشخصي (الاسم، البريد الإلكتروني، رابط الصورة).
    (REQ-FUN-021)
    """,
)
async def update_my_profile_endpoint(
    user_in: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لتحديث الملف الشخصي للمستخدم الحالي."""
    return core_service.update_user_profile(db=db, db_user=current_user, user_in=user_in)


@router.patch(
    "/me/password",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="[Authenticated User] تغيير كلمة المرور",
    description="""
    يسمح للمستخدم المسجل دخوله بتغيير كلمة المرور الخاصة به.
    (REQ-FUN-025, REQ-FUN-027)
    """,
)
async def change_my_password_endpoint(
    password_data: schemas.UserChangePassword,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لتغيير كلمة مرور المستخدم الحالي."""
    return core_service.change_user_password(db=db, user=current_user, password_data=password_data)


@router.delete(
    "/me",
    response_model=schemas.UserRead,
    summary="[Authenticated User] إلغاء تنشيط حسابي (حذف ناعم)",
    description="""
    يسمح للمستخدم بإلغاء تنشيط حسابه (حذف ناعم) عن طريق تغيير حالته إلى 'محذوف'.
    (REQ-FUN-030)
    """,
)
async def soft_delete_my_account_endpoint(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user),
    reason: Optional[str] = None # سبب الحذف
):
    """نقطة وصول لإلغاء تنشيط حساب المستخدم الحالي (حذف ناعم)."""
    return core_service.soft_delete_user_account(db=db, user_id=current_user.user_id, current_user=current_user, reason=reason)


# ================================================================
# --- نقاط الوصول لإدارة العناوين (Addresses) ---
# ================================================================

@router.post(
    "/me/addresses",
    response_model=address_schemas.AddressRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Authenticated User] إضافة عنوان جديد",
    description="""
    يسمح للمستخدم بإضافة عنوان توصيل أو فوترة جديد إلى حساباته.
    (REQ-FUN-022)
    """,
)
async def add_address_to_my_profile_endpoint(
    address_in: address_schemas.AddressCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لإضافة عنوان جديد للمستخدم الحالي."""
    return address_service.create_new_address(db=db, address_in=address_in, current_user=current_user)

@router.get(
    "/me/addresses",
    response_model=List[address_schemas.AddressRead],
    summary="[Authenticated User] جلب جميع عناويني",
    description="""
    يجلب قائمة بجميع العناوين المسجلة لحساب المستخدم الحالي.
    (REQ-FUN-022)
    """,
)
async def get_my_addresses_endpoint(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لجلب عناوين المستخدم الحالي."""
    return address_service.get_user_addresses(db=db, current_user=current_user)

@router.get(
    "/me/addresses/{address_id}",
    response_model=address_schemas.AddressRead,
    summary="[Authenticated User] جلب تفاصيل عنوان واحد",
    description="""
    يجلب تفاصيل عنوان محدد بالـ ID الخاص به، مع التحقق من ملكية المستخدم.
    (REQ-FUN-022)
    """,
)
async def get_my_address_details_endpoint(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لجلب تفاصيل عنوان محدد للمستخدم الحالي."""
    return address_service.get_address_by_id(db=db, address_id=address_id, current_user=current_user)


@router.patch(
    "/me/addresses/{address_id}",
    response_model=address_schemas.AddressRead,
    summary="[Authenticated User] تحديث عنوان موجود",
    description="""
    يسمح للمستخدم بتحديث تفاصيل عنوان موجود في حسابه.
    (REQ-FUN-022)
    """,
)
async def update_my_address_endpoint(
    address_id: int,
    address_in: address_schemas.AddressUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لتحديث عنوان موجود للمستخدم الحالي."""
    return address_service.update_user_address(db=db, address_id=address_id, address_in=address_in, current_user=current_user)

@router.delete(
    "/me/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Authenticated User] حذف عنوان",
    description="""
    يسمح للمستخدم بحذف عنوان من حسابه.
    يتم التحقق من عدم حذف العنوان الوحيد أو العنوان الافتراضي.
    (REQ-FUN-022)
    """,
)
async def delete_my_address_endpoint(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف عنوان من المستخدم الحالي."""
    address_service.delete_user_address(db=db, address_id=address_id, current_user=current_user)
    return


# ================================================================
# --- نقاط الوصول لتفضيلات المستخدمين (User Preferences) ---
# ================================================================

@router.get(
    "/me/preferences",
    response_model=List[schemas.UserPreferenceRead],
    summary="[Authenticated User] جلب تفضيلاتي",
    description="""
    يجلب قائمة بجميع التفضيلات المحددة لحساب المستخدم الحالي.
    """,
)
async def get_my_preferences_endpoint(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لجلب تفضيلات المستخدم الحالي."""
    return core_service.get_user_preferences(db=db, current_user=current_user)


@router.post(
    "/me/preferences",
    response_model=schemas.UserPreferenceRead,
    status_code=status.HTTP_200_OK, # يمكن أن يكون 200 إذا كان تحديث، 201 إذا كان إنشاء
    summary="[Authenticated User] إنشاء أو تحديث تفضيل",
    description="""
    يسمح للمستخدم بإنشاء تفضيل جديد أو تحديث تفضيل موجود في حسابه.
    """,
)
async def create_or_update_my_preference_endpoint(
    preference_in: schemas.UserPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لإنشاء أو تحديث تفضيل للمستخدم الحالي."""
    return core_service.create_or_update_user_preference(db=db, current_user=current_user, pref_in=preference_in)

@router.delete(
    "/me/preferences/{preference_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Authenticated User] حذف تفضيل",
    description="""
    يسمح للمستخدم بحذف تفضيل معين من حسابه.
    سيؤدي هذا إلى جعل النظام يستخدم القيمة الافتراضية لهذا التفضيل.
    """,
)
async def delete_my_preference_endpoint(
    preference_key: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف تفضيل للمستخدم الحالي."""
    core_service.delete_user_preference(db=db, current_user=current_user, preference_key=preference_key)
    return