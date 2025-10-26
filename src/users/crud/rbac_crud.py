# backend\src\users\crud\rbac_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز من Users (المجموعة 1)
from src.users.models import roles_models as models # Role, Permission, RolePermission, UserRole, RoleTranslation
from src.users.models import core_models as user_models # User (لـ UserRole)
# استيراد Schemas
from src.users.schemas import rbac_schemas as schemas


# ==========================================================
# --- CRUD Functions for Role (الأدوار) ---
# ==========================================================

def create_role(db: Session, role_in: schemas.RoleCreate) -> models.Role:
    """
    ينشئ دوراً جديداً في قاعدة البيانات، مع ترجماته الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_in (schemas.RoleCreate): بيانات الدور للإنشاء.

    Returns:
        models.Role: كائن الدور الذي تم إنشاؤه.
    """
    role_data = role_in.model_dump(exclude={"translations"})
    db_role = models.Role(**role_data)

    if role_in.translations:
        for trans in role_in.translations:
            db_role.translations.append(models.RoleTranslation(**trans.model_dump()))

    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def get_role_by_id(db: Session, role_id: int) -> Optional[models.Role]:
    """
    جلب دور واحد عن طريق الـ ID الخاص به، مع تحميل صلاحياته وترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور المطلوب.

    Returns:
        Optional[models.Role]: كائن الدور أو None.
    """
    return db.query(models.Role).options(
        joinedload(models.Role.permission_associations).joinedload(models.RolePermission.permission), # صلاحيات الدور
        joinedload(models.Role.translations) # ترجمات الدور
    ).filter(models.Role.role_id == role_id).first()

def get_role_by_key(db: Session, key: str) -> Optional[models.Role]:
    """جلب دور واحد عن طريق مفتاحه النصي (role_name_key)."""
    return db.query(models.Role).filter(models.Role.role_name_key == key).first()

def get_all_roles(db: Session, include_inactive: bool = False) -> List[models.Role]:
    """جلب قائمة بجميع الأدوار مع ترجماتها، مع خيار لتضمين غير النشطة."""
    query = db.query(models.Role).options(joinedload(models.Role.translations))
    if not include_inactive:
        query = query.filter(models.Role.is_active == True)
    return query.order_by(models.Role.role_id).all()

def update_role(db: Session, db_role: models.Role, role_in: schemas.RoleUpdate) -> models.Role:
    """تحديث بيانات دور موجود."""
    update_data = role_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_role, key, value)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def soft_delete_role(db: Session, db_role: models.Role) -> models.Role:
    """يقوم بالحذف الناعم لدور عن طريق تعيين 'is_active' إلى False."""
    db_role.is_active = False
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def delete_role(db: Session, db_role: models.Role) -> None:
    """حذف دور بشكل نهائي من قاعدة البيانات.
    TODO: التحقق من عدم وجود ارتباطات (مستخدمين، صلاحيات) سيتم في طبقة الخدمة.
    """
    db.delete(db_role)
    # لا نقم بعمل commit هنا، ليتم التحكم به من الخدمة
    return


# ==========================================================
# --- CRUD Functions for RoleTranslation (ترجمات الأدوار) ---
# ==========================================================

def add_or_update_role_translation(db: Session, role_id: int, trans_in: schemas.RoleTranslationCreate) -> models.Role:
    """إضافة أو تحديث ترجمة لدور معين.
    يعيد الكائن الأب (Role) كاملاً مع كل ترجماته المحدثة.
    """
    db_role = db.query(models.Role).options(joinedload(models.Role.translations)).filter(models.Role.role_id == role_id).first()
    if not db_role:
        return None # يُفترض أن التحقق من وجود الدور الأم يتم في طبقة الخدمة

    existing_trans = next((t for t in db_role.translations if t.language_code == trans_in.language_code), None)
    if existing_trans:
        existing_trans.translated_role_name = trans_in.translated_role_name
        existing_trans.translated_description = trans_in.translated_description
    else:
        db_role.translations.append(models.RoleTranslation(**trans_in.model_dump()))
    
    db.commit()
    db.refresh(db_role)
    return db_role

def get_role_translation(db: Session, role_id: int, language_code: str) -> Optional[models.RoleTranslation]:
    """جلب ترجمة معينة لدور معين بلغة معينة."""
    return db.query(models.RoleTranslation).filter(
        and_(
            models.RoleTranslation.role_id == role_id,
            models.RoleTranslation.language_code == language_code
        )
    ).first()

def update_role_translation(db: Session, db_translation: models.RoleTranslation, trans_in: schemas.RoleTranslationUpdate) -> models.RoleTranslation:
    """تحديث بيانات ترجمة دور موجودة."""
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_role_translation(db: Session, db_translation: models.RoleTranslation) -> None:
    """حذف ترجمة دور من قاعدة البيانات."""
    db.delete(db_translation)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for Permission (الصلاحيات) ---
# ==========================================================

def create_permission(db: Session, permission_in: schemas.PermissionCreate) -> models.Permission:
    """ينشئ صلاحية جديدة في قاعدة البيانات."""
    db_permission = models.Permission(**permission_in.model_dump())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def get_permission_by_id(db: Session, permission_id: int) -> Optional[models.Permission]:
    """جلب صلاحية واحدة عن طريق الـ ID الخاص بها."""
    return db.query(models.Permission).filter(models.Permission.permission_id == permission_id).first()

def get_permission_by_key(db: Session, permission_key: str) -> Optional[models.Permission]:
    """جلب صلاحية واحدة عن طريق اسمها المفتاحي."""
    return db.query(models.Permission).filter(models.Permission.permission_name_key == permission_key).first()

def get_all_permissions(db: Session, include_inactive: bool = False) -> List[models.Permission]:
    """جلب قائمة بجميع الصلاحيات، مع خيار لتضمين غير النشطة."""
    query = db.query(models.Permission)
    if not include_inactive:
        query = query.filter(models.Permission.is_active == True)
    return query.order_by(models.Permission.permission_id).all()

def update_permission(db: Session, db_permission: models.Permission, permission_in: schemas.PermissionUpdate) -> models.Permission:
    """تحديث بيانات صلاحية موجودة."""
    update_data = permission_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_permission, key, value)
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def soft_delete_permission(db: Session, db_permission: models.Permission) -> models.Permission:
    """يقوم بالحذف الناعم لصلاحية عن طريق تعيين 'is_active' إلى False."""
    db_permission.is_active = False
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def delete_permission(db: Session, db_permission: models.Permission) -> None:
    """حذف صلاحية بشكل نهائي من قاعدة البيانات.
    TODO: التحقق من عدم وجود ارتباطات (أدوار) سيتم في طبقة الخدمة.
    """
    db.delete(db_permission)
    # لا نقم بعمل commit هنا، ليتم التحكم به من الخدمة
    return


# ==========================================================
# --- CRUD Functions for RolePermission (ربط الأدوار بالصلاحيات) ---
# ==========================================================

def add_permission_to_role(db: Session, role: models.Role, permission: models.Permission) -> models.Role:
    """
    إضافة صلاحية إلى دور معين.
    يُستخدم association_proxy في مودل Role، مما يجعل هذه الدالة أبسط.
    """
    # بما أن العلاقة `permissions` في مودل Role تستخدم association_proxy مع creator،
    # يمكننا إضافة الصلاحية مباشرة عبر role.permissions.append.
    # ومع ذلك، يجب التأكد من عدم وجود تكرار لتجنب الأخطاء.
    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()
        db.refresh(role)
    return role

def remove_permission_from_role(db: Session, role: models.Role, permission: models.Permission):
    """
    سحب صلاحية من دور معين.
    يُستخدم association_proxy في مودل Role.
    """
    if permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()
    return

def get_role_permission_association(db: Session, role_id: int, permission_id: int) -> Optional[models.RolePermission]:
    """
    يجلب سجل ربط معين بين دور وصلاحية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        role_id (int): معرف الدور.
        permission_id (int): معرف الصلاحية.

    Returns:
        Optional[models.RolePermission]: كائن الربط أو None.
    """
    return db.query(models.RolePermission).filter(
        and_(
            models.RolePermission.role_id == role_id,
            models.RolePermission.permission_id == permission_id
        )
    ).first()

def delete_role_permission(db: Session, db_role_permission: models.RolePermission) -> None:
    """
    يحذف سجل ربط بين دور وصلاحية (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_role_permission (models.RolePermission): كائن الربط من قاعدة البيانات.
    """
    db.delete(db_role_permission)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for UserRole (ربط المستخدمين بالأدوار) ---
# ==========================================================

def add_role_to_user(db: Session, user: user_models.User, role: models.Role, assigned_by_user_id: Optional[UUID] = None) -> models.UserRole:
    """
    إضافة دور لمستخدم.
    يُستخدم association_proxy في مودل User، مما يجعل هذه الدالة أبسط.
    """
    # بما أن العلاقة `user_roles` في مودل User تستخدم association_proxy مع creator،
    # يمكننا إضافة الدور مباشرة عبر user.user_roles.append(role_obj).
    # ومع ذلك، يجب التأكد من عدم وجود تكرار لتجنب الأخطاء.
    # TODO: يجب إضافة تحقق من عدم التكرار إذا كان Role.users يستخدم association_proxy بشكل متبادل.
    
    # التحقق اليدوي لتجنب duplicate primary key error إذا لم يكن AssociationProxy يدعم ذلك
    existing_user_role = db.query(models.UserRole).filter(
        and_(
            models.UserRole.user_id == user.user_id,
            models.UserRole.role_id == role.role_id
        )
    ).first()
    if existing_user_role:
        return existing_user_role # الدور موجود بالفعل، لا تفعل شيئاً

    db_user_role = models.UserRole(
        user_id=user.user_id,
        role_id=role.role_id,
        assigned_by_user_id=assigned_by_user_id
    )
    db.add(db_user_role)
    db.commit()
    db.refresh(db_user_role)
    return db_user_role

def remove_role_from_user(db: Session, user: user_models.User, role: models.Role):
    """
    سحب دور من مستخدم.
    يُستخدم association_proxy في مودل User.
    """
    # بما أن العلاقة `user_roles` في مودل User تستخدم association_proxy،
    # يمكننا حذف الدور مباشرة عبر user.user_roles.remove(role_obj).
    # TODO: يجب التأكد من كيفية عمل .remove() مع AssociationProxy
    #       أو حذف سجل UserRole مباشرة.
    
    db_user_role = db.query(models.UserRole).filter(
        and_(
            models.UserRole.user_id == user.user_id,
            models.UserRole.role_id == role.role_id
        )
    ).first()
    if db_user_role:
        db.delete(db_user_role)
        db.commit()
    return


def get_user_role_association(db: Session, user_id: UUID, role_id: int) -> Optional[models.UserRole]:
    """
    يجلب سجل ربط معين بين مستخدم ودور.
    """
    return db.query(models.UserRole).filter(
        and_(
            models.UserRole.user_id == user_id,
            models.UserRole.role_id == role_id
        )
    ).first()

def get_roles_for_user(db: Session, user_id: UUID) -> List[models.UserRole]:
    """
    جلب جميع الأدوار المرتبطة بمستخدم معين (من جدول UserRole).
    """
    return db.query(models.UserRole).filter(models.UserRole.user_id == user_id).all()

def reassign_users_to_default_role(db: Session, old_role_id: int, default_role_id: int):
    """
    إعادة إسناد المستخدمين الذين لديهم دور معين (كرول أساسي default_user_role_id) إلى الدور الافتراضي.
    """
    # هذا التحديث يتم على جدول users مباشرة
    updated_rows = db.query(user_models.User).filter(
        user_models.User.default_user_role_id == old_role_id
    ).update(
        {user_models.User.default_user_role_id: default_role_id},
        synchronize_session=False # ضروري للأداء في التحديث المجمع
    )
    # لا نقم بالـ commit هنا، ليتم التحكم بالـ transaction من طبقة الخدمات
    return updated_rows