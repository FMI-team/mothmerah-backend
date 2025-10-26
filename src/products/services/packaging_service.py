# backend\src\products\services\packaging_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

# استيراد المودلز (للتعريفات والـ Type Hinting)
from src.products.models.units_models import ProductPackagingOption, ProductPackagingOptionTranslation, UnitOfMeasure
from src.products.models.products_models import Product # لاستخدامها في التحقق من المنتجات
# استيراد الـ Schemas
from src.products.schemas import packaging_schemas
# استيراد دوال الـ CRUD من الملف الخاص بها
from src.products.crud import packaging_crud
# استيراد الخدمات الأخرى للتحقق من الوجود (مثل خدمة المنتج وخدمة وحدة القياس)
from src.products.services.product_service import get_product_by_id_for_user # لضمان وجود المنتج وملكيته
from src.products.services.unit_of_measure_service import get_unit_of_measure_details # لضمان وجود وحدة القياس
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

# ==========================================================
# --- خدمات خيارات التعبئة (ProductPackagingOption) ---
# ==========================================================

def create_new_packaging_option(db: Session, option_in: packaging_schemas.PackagingOptionCreate, product_id: UUID, current_user: User) -> ProductPackagingOption:
    """
    خدمة لإنشاء خيار تعبئة جديد لمنتج معين.
    تتضمن التحقق من وجود المنتج، ملكية المستخدم للمنتج، وجود وحدة القياس،
    والتحقق من منطق is_default_option.
    """
    # 1. التحقق من وجود المنتج وأن المستخدم يملكه
    # ملاحظة: get_product_by_id_for_user سترمي NotFoundException أو ForbiddenException إذا لم يتم العثور على المنتج أو لم يكن المستخدم يملكه
    product = get_product_by_id_for_user(db, product_id=product_id, user=current_user)

    # 2. التحقق من وجود unit_of_measure_id_for_quantity
    get_unit_of_measure_details(db, option_in.unit_of_measure_id_for_quantity)

    # 3. منطق is_default_option: إذا كان الخيار الجديد هو الافتراضي، قم بإلغاء تعيين الخيار الافتراضي الحالي للمنتج
    if option_in.is_default_option:
        current_default_option = db.query(ProductPackagingOption).filter(
            ProductPackagingOption.product_id == product_id,
            ProductPackagingOption.is_default_option == True
        ).first()
        if current_default_option:
            current_default_option.is_default_option = False
            db.add(current_default_option) # إضافة للتحديث في نفس الـ commit

    # 4. التحقق من تكرار SKU (إذا كان SKU غير None)
    if option_in.sku:
        existing_sku = db.query(ProductPackagingOption).filter(
            ProductPackagingOption.sku == option_in.sku,
            ProductPackagingOption.product_id == product_id # SKU يجب أن يكون فريدًا ضمن المنتج
        ).first()
        if existing_sku:
            raise ConflictException(detail=f"SKU '{option_in.sku}' already exists for this product.")

    # استدعاء دالة CRUD للإنشاء
    return packaging_crud.create_packaging_option(db=db, option_in=option_in, product_id=product_id)


def get_packaging_option_details(db: Session, packaging_option_id: int) -> ProductPackagingOption:
    """
    خدمة لجلب تفاصيل خيار تعبئة واحد بالـ ID، مع معالجة عدم الوجود.
    """
    option = packaging_crud.get_packaging_option(db, packaging_option_id=packaging_option_id)
    if not option:
        raise NotFoundException(detail=f"Packaging option with ID {packaging_option_id} not found.")
    return option

def get_all_packaging_options_for_product(db: Session, product_id: UUID, current_user: Optional[User] = None, include_inactive: bool = False) -> List[ProductPackagingOption]:
    """
    خدمة لجلب جميع خيارات التعبئة لمنتج معين.
    إذا كان المستخدم هو مالك المنتج أو مسؤول، يمكنه رؤية الخيارات غير النشطة.
    """
    # التحقق من وجود المنتج وملكيته/صلاحية المستخدم
    product = get_product_by_id_for_user(db, product_id=product_id, user=current_user)
    
    # تحديد ما إذا كان يجب تضمين الخيارات غير النشطة بناءً على صلاحية المستخدم
    effective_include_inactive = include_inactive
    if current_user and (current_user.user_id == product.seller_user_id or 
                         any(p.permission_name_key == "ADMIN_PRODUCT_VIEW_ANY" for p in current_user.default_role.permissions)):
        effective_include_inactive = True # المالك أو المسؤول يمكنه رؤية كل شيء
    
    return packaging_crud.get_all_packaging_options_for_product(db, product_id=product_id, include_inactive=effective_include_inactive)

def update_packaging_option(db: Session, packaging_option_id: int, option_in: packaging_schemas.PackagingOptionUpdate, current_user: User) -> ProductPackagingOption:
    """
    خدمة لتحديث خيار تعبئة موجود.
    تتضمن التحقق من ملكية المستخدم، ومنطق is_default_option، وتكرار SKU.
    """
    db_option = get_packaging_option_details(db, packaging_option_id) # استخدام دالة الخدمة للتحقق من الوجود

    # التحقق من ملكية المستخدم للمنتج المرتبط بخيار التعبئة
    get_product_by_id_for_user(db, product_id=db_option.product_id, user=current_user)

    # 1. منطق is_default_option
    if option_in.is_default_option is True:
        # إذا تم تعيين هذا الخيار كافتراضي، قم بإلغاء تعيين أي خيار افتراضي آخر للمنتج
        current_default_option = db.query(ProductPackagingOption).filter(
            ProductPackagingOption.product_id == db_option.product_id,
            ProductPackagingOption.is_default_option == True,
            ProductPackagingOption.packaging_option_id != packaging_option_id # استبعاد الخيار الحالي إذا كان هو نفسه
        ).first()
        if current_default_option:
            current_default_option.is_default_option = False
            db.add(current_default_option) # إضافة للتحديث في نفس الـ commit
    elif option_in.is_default_option is False and db_option.is_default_option is True:
        # إذا كان هذا الخيار هو الافتراضي وتم محاولة إلغاء تعيينه، تحقق
        # يمكنك هنا فرض وجود خيار افتراضي دائمًا، أو السماح بعدم وجوده
        # للحفاظ على البساطة، سنسمح بإلغاء الافتراضي دون تعيين بديل آليًا
        pass

    # 2. التحقق من تكرار SKU (إذا تم تحديثه)
    if option_in.sku and option_in.sku != db_option.sku:
        existing_sku = db.query(ProductPackagingOption).filter(
            ProductPackagingOption.sku == option_in.sku,
            ProductPackagingOption.product_id == db_option.product_id # SKU فريد ضمن المنتج
        ).first()
        if existing_sku:
            raise ConflictException(detail=f"SKU '{option_in.sku}' already exists for this product.")

    # 3. التحقق من unit_of_measure_id_for_quantity إذا تم تغييره
    if option_in.unit_of_measure_id_for_quantity and option_in.unit_of_measure_id_for_quantity != db_option.unit_of_measure_id_for_quantity:
        get_unit_of_measure_details(db, option_in.unit_of_measure_id_for_quantity)

    # TODO: منطق عمل إضافي: التحقق مما إذا كان خيار التعبئة مستخدمًا في أي طلبات نشطة قبل السماح بتغييرات معينة
    # (مثلاً: منع تغيير الكمية أو السعر الأساسي إذا كان في طلب مفتوح)

    return packaging_crud.update_packaging_option(db=db, db_option=db_option, option_in=option_in)

def soft_delete_packaging_option(db: Session, packaging_option_id: int, current_user: User) -> ProductPackagingOption:
    """
    خدمة للحذف الناعم لخيار تعبئة بتعيين is_active إلى False.
    تتضمن التحقق من ملكية المستخدم وعدم استخدام الخيار في أي طلبات نشطة.
    """
    db_option = get_packaging_option_details(db, packaging_option_id) # استخدام دالة الخدمة للتحقق من الوجود

    # التحقق من ملكية المستخدم للمنتج المرتبط بخيار التعبئة
    get_product_by_id_for_user(db, product_id=db_option.product_id, user=current_user)

    if not db_option.is_active:
        raise BadRequestException(detail=f"Packaging option with ID {packaging_option_id} is already inactive.")

    # TODO: منطق عمل: التحقق مما إذا كان خيار التعبئة مستخدمًا في أي طلبات نشطة
    # من src.market.models import OrderItem (مثال)
    # if db.query(OrderItem).filter(OrderItem.packaging_option_id == packaging_option_id, OrderItem.order.has(Order.status_id == ACTIVE_ORDER_STATUS_ID)).count() > 0:
    #     raise ForbiddenException(detail=f"Cannot soft-delete packaging option ID {packaging_option_id} because it is part of active orders.")

    # إذا كان الخيار هو الافتراضي، ونقوم بحذفه ناعمًا، يجب التفكير في تعيين خيار افتراضي آخر أو السماح بعدم وجوده
    if db_option.is_default_option:
        # هنا يمكن إضافة منطق لتعيين خيار افتراضي جديد تلقائيًا إذا كان هناك آخرون نشطون
        # أو يمكن تركها بدون خيار افتراضي إذا كان هذا مقبولاً في منطق العمل
        pass # for now, just deactivate it

    return packaging_crud.soft_delete_packaging_option(db=db, db_option=db_option)

# ==========================================================
# --- خدمات ترجمات خيارات التعبئة (ProductPackagingOption Translation) ---
# ==========================================================

def create_packaging_option_translation(db: Session, packaging_option_id: int, trans_in: packaging_schemas.ProductPackagingOptionTranslationCreate, current_user: User) -> ProductPackagingOptionTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لخيار تعبئة معين.
    تتضمن التحقق من وجود خيار التعبئة الأم وملكية المستخدم وعدم تكرار الترجمة.
    """
    # منطق عمل: التحقق من وجود خيار التعبئة الأم وملكيته للمستخدم
    db_option = get_packaging_option_details(db, packaging_option_id)
    get_product_by_id_for_user(db, product_id=db_option.product_id, user=current_user)

    # منطق عمل: التحقق من عدم وجود ترجمة بنفس اللغة للخيار
    existing_translation = packaging_crud.get_packaging_option_translation(db, packaging_option_id=packaging_option_id, language_code=trans_in.language_code)
    if existing_translation:
        raise ConflictException(detail=f"Translation for packaging option ID {packaging_option_id} with language '{trans_in.language_code}' already exists.")

    return packaging_crud.create_packaging_option_translation(db=db, packaging_option_id=packaging_option_id, trans_in=trans_in)

def get_packaging_option_translation_details(db: Session, packaging_option_id: int, language_code: str) -> ProductPackagingOptionTranslation:
    """
    خدمة لجلب ترجمة محددة لخيار تعبئة بلغة معينة، مع معالجة عدم الوجود.
    """
    translation = packaging_crud.get_packaging_option_translation(db, packaging_option_id=packaging_option_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"Translation for packaging option ID {packaging_option_id} in language '{language_code}' not found.")
    return translation

def update_packaging_option_translation(db: Session, packaging_option_id: int, language_code: str, trans_in: packaging_schemas.ProductPackagingOptionTranslationUpdate, current_user: User) -> ProductPackagingOptionTranslation:
    """
    خدمة لتحديث ترجمة خيار تعبئة موجودة.
    تتضمن التحقق من ملكية المستخدم.
    """
    db_translation = get_packaging_option_translation_details(db, packaging_option_id, language_code) # استخدام دالة الخدمة للتحقق

    # التحقق من ملكية المستخدم لخيار التعبئة الأم
    db_option = get_packaging_option_details(db, packaging_option_id)
    get_product_by_id_for_user(db, product_id=db_option.product_id, user=current_user)

    return packaging_crud.update_packaging_option_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_packaging_option_translation(db: Session, packaging_option_id: int, language_code: str, current_user: User):
    """
    خدمة لحذف ترجمة خيار تعبئة معينة (حذف صارم).
    تتضمن التحقق من ملكية المستخدم.
    """
    db_translation = get_packaging_option_translation_details(db, packaging_option_id, language_code) # استخدام دالة الخدمة للتحقق

    # التحقق من ملكية المستخدم لخيار التعبئة الأم
    db_option = get_packaging_option_details(db, packaging_option_id)
    get_product_by_id_for_user(db, product_id=db_option.product_id, user=current_user)

    packaging_crud.delete_packaging_option_translation(db=db, db_translation=db_translation)
    return {"message": "Packaging option translation deleted successfully."}