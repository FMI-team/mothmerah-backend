# backend\src\api\v1\routers\admin_configuration_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional, Dict # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين
from datetime import datetime, date # لتواريخ الصيانة

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User as UserModel # مودل المستخدم، لضمان User type hint

# استيراد Schemas (هياكل البيانات)
from src.configuration.schemas import settings_schemas as schemas # لجميع Schemas System Settings

# استيراد الخدمات (منطق العمل)
from src.configuration.services import ( # لجميع خدمات System Settings
    application_settings_service,
    feature_flags_service,
    system_maintenance_schedule_service
)


# تعريف الراوتر لإدارة إعدادات وتكوينات النظام من جانب المسؤولين.
router = APIRouter(
    prefix="/configuration", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /admin/configuration)
    tags=["Admin - System Settings & Configuration"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_SETTINGS"))] # صلاحية عامة لإدارة الإعدادات
)


# ================================================================
# --- نقاط الوصول لإعدادات التطبيق العامة (Application Settings) ---
# ================================================================

@router.post(
    "/application-settings",
    response_model=schemas.ApplicationSettingRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء إعداد تطبيق جديد"
)
async def create_application_setting_endpoint(
    setting_in: schemas.ApplicationSettingCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """
    إنشاء إعداد تطبيق عام جديد يمكن التحكم فيه من لوحة الإدارة.
    """
    return application_settings_service.create_new_application_setting(db=db, setting_in=setting_in, current_user=current_user)

@router.get(
    "/application-settings",
    response_model=List[schemas.ApplicationSettingRead],
    summary="[Admin] جلب جميع إعدادات التطبيق"
)
async def get_all_application_settings_endpoint(
    db: Session = Depends(get_db),
    module_scope: Optional[str] = None,
    is_editable_by_admin: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
):
    """جلب قائمة بجميع إعدادات التطبيق العامة في النظام."""
    return application_settings_service.get_all_application_settings_service(
        db=db,
        module_scope=module_scope,
        is_editable_by_admin=is_editable_by_admin,
        skip=skip,
        limit=limit
    )

@router.get(
    "/application-settings/{setting_id}",
    response_model=schemas.ApplicationSettingRead,
    summary="[Admin] جلب تفاصيل إعداد تطبيق واحد",
)
async def get_application_setting_details_endpoint(setting_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل إعداد تطبيق واحد بالـ ID الخاص به."""
    return application_settings_service.get_application_setting_details(db=db, setting_id=setting_id)

@router.patch(
    "/application-settings/{setting_id}",
    response_model=schemas.ApplicationSettingRead,
    summary="[Admin] تحديث إعداد تطبيق",
)
async def update_application_setting_endpoint(
    setting_id: int,
    setting_in: schemas.ApplicationSettingUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """تحديث إعداد تطبيق موجود."""
    return application_settings_service.update_application_setting_service(db=db, setting_id=setting_id, setting_in=setting_in, current_user=current_user)

@router.delete(
    "/application-settings/{setting_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف إعداد تطبيق",
    description="""
    حذف إعداد تطبيق عام (حذف صارم).
    """,
)
async def delete_application_setting_endpoint(
    setting_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف إعداد تطبيق."""
    return application_settings_service.delete_application_setting_service(db=db, setting_id=setting_id, current_user=current_user)

# --- ترجمات إعدادات التطبيق ---
@router.post(
    "/application-settings/{setting_id}/translations",
    response_model=schemas.ApplicationSettingTranslationRead, # ترجع الترجمة المنشأة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء ترجمة جديدة لإعداد تطبيق",
)
async def create_application_setting_translation_endpoint(
    setting_id: int,
    trans_in: schemas.ApplicationSettingTranslationCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """إنشاء ترجمة جديدة لإعداد تطبيق بلغة معينة."""
    return application_settings_service.create_application_setting_translation(db=db, setting_id=setting_id, trans_in=trans_in, current_user=current_user)

@router.get(
    "/application-settings/{setting_id}/translations/{language_code}",
    response_model=schemas.ApplicationSettingTranslationRead,
    summary="[Admin] جلب ترجمة محددة لإعداد تطبيق",
)
async def get_application_setting_translation_details_endpoint(
    setting_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة إعداد تطبيق بلغة محددة."""
    return application_settings_service.get_application_setting_translation_details(db=db, setting_id=setting_id, language_code=language_code)

@router.patch(
    "/application-settings/{setting_id}/translations/{language_code}",
    response_model=schemas.ApplicationSettingTranslationRead,
    summary="[Admin] تحديث ترجمة إعداد تطبيق",
)
async def update_application_setting_translation_endpoint(
    setting_id: int,
    language_code: str,
    trans_in: schemas.ApplicationSettingTranslationUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """تحديث ترجمة إعداد تطبيق بلغة محددة."""
    return application_settings_service.update_application_setting_translation(db=db, setting_id=setting_id, language_code=language_code, trans_in=trans_in, current_user=current_user)

@router.delete(
    "/application-settings/{setting_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة إعداد تطبيق",
)
async def remove_application_setting_translation_endpoint(
    setting_id: int,
    language_code: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """حذف ترجمة إعداد تطبيق بلغة محددة."""
    return application_settings_service.remove_application_setting_translation(db=db, setting_id=setting_id, language_code=language_code, current_user=current_user)


# ================================================================
# --- نقاط الوصول لأعلام تفعيل الميزات (Feature Flags) ---
# ================================================================

@router.post(
    "/feature-flags",
    response_model=schemas.FeatureFlagRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء علم ميزة جديد"
)
async def create_feature_flag_endpoint(
    flag_in: schemas.FeatureFlagCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """
    إنشاء علم ميزة جديد للتحكم في تفعيل/تعطيل وظائف معينة في النظام.
    """
    return feature_flags_service.create_new_feature_flag(db=db, flag_in=flag_in, current_user=current_user)

@router.get(
    "/feature-flags",
    response_model=List[schemas.FeatureFlagRead],
    summary="[Admin] جلب جميع أعلام الميزات"
)
async def get_all_feature_flags_endpoint(
    db: Session = Depends(get_db),
    is_enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
):
    """جلب قائمة بجميع أعلام الميزات المعرفة في النظام."""
    return feature_flags_service.get_all_feature_flags_service(
        db=db,
        is_enabled=is_enabled,
        skip=skip,
        limit=limit
    )

@router.get(
    "/feature-flags/{flag_id}",
    response_model=schemas.FeatureFlagRead,
    summary="[Admin] جلب تفاصيل علم ميزة واحد",
)
async def get_feature_flag_details_endpoint(flag_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل علم ميزة واحد بالـ ID الخاص به."""
    return feature_flags_service.get_feature_flag_details(db=db, flag_id=flag_id)

@router.patch(
    "/feature-flags/{flag_id}",
    response_model=schemas.FeatureFlagRead,
    summary="[Admin] تحديث علم ميزة",
)
async def update_feature_flag_endpoint(
    flag_id: int,
    flag_in: schemas.FeatureFlagUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """تحديث علم ميزة موجود."""
    return feature_flags_service.update_feature_flag_service(db=db, flag_id=flag_id, flag_in=flag_in, current_user=current_user)

@router.delete(
    "/feature-flags/{flag_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف علم ميزة",
    description="""
    حذف علم ميزة (حذف صارم).
    """,
)
async def delete_feature_flag_endpoint(
    flag_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف علم ميزة."""
    return feature_flags_service.delete_feature_flag_service(db=db, flag_id=flag_id, current_user=current_user)


# ================================================================
# --- نقاط الوصول لجدول صيانة النظام (System Maintenance Schedule) ---
# ================================================================

@router.post(
    "/maintenance-schedules",
    response_model=schemas.SystemMaintenanceScheduleRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء جدول صيانة جديد",
)
async def create_system_maintenance_schedule_endpoint(
    schedule_in: schemas.SystemMaintenanceScheduleCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """
    إنشاء جدول صيانة جديد لتحديد فترات صيانة النظام.
    """
    return system_maintenance_schedule_service.create_new_system_maintenance_schedule(db=db, schedule_in=schedule_in, current_user=current_user)

@router.get(
    "/maintenance-schedules",
    response_model=List[schemas.SystemMaintenanceScheduleRead],
    summary="[Admin] جلب جميع جداول الصيانة",
)
async def get_all_system_maintenance_schedules_endpoint(
    db: Session = Depends(get_db),
    is_active: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """جلب قائمة بجميع جداول الصيانة المعرفة في النظام."""
    return system_maintenance_schedule_service.get_all_system_maintenance_schedules_service(
        db=db,
        is_active=is_active,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )

@router.get(
    "/maintenance-schedules/{maintenance_id}",
    response_model=schemas.SystemMaintenanceScheduleRead,
    summary="[Admin] جلب تفاصيل جدول صيانة واحد",
)
async def get_system_maintenance_schedule_details_endpoint(maintenance_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل جدول صيانة واحد بالـ ID الخاص به."""
    return system_maintenance_schedule_service.get_system_maintenance_schedule_details(db=db, maintenance_id=maintenance_id)

@router.patch(
    "/maintenance-schedules/{maintenance_id}",
    response_model=schemas.SystemMaintenanceScheduleRead,
    summary="[Admin] تحديث جدول صيانة",
)
async def update_system_maintenance_schedule_endpoint(
    maintenance_id: int,
    schedule_in: schemas.SystemMaintenanceScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """تحديث جدول صيانة موجود."""
    return system_maintenance_schedule_service.update_system_maintenance_schedule_service(db=db, maintenance_id=maintenance_id, schedule_in=schedule_in, current_user=current_user)

@router.delete(
    "/maintenance-schedules/{maintenance_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف جدول صيانة",
    description="""
    حذف جدول صيانة (حذف صارم).
    """,
)
async def delete_system_maintenance_schedule_endpoint(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """نقطة وصول لحذف جدول صيانة."""
    return system_maintenance_schedule_service.delete_system_maintenance_schedule_service(db=db, maintenance_id=maintenance_id, current_user=current_user)