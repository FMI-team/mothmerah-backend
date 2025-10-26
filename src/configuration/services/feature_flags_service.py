# backend\src\configuration\services\feature_flags_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.configuration.models import settings_models as models # FeatureFlag
# استيراد الـ CRUD
from src.configuration.crud import feature_flags_crud as crud
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)

# استيراد Schemas
from src.configuration.schemas import settings_schemas as schemas # FeatureFlag

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for FeatureFlag ---
# ==========================================================

def create_new_feature_flag(db: Session, flag_in: schemas.FeatureFlagCreate, current_user: User) -> models.FeatureFlag:
    """
    خدمة لإنشاء علم ميزة جديد.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        flag_in (schemas.FeatureFlagCreate): بيانات علم الميزة للإنشاء.
        current_user (User): المستخدم الذي ينشئ علم الميزة.

    Returns:
        models.FeatureFlag: كائن علم الميزة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان علم الميزة بنفس المفتاح موجوداً بالفعل.
    """
    # 1. التحقق من عدم وجود علم ميزة بنفس المفتاح
    existing_flag = crud.get_feature_flag_by_name(db, flag_name=flag_in.flag_name) # BRD has flag_name_key, model has flag_name
    if existing_flag:
        raise ConflictException(detail=f"علم الميزة بمفتاح '{flag_in.flag_name}' موجود بالفعل.")
    
    # 2. التحقق من المستخدم الذي يقوم بالإنشاء
    user_exists = core_crud.get_user_by_id(db, current_user.user_id)
    if not user_exists: # لا ينبغي أن يحدث هذا إذا كان current_user قادماً من dependency
        raise NotFoundException(detail=f"المستخدم بمعرف {current_user.user_id} غير موجود.")

    return crud.create_feature_flag(db=db, flag_in=flag_in)

def get_all_feature_flags_service(
    db: Session,
    is_enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.FeatureFlag]:
    """خدمة لجلب قائمة بأعلام تفعيل الميزات، مع خيارات التصفية والترقيم."""
    return crud.get_all_feature_flags(
        db=db,
        is_enabled=is_enabled,
        skip=skip,
        limit=limit
    )

def get_feature_flag_details(db: Session, flag_id: int) -> models.FeatureFlag:
    """
    خدمة لجلب علم ميزة واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        flag_id (int): معرف علم الميزة المطلوب.

    Returns:
        models.FeatureFlag: كائن علم الميزة.

    Raises:
        NotFoundException: إذا لم يتم العثور على علم الميزة.
    """
    db_flag = crud.get_feature_flag(db, flag_id=flag_id)
    if not db_flag:
        raise NotFoundException(detail=f"علم الميزة بمعرف {flag_id} غير موجود.")
    return db_flag

def get_feature_flag_by_name_service(db: Session, flag_name: str) -> models.FeatureFlag:
    """
    خدمة لجلب علم ميزة واحد بالاسم الخاص به.
    """
    db_flag = crud.get_feature_flag_by_name(db, flag_name=flag_name)
    if not db_flag:
        raise NotFoundException(detail=f"علم الميزة بالاسم '{flag_name}' غير موجود.")
    return db_flag


def update_feature_flag_service(db: Session, flag_id: int, flag_in: schemas.FeatureFlagUpdate, current_user: User) -> models.FeatureFlag:
    """
    خدمة لتحديث علم ميزة موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره، وصلاحية المستخدم للتعديل.

    Args:
        db (Session): جلسة قاعدة البيانات.
        flag_id (int): معرف علم الميزة المراد تحديثه.
        flag_in (schemas.FeatureFlagUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الذي يجري التحديث (يجب أن يكون مسؤولاً).

    Returns:
        models.FeatureFlag: كائن علم الميزة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على علم الميزة.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
    """
    db_flag = get_feature_flag_details(db, flag_id) # استخدام دالة الخدمة للتحقق

    # 1. التحقق من تفرد المفتاح إذا تم تحديث flag_name
    if flag_in.flag_name and flag_in.flag_name != db_flag.flag_name: # BRD has flag_name_key, model has flag_name
        existing_flag_by_name = crud.get_feature_flag_by_name(db, flag_name=flag_in.flag_name)
        if existing_flag_by_name and existing_flag_by_name.flag_id != flag_id:
            raise ConflictException(detail=f"علم الميزة بالاسم '{flag_in.flag_name}' موجود بالفعل.")

    # 2. TODO: تطبيق منطق قواعد التفعيل إذا تم تحديثها.

    return crud.update_feature_flag(db, db_flag=db_flag, flag_in=flag_in, updated_by_user_id=current_user.user_id)

def delete_feature_flag_service(db: Session, flag_id: int, current_user: User):
    """
    خدمة لحذف علم ميزة (حذف صارم).
    تتضمن التحقق من صلاحيات المستخدم وعدم وجود أي تبعيات برمجية نشطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        flag_id (int): معرف علم الميزة المراد حذفه.
        current_user (User): المستخدم الذي يقوم بالحذف (يجب أن يكون مسؤولاً).

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على علم الميزة.
        ForbiddenException: إذا كان المستخدم غير مصرح له.
        ConflictException: إذا كان علم الميزة يستخدم حالياً.
    """
    db_flag = get_feature_flag_details(db, flag_id) # استخدام دالة الخدمة للتحقق

    # TODO: التحقق من صلاحية المستخدم (ADMIN_MANAGE_SETTINGS)
    # TODO: التحقق من عدم وجود أي تبعيات برمجية نشطة على هذا العلم قبل الحذف.
    #       هذا يتطلب تحليل الكود أو تتبع الاستخدامات، وهي عملية معقدة.
    #       لأغراض MVP، يمكن السماح بالحذف إذا لم تكن هناك قيود FKs.

    crud.delete_feature_flag(db=db, db_flag=db_flag)
    return {"message": f"تم حذف علم الميزة '{db_flag.flag_name}' بنجاح."}