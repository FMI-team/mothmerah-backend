# backend\src\api\v1\routers\admin_rbac_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional,Dict # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User as UserModel # مودل المستخدم، لضمان User type hint

# استيراد Schemas (هياكل البيانات) الخاصة بالأدوار والصلاحيات
from src.users.schemas import rbac_schemas as schemas # RoleRead, RoleWithPermissionsRead, PermissionRead, GroupedPermissionRead, AssignPermissionRequest, RoleCreate, RoleUpdate, RoleTranslationCreate, RoleTranslationUpdate

# استيراد الخدمات (منطق العمل) المتعلقة بالأدوار والصلاحيات
from src.users.services import rbac_service # لـ get_all_roles_service, get_role_by_id_service, create_new_role, update_existing_role, delete_role_by_id, get_all_permissions_service, get_permission_by_id_service, create_new_permission, update_permission, delete_permission_by_id, assign_permission_to_role, revoke_permission_from_role, manage_role_translation, update_specific_role_translation, remove_specific_role_translation

# تعريف الراوتر لإدارة الأدوار والصلاحيات من جانب المسؤولين.
router = APIRouter(
    prefix="/rbac", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /admin/rbac)
    tags=["Admin - RBAC Management"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_ROLES_PERMISSIONS"))] # صلاحية عامة لإدارة الأدوار والصلاحيات
)

# ================================================================
# --- نقاط الوصول للأدوار (Roles) ---
# ================================================================

@router.post(
    "/roles",
    response_model=schemas.RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء دور جديد",
    description="""
    يسمح للمسؤولين بإنشاء دور وظيفي جديد في النظام، مع ترجماته الأولية.
    (REQ-FUN-034)
    """,
)
async def create_role_endpoint(
    role_in: schemas.RoleCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء دور جديد."""
    return rbac_service.create_new_role(db=db, role_in=role_in)

@router.get(
    "/roles",
    response_model=List[schemas.RoleRead],
    summary="[Admin] جلب جميع الأدوار",
    description="""
    يسمح للمسؤولين بجلب قائمة بجميع الأدوار المعرفة في النظام.
    """,
)
async def get_all_roles_endpoint(
    db: Session = Depends(get_db),
    include_inactive: bool = False # خيار لتضمين الأدوار غير النشطة
):
    """نقطة وصول لجلب جميع الأدوار."""
    return rbac_service.get_all_roles_service(db=db, include_inactive=include_inactive)

@router.get(
    "/roles/{role_id}",
    response_model=schemas.RoleWithPermissionsRead, # لكي تظهر الصلاحيات مدمجة
    summary="[Admin] جلب تفاصيل دور واحد مع صلاحياته",
    description="""
    يسمح للمسؤولين بجلب التفاصيل الكاملة لدور محدد، بما في ذلك جميع الصلاحيات المسندة إليه.
    """,
)
async def get_role_details_endpoint(
    role_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب تفاصيل دور واحد."""
    return rbac_service.get_role_by_id_service(db=db, role_id=role_id)

@router.patch(
    "/roles/{role_id}",
    response_model=schemas.RoleRead,
    summary="[Admin] تحديث دور",
    description="""
    يسمح للمسؤولين بتحديث بيانات دور موجود (مثل اسمه أو حالته).
    """,
)
async def update_role_endpoint(
    role_id: int,
    role_in: schemas.RoleUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث دور."""
    return rbac_service.update_existing_role(db=db, role_id=role_id, role_in=role_in)

@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف دور",
    description="""
    يسمح للمسؤولين بحذف دور من النظام (حذف ناعم أو صارم بناءً على تصميم الدور)،
    ويتم إعادة إسناد المستخدمين المرتبطين إلى دور افتراضي.
    """,
)
async def delete_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف دور."""
    return rbac_service.delete_role_by_id(db=db, role_id_to_delete=role_id) # دالة الخدمة ترجع dict


# --- ترجمات الأدوار (Role Translations) ---
@router.post(
    "/roles/{role_id}/translations",
    response_model=schemas.RoleRead, # ترجع الدور كاملاً مع ترجماته المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لدور",
    description="""
    يسمح للمسؤولين بإنشاء ترجمة جديدة لدور أو تحديث ترجمة موجودة بنفس اللغة.
    """,
)
async def create_role_translation_endpoint(
    role_id: int,
    trans_in: schemas.RoleTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لدور."""
    return rbac_service.create_role_translation(db=db, role_id=role_id, trans_in=trans_in)

@router.get(
    "/roles/{role_id}/translations/{language_code}",
    response_model=schemas.RoleTranslationRead,
    summary="[Admin] جلب ترجمة محددة لدور",
    description="""
    يسمح للمسؤولين بجلب ترجمة محددة لدور معين بلغة معينة.
    """,
)
async def get_role_translation_details_endpoint(
    role_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة دور محددة."""
    return rbac_service.get_role_translation_details(db=db, role_id=role_id, language_code=language_code)

@router.patch(
    "/roles/{role_id}/translations/{language_code}",
    response_model=schemas.RoleRead, # ترجع الدور كاملاً مع ترجماته المحدثة
    summary="[Admin] تحديث ترجمة دور",
    description="""
    يسمح للمسؤولين بتحديث ترجمة موجودة لدور.
    """,
)
async def update_role_translation_endpoint(
    role_id: int,
    language_code: str,
    trans_in: schemas.RoleTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة دور."""
    return rbac_service.update_role_translation(db=db, role_id=role_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/roles/{role_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة دور",
    description="""
    يسمح للمسؤولين بحذف ترجمة دور معينة (حذف صارم).
    """,
)
async def remove_role_translation_endpoint(
    role_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة دور."""
    rbac_service.remove_role_translation(db=db, role_id=role_id, language_code=language_code)
    return

# ================================================================
# --- نقاط الوصول للصلاحيات (Permissions) ---
# ================================================================

@router.post(
    "/permissions",
    response_model=schemas.PermissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء صلاحية جديدة",
    description="""
    يسمح للمسؤولين بإنشاء صلاحية جديدة في النظام.
    """,
)
async def create_permission_endpoint(
    permission_in: schemas.PermissionCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء صلاحية جديدة."""
    return rbac_service.create_new_permission(db=db, permission_in=permission_in)

@router.get(
    "/permissions",
    response_model=List[schemas.GroupedPermissionRead], # لعرضها مجمعة
    summary="[Admin] جلب جميع الصلاحيات (مجمعة حسب الوحدة)",
    description="""
    يسمح للمسؤولين بجلب قائمة بجميع الصلاحيات المعرفة في النظام، مجمعة حسب الوحدة الوظيفية.
    """,
)
async def get_all_permissions_endpoint(
    db: Session = Depends(get_db),
    include_inactive: bool = False # خيار لتضمين الصلاحيات غير النشطة
):
    """نقطة وصول لجلب جميع الصلاحيات (مجمعة)."""
    return rbac_service.get_all_permissions_service(db=db, include_inactive=include_inactive)

@router.get(
    "/permissions/{permission_id}",
    response_model=schemas.PermissionRead,
    summary="[Admin] جلب تفاصيل صلاحية واحدة",
    description="""
    يسمح للمسؤولين بجلب التفاصيل الكاملة لصلاحية محددة.
    """,
)
async def get_permission_details_endpoint(
    permission_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب تفاصيل صلاحية واحدة."""
    return rbac_service.get_permission_by_id_service(db=db, permission_id=permission_id)

@router.patch(
    "/permissions/{permission_id}",
    response_model=schemas.PermissionRead,
    summary="[Admin] تحديث صلاحية",
    description="""
    يسمح للمسؤولين بتحديث بيانات صلاحية موجودة.
    """,
)
async def update_permission_endpoint(
    permission_id: int,
    permission_in: schemas.PermissionUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث صلاحية."""
    return rbac_service.update_permission(db=db, permission_id=permission_id, permission_in=permission_in)

@router.delete(
    "/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف صلاحية",
    description="""
    يسمح للمسؤولين بحذف صلاحية من النظام (حذف ناعم أو صارم).
    لا يمكن حذفها إذا كانت مرتبطة بأدوار حاليًا.
    """,
)
async def delete_permission_endpoint(
    permission_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف صلاحية."""
    rbac_service.delete_permission_by_id(db=db, permission_id=permission_id)
    return

# ================================================================
# --- نقاط الوصول لربط الأدوار بالصلاحيات (Role-Permission Assignment) ---
# ================================================================

@router.post(
    "/roles/{role_id}/permissions/{permission_id}",
    response_model=schemas.RoleWithPermissionsRead,
    status_code=status.HTTP_200_OK, # إذا كان موجوداً سيتم تأكيد وجوده
    summary="[Admin] إسناد صلاحية لدور",
    description="""
    يسمح للمسؤولين بإسناد صلاحية محددة لدور معين.
    """,
)
async def assign_permission_to_role_endpoint(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإسناد صلاحية لدور."""
    return rbac_service.assign_permission_to_role(db=db, role_id=role_id, permission_id=permission_id)

@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] سحب صلاحية من دور",
    description="""
    يسمح للمسؤولين بسحب صلاحية محددة من دور معين.
    """,
)
async def revoke_permission_from_role_endpoint(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لسحب صلاحية من دور."""
    rbac_service.revoke_permission_from_role(db=db, role_id=role_id, permission_id=permission_id)
    return


# ================================================================
# --- نقاط الوصول لربط المستخدمين بالأدوار (User-Role Assignment) ---
# ================================================================

@router.post(
    "/users/{user_id}/roles/{role_id}",
    response_model=schemas.UserRoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إسناد دور إضافي لمستخدم",
    description="""
    يسمح للمسؤولين بإسناد دور وظيفي إضافي لمستخدم محدد.
    (REQ-FUN-035)
    """,
)
async def assign_role_to_user_endpoint(
    user_id: UUID,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user) # المسؤول الذي يقوم بالإسناد
):
    """نقطة وصول لإسناد دور إضافي لمستخدم."""
    return rbac_service.assign_role_to_user(db=db, user_id=user_id, role_id=role_id, assigned_by_user_id=current_user.user_id)

@router.delete(
    "/users/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] سحب دور إضافي من مستخدم",
    description="""
    يسمح للمسؤولين بسحب دور وظيفي إضافي من مستخدم محدد.
    """,
)
async def remove_role_from_user_endpoint(
    user_id: UUID,
    role_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لسحب دور إضافي من مستخدم."""
    rbac_service.remove_role_from_user(db=db, user_id=user_id, role_id=role_id)
    return