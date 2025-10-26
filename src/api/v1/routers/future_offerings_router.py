# backend\src\api\v1\routers\future_offerings_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين والمنتجات من نوع UUID
from datetime import date # لاستخدام تواريخ في Schemas

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User # مودل المستخدم، للتحقق من الصلاحيات

# استيراد Schemas (هياكل البيانات) الخاصة بالمحاصيل المتوقعة
from src.products.schemas import future_offerings_schemas as schemas

# استيراد الخدمات (منطق العمل) المتعلقة بالمحاصيل المتوقعة
from src.products.services import future_offerings_service

# تعريف الراوتر الرئيسي لوحدة المحاصيل المتوقعة.
# هذا الراوتر سيتعامل مع نقاط الوصول الخاصة بالمنتجين (المزارعين والأسر المنتجة).
router = APIRouter(
    prefix="/expected-crops", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/expected-crops)
    tags=["Farmer - Expected Crops Management"] # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
)

# ================================================================
# --- نقاط الوصول للمحاصيل المتوقعة (ExpectedCrop) ---
#    (تتطلب صلاحية CROP_MANAGE_OWN)
# ================================================================

@router.post(
    "/",
    response_model=schemas.ExpectedCropRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Farmer] إنشاء عرض محصول متوقع جديد",
    description="""
    يسمح للمنتج (المزارع/الأسرة المنتجة) بإنشاء عرض جديد لمحصول يتوقع حصاده في المستقبل.
    تُعيّن الحالة الأولية للعرض تلقائيًا (عادةً 'متاح للحجز').
    يتطلب هذا الإجراء صلاحية 'CROP_MANAGE_OWN'.
    """
)
async def create_new_expected_crop_endpoint(
    crop_in: schemas.ExpectedCropCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("CROP_MANAGE_OWN"))
):
    """نقطة وصول لإنشاء محصول متوقع جديد."""
    return future_offerings_service.create_new_expected_crop(db=db, crop_in=crop_in, current_user=current_user)

@router.get(
    "/me",
    response_model=List[schemas.ExpectedCropRead],
    summary="[Farmer] جلب عروض المحاصيل المتوقعة الخاصة بي",
    description="""
    يجلب قائمة بجميع عروض المحاصيل المتوقعة التي قام المنتج (المزارع/الأسرة المنتجة) الحالي بإنشائها.
    """,
)
async def get_my_expected_crops_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("CROP_MANAGE_OWN")),
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب المحاصيل المتوقعة الخاصة بالمنتج الحالي."""
    return future_offerings_service.get_my_expected_crops(db=db, current_user=current_user, skip=skip, limit=limit)

@router.get(
    "/{expected_crop_id}",
    response_model=schemas.ExpectedCropRead,
    summary="[Farmer/Public] جلب تفاصيل عرض محصول متوقع واحد",
    description="""
    يجلب تفاصيل عرض محصول متوقع محدد بالـ ID الخاص به.
    إذا كان المستخدم هو مالك العرض، يمكنه رؤية جميع التفاصيل.
    إذا كان المستخدم عامًا (غير مصادق عليه أو مشترٍ)، يمكنه رؤية العروض النشطة المتاحة فقط.
    """,
)
async def get_expected_crop_details_endpoint(
    expected_crop_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(dependencies.get_current_user_or_none) # يمكن للمستخدمين غير المصادقين رؤية العروض العامة
):
    """نقطة وصول لجلب تفاصيل عرض محصول متوقع."""
    # خدمة الجلب يجب أن تحتوي على منطق التحقق من الصلاحيات (المالك يرى كل شيء، الآخرون يرون النشط فقط)
    return future_offerings_service.get_expected_crop_details(db=db, expected_crop_id=expected_crop_id)


@router.patch(
    "/{expected_crop_id}",
    response_model=schemas.ExpectedCropRead,
    summary="[Farmer] تحديث عرض محصول متوقع",
    description="""
    يسمح للمنتج بتحديث تفاصيل عرض محصول متوقع يملكه.
    يمكن تحديث حقول مثل الكمية المتوقعة، التواريخ، السعر، والملاحظات.
    يمكن أيضًا تغيير حالة العرض (للحذف الناعم مثلاً).
    يتطلب صلاحية 'CROP_MANAGE_OWN' والملكية.
    """,
)
async def update_expected_crop_endpoint(
    expected_crop_id: int,
    crop_in: schemas.ExpectedCropUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("CROP_MANAGE_OWN"))
):
    """نقطة وصول لتحديث عرض محصول متوقع."""
    return future_offerings_service.update_expected_crop(db=db, expected_crop_id=expected_crop_id, crop_in=crop_in, current_user=current_user)

@router.delete(
    "/{expected_crop_id}",
    response_model=schemas.ExpectedCropRead, # ترجع الكائن الذي تم إلغاؤه
    summary="[Farmer] إلغاء عرض محصول متوقع (حذف ناعم)",
    description="""
    يسمح للمنتج بإلغاء عرض محصول متوقع (يعادل الحذف الناعم) عن طريق تغيير حالته إلى 'ملغى'.
    لا يتم حذف السجل فعليًا من قاعدة البيانات.
    يتطلب صلاحية 'CROP_MANAGE_OWN' والملكية.
    """,
)
async def cancel_expected_crop_endpoint(
    expected_crop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("CROP_MANAGE_OWN"))
):
    """نقطة وصول لإلغاء (حذف ناعم) عرض محصول متوقع."""
    return future_offerings_service.cancel_expected_crop(db=db, expected_crop_id=expected_crop_id, current_user=current_user)

# ================================================================
# --- نقاط الوصول لترجمات المحاصيل المتوقعة (ExpectedCropTranslation) ---
#    (تتطلب صلاحية CROP_MANAGE_OWN)
# ================================================================

@router.post(
    "/{expected_crop_id}/translations",
    response_model=schemas.ExpectedCropTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Farmer] إنشاء ترجمة جديدة لعرض محصول متوقع أو تحديثها",
    description="""
    يسمح للمنتج بإنشاء ترجمة جديدة (أو تحديث ترجمة موجودة بنفس اللغة) لاسم المحصول المخصص وملاحظات الزراعة.
    يتطلب صلاحية 'CROP_MANAGE_OWN' والملكية.
    """
)
async def create_expected_crop_translation_endpoint(
    expected_crop_id: int,
    trans_in: schemas.ExpectedCropTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("CROP_MANAGE_OWN"))
):
    """نقطة وصول لإنشاء ترجمة جديدة لعرض محصول متوقع."""
    return future_offerings_service.create_expected_crop_translation(db=db, expected_crop_id=expected_crop_id, trans_in=trans_in, current_user=current_user)

@router.get(
    "/{expected_crop_id}/translations/{language_code}",
    response_model=schemas.ExpectedCropTranslationRead,
    summary="[Farmer/Public] جلب ترجمة محددة لعرض محصول متوقع",
    description="""
    يجلب ترجمة محددة لعرض محصول متوقع بلغة معينة.
    يمكن لأي مستخدم (بما في ذلك العامة) جلب الترجمات.
    """,
)
async def get_expected_crop_translation_details_endpoint(
    expected_crop_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة محددة لعرض محصول متوقع."""
    return future_offerings_service.get_expected_crop_translation_details(db=db, expected_crop_id=expected_crop_id, language_code=language_code)

@router.patch(
    "/{expected_crop_id}/translations/{language_code}",
    response_model=schemas.ExpectedCropTranslationRead,
    summary="[Farmer] تحديث ترجمة عرض محصول متوقع",
    description="""
    يسمح للمنتج بتحديث ترجمة موجودة لاسم المحصول المخصص أو ملاحظات الزراعة.
    يتطلب صلاحية 'CROP_MANAGE_OWN' والملكية.
    """
)
async def update_expected_crop_translation_endpoint(
    expected_crop_id: int,
    language_code: str,
    trans_in: schemas.ExpectedCropTranslationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("CROP_MANAGE_OWN"))
):
    """نقطة وصول لتحديث ترجمة عرض محصول متوقع."""
    return future_offerings_service.update_expected_crop_translation(db=db, expected_crop_id=expected_crop_id, language_code=language_code, trans_in=trans_in, current_user=current_user)

@router.delete(
    "/{expected_crop_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Farmer] حذف ترجمة عرض محصول متوقع",
    description="""
    يسمح للمنتج بحذف ترجمة معينة لعرض محصول متوقع (حذف صارم).
    يتطلب صلاحية 'CROP_MANAGE_OWN' والملكية.
    """,
)
async def delete_expected_crop_translation_endpoint(
    expected_crop_id: int,
    language_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("CROP_MANAGE_OWN"))
):
    """نقطة وصول لحذف ترجمة عرض محصول متوقع."""
    future_offerings_service.delete_expected_crop_translation(db=db, expected_crop_id=expected_crop_id, language_code=language_code, current_user=current_user)
    return