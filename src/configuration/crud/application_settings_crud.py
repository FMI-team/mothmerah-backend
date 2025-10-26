# backend\src\configuration\crud\application_settings_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.configuration.models import settings_models as models # ApplicationSetting, ApplicationSettingTranslation
# استيراد Schemas (لـ type hinting في Create/Update)
from src.configuration.schemas import settings_schemas as schemas
# استيراد مودل Language و User للتحقق من وجود FKs في جداول الترجمة/الإعدادات
from src.lookups.models.lookups_models import Language
from src.users.models.core_models import User


# ==========================================================
# --- CRUD Functions for ApplicationSetting ---
# ==========================================================

def create_application_setting(db: Session, setting_in: schemas.ApplicationSettingCreate) -> models.ApplicationSetting:
    """
    ينشئ إعداد تطبيق جديد في قاعدة البيانات، مع ترجماته الأولية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        setting_in (schemas.ApplicationSettingCreate): بيانات الإعداد للإنشاء.

    Returns:
        models.ApplicationSetting: كائن الإعداد الذي تم إنشاؤه.
    """
    db_setting = models.ApplicationSetting(
        setting_key=setting_in.setting_key,
        setting_value=setting_in.setting_value,
        setting_datatype=setting_in.setting_datatype,
        description_key=setting_in.description_key,
        module_scope=setting_in.module_scope,
        is_editable_by_admin=setting_in.is_editable_by_admin,
        # created_at, updated_at سيتم تعيينهما افتراضياً في المودل
        # updated_by_user_id سيتم تعيينه في طبقة الخدمة
    )
    db.add(db_setting)
    db.flush() # للحصول على setting_id قبل إضافة الترجمات

    if setting_in.translations:
        for trans_in in setting_in.translations:
            # التحقق من وجود اللغة (Language)
            language = db.query(Language).filter(Language.language_code == trans_in.language_code).first()
            if not language:
                # يفضل أن يتم التعامل مع هذا في طبقة الخدمة ورمي NotFoundException
                raise ValueError(f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")
                
            db_translation = models.ApplicationSettingTranslation(
                setting_id=db_setting.setting_id,
                language_code=trans_in.language_code,
                translated_setting_value=trans_in.translated_setting_value,
                translated_setting_description=trans_in.translated_setting_description
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def get_application_setting(db: Session, setting_id: int) -> Optional[models.ApplicationSetting]:
    """
    يجلب إعداد تطبيق واحد بالـ ID الخاص به، مع ترجماته.

    Args:
        db (Session): جلسة قاعدة البيانات.
        setting_id (int): معرف الإعداد المطلوب.

    Returns:
        Optional[models.ApplicationSetting]: كائن الإعداد أو None.
    """
    return db.query(models.ApplicationSetting).options(
        joinedload(models.ApplicationSetting.translations),
        joinedload(models.ApplicationSetting.last_updated_by_user)
    ).filter(models.ApplicationSetting.setting_id == setting_id).first()

def get_application_setting_by_key(db: Session, key: str) -> Optional[models.ApplicationSetting]:
    """جلب إعداد تطبيق عن طريق المفتاح الفريد."""
    return db.query(models.ApplicationSetting).filter(models.ApplicationSetting.setting_key == key).first()

def get_all_application_settings(
    db: Session,
    module_scope: Optional[str] = None,
    is_editable_by_admin: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ApplicationSetting]:
    """
    يجلب قائمة بإعدادات التطبيق، مع خيارات التصفية والترقيم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        module_scope (Optional[str]): تصفية حسب نطاق الوحدة.
        is_editable_by_admin (Optional[bool]): تصفية حسب قابلية التعديل بواسطة المسؤول.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.ApplicationSetting]: قائمة بكائنات الإعدادات.
    """
    query = db.query(models.ApplicationSetting).options(
        joinedload(models.ApplicationSetting.translations),
        joinedload(models.ApplicationSetting.last_updated_by_user)
    )
    if module_scope:
        query = query.filter(models.ApplicationSetting.module_scope == module_scope)
    if is_editable_by_admin is not None:
        query = query.filter(models.ApplicationSetting.is_editable_by_admin == is_editable_by_admin)
    
    return query.order_by(models.ApplicationSetting.setting_key).offset(skip).limit(limit).all()

def update_application_setting(db: Session, db_setting: models.ApplicationSetting, setting_in: schemas.ApplicationSettingUpdate, updated_by_user_id: Optional[UUID] = None) -> models.ApplicationSetting:
    """
    يحدث بيانات إعداد تطبيق موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_setting (models.ApplicationSetting): كائن الإعداد من قاعدة البيانات.
        setting_in (schemas.ApplicationSettingUpdate): البيانات المراد تحديثها.
        updated_by_user_id (Optional[UUID]): معرف المستخدم الذي أجرى التحديث.

    Returns:
        models.ApplicationSetting: كائن الإعداد المحدث.
    """
    update_data = setting_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_setting, key, value)
    
    db_setting.updated_at = datetime.now(timezone.utc)
    db_setting.last_updated_by_user_id = updated_by_user_id # يتم تعيينه هنا
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def delete_application_setting(db: Session, db_setting: models.ApplicationSetting):
    """
    يحذف إعداد تطبيق معين (حذف صارم).
    TODO: التحقق من عدم وجود أي استخدام حيوي للإعداد في الكود أو جداول أخرى سيتم في طبقة الخدمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_setting (models.ApplicationSetting): كائن الإعداد من قاعدة البيانات.
    """
    db.delete(db_setting)
    db.commit()
    return


# ==========================================================
# --- CRUD Functions for ApplicationSettingTranslation ---
# ==========================================================

def create_application_setting_translation(db: Session, setting_id: int, trans_in: schemas.ApplicationSettingTranslationCreate) -> models.ApplicationSettingTranslation:
    """
    ينشئ ترجمة جديدة لإعداد تطبيق معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        setting_id (int): معرف الإعداد الأم.
        trans_in (schemas.ApplicationSettingTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.ApplicationSettingTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models.ApplicationSettingTranslation(
        setting_id=setting_id,
        language_code=trans_in.language_code,
        translated_setting_value=trans_in.translated_setting_value,
        translated_setting_description=trans_in.translated_setting_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_application_setting_translation(db: Session, setting_id: int, language_code: str) -> Optional[models.ApplicationSettingTranslation]:
    """
    يجلب ترجمة إعداد تطبيق محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        setting_id (int): معرف الإعداد.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models.ApplicationSettingTranslation]: كائن الترجمة أو None.
    """
    return db.query(models.ApplicationSettingTranslation).filter(
        and_(
            models.ApplicationSettingTranslation.setting_id == setting_id,
            models.ApplicationSettingTranslation.language_code == language_code
        )
    ).first()

def update_application_setting_translation(db: Session, db_translation: models.ApplicationSettingTranslation, trans_in: schemas.ApplicationSettingTranslationUpdate) -> models.ApplicationSettingTranslation:
    """
    يحدث ترجمة إعداد تطبيق موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.ApplicationSettingTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.ApplicationSettingTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.ApplicationSettingTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_application_setting_translation(db: Session, db_translation: models.ApplicationSettingTranslation):
    """
    يحذف ترجمة إعداد تطبيق معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.ApplicationSettingTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return