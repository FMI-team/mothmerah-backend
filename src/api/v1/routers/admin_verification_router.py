# backend\src\api\v1\routers\admin_verification_router.py

from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional, Dict # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين
from datetime import date # لتاريخ الإصدار/الانتهاء

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User as UserModel # مودل المستخدم، لضمان User type hint

# استيراد Schemas (هياكل البيانات)
from src.users.schemas import license_schemas # LicenseRead, LicenseUpdate, LicenseCreate
from src.users.schemas import verification_lookups_schemas as schemas # LicenseType, IssuingAuthority, UserVerificationStatus, LicenseVerificationStatus
# استيراد الخدمات (منطق العمل)
from src.users.services import verification_service # لجميع خدمات التحقق والتراخيص

# تعريف الراوتر لإدارة التراخيص والتحقق من جانب المسؤولين.
router = APIRouter(
    prefix="/admin/verification", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر
    tags=["Admin - Verification & Licenses"], # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
    dependencies=[Depends(dependencies.has_permission("ADMIN_MANAGE_LICENSES"))] # صلاحية عامة لإدارة التراخيص والتحقق
)

# ================================================================
# --- نقاط الوصول لأنواع التراخيص (License Types) ---
# ================================================================

@router.post(
    "/license-types",
    response_model=schemas.LicenseTypeRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء نوع ترخيص جديد"
)
async def create_license_type_endpoint(
    type_in: schemas.LicenseTypeCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء نوع مرجعي جديد للترخيص (مثلاً: 'سجل تجاري', 'رخصة عمل حر').
    """
    return verification_service.create_new_license_type(db=db, type_in=type_in)

@router.get(
    "/license-types",
    response_model=List[schemas.LicenseTypeRead],
    summary="[Admin] جلب جميع أنواع التراخيص"
)
async def get_all_license_types_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع أنواع التراخيص المرجعية في النظام."""
    return verification_service.get_all_license_types_service(db=db)

@router.get(
    "/license-types/{type_id}",
    response_model=schemas.LicenseTypeRead,
    summary="[Admin] جلب تفاصيل نوع ترخيص واحد"
)
async def get_license_type_details_endpoint(type_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل نوع مرجعي لترخيص بالـ ID الخاص بها."""
    return verification_service.get_license_type_by_id_service(db=db, type_id=type_id)

@router.patch(
    "/license-types/{type_id}",
    response_model=schemas.LicenseTypeRead,
    summary="[Admin] تحديث نوع ترخيص",
)
async def update_license_type_endpoint(
    type_id: int,
    type_in: schemas.LicenseTypeUpdate,
    db: Session = Depends(get_db)
):
    """تحديث نوع مرجعي لترخيص."""
    return verification_service.update_existing_license_type(db=db, type_id=type_id, type_in=type_in)

@router.delete(
    "/license-types/{type_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف نوع ترخيص",
    description="""
    حذف نوع مرجعي لترخيص (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بتراخيص موجودة.
    """,
)
async def delete_license_type_endpoint(type_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف نوع ترخيص."""
    return verification_service.delete_license_type_by_id(db=db, type_id=type_id)

# --- ترجمات أنواع التراخيص ---
@router.post(
    "/license-types/{type_id}/translations",
    response_model=schemas.LicenseTypeRead, # ترجع النوع كاملاً مع ترجماته المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لنوع ترخيص",
    description="""
    إنشاء ترجمة جديدة لنوع مرجعي لترخيص بلغة معينة أو تحديث ترجمة موجودة.
    """,
)
async def create_license_type_translation_endpoint(
    type_id: int,
    trans_in: schemas.LicenseTypeTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لنوع ترخيص."""
    return verification_service.create_license_type_translation(db=db, type_id=type_id, trans_in=trans_in)

@router.get(
    "/license-types/{type_id}/translations/{language_code}",
    response_model=schemas.LicenseTypeTranslationRead,
    summary="[Admin] جلب ترجمة محددة لنوع ترخيص",
    description="""
    جلب ترجمة نوع مرجعية لترخيص بلغة محددة.
    """,
)
async def get_license_type_translation_details_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة نوع ترخيص محددة."""
    return verification_service.get_license_type_translation_details(db=db, type_id=type_id, language_code=language_code)

@router.patch(
    "/license-types/{type_id}/translations/{language_code}",
    response_model=schemas.LicenseTypeRead, # ترجع النوع كاملاً مع ترجماته المحدثة
    summary="[Admin] تحديث ترجمة نوع ترخيص",
    description="""
    تحديث ترجمة نوع مرجعية لترخيص بلغة محددة.
    """,
)
async def update_license_type_translation_endpoint(
    type_id: int,
    language_code: str,
    trans_in: schemas.LicenseTypeTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة نوع ترخيص."""
    return verification_service.update_license_type_translation(db=db, type_id=type_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/license-types/{type_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة نوع ترخيص",
    description="""
    حذف ترجمة نوع مرجعية لترخيص بلغة محددة (حذف صارم).
    """,
)
async def remove_license_type_translation_endpoint(
    type_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة نوع ترخيص."""
    verification_service.remove_license_type_translation(db=db, type_id=type_id, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول للجهات المصدرة للتراخيص (Issuing Authorities) ---
# ================================================================

@router.post(
    "/issuing-authorities",
    response_model=schemas.IssuingAuthorityRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء جهة إصدار جديدة"
)
async def create_issuing_authority_endpoint(
    authority_in: schemas.IssuingAuthorityCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء جهة مصدرة مرجعية جديدة للتراخيص.
    """
    return verification_service.create_new_issuing_authority(db=db, authority_in=authority_in)

@router.get(
    "/issuing-authorities",
    response_model=List[schemas.IssuingAuthorityRead],
    summary="[Admin] جلب جميع جهات الإصدار"
)
async def get_all_issuing_authorities_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع الجهات المصدرة للتراخيص المرجعية في النظام."""
    return verification_service.get_all_issuing_authorities_service(db=db)

@router.get(
    "/issuing-authorities/{authority_id}",
    response_model=schemas.IssuingAuthorityRead,
    summary="[Admin] جلب تفاصيل جهة إصدار واحدة"
)
async def get_issuing_authority_details_endpoint(authority_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل جهة مصدرة مرجعية للتراخيص بالـ ID الخاص بها."""
    return verification_service.get_issuing_authority_details(db=db, authority_id=authority_id)

@router.patch(
    "/issuing-authorities/{authority_id}",
    response_model=schemas.IssuingAuthorityRead,
    summary="[Admin] تحديث جهة إصدار",
)
async def update_issuing_authority_endpoint(
    authority_id: int,
    authority_in: schemas.IssuingAuthorityUpdate,
    db: Session = Depends(get_db)
):
    """تحديث جهة مصدرة مرجعية للتراخيص."""
    return verification_service.update_issuing_authority(db=db, authority_id=authority_id, authority_in=authority_in)

@router.delete(
    "/issuing-authorities/{authority_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف جهة إصدار",
    description="""
    حذف جهة إصدار مرجعية للتراخيص (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بتراخيص موجودة.
    """,
)
async def delete_issuing_authority_endpoint(authority_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف جهة إصدار."""
    return verification_service.delete_issuing_authority_by_id(db=db, authority_id=authority_id)

# --- ترجمات الجهات المصدرة للتراخيص ---
@router.post(
    "/issuing-authorities/{authority_id}/translations",
    response_model=schemas.IssuingAuthorityRead, # ترجع الجهة كاملاً مع ترجماتها المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لجهة إصدار",
    description="""
    إنشاء ترجمة جديدة لجهة مصدرة للتراخيص بلغة معينة أو تحديث ترجمة موجودة.
    """,
)
async def create_issuing_authority_translation_endpoint(
    authority_id: int,
    trans_in: schemas.IssuingAuthorityTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لجهة إصدار."""
    return verification_service.create_issuing_authority_translation(db=db, authority_id=authority_id, trans_in=trans_in)

@router.get(
    "/issuing-authorities/{authority_id}/translations/{language_code}",
    response_model=schemas.IssuingAuthorityTranslationRead,
    summary="[Admin] جلب ترجمة محددة لجهة إصدار",
    description="""
    جلب ترجمة جهة مصدرة مرجعية للتراخيص بلغة محددة.
    """,
)
async def get_issuing_authority_translation_details_endpoint(
    authority_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة جهة إصدار محددة."""
    return verification_service.get_issuing_authority_translation_details(db=db, authority_id=authority_id, language_code=language_code)

@router.patch(
    "/issuing-authorities/{authority_id}/translations/{language_code}",
    response_model=schemas.IssuingAuthorityRead, # ترجع الجهة كاملاً مع ترجماتها المحدثة
    summary="[Admin] تحديث ترجمة جهة إصدار",
    description="""
    تحديث ترجمة جهة مصدرة مرجعية للتراخيص بلغة محددة.
    """,
)
async def update_issuing_authority_translation_endpoint(
    authority_id: int,
    language_code: str,
    trans_in: schemas.IssuingAuthorityTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة جهة إصدار."""
    return verification_service.update_issuing_authority_translation(db=db, authority_id=authority_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/issuing-authorities/{authority_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة جهة إصدار",
    description="""
    حذف ترجمة جهة مصدرة مرجعية للتراخيص بلغة محددة (حذف صارم).
    """,
)
async def remove_issuing_authority_translation_endpoint(
    authority_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة جهة إصدار."""
    verification_service.remove_issuing_authority_translation(db=db, authority_id=authority_id, language_code=language_code)
    return


# ================================================================
# --- نقاط الوصول لحالات التحقق من المستخدم (User Verification Statuses) ---
# ================================================================

@router.post(
    "/user-verification-statuses",
    response_model=schemas.UserVerificationStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة تحقق مستخدم جديدة"
)
async def create_user_verification_status_endpoint(
    status_in: schemas.UserVerificationStatusCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مرجعية جديدة للتحقق من المستخدم.
    """
    return verification_service.create_new_user_verification_status(db=db, status_in=status_in)

@router.get(
    "/user-verification-statuses",
    response_model=List[schemas.UserVerificationStatusRead],
    summary="[Admin] جلب جميع حالات التحقق من المستخدم"
)
async def get_all_user_verification_statuses_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع حالات التحقق من المستخدم المرجعية في النظام."""
    return verification_service.get_all_user_verification_statuses_service(db=db)

@router.get(
    "/user-verification-statuses/{user_verification_status_id}",
    response_model=schemas.UserVerificationStatusRead,
    summary="[Admin] جلب تفاصيل حالة تحقق مستخدم واحدة"
)
async def get_user_verification_status_details_endpoint(user_verification_status_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل حالة مرجعية للتحقق من المستخدم بالـ ID الخاص بها."""
    return verification_service.get_user_verification_status_details_service(db=db, user_verification_status_id=user_verification_status_id)

@router.patch(
    "/user-verification-statuses/{user_verification_status_id}",
    response_model=schemas.UserVerificationStatusRead,
    summary="[Admin] تحديث حالة تحقق مستخدم",
)
async def update_user_verification_status_endpoint(
    user_verification_status_id: int,
    status_in: schemas.UserVerificationStatusUpdate,
    db: Session = Depends(get_db)
):
    """تحديث حالة مرجعية للتحقق من المستخدم."""
    return verification_service.update_user_verification_status(db=db, user_verification_status_id=user_verification_status_id, status_in=status_in)

@router.delete(
    "/user-verification-statuses/{user_verification_status_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف حالة تحقق مستخدم",
    description="""
    حذف حالة مرجعية للتحقق من المستخدم (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بمستخدمين حاليًا.
    """,
)
async def delete_user_verification_status_endpoint(user_verification_status_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف حالة تحقق مستخدم."""
    return verification_service.delete_user_verification_status(db=db, user_verification_status_id=user_verification_status_id)

# --- ترجمات حالات التحقق من المستخدم ---
@router.post(
    "/user-verification-statuses/{user_verification_status_id}/translations",
    response_model=schemas.UserVerificationStatusRead, # ترجع الحالة كاملاً مع ترجماتها المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لحالة تحقق مستخدم",
    description="""
    إنشاء ترجمة جديدة لحالة مرجعية للتحقق من المستخدم بلغة معينة أو تحديث ترجمة موجودة.
    """,
)
async def create_user_verification_status_translation_endpoint(
    user_verification_status_id: int,
    trans_in: schemas.UserVerificationStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لحالة تحقق مستخدم."""
    return verification_service.create_user_verification_status_translation(db=db, user_verification_status_id=user_verification_status_id, trans_in=trans_in)

@router.get(
    "/user-verification-statuses/{user_verification_status_id}/translations/{language_code}",
    response_model=schemas.UserVerificationStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة تحقق مستخدم",
    description="""
    جلب ترجمة حالة مرجعية للتحقق من المستخدم بلغة محددة.
    """,
)
async def get_user_verification_status_translation_details_endpoint(
    user_verification_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة حالة تحقق مستخدم محددة."""
    return verification_service.get_user_verification_status_translation_details(db=db, user_verification_status_id=user_verification_status_id, language_code=language_code)

@router.patch(
    "/user-verification-statuses/{user_verification_status_id}/translations/{language_code}",
    response_model=schemas.UserVerificationStatusRead, # ترجع الحالة كاملاً مع ترجماتها المحدثة
    summary="[Admin] تحديث ترجمة لحالة تحقق مستخدم",
    description="""
    تحديث ترجمة حالة مرجعية للتحقق من المستخدم بلغة محددة.
    """,
)
async def update_user_verification_status_translation_endpoint(
    user_verification_status_id: int,
    language_code: str,
    trans_in: schemas.UserVerificationStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة لحالة تحقق مستخدم."""
    return verification_service.update_user_verification_status_translation(db=db, user_verification_status_id=user_verification_status_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/user-verification-statuses/{user_verification_status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة لحالة تحقق مستخدم",
    description="""
    حذف ترجمة حالة مرجعية للتحقق من المستخدم بلغة محددة (حذف صارم).
    """,
)
async def remove_user_verification_status_translation_endpoint(
    user_verification_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة لحالة تحقق مستخدم."""
    verification_service.remove_user_verification_status_translation(db=db, user_verification_status_id=user_verification_status_id, language_code=language_code)
    return

# ================================================================
# --- نقاط الوصول لحالات التحقق من التراخيص (License Verification Statuses) ---
# ================================================================

@router.post(
    "/license-verification-statuses",
    response_model=schemas.LicenseVerificationStatusRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء حالة تحقق ترخيص جديدة"
)
async def create_license_verification_status_endpoint(
    status_in: schemas.LicenseVerificationStatusCreate,
    db: Session = Depends(get_db)
):
    """
    إنشاء حالة مرجعية جديدة للتحقق من التراخيص.
    """
    return verification_service.create_new_license_verification_status(db=db, status_in=status_in)

@router.get(
    "/license-verification-statuses",
    response_model=List[schemas.LicenseVerificationStatusRead],
    summary="[Admin] جلب جميع حالات التحقق من التراخيص"
)
async def get_all_license_verification_statuses_endpoint(db: Session = Depends(get_db)):
    """جلب قائمة بجميع حالات التحقق من التراخيص المرجعية في النظام."""
    return verification_service.get_all_license_verification_statuses_service(db=db)

@router.get(
    "/license-verification-statuses/{license_verification_status_id}",
    response_model=schemas.LicenseVerificationStatusRead,
    summary="[Admin] جلب تفاصيل حالة تحقق ترخيص واحدة"
)
async def get_license_verification_status_details_endpoint(license_verification_status_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل حالة مرجعية للتحقق من الترخيص بالـ ID الخاص بها."""
    return verification_service.get_license_verification_status_details_service(db=db, license_verification_status_id=license_verification_status_id)

@router.patch(
    "/license-verification-statuses/{license_verification_status_id}",
    response_model=schemas.LicenseVerificationStatusRead,
    summary="[Admin] تحديث حالة تحقق ترخيص",
)
async def update_license_verification_status_endpoint(
    license_verification_status_id: int,
    status_in: schemas.LicenseVerificationStatusUpdate,
    db: Session = Depends(get_db)
):
    """تحديث حالة مرجعية للتحقق من الترخيص."""
    return verification_service.update_license_verification_status(db=db, license_verification_status_id=license_verification_status_id, status_in=status_in)

@router.delete(
    "/license-verification-statuses/{license_verification_status_id}",
    status_code=status.HTTP_200_OK, # قد ترجع رسالة بدلاً من 204
    response_model=Dict[str,str], # إذا كانت الخدمة ترجع رسالة
    summary="[Admin] حذف حالة تحقق ترخيص",
    description="""
    حذف حالة مرجعية للتحقق من الترخيص (حذف صارم).
    لا يمكن حذفها إذا كانت مرتبطة بتراخيص حاليًا.
    """,
)
async def delete_license_verification_status_endpoint(license_verification_status_id: int, db: Session = Depends(get_db)):
    """نقطة وصول لحذف حالة تحقق ترخيص."""
    return verification_service.delete_license_verification_status_by_id(db=db, license_verification_status_id=license_verification_status_id)

# --- ترجمات حالات التحقق من التراخيص ---
@router.post(
    "/license-verification-statuses/{license_verification_status_id}/translations",
    response_model=schemas.LicenseVerificationStatusRead, # ترجع الحالة كاملاً مع ترجماتها المحدثة
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] إنشاء/تحديث ترجمة لحالة تحقق ترخيص",
    description="""
    إنشاء ترجمة جديدة لحالة مرجعية للتحقق من التراخيص بلغة معينة أو تحديث ترجمة موجودة.
    """,
)
async def create_license_verification_status_translation_endpoint(
    license_verification_status_id: int,
    trans_in: schemas.LicenseVerificationStatusTranslationCreate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لإنشاء/تحديث ترجمة لحالة تحقق ترخيص."""
    return verification_service.create_license_verification_status_translation(db=db, license_verification_status_id=license_verification_status_id, trans_in=trans_in)

@router.get(
    "/license-verification-statuses/{license_verification_status_id}/translations/{language_code}",
    response_model=schemas.LicenseVerificationStatusTranslationRead,
    summary="[Admin] جلب ترجمة محددة لحالة تحقق ترخيص",
    description="""
    جلب ترجمة حالة مرجعية للتحقق من التراخيص بلغة محددة.
    """,
)
async def get_license_verification_status_translation_details_endpoint(
    license_verification_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة حالة تحقق ترخيص محددة."""
    return verification_service.get_license_verification_status_translation_details(db=db, license_verification_status_id=license_verification_status_id, language_code=language_code)

@router.patch(
    "/license-verification-statuses/{license_verification_status_id}/translations/{language_code}",
    response_model=schemas.LicenseVerificationStatusRead, # ترجع الحالة كاملاً مع ترجماتها المحدثة
    summary="[Admin] تحديث ترجمة لحالة تحقق ترخيص",
    description="""
    تحديث ترجمة حالة مرجعية للتحقق من التراخيص بلغة محددة.
    """,
)
async def update_license_verification_status_translation_endpoint(
    license_verification_status_id: int,
    language_code: str,
    trans_in: schemas.LicenseVerificationStatusTranslationUpdate,
    db: Session = Depends(get_db)
):
    """نقطة وصول لتحديث ترجمة لحالة تحقق ترخيص."""
    return verification_service.update_license_verification_status_translation(db=db, license_verification_status_id=license_verification_status_id, language_code=language_code, trans_in=trans_in)

@router.delete(
    "/license-verification-statuses/{license_verification_status_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] حذف ترجمة لحالة تحقق ترخيص",
    description="""
    حذف ترجمة حالة مرجعية للتحقق من التراخيص بلغة محددة (حذف صارم).
    """,
)
async def remove_license_verification_status_translation_endpoint(
    license_verification_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لحذف ترجمة لحالة تحقق ترخيص."""
    verification_service.remove_license_verification_status_translation(db=db, license_verification_status_id=license_verification_status_id, language_code=language_code)
    return
    