# backend/src/api/v1/routers/products_router.py

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from src.db.session import get_db
from src.api.v1 import dependencies
from src.users.models.core_models import User
from src.products.services import product_service, variety_service, packaging_service, image_service, future_offerings_service
from src.products import schemas
# تأكد من استيراد الـ Schemas الفردية مباشرة إذا كان هذا النمط متبعًا في ملفك، مثلاً:
from src.products.schemas import packaging_schemas, image_schemas, variety_schemas, future_offerings_schemas

router = APIRouter()

# ... داخل router = APIRouter() ...

# ================================================================
# --- القسم الجديد: نقاط الوصول لإدارة خيارات التعبئة (Packaging Options) ---
# ================================================================
packaging_options_router = APIRouter(
    prefix="/{product_id}/packaging-options", # هذا الراوتر يعتمد على product_id في المسار
    tags=["Seller - Product Packaging Options"],
    dependencies=[Depends(dependencies.has_permission("PRODUCT_MANAGE_PACKAGING_OWN"))] # حماية المجموعة كاملة
)

@packaging_options_router.post(
    "/",
    response_model=packaging_schemas.PackagingOptionRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller] إضافة خيار تعبئة جديد لمنتج"
)
def create_packaging_option_for_product(
    product_id: UUID,
    option_in: packaging_schemas.PackagingOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """إنشاء خيار تعبئة جديد لمنتج يملكه البائع."""
    return packaging_service.create_new_packaging_option(db, option_in=option_in, product_id=product_id, current_user=current_user)

@packaging_options_router.get(
    "/",
    response_model=List[packaging_schemas.PackagingOptionRead],
    summary="[Seller/Public] عرض كل خيارات التعبئة لمنتج معين"
)
def get_packaging_options(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(dependencies.get_current_user_or_none), # يمكن للمستخدمين غير المسجلين رؤية الخيارات النشطة
    include_inactive: bool = False # يمكن للمالك/المسؤول طلب رؤية غير النشطة
):
    """جلب قائمة بخيارات التعبئة لمنتج. للمالك أو المسؤول: يعرض كل الخيارات. للعامة: يعرض الخيارات النشطة فقط."""
    return packaging_service.get_all_packaging_options_for_product(db, product_id=product_id, current_user=current_user, include_inactive=include_inactive)


@packaging_options_router.get(
    "/{packaging_option_id}",
    response_model=packaging_schemas.PackagingOptionRead,
    summary="[Seller/Public] جلب تفاصيل خيار تعبئة واحد"
)
def get_single_packaging_option(
    product_id: UUID, # للتأكد من السياق إذا كان مطلوبًا (يمكن إزالته من المسار إذا لم يكن ضروريًا للخدمة)
    packaging_option_id: int,
    db: Session = Depends(get_db)
):
    """جلب تفاصيل خيار تعبئة واحد بالـ ID الخاص به."""
    return packaging_service.get_packaging_option_details(db, packaging_option_id=packaging_option_id) # خدمة الجلب لا تحتاج product_id بالضرورة

@packaging_options_router.patch(
    "/{packaging_option_id}",
    response_model=packaging_schemas.PackagingOptionRead,
    summary="[Seller] تحديث خيار تعبئة موجود"
)
def update_packaging_option(
    product_id: UUID, # للتأكد من السياق
    packaging_option_id: int,
    option_in: packaging_schemas.PackagingOptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """تحديث خيار تعبئة يملكه البائع."""
    return packaging_service.update_packaging_option(db, packaging_option_id=packaging_option_id, option_in=option_in, current_user=current_user)

@packaging_options_router.delete(
    "/{packaging_option_id}",
    response_model=packaging_schemas.PackagingOptionRead, # قد ترجع الكائن المحذوف ناعمًا
    summary="[Seller] حذف ناعم لخيار تعبئة"
)
def soft_delete_packaging_option(
    product_id: UUID, # للتأكد من السياق
    packaging_option_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """حذف ناعم لخيار تعبئة (بتعيين is_active إلى False)."""
    return packaging_service.soft_delete_packaging_option(db, packaging_option_id=packaging_option_id, current_user=current_user)

# --- نقاط الوصول لترجمات خيارات التعبئة (Packaging Option Translations) ---

@packaging_options_router.post(
    "/{packaging_option_id}/translations",
    response_model=packaging_schemas.ProductPackagingOptionTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller] إنشاء ترجمة جديدة لخيار تعبئة أو تحديثها"
)
def create_packaging_option_translation_endpoint(
    product_id: UUID, # للتأكد من السياق
    packaging_option_id: int,
    trans_in: packaging_schemas.ProductPackagingOptionTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """إنشاء ترجمة جديدة لخيار تعبئة معين. إذا كانت الترجمة بنفس اللغة موجودة، سيتم رفض الطلب."""
    return packaging_service.create_packaging_option_translation(db=db, packaging_option_id=packaging_option_id, trans_in=trans_in, current_user=current_user)

@packaging_options_router.get(
    "/{packaging_option_id}/translations/{language_code}",
    response_model=packaging_schemas.ProductPackagingOptionTranslationRead,
    summary="[Seller/Public] جلب ترجمة محددة لخيار تعبئة"
)
def get_packaging_option_translation_endpoint(
    product_id: UUID, # للتأكد من السياق
    packaging_option_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """جلب ترجمة خيار تعبئة معينة بلغة محددة."""
    return packaging_service.get_packaging_option_translation_details(db, packaging_option_id=packaging_option_id, language_code=language_code)

@packaging_options_router.patch(
    "/{packaging_option_id}/translations/{language_code}",
    response_model=packaging_schemas.ProductPackagingOptionTranslationRead,
    summary="[Seller] تحديث ترجمة خيار تعبئة"
)
def update_packaging_option_translation_endpoint(
    product_id: UUID, # للتأكد من السياق
    packaging_option_id: int,
    language_code: str,
    trans_in: packaging_schemas.ProductPackagingOptionTranslationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """تحديث ترجمة خيار تعبئة معينة بلغة محددة."""
    return packaging_service.update_packaging_option_translation(db, packaging_option_id=packaging_option_id, language_code=language_code, trans_in=trans_in, current_user=current_user)

@packaging_options_router.delete(
    "/{packaging_option_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Seller] حذف ترجمة خيار تعبئة"
)
def delete_packaging_option_translation_endpoint(
    product_id: UUID, # للتأكد من السياق
    packaging_option_id: int,
    language_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """حذف ترجمة خيار تعبئة معينة بلغة محددة (حذف صارم)."""
    packaging_service.delete_packaging_option_translation(db, packaging_option_id=packaging_option_id, language_code=language_code, current_user=current_user)
    return

# ... في نفس الملف products_router.py، على مستوى الـ router الرئيسي ...

# ================================================================
# --- القسم الجديد: نقاط الوصول لإدارة الصور (Images) ---
# ================================================================
images_router = APIRouter(
    prefix="/images", # هذا الراوتر يمكن أن يكون له prefix خاص به أو يتداخل مع كيانات أخرى
    tags=["Seller - Images"],
    dependencies=[Depends(dependencies.has_permission("PRODUCT_MANAGE_IMAGES_OWN"))] # صلاحية مخصصة لإدارة الصور
)

@images_router.post(
    "/",
    response_model=image_schemas.ImageRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller] تحميل صورة جديدة وربطها بكيان"
)
def upload_image_endpoint(
    image_in: image_schemas.ImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """تحميل صورة جديدة وربطها بكيان (مثل منتج أو خيار تعبئة)."""
    # ملاحظة: التحميل الفعلي للملفات يجب أن يتم عبر FastAPI File Uploads، وهنا يتم تمرير URL للصورة المفترضة
    # إذا كنت تستخدم UploadFile، ستحتاج إلى تعديل الـ Schema والخدمة لاستقبال الملف
    return image_service.create_new_image(db=db, image_in=image_in, current_user=current_user)

@images_router.get(
    "/for-entity/{entity_type}/{entity_id}",
    response_model=List[image_schemas.ImageRead],
    summary="[Public] جلب كل الصور لكيان معين"
)
def get_images_for_entity_endpoint(
    entity_type: str, # مثال: "PRODUCT", "PACKAGING_OPTION"
    entity_id: str, # ID الكيان المرتبط (UUID أو int كسلسلة)
    db: Session = Depends(get_db)
):
    """جلب قائمة بجميع الصور المرتبطة بكيان معين (منتج، خيار تعبئة)."""
    return image_service.get_images_for_entity(db, entity_id=entity_id, entity_type=entity_type)

@images_router.get("/{image_id}", response_model=image_schemas.ImageRead)
def get_image_details_endpoint(image_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل صورة واحدة بالـ ID الخاص بها."""
    return image_service.get_image_details(db, image_id=image_id)

@images_router.patch(
    "/{image_id}",
    response_model=image_schemas.ImageRead,
    summary="[Seller] تحديث سجل صورة موجود"
)
def update_image_endpoint(
    image_id: int,
    image_in: image_schemas.ImageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """تحديث بيانات سجل صورة موجود. يتطلب ملكية المستخدم للكيان المرتبط بالصورة."""
    return image_service.update_image(db, image_id=image_id, image_in=image_in, current_user=current_user)

@images_router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Seller] حذف سجل صورة"
)
def delete_image_endpoint(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """حذف سجل صورة معين (حذف صارم). يتطلب ملكية المستخدم للكيان المرتبط بالصورة."""
    image_service.delete_image(db, image_id=image_id, current_user=current_user)
    return


# ================================================================
# --- نقاط الوصول الخاصة بالبائع (محمية بصلاحيات) ---
# ================================================================

@router.post("/", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED, summary="[Seller] Create a new product")
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRODUCT_CREATE_OWN"))
):
    """إنشاء منتج جديد. الحالة الأولية ستكون 'مسودة'."""
    return product_service.create_new_product(db=db, product_in=product_in, seller=current_user)

@router.get("/me", response_model=List[schemas.ProductRead], summary="[Seller] Get my products")
def get_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRODUCT_VIEW_OWN"))
):
    """جلب قائمة بجميع المنتجات الخاصة بالبائع الحالي."""
    return product_service.get_all_products_by_seller(db=db, seller=current_user)

@router.patch("/{product_id}", response_model=schemas.ProductRead, summary="[Seller] Update my product")
def update_my_product(
    product_id: UUID,
    product_in: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRODUCT_UPDATE_OWN"))
):
    """تحديث تفاصيل منتج يملكه البائع الحالي."""
    return product_service.update_existing_product(db=db, product_id=product_id, product_in=product_in, user=current_user)

@router.delete("/{product_id}", response_model=dict, summary="[Seller] Soft delete my product")
def delete_my_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRODUCT_DELETE_OWN"))
):
    """حذف ناعم لمنتج (أرشفته) يملكه البائع الحالي."""
    return product_service.soft_delete_product_by_id(db=db, product_id=product_id, user=current_user)


# ================================================================
# --- نقاط الوصول العامة (للزوار والمشترين) ---
# ================================================================

@router.get("/", response_model=List[schemas.ProductRead], summary="[Public] Get all active products")
def get_public_products(db: Session = Depends(get_db)):
    """جلب قائمة بالمنتجات النشطة فقط المتاحة للعامة."""
    return product_service.get_public_active_products(db)

@router.get("/{product_id}", response_model=schemas.ProductRead, summary="[Public] Get single product details")
def get_single_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(dependencies.get_current_user_or_none)
):
    """
    جلب تفاصيل منتج واحد.
    - للعامة: يعرض المنتج فقط إذا كان نشطًا.
    - للمالك أو المسؤول: يعرض المنتج بكل حالاته.
    """
    return product_service.get_product_by_id_for_user(db=db, product_id=product_id, user=current_user)

# --- Endpoints for Product Translations ---

@router.post("/{product_id}/translations", response_model=schemas.ProductRead, summary="[Seller] Add or update a translation")
def manage_product_translation(
    product_id: UUID,
    trans_in: schemas.ProductTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRODUCT_UPDATE_OWN"))
):
    return product_service.manage_product_translation(db, product_id=product_id, trans_in=trans_in, user=current_user)

@router.delete("/{product_id}/translations/{language_code}", status_code=status.HTTP_204_NO_CONTENT, summary="[Seller] Delete a translation")
def delete_product_translation(
    product_id: UUID,
    language_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("PRODUCT_UPDATE_OWN"))
):
    product_service.remove_product_translation(db, product_id=product_id, language_code=language_code, user=current_user)
    return

# ================================================================
# --- القسم الجديد: نقاط الوصول لإدارة أصناف المنتج (Varieties) ---
# ================================================================
varieties_router = APIRouter(
    prefix="/{product_id}/varieties",
    tags=["Seller - Product Varieties"],
    dependencies=[Depends(dependencies.has_permission("PRODUCT_UPDATE_OWN"))] # حماية المجموعة كاملة
)

@varieties_router.post("/", response_model=variety_schemas.ProductVarietyRead, status_code=status.HTTP_201_CREATED)
def create_variety_for_product(
    product_id: UUID,
    variety_in: variety_schemas.ProductVarietyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """[Seller] إنشاء صنف جديد لمنتج معين."""
    # نتأكد أن الـ product_id في المسار هو نفسه في الطلب
    if product_id != variety_in.product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID in URL does not match Product ID in request body."
        )
    return variety_service.create_new_variety(db, variety_in=variety_in, user=current_user)

@varieties_router.get("/", response_model=List[variety_schemas.ProductVarietyRead])
def get_varieties_for_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """[Seller] جلب كل الأصناف لمنتج معين."""
    return variety_service.get_all_varieties_for_a_product(db, product_id=product_id, user=current_user)

@varieties_router.patch("/{variety_id}", response_model=variety_schemas.ProductVarietyRead)
def update_variety_for_product(
    variety_id: int,
    variety_in: variety_schemas.ProductVarietyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """[Seller] تحديث صنف معين."""
    return variety_service.update_existing_variety(db, variety_id=variety_id, variety_in=variety_in, user=current_user)

@varieties_router.delete("/{variety_id}", response_model=dict)
def delete_variety_for_product(
    variety_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """[Seller] حذف ناعم (إلغاء تفعيل) لصنف معين."""
    return variety_service.soft_delete_variety_by_id(db, variety_id=variety_id, user=current_user)

# --- نقاط الوصول لإدارة ترجمات الأصناف ---

@varieties_router.post("/{variety_id}/translations", response_model=variety_schemas.ProductVarietyRead)
def manage_variety_translation(
    variety_id: int,
    trans_in: variety_schemas.ProductVarietyTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """[Seller] إضافة أو تحديث ترجمة لصنف معين."""
    return variety_service.manage_variety_translation(db, variety_id=variety_id, trans_in=trans_in, user=current_user)

@varieties_router.delete("/{variety_id}/translations/{language_code}", response_model=dict)
def delete_variety_translation(
    variety_id: int,
    language_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """[Seller] حذف ترجمة معينة لصنف."""
    return variety_service.remove_variety_translation(db, variety_id=variety_id, language_code=language_code, user=current_user)


# ================================================================
# --- نقاط الوصول لسجل أسعار المنتج (ProductPriceHistory) ---
#    (للعرض العام أو الخاص بالبائع)
# ================================================================

@router.get(
    "/packaging-options/{packaging_option_id}/price-history",
    response_model=List[future_offerings_schemas.ProductPriceHistoryRead],
    summary="[Public/Seller] جلب سجل تاريخ أسعار خيار تعبئة",
    description="""
    يجلب قائمة بسجلات تاريخ الأسعار لخيار تعبئة منتج محدد.
    تُعرض السجلات بترتيب زمني تنازلي (الأحدث أولاً).
    يمكن لأي مستخدم (بما في ذلك العامة) رؤية تاريخ الأسعار.
    """,
)
async def get_price_history_for_packaging_option_endpoint(
    packaging_option_id: int, # معرف خيار التعبئة
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب تاريخ أسعار خيار تعبئة."""
    return future_offerings_service.get_all_product_price_history_for_packaging_option(
        db=db,
        packaging_option_id=packaging_option_id,
        skip=skip,
        limit=limit
    )

@router.get(
    "/price-history/{price_history_id}",
    response_model=future_offerings_schemas.ProductPriceHistoryRead,
    summary="[Public/Seller] جلب سجل تاريخ سعر واحد",
    description="""
    يجلب تفاصيل سجل تاريخ سعر واحد باستخدام الـ ID الخاص به.
    يمكن لأي مستخدم (بما في ذلك العامة) رؤية سجل السعر.
    """,
)
async def get_single_price_history_entry_endpoint(
    price_history_id: int, # معرف سجل السعر
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب تفاصيل سجل تاريخ سعر محدد."""
    return future_offerings_service.get_product_price_history_entry(db=db, price_history_id=price_history_id)




router.include_router(varieties_router) 
# ... في نهاية تعريف الـ router الرئيسي في products_router.py ...

# دمج راوتر خيارات التعبئة ضمن الراوتر الرئيسي للمنتجات
router.include_router(packaging_options_router)

# دمج راوتر الصور ضمن الراوتر الرئيسي للمنتجات
router.include_router(images_router)
