# backend\src\configuration\services\application_settings_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لتسجيل الوقت الحالي

# استيراد المودلز
from src.configuration.models import settings_models as models # ApplicationSetting, ApplicationSettingTranslation
# استيراد الـ CRUD
from src.configuration.crud import application_settings_crud as crud
from src.users.crud import core_crud # للتحقق من وجود المستخدم (User)
from src.lookups.crud import languages_crud # للتحقق من وجود اللغة (Language)

# استيراد Schemas
from src.configuration.schemas import settings_schemas as schemas # ApplicationSetting, ApplicationSettingTranslation

# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)


# ==========================================================
# --- Services for ApplicationSetting ---
# ==========================================================

def create_new_application_setting(db: Session, setting_in: schemas.ApplicationSettingCreate, current_user: User) -> models.ApplicationSetting:
    """
    خدمة لإنشاء إعداد تطبيق جديد مع ترجماته الأولية.
    تتضمن التحقق من عدم التكرار.

    Args:
        db (Session): جلسة قاعدة البيانات.
        setting_in (schemas.ApplicationSettingCreate): بيانات الإعداد للإنشاء.
        current_user (User): المستخدم الذي ينشئ الإعداد.

    Returns:
        models.ApplicationSetting: كائن الإعداد الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كان الإعداد بمفتاح معين موجوداً بالفعل.
        NotFoundException: إذا كانت اللغة المحددة للترجمة غير موجودة.
    """
    # 1. التحقق من عدم وجود إعداد بنفس المفتاح
    existing_setting = crud.get_application_setting_by_key(db, key=setting_in.setting_key)
    if existing_setting:
        raise ConflictException(detail=f"الإعداد بمفتاح '{setting_in.setting_key}' موجود بالفعل.")
    
    # 2. التحقق من وجود اللغات المستخدمة في الترجمات
    if setting_in.translations:
        for trans_in in setting_in.translations:
            language_obj = languages_crud.get_language(db, language_code=trans_in.language_code)
            if not language_obj:
                raise NotFoundException(detail=f"رمز اللغة '{trans_in.language_code}' غير موجود في نظام اللغات.")

    # 3. التحقق من المستخدم الذي يقوم بالإنشاء
    user_exists = core_crud.get_user_by_id(db, current_user.user_id)
    if not user_exists: # لا ينبغي أن يحدث هذا إذا كان current_user قادماً من dependency
        raise NotFoundException(detail=f"المستخدم بمعرف {current_user.user_id} غير موجود.")

    return crud.create_application_setting(db=db, setting_in=setting_in)

def get_all_application_settings_service(
    db: Session,
    module_scope: Optional[str] = None,
    is_editable_by_admin: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ApplicationSetting]:
    """خدمة لجلب قائمة بإعدادات التطبيق، مع خيارات التصفية والترقيم."""
    return crud.get_all_application_settings(
        db=db,
        module_scope=module_scope,
        is_editable_by_admin=is_editable_by_admin,
        skip=skip,
        limit=limit
    )

def get_application_setting_details(db: Session, setting_id: int) -> models.ApplicationSetting:
    """
    خدمة لجلب إعداد تطبيق واحد بالـ ID الخاص به، مع معالجة عدم الوجود.
    """
    db_setting = crud.get_application_setting(db, setting_id=setting_id)
    if not db_setting:
        raise NotFoundException(detail=f"إعداد التطبيق بمعرف {setting_id} غير موجود.")
    return db_setting

def get_application_setting_by_key_service(db: Session, setting_key: str) -> models.ApplicationSetting:
    """
    خدمة لجلب إعداد تطبيق واحد بالمفتاح الخاص به، مع معالجة عدم الوجود.
    """
    db_setting = crud.get_application_setting_by_key(db, key=setting_key)
    if not db_setting:
        raise NotFoundException(detail=f"إعداد التطبيق بمفتاح '{setting_key}' غير موجود.")
    return db_setting

def update_application_setting_service(db: Session, setting_id: int, setting_in: schemas.ApplicationSettingUpdate, current_user: User) -> models.ApplicationSetting:
    """
    خدمة لتحديث إعداد تطبيق موجود.
    تتضمن التحقق من تفرد المفتاح إذا تم تغييره، وصلاحية المستخدم للتعديل.

    Args:
        db (Session): جلسة قاعدة البيانات.
        setting_id (int): معرف الإعداد المراد تحديثه.
        setting_in (schemas.ApplicationSettingUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الذي يجري التحديث (يجب أن يكون مسؤولاً).

    Returns:
        models.ApplicationSetting: كائن الإعداد المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإعداد.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
        ForbiddenException: إذا كان الإعداد غير قابل للتعديل بواسطة المسؤول.
    """
    db_setting = get_application_setting_details(db, setting_id) # استخدام دالة الخدمة للتحقق

    # 1. التحقق من صلاحية المستخدم للتعديل (إذا كان الإعداد غير قابل للتعديل من المسؤول، أو المستخدم ليس مسؤولاً)
    # TODO: يجب أن يكون هناك تحقق من صلاحية ADMIN_MANAGE_SETTINGS
    if not db_setting.is_editable_by_admin:
        raise ForbiddenException(detail=f"الإعداد '{db_setting.setting_key}' غير قابل للتعديل بواسطة المسؤولين.")

    # 2. التحقق من تفرد المفتاح إذا تم تحديث setting_key
    if setting_in.setting_key and setting_in.setting_key != db_setting.setting_key:
        existing_setting_by_key = crud.get_application_setting_by_key(db, key=setting_in.setting_key)
        if existing_setting_by_key and existing_setting_by_key.setting_id != setting_id:
            raise ConflictException(detail=f"الإعداد بمفتاح '{setting_in.setting_key}' موجود بالفعل.")

    # 3. TODO: التحقق من صحة 'setting_value' بناءً على 'setting_datatype'
    #    مثال: إذا كان datatype هو 'INTEGER'، تأكد أن setting_value يمكن تحويله لعدد صحيح.
    #    يمكن استخدام دالة مساعدة هنا (parse_setting_value).

    return crud.update_application_setting(db, db_setting=db_setting, setting_in=setting_in, updated_by_user_id=current_user.user_id)

def delete_application_setting_service(db: Session, setting_id: int, current_user: User):
    """
    خدمة لحذف إعداد تطبيق (حذف صارم).
    تتضمن التحقق من صلاحيات المستخدم وعدم وجود أي استخدامات حيوية للإعداد.

    Args:
        db (Session): جلسة قاعدة البيانات.
        setting_id (int): معرف الإعداد المراد حذفه.
        current_user (User): المستخدم الذي يقوم بالحذف (يجب أن يكون مسؤولاً).

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإعداد.
        ForbiddenException: إذا كان الإعداد غير قابل للحذف أو المستخدم غير مصرح له.
        ConflictException: إذا كان الإعداد يستخدم حالياً.
    """
    db_setting = get_application_setting_details(db, setting_id) # استخدام دالة الخدمة للتحقق

    # TODO: التحقق من صلاحية المستخدم (ADMIN_MANAGE_SETTINGS)
    # TODO: التحقق من أن الإعداد ليس حيوياً للنظام ولا يمكن حذفه (مثلاً مفتاح عمولة أساسي).
    # TODO: التحقق من عدم وجود أي استخدام حيوي للإعداد في الكود أو جداول أخرى.

    crud.delete_application_setting(db=db, db_setting=db_setting)
    return {"message": f"تم حذف إعداد التطبيق '{db_setting.setting_key}' بنجاح."}


# ==========================================================
# --- Services for ApplicationSettingTranslation ---
# ==========================================================

def create_application_setting_translation(db: Session, setting_id: int, trans_in: schemas.ApplicationSettingTranslationCreate, current_user: User) -> models.ApplicationSettingTranslation:
    """خدمة لإنشاء ترجمة جديدة لإعداد تطبيق."""
    # 1. التحقق من وجود الإعداد الأم
    get_application_setting_details(db, setting_id)

    # 2. التحقق من وجود اللغة
    languages_crud.get_language(db, language_code=trans_in.language_code)

    # 3. التحقق من عدم وجود ترجمة بنفس اللغة
    existing_translation = crud.get_application_setting_translation(db, setting_id=setting_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"الترجمة للإعداد بمعرف {setting_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")
    
    # TODO: التحقق من صلاحية المستخدم للتعديل (ADMIN_MANAGE_SETTINGS)

    return crud.create_application_setting_translation(db=db, setting_id=setting_id, trans_in=trans_in)

def get_application_setting_translation_details(db: Session, setting_id: int, language_code: str) -> models.ApplicationSettingTranslation:
    """خدمة لجلب ترجمة إعداد تطبيق محددة."""
    translation = crud.get_application_setting_translation(db, setting_id=setting_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للإعداد بمعرف {setting_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_application_setting_translation(db: Session, setting_id: int, language_code: str, trans_in: schemas.ApplicationSettingTranslationUpdate, current_user: User) -> models.ApplicationSettingTranslation:
    """خدمة لتحديث ترجمة إعداد تطبيق موجودة."""
    db_translation = get_application_setting_translation_details(db, setting_id, language_code) # التحقق من وجود الترجمة

    # TODO: التحقق من صلاحية المستخدم للتعديل (ADMIN_MANAGE_SETTINGS)

    return crud.update_application_setting_translation(db, db_translation=db_translation, trans_in=trans_in)

def remove_application_setting_translation(db: Session, setting_id: int, language_code: str, current_user: User):
    """خدمة لحذف ترجمة إعداد تطبيق معينة."""
    db_translation = get_application_setting_translation_details(db, setting_id, language_code) # التحقق من وجود الترجمة

    # TODO: التحقق من صلاحية المستخدم للحذف (ADMIN_MANAGE_SETTINGS)

    crud.delete_application_setting_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة إعداد التطبيق بنجاح."}