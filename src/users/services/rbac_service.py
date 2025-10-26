# backend\src\users\services\rbac_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from itertools import groupby
from operator import attrgetter

# استيراد المودلز
from src.users.models.roles_models import Role, RoleTranslation, Permission, RolePermission, UserRole
from src.users.models.core_models import User # لـ User (في reassign users)
# استيراد الـ CRUD
from src.users.crud import rbac_crud
from src.users.crud import core_crud # لـ User
# استيراد Schemas
from src.users.schemas import rbac_schemas as schemas
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- خدمات الأدوار (Role) ---
# ==========================================================

def create_new_role(db: Session, role_in: schemas.RoleCreate) -> Role:
    """
    خدمة لإنشاء دور جديد مع ترجماته الأولية.
    تتضمن التحقق من عدم تكرار المفتاح.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_in (schemas.RoleCreate): بيانات الدور للإنشاء.

    Returns:
        Role: كائن الدور الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان الدور بمفتاح معين موجوداً بالفعل.
    """
    # 1. التحقق من عدم وجود دور بنفس المفتاح
    existing_role = rbac_crud.get_role_by_key(db, key=role_in.role_name_key)
    if existing_role:
        raise ConflictException(detail=f"الدور بمفتاح '{role_in.role_name_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود الترجمة الافتراضية (TODO)
    # TODO: منطق عمل: التأكد من أن translations تحتوي على ترجمة افتراضية (مثلاً العربية) عند الإنشاء.

    return rbac_crud.create_role(db=db, role_in=role_in)

def get_all_roles_service(db: Session, include_inactive: bool = False) -> List[Role]:
    """
    خدمة لجلب قائمة بجميع الأدوار مع ترجماتها، مع خيار لتضمين غير النشطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        include_inactive (bool): هل يجب تضمين الأدوار غير النشطة؟

    Returns:
        List[Role]: قائمة بكائنات الأدوار.
    """
    return rbac_crud.get_all_roles(db, include_inactive=include_inactive)

def get_role_by_id_service(db: Session, role_id: int) -> Role:
    """
    خدمة لجلب دور واحد بالـ ID، مع تحميل صلاحياته وترجماته ومعالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور المطلوب.

    Returns:
        Role: كائن الدور.

    Raises:
        NotFoundException: إذا لم يتم العثور على الدور.
    """
    role = rbac_crud.get_role_by_id(db, role_id)
    if not role:
        raise NotFoundException(detail=f"الدور بمعرف {role_id} غير موجود.")
    return role

def update_existing_role(db: Session, role_id: int, role_in: schemas.RoleUpdate) -> Role:
    """
    خدمة لتحديث دور موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور المراد تحديثه.
        role_in (schemas.RoleUpdate): البيانات المراد تحديثها.

    Returns:
        Role: كائن الدور المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الدور.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_role = get_role_by_id_service(db, role_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث role_name_key
    if role_in.role_name_key and role_in.role_name_key != db_role.role_name_key:
        existing_role_by_key = rbac_crud.get_role_by_key(db, key=role_in.role_name_key)
        if existing_role_by_key and existing_role_by_key.role_id != role_id:
            raise ConflictException(detail=f"الدور بمفتاح '{role_in.role_name_key}' موجود بالفعل.")

    return rbac_crud.update_role(db, db_role=db_role, role_in=role_in)

def delete_role_by_id(db: Session, role_id_to_delete: int):
    """
    خدمة لحذف دور بشكل آمن (حذف ناعم إذا كان له is_active، أو صارم مع إعادة إسناد).
    تتضمن التحقق من عدم حذف الدور الافتراضي، وإعادة إسناد المستخدمين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id_to_delete (int): معرف الدور المراد حذفه.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الدور.
        BadRequestException: إذا حاول حذف الدور الافتراضي.
        ConflictException: إذا كانت هناك مشكلة في إعادة الإسناد.
    """
    db_role_to_delete = get_role_by_id_service(db, role_id_to_delete) # استخدام دالة الخدمة للتحقق

    # 1. جلب الدور الافتراضي (Default Role)
    DEFAULT_ROLE_KEY = "BASE_USER"
    default_role = rbac_crud.get_role_by_key(db, key=DEFAULT_ROLE_KEY)
    if not default_role:
        raise ConflictException(detail=f"الدور الافتراضي '{DEFAULT_ROLE_KEY}' غير موجود في قاعدة البيانات. يرجى تهيئة البيانات المرجعية.")
    
    # 2. منع حذف الدور الافتراضي نفسه
    if db_role_to_delete.role_id == default_role.role_id:
        raise BadRequestException(detail="لا يمكن حذف الدور الافتراضي للنظام.")

    # 3. التحقق من وجود مستخدمين لديهم هذا الدور كدور أساسي أو إضافي
    users_with_default_role_count = db.query(User).filter(User.default_user_role_id == role_id_to_delete).count()
    users_with_additional_role_count = db.query(UserRole).filter(UserRole.role_id == role_id_to_delete).count()

    if users_with_default_role_count > 0 or users_with_additional_role_count > 0:
        # إذا كان هناك مستخدمون مرتبطون، قم بإعادة إسنادهم
        rbac_crud.reassign_users_to_default_role(
            db=db,
            old_role_id=db_role_to_delete.role_id,
            default_role_id=default_role.role_id
        )
        db.commit() # commit لعملية إعادة الإسناد
    
    # 4. الآن، بعد أن تم نقل كل المستخدمين (أو إذا لم يكن هناك)، يمكننا حذف الدور بأمان
    # إذا كان الدور له is_active، نقوم بالحذف الناعم
    if db_role_to_delete.is_active is not None: # يفترض أن هذا الحقل موجود في المودل
        rbac_crud.soft_delete_role(db, db_role=db_role_to_delete)
        db.commit()
        return {"message": f"تم تعطيل الدور '{db_role_to_delete.role_name_key}' وإعادة إسناد المستخدمين المرتبطين إلى الدور الافتراضي."}
    else: # حذف صارم إذا لم يكن هناك is_active
        rbac_crud.delete_role(db, db_role=db_role_to_delete)
        db.commit()
        return {"message": f"تم حذف الدور '{db_role_to_delete.role_name_key}' بشكل دائم وإعادة إسناد المستخدمين المرتبطين إلى الدور الافتراضي."}


# ==========================================================
# --- خدمات ترجمات الأدوار (RoleTranslation) ---
# ==========================================================

def create_role_translation(db: Session, role_id: int, trans_in: schemas.RoleTranslationCreate) -> Role:
    """
    خدمة لإنشاء ترجمة جديدة لدور.
    تتضمن التحقق من وجود الدور الأم وعدم تكرار الترجمة لنفس اللغة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور الأم.
        trans_in (schemas.RoleTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        Role: كائن الدور الأم المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الدور الأم.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    db_role = get_role_by_id_service(db, role_id) # التحقق من وجود الدور الأم

    # التحقق من عدم وجود ترجمة بنفس اللغة
    if rbac_crud.get_role_translation(db, role_id=role_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة للدور بمعرف {role_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    updated_role = rbac_crud.add_or_update_role_translation(db, role_id=role_id, trans_in=trans_in)
    db.commit() # الـ commit يتم داخل دالة CRUD
    return updated_role

def get_role_translation_details(db: Session, role_id: int, language_code: str) -> RoleTranslation:
    """
    خدمة لجلب ترجمة دور محددة بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور الأم.
        language_code (str): رمز اللغة.

    Returns:
        RoleTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = rbac_crud.get_role_translation(db, role_id=role_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للدور بمعرف {role_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_role_translation(db: Session, role_id: int, language_code: str, trans_in: schemas.RoleTranslationUpdate) -> Role:
    """
    خدمة لتحديث ترجمة دور موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.RoleTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        Role: كائن الدور الأم المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_role_translation_details(db, role_id, language_code) # التحقق من وجود الترجمة
    # add_or_update_role_translation تقوم بالتحديث أيضاً، لكن للتوضيح، يمكن استخدامها هنا
    updated_role = rbac_crud.add_or_update_role_translation(db, role_id=role_id, trans_in=schemas.RoleTranslationCreate(
        language_code=language_code,
        translated_role_name=trans_in.translated_role_name,
        translated_description=trans_in.translated_description
    ))
    db.commit() # commit داخل الدالة crud
    return updated_role

def remove_role_translation(db: Session, role_id: int, language_code: str):
    """
    خدمة لحذف ترجمة دور معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور الأم.
        language_code (str): رمز اللغة للترجمة المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    db_translation = get_role_translation_details(db, role_id, language_code) # التحقق من وجود الترجمة
    rbac_crud.delete_role_translation(db, db_translation=db_translation)
    db.commit()
    return {"message": "تم حذف ترجمة الدور بنجاح."}


# ==========================================================
# --- خدمات الصلاحيات (Permission) ---
# ==========================================================

def create_new_permission(db: Session, permission_in: schemas.PermissionCreate) -> Permission:
    """
    خدمة لإنشاء صلاحية جديدة.
    تتضمن التحقق من عدم تكرار المفتاح.

    Args:
        db (Session): جلسة قاعدة البيانات.
        permission_in (schemas.PermissionCreate): بيانات الصلاحية للإنشاء.

    Returns:
        Permission: كائن الصلاحية الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت الصلاحية بمفتاح معين موجودة بالفعل.
    """
    # 1. التحقق من عدم وجود صلاحية بنفس المفتاح
    existing_permission = rbac_crud.get_permission_by_key(db, key=permission_in.permission_name_key)
    if existing_permission:
        raise ConflictException(detail=f"الصلاحية بمفتاح '{permission_in.permission_name_key}' موجودة بالفعل.")

    return rbac_crud.create_permission(db=db, permission_in=permission_in)

def get_all_permissions_service(db: Session, include_inactive: bool = False) -> List[Permission]:
    """
    خدمة لجلب قائمة بجميع الصلاحيات، مع خيار لتضمين غير النشطة.
    """
    return rbac_crud.get_all_permissions(db, include_inactive=include_inactive)

def get_permission_by_id_service(db: Session, permission_id: int) -> Permission:
    """
    خدمة لجلب صلاحية واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    permission = rbac_crud.get_permission_by_id(db, permission_id)
    if not permission:
        raise NotFoundException(detail=f"الصلاحية بمعرف {permission_id} غير موجودة.")
    return permission

def update_permission(db: Session, permission_id: int, permission_in: schemas.PermissionUpdate) -> Permission:
    """
    خدمة لتحديث صلاحية موجودة.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره.

    Args:
        db (Session): جلسة قاعدة البيانات.
        permission_id (int): معرف الصلاحية المراد تحديثها.
        permission_in (schemas.PermissionUpdate): البيانات المراد تحديثها.

    Returns:
        Permission: كائن الصلاحية المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الصلاحية.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_permission = get_permission_by_id_service(db, permission_id) # استخدام دالة الخدمة للتحقق

    # التحقق من تفرد المفتاح إذا تم تحديث permission_name_key
    if permission_in.permission_name_key and permission_in.permission_name_key != db_permission.permission_name_key:
        existing_permission_by_key = rbac_crud.get_permission_by_key(db, key=permission_in.permission_name_key)
        if existing_permission_by_key and existing_permission_by_key.permission_id != permission_id:
            raise ConflictException(detail=f"الصلاحية بمفتاح '{permission_in.permission_name_key}' موجودة بالفعل.")

    return rbac_crud.update_permission(db, db_permission=db_permission, permission_in=permission_in)

def delete_permission_by_id(db: Session, permission_id: int):
    """
    خدمة لحذف صلاحية بشكل آمن (حذف ناعم إذا كان لها is_active، أو صارم).
    تتضمن التحقق من عدم وجود أدوار مرتبطة بها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        permission_id (int): معرف الصلاحية المراد حذفها.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الصلاحية.
        ConflictException: إذا كانت الصلاحية مرتبطة بأدوار.
    """
    db_permission_to_delete = get_permission_by_id_service(db, permission_id) # استخدام دالة الخدمة للتحقق

    # التحقق من عدم وجود ارتباطات بأدوار
    if db_permission_to_delete.role_associations: # إذا كان هناك أدوار مرتبطة بها
        raise ConflictException(detail=f"لا يمكن حذف الصلاحية بمعرف {permission_id} لأنها مرتبطة بأدوار حاليًا.")
    
    # إذا كان للصلاحية is_active، نقوم بالحذف الناعم
    if db_permission_to_delete.is_active is not None: # يفترض أن هذا الحقل موجود في المودل
        rbac_crud.soft_delete_permission(db, db_permission=db_permission_to_delete)
        db.commit()
        return {"message": f"تم تعطيل الصلاحية '{db_permission_to_delete.permission_name_key}' بنجاح."}
    else: # حذف صارم إذا لم يكن هناك is_active
        rbac_crud.delete_permission(db, db_permission=db_permission_to_delete)
        db.commit()
        return {"message": f"تم حذف الصلاحية '{db_permission_to_delete.permission_name_key}' بشكل دائم."}


# ==========================================================
# --- خدمات ربط الأدوار بالصلاحيات (RolePermission) ---
# ==========================================================

def assign_permission_to_role(db: Session, role_id: int, permission_id: int) -> Role:
    """
    خدمة لإسناد صلاحية لدور.
    تتضمن التحقق من وجود الدور والصلاحية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور.
        permission_id (int): معرف الصلاحية.

    Returns:
        Role: كائن الدور بعد الإسناد.

    Raises:
        NotFoundException: إذا لم يتم العثور على الدور أو الصلاحية.
        ConflictException: إذا كانت الصلاحية مسندة للدور بالفعل.
    """
    db_role = get_role_by_id_service(db, role_id)
    db_permission = get_permission_by_id_service(db, permission_id)

    # التحقق من أن الصلاحية غير مسندة للدور بالفعل
    if db_permission in db_role.permissions: # تستخدم association_proxy
        raise ConflictException(detail=f"الصلاحية '{db_permission.permission_name_key}' مسندة بالفعل للدور '{db_role.role_name_key}'.")

    return rbac_crud.add_permission_to_role(db, role=db_role, permission=db_permission)

def revoke_permission_from_role(db: Session, role_id: int, permission_id: int):
    """
    خدمة لسحب صلاحية من دور.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور.
        permission_id (int): معرف الصلاحية.

    Returns:
        dict: رسالة تأكيد.

    Raises:
        NotFoundException: إذا لم يتم العثور على الدور أو الصلاحية.
    """
    db_role = get_role_by_id_service(db, role_id)
    db_permission = get_permission_by_id_service(db, permission_id)

    # التحقق من وجود الربط
    if db_permission not in db_role.permissions: # تستخدم association_proxy
        raise NotFoundException(detail=f"الصلاحية '{db_permission.permission_name_key}' ليست مسندة للدور '{db_role.role_name_key}'.")

    rbac_crud.remove_permission_from_role(db, role=db_role, permission=db_permission)
    return {"message": "تم سحب الصلاحية من الدور بنجاح."}


# ==========================================================
# --- خدمات ربط المستخدمين بالأدوار (UserRole) ---
# ==========================================================

def assign_role_to_user(db: Session, user_id: UUID, role_id: int, assigned_by_user_id: UUID) -> UserRole:
    """
    خدمة لإسناد دور إضافي لمستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.
        role_id (int): معرف الدور.
        assigned_by_user_id (UUID): معرف المستخدم الذي يقوم بالإسناد.

    Returns:
        UserRole: كائن الربط الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم أو الدور.
        ConflictException: إذا كان الدور مسنداً للمستخدم بالفعل.
        BadRequestException: إذا كان الدور المراد إسناده هو الدور الافتراضي للمستخدم.
    """
    # 1. التحقق من وجود المستخدمين والدور
    db_user = core_crud.get_user_by_id(db, user_id)
    if not db_user: raise NotFoundException(detail=f"المستخدم بمعرف {user_id} غير موجود.")
    db_role = get_role_by_id_service(db, role_id) # استخدام دالة الخدمة للتحقق
    assigned_by_user_obj = core_crud.get_user_by_id(db, assigned_by_user_id)
    if not assigned_by_user_obj: raise NotFoundException(detail=f"المستخدم الذي يقوم بالإسناد بمعرف {assigned_by_user_id} غير موجود.")

    # 2. منع إسناد الدور الافتراضي للمستخدم كدور إضافي
    if db_user.default_user_role_id == role_id:
        raise BadRequestException(detail="لا يمكن إسناد الدور الافتراضي للمستخدم كدور إضافي. إنه مسند بالفعل.")

    # 3. التحقق من أن الدور غير مسند للمستخدم بالفعل
    existing_user_role = rbac_crud.get_user_role_association(db, user_id=user_id, role_id=role_id)
    if existing_user_role:
        raise ConflictException(detail=f"الدور '{db_role.role_name_key}' مسند بالفعل للمستخدم '{db_user.user_id}'.")

    return rbac_crud.add_role_to_user(db, user=db_user, role=db_role, assigned_by_user_id=assigned_by_user_id)

def remove_role_from_user(db: Session, user_id: UUID, role_id: int):
    """
    خدمة لسحب دور إضافي من مستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.
        role_id (int): معرف الدور.

    Returns:
        dict: رسالة تأكيد.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستخدم أو الدور.
        BadRequestException: إذا حاول سحب الدور الافتراضي أو الدور غير المسند.
    """
    db_user = core_crud.get_user_by_id(db, user_id)
    if not db_user: raise NotFoundException(detail=f"المستخدم بمعرف {user_id} غير موجود.")
    db_role = get_role_by_id_service(db, role_id) # استخدام دالة الخدمة للتحقق

    # منع سحب الدور الافتراضي
    if db_user.default_user_role_id == role_id:
        raise BadRequestException(detail="لا يمكن سحب الدور الافتراضي للمستخدم. يرجى تغيير دوره الأساسي بدلاً من ذلك.")
    
    # التحقق من أن الدور مسند للمستخدم بالفعل
    existing_user_role = rbac_crud.get_user_role_association(db, user_id=user_id, role_id=role_id)
    if not existing_user_role:
        raise NotFoundException(detail=f"الدور '{db_role.role_name_key}' ليس مسنداً للمستخدم '{db_user.user_id}'.")

    rbac_crud.remove_role_from_user(db, user=db_user, role=db_role)
    return {"message": "تم سحب الدور من المستخدم بنجاح."}