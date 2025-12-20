# backend\src\api\v1\routers\admin_core_users_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User as UserModel # مودل المستخدم، لضمان User type hint

# استيراد Schemas (هياكل البيانات)
from src.users.schemas import core_schemas as schemas # UserRead, UserUpdate
from src.users.schemas.management_schemas import AdminUserStatusUpdate # لـ AdminUserStatusUpdate

# استيراد الخدمات (منطق العمل)
from src.users.services import core_service # لـ get_user_profile, update_user_profile, get_user_account_history
from src.users.services import management_service # لـ change_user_status_by_admin


# تعريف الراوتر لإدارة المستخدمين الأساسية من جانب المسؤولين.
router = APIRouter(
    prefix="/users", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /admin/users)
    tags=["Admin - Core User Management"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_USERS"))] # صلاحية عامة لإدارة المستخدمين
)

# ================================================================
# --- نقاط الوصول لإدارة المستخدمين الأساسية (Core User Management) ---
# ================================================================

@router.get(
    "/",
    response_model=List[schemas.UserRead],
    summary="[Admin] جلب جميع المستخدمين",
    description="""
    يسمح للمسؤولين بجلب قائمة بجميع المستخدمين المسجلين في النظام.
    """,
)
async def get_all_users_for_admin_endpoint(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    # TODO: يمكن إضافة فلاتر للبحث (مثل phone_number, email, status_name_key, user_type_key)
):
    """نقطة وصول لجلب جميع المستخدمين."""
    return core_service.get_all_users(db=db, skip=skip, limit=limit, include_deleted=False)


@router.get(
    "/{user_id}",
    response_model=schemas.UserRead,
    summary="[Admin] جلب تفاصيل مستخدم واحد",
    description="""
    يسمح للمسؤولين بجلب التفاصيل الكاملة لمستخدم محدد بالـ ID الخاص به.
    """,
)
async def get_user_details_admin_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب تفاصيل مستخدم محدد للمسؤول."""
    # دالة get_user_profile في core_service تتحقق من صلاحيات المستخدم الحالي (الذي يطلب البيانات)
    # وهنا، المسؤول يملك صلاحية ADMIN_MANAGE_USERS، لذا يجب أن تمرر له صلاحية الرؤية العامة.
    # get_user_profile(db, user_id, current_user) # إذا كانت الدالة تتطلب current_user
    # لكن يمكننا أيضاً استخدام دالة خدمة مبسطة للمسؤول لا تتطلب current_user
    return core_service.get_user_profile(db=db, user_id=user_id) # استخدام دالة الخدمة مع التحقق من الصلاحيات


@router.patch(
    "/{user_id}/status",
    response_model=schemas.UserRead,
    summary="[Admin] تغيير حالة حساب المستخدم",
    description="""
    يسمح للمسؤولين بتغيير الحالة التشغيلية لحساب مستخدم (مثلاً: تفعيل، تعليق، حظر).
    يتم توثيق التغيير في سجل تاريخ حالة الحساب.
    (REQ-FUN-004)
    """,
)
async def change_user_status_endpoint(
    user_id: UUID,
    status_data: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user) # المسؤول الذي يقوم بالإجراء
):
    """نقطة وصول لتغيير حالة حساب المستخدم بواسطة المسؤول."""
    return management_service.change_user_status_by_admin(db=db, target_user_id=user_id, status_data=status_data, admin_user=current_user)

@router.delete(
    "/{user_id}",
    response_model=schemas.UserRead,
    summary="[Admin] حذف ناعم لحساب مستخدم",
    description="""
    يسمح للمسؤولين بحذف ناعم لحساب مستخدم (بتعيين is_deleted إلى True وتحديث حالته).
    (REQ-FUN-030)
    """,
)
async def soft_delete_user_account_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف ناعم لحساب مستخدم."""
    return core_service.soft_delete_user_account(db=db, user_id=user_id, current_user=current_user, reason="تم الحذف بواسطة المسؤول.")


@router.get(
    "/{user_id}/account-history",
    response_model=List[schemas.AccountStatusHistoryRead],
    summary="[Admin] جلب سجل تغييرات حالة حساب المستخدم",
    description="""
    يسمح للمسؤولين بجلب سجل تاريخ التغييرات التي طرأت على حالة حساب مستخدم محدد.
    (REQ-FUN-031)
    """,
)
async def get_user_account_history_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user) # المستخدم الذي يطلب السجل
):
    """نقطة وصول لجلب سجل تغييرات حالة حساب المستخدم."""
    return core_service.get_user_account_history(db=db, user_id_to_view=user_id, requesting_user=current_user)