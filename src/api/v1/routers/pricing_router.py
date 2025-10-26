# backend\src\api\v1\routers\pricing_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User # مودل المستخدم، للتحقق من الصلاحيات

# استيراد Schemas (هياكل البيانات) الخاصة بالأسعار
from src.pricing.schemas import pricing_schemas as schemas

# استيراد الخدمات (منطق العمل) المتعلقة بالأسعار
from src.pricing.services import pricing_service

# تعريف الراوتر الرئيسي لوحدة إدارة الأسعار الديناميكية.
# هذا الراوتر سيتعامل مع نقاط الوصول الخاصة بالبائعين والمسؤولين لإدارة قواعد التسعير.
router = APIRouter(
    prefix="/pricing-rules", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/pricing-rules)
    tags=["Pricing - Dynamic Rules Management"] # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
)

# ================================================================
# --- نقاط الوصول لقواعد شرائح الأسعار (PriceTierRule) ---
#    (تتطلب صلاحية PRICING_RULE_MANAGE_OWN أو ADMIN_PRICING_RULE_MANAGE_ANY)
# ================================================================

@router.post(
    "/",
    response_model=schemas.PriceTierRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller/Admin] إنشاء قاعدة سعر متدرج جديدة",
    description="""
    يسمح للبائع أو المسؤول بإنشاء قاعدة جديدة للتسعير المتدرج (tiered pricing).
    تُستخدم هذه القواعد لتطبيق خصومات بناءً على الكمية على المنتجات.
    يتطلب صلاحية 'PRICING_RULE_MANAGE_OWN' للمالك أو 'ADMIN_PRICING_RULE_MANAGE_ANY' للمسؤول.
    """
)
async def create_price_tier_rule_endpoint(
    rule_in: schemas.PriceTierRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_CREATE_OWN")) # صلاحية لإنشاء قاعدة سعر
):
    """نقطة وصول لإنشاء قاعدة سعر متدرج جديدة."""
    return pricing_service.create_new_price_tier_rule(db=db, rule_in=rule_in, current_user=current_user)

@router.get(
    "/",
    response_model=List[schemas.PriceTierRuleRead],
    summary="[Seller/Admin] جلب جميع قواعد الأسعار المتدرجة",
    description="""
    يجلب قائمة بجميع قواعد الأسعار المتدرجة في النظام.
    للبائع: يجلب القواعد التي أنشأها فقط. للمسؤول: يجلب جميع القواعد.
    """,
)
async def get_all_price_tier_rules_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_VIEW_OWN")), # صلاحية رؤية قواعد السعر
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب قواعد الأسعار المتدرجة."""
    # خدمة get_all_price_tier_rules ستطبق منطق التصفية حسب المستخدم (مالك/مسؤول)
    return pricing_service.get_all_price_tier_rules(db=db, current_user=current_user, skip=skip, limit=limit)

@router.get(
    "/{rule_id}",
    response_model=schemas.PriceTierRuleRead,
    summary="[Seller/Admin] جلب تفاصيل قاعدة سعر متدرج واحدة",
    description="""
    يجلب تفاصيل قاعدة سعر متدرج محددة بالـ ID الخاص بها، بما في ذلك مستوياتها وترجماتها.
    يتطلب صلاحية 'PRICING_RULE_VIEW_OWN' ويتم التحقق من ملكية المستخدم أو صلاحياته الإدارية.
    """,
)
async def get_price_tier_rule_details_endpoint(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_VIEW_OWN"))
):
    """نقطة وصول لجلب تفاصيل قاعدة سعر متدرج."""
    return pricing_service.get_price_tier_rule_details(db=db, rule_id=rule_id, current_user=current_user)

@router.patch(
    "/{rule_id}",
    response_model=schemas.PriceTierRuleRead,
    summary="[Seller/Admin] تحديث قاعدة سعر متدرج",
    description="""
    يسمح للبائع أو المسؤول بتحديث تفاصيل قاعدة سعر متدرج يملكها (أو أي قاعدة للمسؤول).
    يتطلب صلاحية 'PRICING_RULE_UPDATE_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """,
)
async def update_price_tier_rule_endpoint(
    rule_id: int,
    rule_in: schemas.PriceTierRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_UPDATE_OWN")) # صلاحية لتحديث قاعدة سعر
):
    """نقطة وصول لتحديث قاعدة سعر متدرج."""
    return pricing_service.update_price_tier_rule(db=db, rule_id=rule_id, rule_in=rule_in, current_user=current_user)

@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Seller/Admin] حذف قاعدة سعر متدرج",
    description="""
    يسمح للبائع أو المسؤول بحذف قاعدة سعر متدرج (حذف صارم).
    لا يمكن حذف القاعدة إذا كانت مرتبطة بمستويات أو إسنادات نشطة.
    يتطلب صلاحية 'PRICING_RULE_DELETE_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """,
)
async def delete_price_tier_rule_endpoint(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_DELETE_OWN")) # صلاحية لحذف قاعدة سعر
):
    """نقطة وصول لحذف قاعدة سعر متدرج."""
    pricing_service.delete_price_tier_rule(db=db, rule_id=rule_id, current_user=current_user)
    return

# ================================================================
# --- نقاط الوصول لترجمات قواعد شرائح الأسعار (PriceTierRuleTranslation) ---
# ================================================================

@router.post(
    "/{rule_id}/translations",
    response_model=schemas.PriceTierRuleTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller/Admin] إنشاء/تحديث ترجمة لقاعدة سعر",
    description="""
    يسمح للبائع أو المسؤول بإنشاء ترجمة جديدة لقاعدة سعر متدرج (أو تحديث ترجمة موجودة بنفس اللغة).
    يتطلب صلاحية 'PRICING_RULE_UPDATE_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """
)
async def create_price_tier_rule_translation_endpoint(
    rule_id: int,
    trans_in: schemas.PriceTierRuleTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_UPDATE_OWN"))
):
    """نقطة وصول لإنشاء/تحديث ترجمة لقاعدة سعر متدرج."""
    return pricing_service.create_price_tier_rule_translation(db=db, rule_id=rule_id, trans_in=trans_in, current_user=current_user)

@router.get(
    "/{rule_id}/translations/{language_code}",
    response_model=schemas.PriceTierRuleTranslationRead,
    summary="[Seller/Admin/Public] جلب ترجمة محددة لقاعدة سعر",
    description="""
    يجلب ترجمة محددة لقاعدة سعر متدرج بلغة معينة.
    يمكن لأي مستخدم جلب الترجمات.
    """,
)
async def get_price_tier_rule_translation_details_endpoint(
    rule_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة محددة لقاعدة سعر متدرج."""
    return pricing_service.get_price_tier_rule_translation_details(db=db, rule_id=rule_id, language_code=language_code)

@router.patch(
    "/{rule_id}/translations/{language_code}",
    response_model=schemas.PriceTierRuleTranslationRead,
    summary="[Seller/Admin] تحديث ترجمة قاعدة سعر",
    description="""
    يسمح للبائع أو المسؤول بتحديث ترجمة موجودة لقاعدة سعر متدرج.
    يتطلب صلاحية 'PRICING_RULE_UPDATE_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """
)
async def update_price_tier_rule_translation_endpoint(
    rule_id: int,
    language_code: str,
    trans_in: schemas.PriceTierRuleTranslationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_UPDATE_OWN"))
):
    """نقطة وصول لتحديث ترجمة قاعدة سعر متدرج."""
    return pricing_service.update_price_tier_rule_translation(db=db, rule_id=rule_id, language_code=language_code, trans_in=trans_in, current_user=current_user)

@router.delete(
    "/{rule_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Seller/Admin] حذف ترجمة قاعدة سعر",
    description="""
    يسمح للبائع أو المسؤول بحذف ترجمة معينة لقاعدة سعر متدرج (حذف صارم).
    يتطلب صلاحية 'PRICING_RULE_UPDATE_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """,
)
async def delete_price_tier_rule_translation_endpoint(
    rule_id: int,
    language_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_UPDATE_OWN"))
):
    """نقطة وصول لحذف ترجمة قاعدة سعر متدرج."""
    pricing_service.delete_price_tier_rule_translation(db=db, rule_id=rule_id, language_code=language_code, current_user=current_user)
    return

# ================================================================
# --- نقاط الوصول لمستويات/درجات قاعدة شريحة السعر (PriceTierRuleLevel) ---
#    (تتطلب صلاحية PRICING_RULE_MANAGE_OWN أو ADMIN_PRICING_RULE_MANAGE_ANY)
#    هذه النقاط ستكون nested تحت /pricing-rules/{rule_id}/levels
# ================================================================

# راوتر فرعي للمستويات
levels_router = APIRouter(
    prefix="/{rule_id}/levels",
    tags=["Pricing - Rule Levels"]
)

@levels_router.post(
    "/",
    response_model=schemas.PriceTierRuleLevelRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller/Admin] إضافة مستوى جديد لقاعدة سعر",
    description="""
    يسمح للبائع أو المسؤول بإضافة مستوى سعري جديد (شريحة) لقاعدة تسعير متدرج موجودة.
    يتطلب صلاحية 'PRICING_RULE_MANAGE_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """
)
async def create_price_tier_rule_level_endpoint(
    rule_id: int,
    level_in: schemas.PriceTierRuleLevelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_MANAGE_OWN"))
):
    """نقطة وصول لإضافة مستوى جديد لقاعدة سعر متدرج."""
    # تأكد من أن rule_id في المسار يطابق rule_id في الـ body إذا كان موجودًا
    if level_in.rule_id != rule_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="معرف القاعدة في المسار لا يتطابق مع معرف القاعدة في البيانات.")
    return pricing_service.create_price_tier_rule_level(db=db, level_in=level_in, current_user=current_user)

@levels_router.get(
    "/",
    response_model=List[schemas.PriceTierRuleLevelRead],
    summary="[Seller/Admin] جلب جميع مستويات قاعدة سعر",
    description="""
    يجلب قائمة بجميع المستويات السعرية المرتبطة بقاعدة تسعير متدرج معينة.
    """,
)
async def get_all_price_tier_rule_levels_endpoint(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب مستويات قاعدة سعر متدرج."""
    # لا يوجد صلاحية محددة للعرض هنا، ولكن صلاحية Rule_View_OWN قد تتحكم في رؤية القاعدة الأم.
    return pricing_service.get_all_price_tier_rule_levels_for_rule(db=db, rule_id=rule_id)

@levels_router.patch(
    "/{level_id}",
    response_model=schemas.PriceTierRuleLevelRead,
    summary="[Seller/Admin] تحديث مستوى قاعدة سعر",
    description="""
    يسمح للبائع أو المسؤول بتحديث مستوى سعري موجود ضمن قاعدة معينة.
    يتطلب صلاحية 'PRICING_RULE_MANAGE_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """,
)
async def update_price_tier_rule_level_endpoint(
    rule_id: int,
    level_id: int,
    level_in: schemas.PriceTierRuleLevelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_MANAGE_OWN"))
):
    """نقطة وصول لتحديث مستوى قاعدة سعر متدرج."""
    return pricing_service.update_price_tier_rule_level(db=db, level_id=level_id, level_in=level_in, current_user=current_user)

@levels_router.delete(
    "/{level_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Seller/Admin] حذف مستوى قاعدة سعر",
    description="""
    يسمح للبائع أو المسؤول بحذف مستوى سعري محدد من قاعدة معينة (حذف صارم).
    يتطلب صلاحية 'PRICING_RULE_MANAGE_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """,
)
async def delete_price_tier_rule_level_endpoint(
    rule_id: int,
    level_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_MANAGE_OWN"))
):
    """نقطة وصول لحذف مستوى قاعدة سعر متدرج."""
    pricing_service.delete_price_tier_rule_level(db=db, level_id=level_id, current_user=current_user)
    return

# ================================================================
# --- نقاط الوصول لإسناد قواعد شرائح الأسعار لخيارات التعبئة (ProductPackagingPriceTierRuleAssignment) ---
#    (تتطلب صلاحية PRICING_RULE_ASSIGN_OWN أو ADMIN_PRICING_RULE_MANAGE_ANY)
# ================================================================

# راوتر فرعي للإسنادات
assignments_router = APIRouter(
    prefix="/assignments",
    tags=["Pricing - Rule Assignments"]
)

@assignments_router.post(
    "/",
    response_model=schemas.ProductPackagingPriceTierRuleAssignmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller/Admin] إسناد قاعدة سعر متدرج لخيار تعبئة",
    description="""
    يسمح للبائع أو المسؤول بإسناد قاعدة سعر متدرج معينة (rule_id) إلى خيار تعبئة وتغليف محدد (packaging_option_id).
    هذا الإسناد قد يكون له تاريخ بداية ونهاية، وحالة تفعيل.
    يتطلب صلاحية 'PRICING_RULE_ASSIGN_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """,
)
async def create_price_tier_rule_assignment_endpoint(
    assignment_in: schemas.ProductPackagingPriceTierRuleAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_ASSIGN_OWN"))
):
    """نقطة وصول لإنشاء إسناد قاعدة سعر متدرج."""
    return pricing_service.create_price_tier_rule_assignment(db=db, assignment_in=assignment_in, current_user=current_user)

@assignments_router.get(
    "/active-for-packaging-option/{packaging_option_id}",
    response_model=List[schemas.ProductPackagingPriceTierRuleAssignmentRead],
    summary="[Public] جلب الإسنادات النشطة لخيار تعبئة",
    description="""
    يجلب جميع إسنادات قواعد السعر المتدرج النشطة حاليًا لخيار تعبئة محدد.
    يُستخدم هذا لغرض حساب السعر الفعال (Effective Price).
    يمكن لأي مستخدم جلب هذه المعلومات.
    """,
)
async def get_active_assignments_for_packaging_option_endpoint(
    packaging_option_id: int,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب الإسنادات النشطة لخيار تعبئة."""
    return pricing_service.get_active_assignments_for_packaging_option(db=db, packaging_option_id=packaging_option_id)

@assignments_router.get(
    "/{assignment_id}",
    response_model=schemas.ProductPackagingPriceTierRuleAssignmentRead,
    summary="[Seller/Admin] جلب تفاصيل إسناد قاعدة سعر",
    description="""
    يجلب تفاصيل إسناد قاعدة سعر متدرج محدد بالـ ID الخاص به.
    يتطلب صلاحية 'PRICING_RULE_ASSIGN_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """,
)
async def get_price_tier_rule_assignment_details_endpoint(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_ASSIGN_OWN"))
):
    """نقطة وصول لجلب تفاصيل إسناد قاعدة سعر متدرج."""
    return pricing_service.get_price_tier_rule_assignment_details(db=db, assignment_id=assignment_id, current_user=current_user)

@assignments_router.patch(
    "/{assignment_id}",
    response_model=schemas.ProductPackagingPriceTierRuleAssignmentRead,
    summary="[Seller/Admin] تحديث إسناد قاعدة سعر",
    description="""
    يسمح للبائع أو المسؤول بتحديث إسناد قاعدة سعر متدرج موجود.
    يمكن تحديث تاريخي البدء والانتهاء، وحالة التفعيل (is_active).
    يتطلب صلاحية 'PRICING_RULE_ASSIGN_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """,
)
async def update_price_tier_rule_assignment_endpoint(
    assignment_id: int,
    assignment_in: schemas.ProductPackagingPriceTierRuleAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_ASSIGN_OWN"))
):
    """نقطة وصول لتحديث إسناد قاعدة سعر متدرج."""
    return pricing_service.update_price_tier_rule_assignment(db=db, assignment_id=assignment_id, assignment_in=assignment_in, current_user=current_user)

@assignments_router.delete(
    "/{assignment_id}",
    response_model=schemas.ProductPackagingPriceTierRuleAssignmentRead, # ترجع الكائن المحذوف ناعمًا
    summary="[Seller/Admin] حذف ناعم لإسناد قاعدة سعر",
    description="""
    يسمح للبائع أو المسؤول بحذف ناعم لإسناد قاعدة سعر متدرج (بتعيين is_active إلى False).
    لا يتم حذف السجل فعليًا من قاعدة البيانات.
    يتطلب صلاحية 'PRICING_RULE_ASSIGN_OWN' أو 'ADMIN_PRICING_RULE_MANAGE_ANY'.
    """,
)
async def soft_delete_price_tier_rule_assignment_endpoint(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRICING_RULE_ASSIGN_OWN"))
):
    """نقطة وصول لحذف ناعم لإسناد قاعدة سعر متدرج."""
    return pricing_service.soft_delete_price_tier_rule_assignment(db=db, assignment_id=assignment_id, current_user=current_user)

# ================================================================
# --- دمج الراوترات الفرعية في الراوتر الرئيسي (pricing_router) ---
# ================================================================
router.include_router(levels_router)
router.include_router(assignments_router)