# backend\src\configuration\crud\feature_flags_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.configuration.models import settings_models as models # FeatureFlag
# استيراد Schemas (لـ type hinting في Create/Update)
from src.configuration.schemas import settings_schemas as schemas
# استيراد مودل User للتحقق من وجود FKs في جداول FeatureFlag
from src.users.models.core_models import User


# ==========================================================
# --- CRUD Functions for FeatureFlag ---
# ==========================================================

def create_feature_flag(db: Session, flag_in: schemas.FeatureFlagCreate) -> models.FeatureFlag:
    """
    ينشئ علم ميزة جديد في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        flag_in (schemas.FeatureFlagCreate): بيانات علم الميزة للإنشاء.

    Returns:
        models.FeatureFlag: كائن علم الميزة الذي تم إنشاؤه.
    """
    db_flag = models.FeatureFlag(
        flag_name=flag_in.flag_name, # BRD has flag_name_key, model has flag_name
        description_key=flag_in.description_key,
        is_enabled=flag_in.is_enabled,
        activation_rules=flag_in.activation_rules,
        # created_at, updated_at سيتم تعيينهما افتراضياً في المودل
        # updated_by_user_id سيتم تعيينه في طبقة الخدمة
    )
    db.add(db_flag)
    db.commit()
    db.refresh(db_flag)
    return db_flag

def get_feature_flag(db: Session, flag_id: int) -> Optional[models.FeatureFlag]:
    """
    يجلب علم ميزة واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        flag_id (int): معرف علم الميزة المطلوب.

    Returns:
        Optional[models.FeatureFlag]: كائن علم الميزة أو None.
    """
    return db.query(models.FeatureFlag).options(
        joinedload(models.FeatureFlag.last_updated_by_user)
    ).filter(models.FeatureFlag.flag_id == flag_id).first()

def get_feature_flag_by_name(db: Session, flag_name: str) -> Optional[models.FeatureFlag]:
    """جلب علم ميزة عن طريق المفتاح الفريد (الاسم)."""
    return db.query(models.FeatureFlag).filter(models.FeatureFlag.flag_name == flag_name).first() # BRD has flag_name_key, model has flag_name


def get_all_feature_flags(
    db: Session,
    is_enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.FeatureFlag]:
    """
    يجلب قائمة بأعلام تفعيل الميزات، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        is_enabled (Optional[bool]): تصفية حسب حالة التفعيل.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.FeatureFlag]: قائمة بكائنات أعلام الميزات.
    """
    query = db.query(models.FeatureFlag).options(
        joinedload(models.FeatureFlag.last_updated_by_user)
    )
    if is_enabled is not None:
        query = query.filter(models.FeatureFlag.is_enabled == is_enabled)
    
    return query.order_by(models.FeatureFlag.flag_name).offset(skip).limit(limit).all()

def update_feature_flag(db: Session, db_flag: models.FeatureFlag, flag_in: schemas.FeatureFlagUpdate, updated_by_user_id: Optional[UUID] = None) -> models.FeatureFlag:
    """
    يحدث بيانات علم ميزة موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_flag (models.FeatureFlag): كائن علم الميزة من قاعدة البيانات.
        flag_in (schemas.FeatureFlagUpdate): البيانات المراد تحديثها.
        updated_by_user_id (Optional[UUID]): معرف المستخدم الذي أجرى التحديث.

    Returns:
        models.FeatureFlag: كائن علم الميزة المحدث.
    """
    update_data = flag_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_flag, key, value)
    
    db_flag.updated_at = datetime.now(timezone.utc)
    db_flag.last_updated_by_user_id = updated_by_user_id # يتم تعيينه هنا
    db.add(db_flag)
    db.commit()
    db.refresh(db_flag)
    return db_flag

def delete_feature_flag(db: Session, db_flag: models.FeatureFlag):
    """
    يحذف علم ميزة معين (حذف صارم).
    TODO: التحقق من عدم وجود أي تبعيات برمجية نشطة على هذا العلم قبل الحذف.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_flag (models.FeatureFlag): كائن علم الميزة من قاعدة البيانات.
    """
    db.delete(db_flag)
    db.commit()
    return