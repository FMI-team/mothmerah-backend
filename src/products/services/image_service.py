# backend\src\products\services\image_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

# استيراد المودلز (للتعريفات والـ Type Hinting)
from src.products.models.units_models import Image
from src.products.models.products_models import Product # للتحقق من وجود المنتج
from src.products.models.units_models import ProductPackagingOption # للتحقق من وجود خيار التعبئة
# استيراد الـ Schemas
from src.products.schemas import image_schemas
# استيراد دوال الـ CRUD من الملف الخاص بها
from src.products.crud import image_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

# ==========================================================
# --- خدمات الصور (Image) ---
# ==========================================================

def create_new_image(db: Session, image_in: image_schemas.ImageCreate, current_user: User) -> Image:
    """
    خدمة لإنشاء سجل صورة جديد وربطه بكيان.
    تتضمن التحقق من وجود الكيان (المنتج أو خيار التعبئة) وملكية المستخدم.
    """
    # 1. التحقق من صلاحية المستخدم (يجب أن يكون مالك الكيان أو مسؤول)
    # هذا التحقق سيكون أكثر تفصيلاً في الـ router أو الـ middleware
    # ولكن هنا نتحقق من أن المستخدم موجود
    if not current_user:
        raise ForbiddenException(detail="Authentication required to upload images.")

    # 2. التحقق من وجود الكيان المرتبط ونوع الكيان
    entity_id_str = str(image_in.entity_id) # تأكد من التعامل مع entity_id كسلسلة
    if image_in.entity_type == "PRODUCT":
        # نفترض أن get_product_by_id_for_user تتحقق من الملكية
        from src.products.services.product_service import get_product_by_id_for_user
        product = get_product_by_id_for_user(db, product_id=UUID(entity_id_str), user=current_user)
        # يمكنك إضافة تحققات إضافية هنا إذا كان هناك حد أقصى لعدد الصور للمنتج
    elif image_in.entity_type == "PACKAGING_OPTION":
        # نحتاج لخدمة تجلب خيار التعبئة وتتحقق من ملكية المنتج الأم
        from src.products.services.packaging_service import get_packaging_option_details
        packaging_option = get_packaging_option_details(db, packaging_option_id=int(entity_id_str))
        # الآن تحقق من ملكية المنتج الأم لخيار التعبئة
        from src.products.services.product_service import get_product_by_id_for_user
        get_product_by_id_for_user(db, product_id=packaging_option.product_id, user=current_user)
        # يمكنك إضافة تحققات إضافية هنا إذا كان هناك حد أقصى لعدد الصور لخيار التعبئة
    # TODO: أضف أنواع كيانات أخرى هنا (مثل 'AUCTION_LOT')
    else:
        raise BadRequestException(detail=f"Unsupported entity type for image: {image_in.entity_type}")

    # 3. منطق is_primary_image: إذا تم تعيين هذه الصورة كصورة رئيسية، قم بإلغاء تعيين أي صورة رئيسية سابقة لنفس الكيان
    if image_in.is_primary_image:
        current_primary_image = db.query(Image).filter(
            Image.entity_id == entity_id_str,
            Image.entity_type == image_in.entity_type,
            Image.is_primary_image == True
        ).first()
        if current_primary_image:
            current_primary_image.is_primary_image = False
            db.add(current_primary_image) # إضافة للتحديث في نفس الـ commit

    # 4. استدعاء دالة CRUD للإنشاء
    return image_crud.create_image(db=db, image_in=image_in, uploaded_by_user_id=current_user.user_id)

def get_image_details(db: Session, image_id: int) -> Image:
    """
    خدمة لجلب تفاصيل صورة واحدة بالـ ID، مع معالجة عدم الوجود.
    """
    image = image_crud.get_image(db, image_id=image_id)
    if not image:
        raise NotFoundException(detail=f"Image with ID {image_id} not found.")
    return image

def get_images_for_entity(db: Session, entity_id: str, entity_type: str) -> List[Image]:
    """
    خدمة لجلب جميع الصور المرتبطة بكيان معين.
    لا تتطلب صلاحية خاصة للعرض (الصور عادة ما تكون عامة).
    """
    # لا يوجد هنا تحقق من ملكية المستخدم لأن الصور عادة ما تكون للعرض العام
    # ولكن يمكن إضافة تحققات إذا كانت هناك صور خاصة
    return image_crud.get_images_for_entity(db, entity_id=entity_id, entity_type=entity_type)

def update_image(db: Session, image_id: int, image_in: image_schemas.ImageUpdate, current_user: User) -> Image:
    """
    خدمة لتحديث سجل صورة موجود.
    تتضمن التحقق من ملكية المستخدم للكيان المرتبط.
    """
    db_image = get_image_details(db, image_id) # استخدام دالة الخدمة للتحقق من الوجود

    # 1. التحقق من ملكية المستخدم للكيان المرتبط بالصورة
    entity_id_str = str(db_image.entity_id)
    if db_image.entity_type == "PRODUCT":
        from src.products.services.product_service import get_product_by_id_for_user
        get_product_by_id_for_user(db, product_id=UUID(entity_id_str), user=current_user)
    elif db_image.entity_type == "PACKAGING_OPTION":
        from src.products.services.packaging_service import get_packaging_option_details
        packaging_option = get_packaging_option_details(db, packaging_option_id=int(entity_id_str))
        from src.products.services.product_service import get_product_by_id_for_user
        get_product_by_id_for_user(db, product_id=packaging_option.product_id, user=current_user)
    # TODO: أضف أنواع كيانات أخرى هنا
    else:
        raise BadRequestException(detail=f"Unsupported entity type for image update: {db_image.entity_type}")

    # 2. منطق is_primary_image: إذا تم تعيين هذه الصورة كصورة رئيسية، قم بإلغاء تعيين أي صورة رئيسية سابقة لنفس الكيان
    if image_in.is_primary_image is True:
        current_primary_image = db.query(Image).filter(
            Image.entity_id == entity_id_str,
            Image.entity_type == db_image.entity_type,
            Image.is_primary_image == True,
            Image.image_id != image_id # استبعاد الصورة الحالية إذا كانت هي نفسها
        ).first()
        if current_primary_image:
            current_primary_image.is_primary_image = False
            db.add(current_primary_image) # إضافة للتحديث في نفس الـ commit
    elif image_in.is_primary_image is False and db_image.is_primary_image is True:
        # إذا كانت هذه الصورة هي الرئيسية وتم محاولة إلغاء تعيينها
        # يمكنك هنا فرض وجود صورة رئيسية دائمًا، أو السماح بعدم وجودها
        pass # For now, just allow deactivation

    return image_crud.update_image(db=db, db_image=db_image, image_in=image_in)

def delete_image(db: Session, image_id: int, current_user: User):
    """
    خدمة لحذف سجل صورة معين (حذف صارم).
    تتضمن التحقق من ملكية المستخدم للكيان المرتبط.
    """
    db_image = get_image_details(db, image_id) # استخدام دالة الخدمة للتحقق من الوجود

    # 1. التحقق من ملكية المستخدم للكيان المرتبط بالصورة
    entity_id_str = str(db_image.entity_id)
    if db_image.entity_type == "PRODUCT":
        from src.products.services.product_service import get_product_by_id_for_user
        get_product_by_id_for_user(db, product_id=UUID(entity_id_str), user=current_user)
    elif db_image.entity_type == "PACKAGING_OPTION":
        from src.products.services.packaging_service import get_packaging_option_details
        packaging_option = get_packaging_option_details(db, packaging_option_id=int(entity_id_str))
        from src.products.services.product_service import get_product_by_id_for_user
        get_product_by_id_for_user(db, product_id=packaging_option.product_id, user=current_user)
    # TODO: أضف أنواع كيانات أخرى هنا
    else:
        raise BadRequestException(detail=f"Unsupported entity type for image deletion: {db_image.entity_type}")

    # 2. منطق إضافي قبل الحذف: إذا كانت الصورة المحذوفة هي الصورة الرئيسية، يجب التفكير في تعيين صورة رئيسية بديلة
    if db_image.is_primary_image:
        # يمكنك هنا إضافة منطق لتعيين صورة رئيسية جديدة تلقائيًا من الصور المتبقية للكيان
        pass # For now, just delete it

    image_crud.delete_image(db=db, db_image=db_image)
    # TODO: هنا يجب إضافة منطق لحذف الملف الفعلي للصورة من خدمة التخزين السحابي (مثل AWS S3)
    # هذا يتطلب تكاملًا مع مكتبة التخزين السحابي الخاصة بك.
    # مثال: delete_from_s3(db_image.image_url)
    return {"message": "Image deleted successfully."}