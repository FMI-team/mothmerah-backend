# backend\src\users\services\address_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز
from src.users.models import addresses_models as models # Address
# استيراد الـ CRUD
from src.users.crud import address_crud # لـ Address CRUDs
# استيراد Schemas
from src.users.schemas import address_schemas as schemas # Address
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.users.services.address_lookups_service import ( # للتحقق من وجود أنواع العناوين والمدن والأحياء والدول والمحافظات
    get_address_type_by_id_service,
    get_country_by_code_service,
    get_governorate_by_id_service,
    get_city_by_id_service,
    get_district_by_id_service
)


# ==========================================================
# --- خدمات العناوين (Address) ---
# ==========================================================

def create_new_address(db: Session, address_in: schemas.AddressCreate, current_user: User) -> models.Address:
    """
    خدمة لإنشاء عنوان جديد لمستخدم معين.
    [REQ-FUN-022]: السماح للمستخدمين بإضافة عنوان.
    تتضمن التحقق من وجود الكيانات الجغرافية ونوع العنوان، ومنطق العنوان الأساسي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        address_in (schemas.AddressCreate): بيانات العنوان للإنشاء.
        current_user (User): المستخدم الحالي الذي ينشئ العنوان.

    Returns:
        models.Address: كائن العنوان الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على نوع العنوان، الدولة، المحافظة، المدينة، أو الحي.
        ConflictException: إذا حاول المستخدم تعيين عنوان أساسي وهناك عنوان أساسي آخر لنفس النوع.
        BadRequestException: إذا كانت البيانات غير صالحة.
    """
    # 1. التحقق من وجود نوع العنوان (address_type_id)
    get_address_type_by_id_service(db, address_in.address_type_id)

    # 2. التحقق من وجود الكيانات الجغرافية
    get_country_by_code_service(db, address_in.country_code)
    get_city_by_id_service(db, address_in.city_id)
    if address_in.governorate_id:
        get_governorate_by_id_service(db, address_in.governorate_id)
    if address_in.district_id:
        get_district_by_id_service(db, address_in.district_id)
    
    # 3. منطق العنوان الأساسي (is_primary)
    if address_in.is_primary:
        # إذا حاول المستخدم تعيين هذا كعنوان أساسي، يجب إلغاء تعيين أي عنوان آخر كعنوان أساسي لنفس المستخدم ونوع العنوان.
        existing_primary_addresses = db.query(models.Address).filter(
            models.Address.user_id == current_user.user_id,
            models.Address.address_type_id == address_in.address_type_id,
            models.Address.is_primary == True
        ).all()
        for addr in existing_primary_addresses:
            addr.is_primary = False
            db.add(addr) # إضافة للتحديث في نفس الـ transaction
    
    # 4. استدعاء CRUD لإنشاء العنوان
    db_address = address_crud.create_address(db=db, address_in=address_in, user_id=current_user.user_id)
    db.commit() # commit لكل التغييرات (إنشاء العنوان وتحديث is_primary للعناوين الأخرى)

    return db_address

def get_user_addresses(db: Session, current_user: User) -> List[models.Address]:
    """
    خدمة لجلب عناوين المستخدم الحالي.
    [REQ-FUN-022]: السماح للمستخدمين بإدارة دفتر عناوين متعدد.
    """
    return address_crud.get_addresses_for_user(db=db, user_id=current_user.user_id)

def get_address_by_id(db: Session, address_id: int, current_user: Optional[User] = None) -> models.Address:
    """
    خدمة لجلب عنوان واحد بالـ ID، مع التحقق من ملكية المستخدم أو صلاحيات المسؤول.
    يمكن أن تستخدم من خدمات أخرى (مثل الطلبات) دون تمرير current_user.

    Args:
        db (Session): جلسة قاعدة البيانات.
        address_id (int): معرف العنوان المطلوب.
        current_user (Optional[User]): المستخدم الحالي الذي يطلب العنوان (لتحقق الملكية).

    Returns:
        models.Address: كائن العنوان المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على العنوان.
        ForbiddenException: إذا كان المستخدم غير مالك وليس مسؤولاً.
    """
    db_address = address_crud.get_address_by_id(db=db, address_id=address_id)
    if not db_address:
        raise NotFoundException(detail=f"العنوان بمعرف {address_id} غير موجود.")

    # التحقق من الملكية إذا تم توفير المستخدم
    if current_user:
        if db_address.user_id != current_user.user_id and \
           not any(p.permission_name_key == "ADMIN_ADDRESS_VIEW_ANY" for p in current_user.default_role.permissions): # TODO: صلاحية ADMIN_ADDRESS_VIEW_ANY
            raise ForbiddenException(detail="غير مصرح لك برؤية تفاصيل هذا العنوان.")
    
    return db_address

def update_user_address(db: Session, address_id: int, address_in: schemas.AddressUpdate, current_user: User) -> models.Address:
    """
    خدمة لتحديث عنوان موجود لمستخدم معين.
    [REQ-FUN-022]: السماح للمستخدمين بتعديل عنوان حالي.
    تتضمن التحقق من ملكية المستخدم، ووجود الكيانات المرتبطة، ومنطق العنوان الأساسي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        address_id (int): معرف العنوان المراد تحديثه.
        address_in (schemas.AddressUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي الذي يجري التحديث.

    Returns:
        models.Address: كائن العنوان المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على العنوان.
        ForbiddenException: إذا لم يكن المستخدم يملك العنوان أو غير مصرح له.
        ConflictException: إذا كانت هناك محاولة تعيين عنوان أساسي آخر يتعارض.
    """
    db_address = get_address_by_id(db, address_id=address_id, current_user=current_user) # التحقق من الوجود والملكية

    # 1. التحقق من وجود نوع العنوان (address_type_id) إذا تم تحديثه
    if address_in.address_type_id and address_in.address_type_id != db_address.address_type_id:
        get_address_type_by_id_service(db, address_in.address_type_id)

    # 2. التحقق من وجود الكيانات الجغرافية إذا تم تحديثها
    if address_in.country_code and address_in.country_code != db_address.country_code:
        get_country_by_code_service(db, address_in.country_code)
    if address_in.governorate_id and address_in.governorate_id != db_address.governorate_id:
        get_governorate_by_id_service(db, address_in.governorate_id)
    if address_in.city_id and address_in.city_id != db_address.city_id:
        get_city_by_id_service(db, address_in.city_id)
    if address_in.district_id and address_in.district_id != db_address.district_id:
        get_district_by_id_service(db, address_in.district_id)

    # 3. منطق العنوان الأساسي (is_primary)
    if address_in.is_primary == True and not db_address.is_primary:
        # إذا تم تعيين هذا كعنوان أساسي جديد، يجب إلغاء تعيين أي عنوان آخر كعنوان أساسي
        existing_primary_addresses = db.query(models.Address).filter(
            models.Address.user_id == current_user.user_id,
            models.Address.address_type_id == (address_in.address_type_id or db_address.address_type_id),
            models.Address.is_primary == True,
            models.Address.address_id != address_id # استبعاد العنوان الحالي
        ).all()
        for addr in existing_primary_addresses:
            addr.is_primary = False
            db.add(addr) # إضافة للتحديث في نفس الـ transaction

    return address_crud.update_address(db=db, db_address=db_address, address_in=address_in)

def delete_user_address(db: Session, address_id: int, current_user: User):
    """
    خدمة لحذف عنوان مستخدم.
    [REQ-FUN-022]: السماح للمستخدمين بحذف عنوان.
    تتضمن التحقق من ملكية المستخدم، وعدم حذف العنوان الوحيد، وعدم حذف العنوان الأساسي.

    Args:
        db (Session): جلسة قاعدة البيانات.
        address_id (int): معرف العنوان المراد حذفه.
        current_user (User): المستخدم الحالي الذي يجري الحذف.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على العنوان.
        ForbiddenException: إذا لم يكن المستخدم يملك العنوان أو غير مصرح له.
        BadRequestException: إذا حاول حذف العنوان الوحيد أو العنوان الأساسي.
    """
    db_address = get_address_by_id(db, address_id=address_id, current_user=current_user) # التحقق من الوجود والملكية

    # 1. التحقق من عدم حذف العنوان الوحيد (REQ-FUN-022)
    user_addresses = address_crud.get_addresses_for_user(db, user_id=current_user.user_id)
    if len(user_addresses) == 1:
        raise BadRequestException(detail="لا يمكن حذف العنوان الوحيد المسجل. يرجى إضافة عنوان آخر أولاً.")
    
    # 2. التحقق من عدم حذف العنوان الأساسي (REQ-FUN-022)
    if db_address.is_primary:
        raise BadRequestException(detail="لا يمكن حذف العنوان الأساسي. يرجى تعيين عنوان آخر كافتراضي أولاً.")

    # TODO: منطق عمل: التحقق من عدم وجود الطلبات النشطة أو المنتجات المرتبطة بهذا العنوان.
    #       (مثل Order.shipping_address_id أو Order.billing_address_id)
    #       هذا يتطلب استيراد مودل Order.

    address_crud.delete_address(db=db, db_address=db_address)
    db.commit()
    return {"message": "تم حذف العنوان بنجاح."}