# backend/src/api/v1/routers/user_admin_router.py

from fastapi import APIRouter, Depends, status,Form,File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from src.db import base

# استيرادات عامة
from src.db.session import get_db
from src.api.v1 import dependencies

# استيرادات خاصة بوحدة المستخدمين فقط
from src.users.schemas import rbac_schemas, management_schemas,license_schemas, core_schemas
from src.users.services import rbac_service, management_service
from src.users import models as user_models # استيراد للتحقق

from uuid import UUID

# from src.db.base_class import Base # استيراد User من Base

# --- 1. إنشاء الراوتر الرئيسي للإدارة ---
# هذا هو الراوتر الذي سيتم تسجيله في main.py
# لن نضع له prefix أو tags هنا، بل في main.py
# هذا هو الراوتر الوحيد الذي سنتعامل معه كـ "رئيسي" في هذا الملف.
router = APIRouter()

# ================================================================
# --- 3. تعريف وتنظيم الراوترات الفرعية لكل قسم ---
# ================================================================

# --- القسم الفرعي الأول: إدارة الأدوار والصلاحيات (RBAC) ---

rbac_router = APIRouter(
    prefix="/rbac",
    tags=["Admin - Users (RBAC)"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_ROLES"))] # حماية المجموعة كاملة
)

# --- نقاط وصول للأدوار ---
@rbac_router.post("/roles", response_model=rbac_schemas.RoleRead, status_code=status.HTTP_201_CREATED)
def create_new_role_endpoint(role_in: rbac_schemas.RoleCreate, db: Session = Depends(get_db)):
    """إنشاء دور وظيفي جديد مع ترجماته الأولية."""
    return rbac_service.create_new_role(db, role_in=role_in)

# --- نقاط وصول لترجمات الأدوار ---
@rbac_router.post("/roles/{role_id}/translations", response_model=rbac_schemas.RoleRead)
def manage_role_translation_endpoint(
    role_id: int,
    trans_in: rbac_schemas.RoleTranslationCreate,
    db: Session = Depends(get_db)
):
    """إضافة أو تحديث ترجمة لدور معين."""
    return rbac_service.manage_role_translation(db, role_id=role_id, trans_in=trans_in)

@rbac_router.get("/roles", response_model=List[rbac_schemas.RoleRead])
def get_all_roles(db: Session = Depends(get_db)):
    """
    جلب قائمة بجميع الأدوار المعرفة في النظام.
    """
    return rbac_service.get_all_roles(db)

@rbac_router.get("/permissions", response_model=List[rbac_schemas.GroupedPermissionRead])
def get_all_permissions(db: Session = Depends(get_db)):
    """
    جلب قائمة بجميع الصلاحيات المتاحة في النظام، مجمعة حسب الوحدة.
    """
    return rbac_service.get_all_permissions(db)

@rbac_router.get("/roles/{role_id}", response_model=rbac_schemas.RoleWithPermissionsRead)
def get_role_details(role_id: int, db: Session = Depends(get_db)):
    """
    جلب التفاصيل الكاملة لدور واحد، بما في ذلك جميع الصلاحيات الممنوحة له.
    """
    return rbac_service.get_role_with_permissions(db, role_id=role_id)

@rbac_router.post("/roles/{role_id}/permissions", response_model=rbac_schemas.RoleWithPermissionsRead, dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_PERMISSIONS"))])
def assign_permission_to_role(role_id: int, request: rbac_schemas.AssignPermissionRequest, db: Session = Depends(get_db)):
    """
    منح صلاحية جديدة لدور معين.
    """    
    return rbac_service.assign_permission_to_role(db=db, role_id=role_id, permission_id=request.permission_id) # للبحث بالرقم
    # return rbac_service.assign_permission_to_role(db=db, role_id=role_id, permission_key=request.permission_key) # للبحث بالاسم

@rbac_router.delete("/roles/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(dependencies.has_permission("RBAC_MANAGE_PERMISSIONS"))])
def revoke_permission_from_role(role_id: int, permission_id: int, db: Session = Depends(get_db)):
    """
    سحب صلاحية من دور معين.
    """
    rbac_service.revoke_permission_from_role(db=db, role_id=role_id, permission_id=permission_id) # للبحث بالرغم
    # rbac_service.revoke_permission_from_role(db=db, role_id=role_id, permission_key=permission_key) # للبحث بالاسم
    return

@rbac_router.patch("/roles/{role_id}", response_model=rbac_schemas.RoleRead)
def update_role_endpoint(role_id: int, role_in: rbac_schemas.RoleUpdate, db: Session = Depends(get_db)):
    """تحديث بيانات دور معين (مثل الاسم أو حالة التفعيل)."""
    return rbac_service.update_existing_role(db, role_id=role_id, role_in=role_in)

@rbac_router.delete("/roles/{role_id}", response_model=dict)
def delete_role_endpoint(role_id: int, db: Session = Depends(get_db)):
    """حذف دور. سيتم نقل المستخدمين المرتبطين به إلى الدور الافتراضي."""
    return rbac_service.delete_role_by_id(db, role_id_to_delete=role_id)

# داخل rbac_router

@rbac_router.patch("/roles/{role_id}/translations/{language_code}", response_model=rbac_schemas.RoleTranslationRead)
def update_role_translation_endpoint(
    role_id: int,
    language_code: str,
    trans_in: rbac_schemas.RoleTranslationUpdate,
    db: Session = Depends(get_db)
):
    """تحديث ترجمة موجودة لدور معين."""
    # نحتاج لتعديل الخدمة لترجع الترجمة المحدثة وليس الدور كاملاً
    # سنقوم بتعديل هذا لاحقًا إذا احتجنا
    return rbac_service.update_specific_role_translation(db, role_id=role_id, language_code=language_code, trans_in=trans_in)

@rbac_router.delete("/roles/{role_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role_translation_endpoint(
    role_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة لدور معين بلغة محددة."""
    rbac_service.remove_specific_role_translation(db, role_id=role_id, language_code=language_code)
    return

# --- القسم الفرعي الثاني: إدارة الجداول المرجعية (Lookups) ---
# lookups_router = APIRouter(
#     prefix="/lookups",
#     tags=["Admin - Lookups License & Authorities"],
#     dependencies=[Depends(dependencies.has_permission("MANAGE_LOOKUPS"))]
# )

# ================================================================
# القسم 2: إدارة الجداول المرجعية للمستخدمين (User Lookups)
# (هذا هو الراوتر الموحد الذي يحل محل lookups_router و management_router)
# ================================================================
user_lookups_router = APIRouter(
    prefix="/lookups",
    tags=["Admin - Users (Lookups)"],
    dependencies=[Depends(dependencies.has_permission("MANAGE_USERS_LOOKUPS"))]
)

@user_lookups_router.get(
    "/license-types",
    response_model=List[management_schemas.LicenseTypeRead],
    summary="جلب جميع أنواع التراخيص"
)
def get_all_license_types(db: Session = Depends(get_db)):
    return management_service.get_all_license_types(db)

@user_lookups_router.get(
    "/issuing-authorities",
    response_model=List[management_schemas.IssuingAuthorityRead],
    summary="جلب جميع جهات الإصدار"
    # dependencies=[Depends(dependencies.has_permission("VIEW_LICENSE_LOOKUPS"))]
)
def get_all_issuing_authorities(db: Session = Depends(get_db)):
    return management_service.get_all_authorities(db)

@user_lookups_router.patch("/issuing-authorities/{authority_id}", response_model=management_schemas.IssuingAuthorityRead)
def update_issuing_authority(authority_id: int, authority_in: management_schemas.IssuingAuthorityUpdate, db: Session = Depends(get_db)):
    """تحديث البيانات الأساسية لجهة إصدار."""
    return management_service.update_existing_issuing_authority(db, authority_id=authority_id, authority_in=authority_in)

@user_lookups_router.delete("/issuing-authorities/{authority_id}", response_model=dict)
def delete_issuing_authority(authority_id: int, db: Session = Depends(get_db)):
    """حذف جهة إصدار (فقط إذا لم تكن مستخدمة)."""
    return management_service.delete_issuing_authority_by_id(db, authority_id=authority_id)

@user_lookups_router.delete("/issuing-authorities/{authority_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issuing_authority_translation(authority_id: int, language_code: str, db: Session = Depends(get_db)):
    """حذف ترجمة محددة لجهة إصدار."""
    management_service.remove_issuing_authority_translation(db, authority_id=authority_id, language_code=language_code)
    return

# --- نقاط الوصول لحالات التحقق من المستخدم (UserVerificationStatus) ---
@user_lookups_router.patch("/user-verification-statuses/{status_id}", response_model=management_schemas.UserVerificationStatusRead)
def update_user_verification_status(status_id: int, status_in: management_schemas.UserVerificationStatusUpdate, db: Session = Depends(get_db)):
    """تحديث بيانات حالة التحقق من المستخدم."""
    return management_service.update_existing_user_verification_status(db, status_id=status_id, status_in=status_in)

@user_lookups_router.delete("/user-verification-statuses/{status_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_verification_status_translation(status_id: int, language_code: str, db: Session = Depends(get_db)):
    """حذف ترجمة محددة لحالة التحقق من المستخدم."""
    management_service.remove_user_verification_status_translation(db, status_id=status_id, language_code=language_code)
    return


@user_lookups_router.get(
    "/license-verification-statuses",
    response_model=List[management_schemas.LicenseVerificationStatusRead],
    summary="جلب جميع حالات التحقق من التراخيص"
    # dependencies=[Depends(dependencies.has_permission("VIEW_LICENSE_LOOKUPS"))]
)
def get_all_license_verification_statuses(db: Session = Depends(get_db)):
    return management_service.get_all_license_statuses(db)

@user_lookups_router.patch("/license-verification-statuses/{status_id}", response_model=management_schemas.LicenseVerificationStatusRead)
def update_license_verification_status(status_id: int, status_in: management_schemas.LicenseVerificationStatusUpdate, db: Session = Depends(get_db)):
    """تحديث بيانات حالة تحقق من ترخيص."""
    return management_service.update_existing_license_verification_status(db, status_id=status_id, status_in=status_in)

@user_lookups_router.delete("/license-verification-statuses/{status_id}", response_model=dict)
def delete_license_verification_status(status_id: int, db: Session = Depends(get_db)):
    """حذف حالة تحقق من ترخيص (فقط إذا لم تكن مستخدمة)."""
    return management_service.delete_license_verification_status_by_id(db, status_id=status_id)

@user_lookups_router.patch("/license-types/{type_id}", response_model=management_schemas.LicenseTypeRead)
def update_license_type(type_id: int, type_in: management_schemas.LicenseTypeUpdate, db: Session = Depends(get_db)):
    """تحديث البيانات الأساسية لنوع ترخيص."""
    return management_service.update_existing_license_type(db, type_id=type_id, type_in=type_in)

@user_lookups_router.delete("/license-types/{type_id}", response_model=dict)
def delete_license_type(type_id: int, db: Session = Depends(get_db)):
    """حذف نوع ترخيص (فقط إذا لم يكن مستخدماً)."""
    return management_service.delete_license_type_by_id(db, type_id=type_id)

@user_lookups_router.delete("/license-types/{type_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_license_type_translation(type_id: int, language_code: str, db: Session = Depends(get_db)):
    """حذف ترجمة محددة لنوع ترخيص."""
    management_service.remove_license_type_translation(db, type_id=type_id, language_code=language_code)
    return

# ================================================================
# --- قسم إدارة الجداول المرجعية (Lookups Management) ---
# ================================================================
# management_router = APIRouter(
#     prefix="/management",
#     tags=["Admin - Users (Lookups)"],
#     dependencies=[Depends(dependencies.has_permission("MANAGE_USERS_LOOKUPS"))]
# )

# --- نقاط الوصول لأنواع المستخدمين (UserType) ---
@user_lookups_router.post("/user-types", response_model=management_schemas.UserTypeRead, status_code=status.HTTP_201_CREATED)
def create_user_type_endpoint(type_in: management_schemas.UserTypeCreate, db: Session = Depends(get_db)):
    """إنشاء نوع مستخدم جديد (مثل: بائع، مشترٍ)."""
    return management_service.create_new_user_type(db, type_in=type_in)

@user_lookups_router.get("/user-types", response_model=List[management_schemas.UserTypeRead])
def get_all_user_types_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع أنواع المستخدمين في النظام."""
    return management_service.get_all_user_types(db)

@user_lookups_router.patch("/user-types/{type_id}", response_model=management_schemas.UserTypeRead)
def update_user_type_endpoint(type_id: int, type_in: management_schemas.UserTypeUpdate, db: Session = Depends(get_db)):
    """تحديث البيانات الأساسية لنوع مستخدم."""
    return management_service.update_existing_user_type(db, type_id=type_id, type_in=type_in)

@user_lookups_router.delete("/user-types/{type_id}", status_code=status.HTTP_200_OK)
def delete_user_type_endpoint(type_id: int, db: Session = Depends(get_db)):
    """
    حذف نوع مستخدم.
    سيتم نقل المستخدمين المرتبطين إلى النوع الافتراضي قبل الحذف.
    """
    return management_service.delete_user_type_by_id(db, type_id_to_delete=type_id)

# ================================================================
# --- قسم المستخدمين (Users Management) ---
# ================================================================

# --- نقاط الوصول لحالات الحساب (AccountStatus) ---

@user_lookups_router.get(
    "/account-statuses",
    response_model=List[management_schemas.AccountStatusRead],
    summary="جلب جميع حالات الحساب"
)
def get_all_account_statuses(db: Session = Depends(get_db)):
    """جلب قائمة بجميع حالات الحساب مع ترجماتها."""
    return management_service.get_all_statuses(db)

@user_lookups_router.get(
    "/account-statuses/{status_id}", 
    response_model=management_schemas.AccountStatusRead,
    summary="جلب تفاصيل حالة حساب واحدة",
)
def get_single_account_status(status_id: int, db: Session = Depends(get_db)):
    return management_service.get_status_by_id(db, status_id=status_id)

@user_lookups_router.patch(
    "/account-statuses/{status_id}", 
    response_model=management_schemas.AccountStatusRead,
    summary="تحديث حالة حساب",
)
def update_account_status(
    status_id: int, 
    status_in: management_schemas.AccountStatusUpdate, 
    db: Session = Depends(get_db)
):
    return management_service.update_existing_account_status(db, status_id=status_id, status_in=status_in)

# --- نقاط وصول ترجمات حالات الحساب (Translations) ---
@user_lookups_router.post(
    "/account-statuses/{status_id}/translations",
    response_model=management_schemas.AccountStatusRead,
    summary="إضافة أو تحديث ترجمة لحالة حساب"
)
def add_or_update_account_status_translation(
    status_id: int,
    trans_in: management_schemas.AccountStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """
    - إذا كانت الترجمة بنفس اللغة موجودة، سيتم تحديثها.
    - إذا لم تكن موجودة، سيتم إضافتها كترجمة جديدة.
    """
    return management_service.manage_status_translation(db, status_id=status_id, trans_in=trans_in)

@user_lookups_router.delete(
    "/account-statuses/{status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف ترجمة معينة لحالة حساب"
)
def delete_account_status_translation(
    status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """حذف ترجمة محددة عن طريق رمز اللغة."""
    management_service.remove_status_translation(db, status_id=status_id, language_code=language_code)
    return

@user_lookups_router.post(
    "/account-statuses",
    response_model=management_schemas.AccountStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="إنشاء حالة حساب جديدة"
)
def create_account_status(
    status_in: management_schemas.AccountStatusCreate,
    db: Session = Depends(get_db)
):
    """إنشاء حالة حساب جديدة مع ترجماتها الأولية."""
    return management_service.create_new_account_status(db=db, status_in=status_in)


# --- Endpoints for LicenseType ---
@user_lookups_router.post(
    "/license-types",
    response_model=management_schemas.LicenseTypeRead,
    status_code=status.HTTP_201_CREATED,
    summary="إنشاء نوع ترخيص جديد"
)
def create_license_type(
    type_in: management_schemas.LicenseTypeCreate,
    db: Session = Depends(get_db)
):
    return management_service.create_new_license_type(db=db, type_in=type_in)

# --- Endpoints for LicenseVerificationStatus ---

@user_lookups_router.post(
    "/license-types/{type_id}/translations",
    response_model=management_schemas.LicenseTypeRead,
    summary="إضافة أو تحديث ترجمة لنوع ترخيص",
)
def add_or_update_license_type_translation(
    type_id: int,
    trans_in: management_schemas.LicenseTypeTranslationCreate,
    db: Session = Depends(get_db)
):
    return management_service.manage_license_type_translation(db, type_id=type_id, trans_in=trans_in)


# --- Endpoints for IssuingAuthority ---
@user_lookups_router.post(
    "/issuing-authorities",
    response_model=management_schemas.IssuingAuthorityRead,
    status_code=status.HTTP_201_CREATED,
    summary="إنشاء جهة إصدار جديدة"
)
def create_issuing_authority(
    authority_in: management_schemas.IssuingAuthorityCreate,
    db: Session = Depends(get_db)
):
    return management_service.create_new_issuing_authority(db=db, authority_in=authority_in)

# ================================================================
# --- نقاط الوصول الخاصة بتراخيص المستخدم (User Licenses) ---
# ================================================================

@router.post(
    "/me/licenses", 
    response_model=license_schemas.LicenseRead,
    status_code=status.HTTP_201_CREATED,
    summary="رفع ترخيص جديد للمستخدم الحالي",
    dependencies=[Depends(dependencies.has_permission("LICENSE_CREATE_OWN"))]
)
def upload_license_for_user(
    # الحقول النصية يتم استقبالها كـ Form fields
    license_type_id: int = Form(...),
    license_number: str = Form(...),
    issuing_authority_id: Optional[int] = Form(None),
    issue_date: Optional[date] = Form(None),
    expiry_date: Optional[date] = Form(None),
    # الملف يتم استقباله كـ UploadFile
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: base.User = Depends(dependencies.get_current_active_user)
):
    """
    نقطة وصول محمية تسمح للمستخدم برفع ملف ترخيص جديد.
    """
    license_data = {
        "license_type_id": license_type_id,
        "license_number": license_number,
        "issuing_authority_id": issuing_authority_id,
        "issue_date": issue_date,
        "expiry_date": expiry_date
    }
    return verification_service.upload_new_license(db=db, user=current_user, license_data=license_data, file=file)

@router.get(
    "/me/licenses",
    response_model=List[license_schemas.LicenseRead],
    summary="جلب قائمة بجميع تراخيص المستخدم الحالي",
    dependencies=[Depends(dependencies.has_permission("LICENSE_VIEW_OWN"))]
)
def get_my_licenses_endpoint(
    db: Session = Depends(get_db),
    current_user: base.User = Depends(dependencies.get_current_active_user)
):
    """
    يعيد قائمة بجميع التراخيص التي قام المستخدم الحالي برفعها.
    """
    return verification_service.get_licenses_for_user(db, user=current_user)

@router.patch(
    "/me/licenses/{license_id}",
    response_model=license_schemas.LicenseRead,
    summary="تحديث بيانات ترخيص معين",
    dependencies=[Depends(dependencies.has_permission("LICENSE_UPDATE_OWN"))]
)
def update_my_license_endpoint(
    license_id: int,
    license_in: license_schemas.LicenseUpdate,
    db: Session = Depends(get_db),
    current_user: base.User = Depends(dependencies.get_current_active_user)
):
    """
    يسمح للمستخدم بتحديث بيانات ترخيص يملكه.
    """
    return verification_service.update_license_by_user(
        db=db, license_id=license_id, license_in=license_in, user=current_user
    )

@router.delete(
    "/me/licenses/{license_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف ترخيص معين",
    dependencies=[Depends(dependencies.has_permission("LICENSE_DELETE_OWN"))]
)
def delete_my_license_endpoint(
    license_id: int,
    db: Session = Depends(get_db),
    current_user: base.User = Depends(dependencies.get_current_active_user)
):
    """
    يسمح للمستخدم بحذف ترخيص يملكه.
    """
    verification_service.delete_license_by_user(db=db, license_id=license_id, user=current_user)
    return

# ================================================================
# --- قسم إدارة المستخدمين (Admin - User Actions) ---
# ================================================================
@router.patch(
    "/users/{user_id}/status",
    response_model=core_schemas.UserRead,
    summary="[Admin] Update User Account Status",
    tags=["Admin - Users Management"],
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_USERS"))] # صلاحية مقترحة
)
def update_user_status_by_admin(
    user_id: UUID,
    status_data: management_schemas.AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: base.User = Depends(dependencies.get_current_active_user)
):
    """
    يسمح للمسؤول بتغيير حالة حساب مستخدم معين (مثل تفعيل، تعليق، حظر).
    يتم تسجيل كل تغيير في سجل التدقيق (Audit Log) مع السبب.
    """
    return management_service.change_user_status_by_admin(
        db=db,
        target_user_id=user_id,
        status_data=status_data,
        admin_user=current_admin
    )

# ================================================================
# --- دمج الراوترات الفرعية في راوتر إدارة المستخدمين الرئيسي ---
# ================================================================
router.include_router(rbac_router)
router.include_router(user_lookups_router)
