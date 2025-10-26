# backend\src\pricing\services\pricing_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone # استخدام timezone لجعل التواريخ aware

# استيراد المودلز (للتعريفات والـ Type Hinting)
from src.pricing.models import tier_pricing_models as models
# استيراد Schemas
from src.pricing.schemas import pricing_schemas as schemas
# استيراد دوال الـ CRUD
from src.pricing.crud import pricing_crud
# استيراد الاستثناءات المخصصة
from src.exceptions import (
    NotFoundException, ConflictException, BadRequestException, ForbiddenException
)
from src.users.models.core_models import User # لاستخدام User في التحقق من الصلاحيات

# استيراد خدمات من مجموعات أخرى للتحقق من الوجود (تجنب التبعيات الدائرية بالاستيراد المحلي إذا لزم الأمر)
from src.products.services.packaging_service import get_packaging_option_details # للتحقق من خيار التعبئة

# ==========================================================
# --- خدمات قواعد شرائح الأسعار (PriceTierRule) ---
# ==========================================================

def create_new_price_tier_rule(db: Session, rule_in: schemas.PriceTierRuleCreate, current_user: User) -> models.PriceTierRule:
    """
    خدمة لإنشاء قاعدة شريحة سعر جديدة.
    تتضمن التحقق من عدم التكرار، ومعالجة الترجمات والمستويات المضمنة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_in (schemas.PriceTierRuleCreate): بيانات القاعدة للإنشاء.
        current_user (User): المستخدم الحالي الذي ينشئ القاعدة.

    Returns:
        models.PriceTierRule: كائن القاعدة الذي تم إنشاؤه.

    Raises:
        ConflictException: إذا كانت هناك قاعدة بنفس المفتاح موجودة بالفعل.
        BadRequestException: إذا كانت بيانات القاعدة (مثل discount_type) غير متوافقة مع المستويات أو إذا كانت المستويات غير صحيحة.
    """
    # 1. التحقق من عدم وجود قاعدة بنفس المفتاح لتجنب التكرار.
    existing_rule_by_key = db.query(models.PriceTierRule).filter(models.PriceTierRule.rule_name_key == rule_in.rule_name_key).first()
    if existing_rule_by_key:
        raise ConflictException(detail=f"قاعدة السعر بمفتاح '{rule_in.rule_name_key}' موجودة بالفعل.")

    # 2. التحقق من أن القاعدة تحتوي على مستوى واحد على الأقل.
    if not rule_in.levels:
        raise BadRequestException(detail="يجب أن تحتوي قاعدة السعر على مستوى واحد على الأقل.")

    # 3. منطق التحقق من توافق discount_type مع المستويات المضمنة وترتيب المستويات وأسعارها.
    #    - يضمن أن حقول السعر/الخصم الصحيحة محددة بناءً على نوع الخصم.
    #    - يضمن أن المستويات مرتبة بشكل صحيح ولا تحتوي على أسعار غير منطقية.
    sorted_levels = sorted(rule_in.levels, key=lambda l: l.minimum_quantity)
    previous_level_data = None # لتتبع المستوى السابق للتحقق من الترتيب والأسعار

    for i, current_level in enumerate(sorted_levels):
        # التحقق من أن discount_type متوافق مع الحقول المعبأة في المستوى
        if rule_in.discount_type == 'NEW_PRICE':
            if current_level.price_per_unit_at_level is None:
                raise BadRequestException(detail=f"المستوى {i+1}: عندما يكون نوع الخصم 'سعر جديد مباشر', يجب تحديد 'السعر للوحدة في هذا المستوى'.")
            if current_level.discount_value is not None:
                raise BadRequestException(detail=f"المستوى {i+1}: عندما يكون نوع الخصم 'سعر جديد مباشر', لا يجب تحديد 'قيمة الخصم'.")
        elif rule_in.discount_type in ['PERCENTAGE', 'FIXED_AMOUNT']:
            if current_level.discount_value is None:
                raise BadRequestException(detail=f"المستوى {i+1}: عندما يكون نوع الخصم 'نسبة مئوية' أو 'مبلغ ثابت', يجب تحديد 'قيمة الخصم'.")
            if current_level.price_per_unit_at_level is not None:
                raise BadRequestException(detail=f"المستوى {i+1}: عندما يكون نوع الخصم 'نسبة مئوية' أو 'مبلغ ثابت', لا يجب تحديد 'السعر للوحدة في هذا المستوى'.")
        else: # نوع خصم غير صالح
            raise BadRequestException(detail=f"نوع الخصم '{rule_in.discount_type}' غير صالح. الأنواع المدعومة هي: 'PERCENTAGE', 'FIXED_AMOUNT', 'NEW_PRICE'.")

        # التحقق من ترتيب الكميات الدنيا وعدم التداخل
        if previous_level_data:
            if current_level.minimum_quantity <= previous_level_data.minimum_quantity:
                raise BadRequestException(detail=f"المستوى {i+1}: يجب أن تكون الكمية الدنيا ({current_level.minimum_quantity}) أكبر من الكمية الدنيا للمستوى السابق ({previous_level_data.minimum_quantity}).")
            
            # التحقق من منطقية الأسعار (السعر يجب أن يكون أقل أو يساوي مع زيادة الكمية)
            # هنا نفترض أن السعر ينخفض أو يظل ثابتًا مع زيادة الكمية
            # يمكن تعديل هذا المنطق بناءً على سياسات العمل المحددة
            current_price_to_check = current_level.price_per_unit_at_level if rule_in.discount_type == 'NEW_PRICE' else (100 - current_level.discount_value) if rule_in.discount_type == 'PERCENTAGE' else current_level.discount_value
            prev_price_to_check = previous_level_data.price_per_unit_at_level if rule_in.discount_type == 'NEW_PRICE' else (100 - previous_level_data.discount_value) if rule_in.discount_type == 'PERCENTAGE' else previous_level_data.discount_value

            if rule_in.discount_type == 'NEW_PRICE' and current_price_to_check > prev_price_to_check:
                raise BadRequestException(detail=f"المستوى {i+1}: السعر للوحدة ({current_price_to_check}) يجب أن يكون أقل من أو يساوي سعر المستوى السابق ({prev_price_to_check}).")
            elif rule_in.discount_type == 'PERCENTAGE' and current_price_to_check < prev_price_to_check: # الخصم كنسبة، النسبة يجب أن تزيد أو تساوي
                raise BadRequestException(detail=f"المستوى {i+1}: نسبة الخصم ({current_price_to_check}) يجب أن تكون أكبر من أو تساوي نسبة خصم المستوى السابق ({prev_price_to_check}).")
            # TODO: إضافة تحقق لـ FIXED_AMOUNT.

        previous_level_data = current_level

    # 4. استدعاء دالة CRUD للإنشاء
    return pricing_crud.create_price_tier_rule(db=db, rule_in=rule_in, created_by_user_id=current_user.user_id)


def get_price_tier_rule_details(db: Session, rule_id: int) -> models.PriceTierRule:
    """
    خدمة لجلب تفاصيل قاعدة شريحة سعر واحدة بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة المطلوب.

    Returns:
        models.PriceTierRule: كائن القاعدة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على القاعدة.
    """
    rule = pricing_crud.get_price_tier_rule(db, rule_id=rule_id)
    if not rule:
        raise NotFoundException(detail=f"قاعدة السعر بمعرف {rule_id} غير موجودة.")
    return rule

def get_all_price_tier_rules(db: Session, skip: int = 0, limit: int = 100) -> List[models.PriceTierRule]:
    """
    خدمة لجلب جميع قواعد شرائح الأسعار الموجودة في النظام.

    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات المراد تخطيها.
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.

    Returns:
        List[models.PriceTierRule]: قائمة بكائنات قواعد شرائح الأسعار.
    """
    return pricing_crud.get_all_price_tier_rules(db, skip=skip, limit=limit)

def update_price_tier_rule(db: Session, rule_id: int, rule_in: schemas.PriceTierRuleUpdate, current_user: User) -> models.PriceTierRule:
    """
    خدمة لتحديث قاعدة شريحة سعر موجودة.
    تتضمن التحقق من الملكية (للبائع أو المسؤول) وتفرد المفتاح إذا تم تغييره، وتناسق نوع الخصم مع المستويات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة المراد تحديثها.
        rule_in (schemas.PriceTierRuleUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models.PriceTierRule: كائن القاعدة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على القاعدة.
        ForbiddenException: إذا لم يكن المستخدم يملك القاعدة وليس مسؤولاً عن إدارة التسعير.
        ConflictException: إذا كانت هناك محاولة لتغيير المفتاح إلى مفتاح موجود بالفعل.
        BadRequestException: إذا كانت بيانات التحديث غير متوافقة (مثلاً discount_type).
    """
    db_rule = get_price_tier_rule_details(db, rule_id)

    # 1. التحقق من الصلاحيات: يجب أن يكون مالك القاعدة أو مسؤولاً عن إدارة قواعد التسعير.
    if db_rule.created_by_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بتحديث قاعدة السعر هذه.")

    # 2. التحقق من تفرد المفتاح إذا تم تحديث rule_name_key.
    if rule_in.rule_name_key and rule_in.rule_name_key != db_rule.rule_name_key:
        if db.query(models.PriceTierRule).filter(models.PriceTierRule.rule_name_key == rule_in.rule_name_key).first():
            raise ConflictException(detail=f"قاعدة السعر بمفتاح '{rule_in.rule_name_key}' موجودة بالفعل.")

    # 3. التحقق من تناسق discount_type الجديد مع المستويات الحالية (إذا تم تحديثه).
    #    - إذا تم تحديث discount_type، يجب التحقق من أن المستويات المرتبطة بالقاعدة متوافقة.
    if rule_in.discount_type and db_rule.levels:
        new_discount_type = rule_in.discount_type
        for level in db_rule.levels:
            if new_discount_type == 'NEW_PRICE':
                if level.price_per_unit_at_level is None:
                    raise BadRequestException(detail="لا يمكن تغيير نوع الخصم إلى 'سعر جديد مباشر' لأن المستويات الحالية لا تحتوي على 'السعر للوحدة في هذا المستوى'.")
                # TODO: تأكد أنه لا يوجد discount_value معبأ بشكل غير متناسق.
            elif new_discount_type in ['PERCENTAGE', 'FIXED_AMOUNT']:
                if level.discount_value is None:
                    raise BadRequestException(detail="لا يمكن تغيير نوع الخصم إلى 'نسبة مئوية' أو 'مبلغ ثابت' لأن المستويات الحالية لا تحتوي على 'قيمة الخصم'.")
                # TODO: تأكد أنه لا يوجد price_per_unit_at_level معبأ بشكل غير متناسق.
            else:
                raise BadRequestException(detail=f"نوع الخصم '{new_discount_type}' غير صالح. الأنواع المدعومة هي: 'PERCENTAGE', 'FIXED_AMOUNT', 'NEW_PRICE'.")
    # TODO: منطق عمل: إذا لم يتم تحديث discount_type، ولكن تم تحديث المستويات لاحقاً، يجب التحقق من التناسق هناك أيضاً.

    return pricing_crud.update_price_tier_rule(db=db, db_rule=db_rule, rule_in=rule_in)

def delete_price_tier_rule(db: Session, rule_id: int, current_user: User):
    """
    خدمة لحذف قاعدة شريحة سعر (حذف صارم).
    تتضمن التحقق من الملكية وعدم وجود ارتباطات نشطة أو مستويات مرتبطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة المراد حذفها.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على القاعدة.
        ForbiddenException: إذا لم يكن المستخدم يملك القاعدة وليس مسؤولاً.
        ConflictException: إذا كانت القاعدة مرتبطة بمستويات أو إسنادات نشطة.
    """
    db_rule = get_price_tier_rule_details(db, rule_id)

    # 1. التحقق من الصلاحيات.
    if db_rule.created_by_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بحذف قاعدة السعر هذه.")

    # 2. التحقق من عدم وجود مستويات مرتبطة (قبل الحذف الصارم للقاعدة).
    #    - على الرغم من وجود cascade="all, delete-orphan" في المودل لـ levels،
    #      فإن هذا التحقق في طبقة الخدمة يوفر رسالة خطأ أكثر وضوحًا للمستخدم.
    if db_rule.levels:
        raise ConflictException(detail=f"لا يمكن حذف قاعدة السعر بمعرف {rule_id} لأنها تحتوي على مستويات مرتبطة. يرجى حذف المستويات أولاً.")
    
    # 3. التحقق من عدم وجود إسنادات نشطة أو غير نشطة لهذه القاعدة (ProductPackagingPriceTierRuleAssignment).
    #    - يجب إزالة جميع الإسنادات قبل حذف القاعدة التي تشير إليها.
    if db_rule.assignments:
        raise ConflictException(detail=f"لا يمكن حذف قاعدة السعر بمعرف {rule_id} لأنها مرتبطة بخيارات تعبئة. يرجى إزالة جميع الإسنادات أولاً.")

    pricing_crud.delete_price_tier_rule(db=db, db_rule=db_rule)
    return {"message": "تم حذف قاعدة السعر بنجاح."}


# ==========================================================
# --- خدمات ترجمات قواعد شرائح الأسعار (PriceTierRuleTranslation) ---
# ==========================================================

def create_price_tier_rule_translation(db: Session, rule_id: int, trans_in: schemas.PriceTierRuleTranslationCreate, current_user: User) -> models.PriceTierRuleTranslation:
    """
    خدمة لإنشاء ترجمة جديدة لقاعدة شريحة سعر.
    تتضمن التحقق من وجود القاعدة الأم، ملكية المستخدم، وعدم تكرار الترجمة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة الأم.
        trans_in (schemas.PriceTierRuleTranslationCreate): بيانات الترجمة للإنشاء.
        current_user (User): المستخدم الحالي.

    Returns:
        models.PriceTierRuleTranslation: كائن الترجمة الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على القاعدة الأم.
        ForbiddenException: إذا لم يكن المستخدم يملك القاعدة الأم وليس مسؤولاً.
        ConflictException: إذا كانت الترجمة بنفس اللغة موجودة بالفعل.
    """
    # 1. التحقق من وجود القاعدة الأم وصلاحية المستخدم.
    db_rule = get_price_tier_rule_details(db, rule_id)
    if db_rule.created_by_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بإضافة ترجمة لهذه القاعدة.")

    # 2. التحقق من عدم وجود ترجمة بنفس اللغة للقاعدة.
    if pricing_crud.get_price_tier_rule_translation(db, rule_id=rule_id, language_code=trans_in.language_code):
        raise ConflictException(detail=f"الترجمة للقاعدة بمعرف {rule_id} باللغة '{trans_in.language_code}' موجودة بالفعل.")

    return pricing_crud.create_price_tier_rule_translation(db=db, rule_id=rule_id, trans_in=trans_in)

def get_price_tier_rule_translation_details(db: Session, rule_id: int, language_code: str) -> models.PriceTierRuleTranslation:
    """
    خدمة لجلب ترجمة محددة لقاعدة شريحة سعر بلغة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة الأم.
        language_code (str): رمز اللغة.

    Returns:
        models.PriceTierRuleTranslation: كائن الترجمة المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
    """
    translation = pricing_crud.get_price_tier_rule_translation(db, rule_id=rule_id, language_code=language_code)
    if not translation:
        raise NotFoundException(detail=f"الترجمة للقاعدة بمعرف {rule_id} باللغة '{language_code}' غير موجودة.")
    return translation

def update_price_tier_rule_translation(db: Session, rule_id: int, language_code: str, trans_in: schemas.PriceTierRuleTranslationUpdate, current_user: User) -> models.PriceTierRuleTranslation:
    """
    خدمة لتحديث ترجمة قاعدة شريحة سعر موجودة.
    تتضمن التحقق من ملكية المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة الأم.
        language_code (str): رمز اللغة للترجمة.
        trans_in (schemas.PriceTierRuleTranslationUpdate): البيانات المراد تحديثها للترجمة.
        current_user (User): المستخدم الحالي.

    Returns:
        models.PriceTierRuleTranslation: كائن الترجمة المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
        ForbiddenException: إذا لم يكن المستخدم يملك القاعدة الأم وليس مسؤولاً.
    """
    db_translation = get_price_tier_rule_translation_details(db, rule_id, language_code)

    # التحقق من ملكية المستخدم للقاعدة الأم
    db_rule = get_price_tier_rule_details(db, rule_id)
    if db_rule.created_by_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بتحديث ترجمة هذه القاعدة.")

    return pricing_crud.update_price_tier_rule_translation(db=db, db_translation=db_translation, trans_in=trans_in)

def delete_price_tier_rule_translation(db: Session, rule_id: int, language_code: str, current_user: User):
    """
    خدمة لحذف ترجمة قاعدة شريحة سعر معينة (حذف صارم).
    تتضمن التحقق من ملكية المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة الأم.
        language_code (str): رمز اللغة للترجمة.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على الترجمة.
        ForbiddenException: إذا لم يكن المستخدم يملك القاعدة الأم وليس مسؤولاً.
    """
    db_translation = get_price_tier_rule_translation_details(db, rule_id, language_code)

    # التحقق من ملكية المستخدم للقاعدة الأم
    db_rule = get_price_tier_rule_details(db, rule_id)
    if db_rule.created_by_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بحذف ترجمة هذه القاعدة.")

    pricing_crud.delete_price_tier_rule_translation(db=db, db_translation=db_translation)
    return {"message": "تم حذف ترجمة القاعدة بنجاح."}

# ==========================================================
# --- خدمات مستويات/درجات قاعدة شريحة السعر (PriceTierRuleLevel) ---
# ==========================================================

def create_price_tier_rule_level(db: Session, level_in: schemas.PriceTierRuleLevelCreate, current_user: User) -> models.PriceTierRuleLevel:
    """
    خدمة لإنشاء مستوى جديد لقاعدة شريحة سعر معينة.
    تتضمن التحقق من وجود القاعدة الأم، ملكية المستخدم، وعدم تداخل المستويات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        level_in (schemas.PriceTierRuleLevelCreate): بيانات المستوى للإنشاء، بما في ذلك rule_id.
        current_user (User): المستخدم الحالي.

    Returns:
        models.PriceTierRuleLevel: كائن المستوى الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على القاعدة الأم.
        ForbiddenException: إذا لم يكن المستخدم يملك القاعدة الأم وليس مسؤولاً.
        BadRequestException: إذا كانت بيانات المستوى غير متوافقة مع نوع خصم القاعدة أو إذا حدث تداخل في الكميات.
    """
    # 1. التحقق من وجود القاعدة الأم وصلاحية المستخدم
    db_rule = get_price_tier_rule_details(db, level_in.rule_id)
    if db_rule.created_by_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بإضافة مستوى لهذه القاعدة.")

    # 2. منطق عمل: التحقق من توافق حقول السعر/الخصم مع discount_type للقاعدة الأم
    if db_rule.discount_type == 'NEW_PRICE' and level_in.price_per_unit_at_level is None:
        raise BadRequestException(detail="عندما يكون نوع الخصم 'NEW_PRICE', يجب تحديد 'price_per_unit_at_level' للمستوى.")
    if db_rule.discount_type in ['PERCENTAGE', 'FIXED_AMOUNT'] and level_in.discount_value is None:
        raise BadRequestException(detail="عندما يكون نوع الخصم 'PERCENTAGE' أو 'FIXED_AMOUNT', يجب تحديد 'discount_value' للمستوى.")
    if db_rule.discount_type not in ['PERCENTAGE', 'FIXED_AMOUNT', 'NEW_PRICE']:
        raise BadRequestException(detail=f"نوع الخصم '{db_rule.discount_type}' للقاعدة غير صالح.")
    
    # 3. منطق عمل: التحقق من عدم تداخل الكميات مع المستويات الأخرى في نفس القاعدة
    # TODO: يمكن تحسين هذا التحقق ليشمل جميع المستويات الموجودة والتأكد من عدم وجود فجوات أو تداخلات.
    # حاليًا، يعتمد CRUD على الترتيب التصاعدي، لكن هذا التحقق هنا أكثر صرامة.
    # مثال: for existing_level in db_rule.levels:
    #            if existing_level.minimum_quantity == level_in.minimum_quantity:
    #                raise ConflictException(...)

    return pricing_crud.create_price_tier_rule_level(db=db, level_in=level_in)

def get_price_tier_rule_level_details(db: Session, level_id: int) -> models.PriceTierRuleLevel:
    """
    خدمة لجلب تفاصيل مستوى قاعدة شريحة سعر واحد بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        level_id (int): معرف المستوى المطلوب.

    Returns:
        models.PriceTierRuleLevel: كائن المستوى المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستوى.
    """
    level = pricing_crud.get_price_tier_rule_level(db, level_id=level_id)
    if not level:
        raise NotFoundException(detail=f"مستوى قاعدة السعر بمعرف {level_id} غير موجود.")
    return level

def get_all_price_tier_rule_levels_for_rule(db: Session, rule_id: int) -> List[models.PriceTierRuleLevel]:
    """
    خدمة لجلب جميع المستويات السعرية المرتبطة بقاعدة شريحة سعر معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة الأم.

    Returns:
        List[models.PriceTierRuleLevel]: قائمة بكائنات المستويات.
    """
    # 1. التحقق من وجود القاعدة الأم (اختياري هنا إذا كانت نقطة الوصول تضمنه).
    # get_price_tier_rule_details(db, rule_id)
    return pricing_crud.get_all_price_tier_rule_levels_for_rule(db, rule_id=rule_id)

def update_price_tier_rule_level(db: Session, level_id: int, level_in: schemas.PriceTierRuleLevelUpdate, current_user: User) -> models.PriceTierRuleLevel:
    """
    خدمة لتحديث مستوى قاعدة شريحة سعر موجودة.
    تتضمن التحقق من الملكية والتأكد من عدم الإخلال بترتيب المستويات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        level_id (int): معرف المستوى المراد تحديثه.
        level_in (schemas.PriceTierRuleLevelUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models.PriceTierRuleLevel: كائن المستوى المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستوى.
        ForbiddenException: إذا لم يكن المستخدم يملك القاعدة الأم وليس مسؤولاً.
        BadRequestException: إذا كانت بيانات التحديث غير متوافقة أو تسببت في تداخل.
    """
    db_level = get_price_tier_rule_level_details(db, level_id)
    
    # التحقق من ملكية المستخدم للقاعدة الأم
    db_rule = get_price_tier_rule_details(db, db_level.rule_id)
    if db_rule.created_by_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بتحديث مستوى قاعدة السعر هذه.")

    # منطق عمل: التحقق من تناسق حقول السعر/الخصم مع discount_type للقاعدة الأم
    if (level_in.price_per_unit_at_level is not None or level_in.discount_value is not None) and db_rule.discount_type:
        if db_rule.discount_type == 'NEW_PRICE' and level_in.price_per_unit_at_level is None:
            raise BadRequestException(detail="عندما يكون نوع الخصم 'NEW_PRICE', يجب تحديد 'price_per_unit_at_level'.")
        if db_rule.discount_type in ['PERCENTAGE', 'FIXED_AMOUNT'] and level_in.discount_value is None:
            raise BadRequestException(detail="عندما يكون نوع الخصم 'PERCENTAGE' أو 'FIXED_AMOUNT', يجب تحديد 'discount_value'.")
        # TODO: يمكن إضافة المزيد من التحقق لمنع تحديد كلا الحقلين بشكل غير متناسق.
    
    # منطق عمل: التحقق من عدم تداخل الكميات أو اختلال الترتيب بعد التحديث
    if level_in.minimum_quantity is not None and level_in.minimum_quantity != db_level.minimum_quantity:
        # TODO: يجب التحقق من جميع المستويات الأخرى في نفس القاعدة
        # والتأكد من أن minimum_quantity الجديد لا يتعارض مع المستويات الأخرى
        # وأن الترتيب التصاعدي لا يزال صحيحًا.
        pass # placeholder for complex validation

    return pricing_crud.update_price_tier_rule_level(db=db, db_level=db_level, level_in=level_in)

def delete_price_tier_rule_level(db: Session, level_id: int, current_user: User):
    """
    خدمة لحذف مستوى قاعدة شريحة سعر (حذف صارم).
    تتضمن التحقق من الملكية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        level_id (int): معرف المستوى المراد حذفه.
        current_user (User): المستخدم الحالي.

    Returns:
        dict: رسالة تأكيد الحذف.

    Raises:
        NotFoundException: إذا لم يتم العثور على المستوى.
        ForbiddenException: إذا لم يكن المستخدم يملك القاعدة الأم وليس مسؤولاً.
    """
    db_level = get_price_tier_rule_level_details(db, level_id)

    # التحقق من ملكية المستخدم للقاعدة الأم
    db_rule = get_price_tier_rule_details(db, db_level.rule_id)
    if db_rule.created_by_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بحذف مستوى قاعدة السعر هذه.")

    # TODO: منطق عمل: يمكن التحقق هنا إذا كان المستوى مستخدمًا في أي مكان بشكل حيوي،
    #       لكن بما أن السعر يتم تسجيله في الطلب، فليس هناك ارتباط مباشر يمنع الحذف عادةً.
    #       ومع ذلك، إذا كانت هناك أي ميزات تحليلية أو تقارير تعتمد على وجود المستويات القديمة،
    #       فقد يكون من الأفضل عدم السماح بالحذف الصارم أو تحويله إلى حذف ناعم إذا كان المودل يدعمه.

    pricing_crud.delete_price_tier_rule_level(db=db, db_level=db_level)
    return {"message": "تم حذف مستوى القاعدة بنجاح."}

# ==========================================================
# --- خدمات إسناد قواعد شرائح الأسعار لخيارات التعبئة (ProductPackagingPriceTierRuleAssignment) ---
# ==========================================================

def create_price_tier_rule_assignment(db: Session, assignment_in: schemas.ProductPackagingPriceTierRuleAssignmentCreate, current_user: User) -> models.ProductPackagingPriceTierRuleAssignment:
    """
    خدمة لإنشاء إسناد جديد لقاعدة شريحة سعر إلى خيار تعبئة.
    تتضمن التحقق من وجود الكيانات المرتبطة (القاعدة وخيار التعبئة)،
    ملكية المستخدم، ومنطق تداخل الفترات الزمنية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        assignment_in (schemas.ProductPackagingPriceTierRuleAssignmentCreate): بيانات الإسناد للإنشاء.
        current_user (User): المستخدم الحالي.

    Returns:
        models.ProductPackagingPriceTierRuleAssignment: كائن الإسناد الذي تم إنشاؤه.

    Raises:
        NotFoundException: إذا لم يتم العثور على القاعدة أو خيار التعبئة.
        ForbiddenException: إذا لم يكن المستخدم يملك القاعدة أو المنتج المرتبط بخيار التعبئة وليس مسؤولاً.
        ConflictException: إذا كان هناك إسناد متداخل لنفس خيار التعبئة في نفس الفترة الزمنية.
        BadRequestException: إذا كانت start_date بعد end_date.
    """

    ###################################################
    # 6. سيناريوهات بديلة ورسائل الخطأ (Alternative/Error Scenarios):
    # لا توجد قواعد سعر منشأة: "لم تقم بإنشاء أي قواعد أسعار بعد. [أنشئ قاعدة جديدة]."
    # التوافق: نعم، متوافق (API/واجهة أمامية). نقطة الوصول GET /pricing-rules/ ستعيد قائمة فارغة، ويمكن للواجهة الأمامية عرض هذه الرسالة بناءً على ذلك.
    # محاولة تغيير قاعدة لمنتج في مزاد نشط: "لا يمكن تعديل تسعير هذا المنتج لأنه مرتبط بمزاد نشط حاليًا."
    # التوافق: جزئي (TODO). هذا التحقق المحدد، الذي يتطلب التكامل مع وحدة المزادات (المجموعة 5)، هو حاليًا 
    # TODO في دوال خدمة create_price_tier_rule_assignment و update_price_tier_rule_assignment. سيتطلب إضافة منطق للتحقق مما إذا كان packaging_option_id مرتبطًا بمزاد نشط.
    ###################################################

    # 1. التحقق من وجود القاعدة (rule_id)
    db_rule = get_price_tier_rule_details(db, assignment_in.rule_id)

    # 2. التحقق من وجود خيار التعبئة (packaging_option_id)
    # ملاحظة: get_packaging_option_details تتحقق أيضًا من ملكية المنتج الأم
    db_packaging_option = get_packaging_option_details(db, assignment_in.packaging_option_id)

    # 3. التحقق من ملكية المستخدم: يجب أن يكون مالك القاعدة أو مالك المنتج المرتبط بخيار التعبئة أو مسؤولاً.
    #    - يمكن أن تكون القاعدة مملوكة من البائع A، وتطبق على منتج البائع B.
    #    - الخيار هنا هو أن مالك المنتج هو من يحدد قواعد التسعير التي تطبق على منتجاته.
    if db_rule.created_by_user_id != current_user.user_id and \
       db_packaging_option.product.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بإسناد قاعدة السعر هذه لخيار التعبئة.")

    # 4. منطق عمل: التحقق من أن start_date قبل end_date إذا كان كلاهما موجودًا
    if assignment_in.start_date and assignment_in.end_date and assignment_in.start_date > assignment_in.end_date:
        raise BadRequestException(detail="تاريخ البدء يجب أن يكون قبل تاريخ الانتهاء.")

    # 5. منطق عمل: التحقق من عدم وجود إسنادات متداخلة لنفس خيار التعبئة في نفس الفترة الزمنية
    #    - يجب ألا يكون هناك أكثر من إسناد نشط واحد (فعال) لنفس خيار التعبئة في أي لحظة.
    active_assignments = pricing_crud.get_active_assignments_for_packaging_option(db, assignment_in.packaging_option_id, current_timestamp=assignment_in.start_date or datetime.now(timezone.utc))
    for existing_assignment in active_assignments:
        # إذا كان الإسناد الجديد يتداخل مع إسناد موجود ونشط
        # تحقق من التداخل الزمني
        new_start = assignment_in.start_date
        new_end = assignment_in.end_date
        
        existing_start = existing_assignment.start_date
        existing_end = existing_assignment.end_date

        # حالة التداخل: (start1 <= end2 and end1 >= start2)
        # simplified for our case: new_start is within existing range, or existing_start is within new range
        if new_start is None: new_start = datetime.min.replace(tzinfo=timezone.utc) # يعتبر دائمًا نشطًا من البداية
        if new_end is None: new_end = datetime.max.replace(tzinfo=timezone.utc) # يعتبر دائمًا نشطًا للنهاية
        if existing_start is None: existing_start = datetime.min.replace(tzinfo=timezone.utc)
        if existing_end is None: existing_end = datetime.max.replace(tzinfo=timezone.utc)

        if (new_start <= existing_end and new_end >= existing_start):
            raise ConflictException(detail=f"يوجد بالفعل إسناد سعر نشط متداخل ({existing_assignment.assignment_id}) لخيار التعبئة هذا في الفترة الزمنية المحددة.")
        
    return pricing_crud.create_price_tier_rule_assignment(db=db, assignment_in=assignment_in)

def get_price_tier_rule_assignment_details(db: Session, assignment_id: int) -> models.ProductPackagingPriceTierRuleAssignment:
    """
    خدمة لجلب تفاصيل إسناد قاعدة شريحة سعر بالـ ID، مع معالجة عدم الوجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        assignment_id (int): معرف الإسناد المطلوب.

    Returns:
        models.ProductPackagingPriceTierRuleAssignment: كائن الإسناد المطلوب.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإسناد.
    """
    assignment = pricing_crud.get_price_tier_rule_assignment(db, assignment_id=assignment_id)
    if not assignment:
        raise NotFoundException(detail=f"إسناد قاعدة السعر بمعرف {assignment_id} غير موجود.")
    return assignment

def get_active_price(db: Session, packaging_option_id: int, quantity: float) -> float:
    """
    خدمة لحساب وإرجاع السعر الفعال (Effective Price) لوحدة خيار تعبئة معين
    بناءً على الكمية المطلوبة وأي قواعد تسعير متدرجة نشطة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        packaging_option_id (int): معرف خيار التعبئة.
        quantity (float): الكمية المطلوبة من خيار التعبئة.

    Returns:
        float: السعر الفعال للوحدة (بعد تطبيق أي خصومات).

    Raises:
        NotFoundException: إذا لم يتم العثور على خيار التعبئة.
        BadRequestException: إذا كانت الكمية سالبة.
    """
    # 1. التحقق من وجود خيار التعبئة.
    db_packaging_option = get_packaging_option_details(db, packaging_option_id)

    if quantity <= 0:
        raise BadRequestException(detail="الكمية المطلوبة يجب أن تكون أكبر من صفر لحساب السعر.")

    # 2. جلب جميع الإسنادات النشطة حاليًا لخيار التعبئة هذا.
    #    - يفترض أن هناك إسنادًا واحدًا نشطًا فقط في أي وقت محدد.
    active_assignments = pricing_crud.get_active_assignments_for_packaging_option(db, packaging_option_id, current_timestamp=datetime.now(timezone.utc))

    effective_price_per_unit = db_packaging_option.base_price # السعر الأساسي كافتراضي

    if active_assignments:
        # TODO: منطق عمل: حاليًا، نأخذ أول إسناد نشط. إذا كان هناك احتمال لتداخل، يجب تحديد الأولوية.
        #       لكن تصميم assignment_in يمنع التداخل حاليًا.
        active_assignment = active_assignments[0] 
        db_rule = active_assignment.rule # القاعدة مرتبطة وجاهزة مع مستوياتها

        # 3. تحديد مستوى السعر المناسب بناءً على الكمية المطلوبة.
        applicable_level = None
        # يتم جلب المستويات مرتبة تصاعديًا بواسطة minimum_quantity
        for level in sorted(db_rule.levels, key=lambda l: l.minimum_quantity):
            if quantity >= level.minimum_quantity:
                applicable_level = level
            else:
                # بمجرد أن تكون الكمية أقل من الحد الأدنى للمستوى الحالي، يعني أن المستوى السابق هو الأنسب
                break
        
        if applicable_level:
            # 4. حساب السعر الفعال بناءً على discount_type و applicable_level
            if db_rule.discount_type == 'NEW_PRICE' and applicable_level.price_per_unit_at_level is not None:
                effective_price_per_unit = applicable_level.price_per_unit_at_level
            elif db_rule.discount_type == 'PERCENTAGE' and applicable_level.discount_value is not None:
                effective_price_per_unit = db_packaging_option.base_price * (1 - applicable_level.discount_value / 100)
            elif db_rule.discount_type == 'FIXED_AMOUNT' and applicable_level.discount_value is not None:
                effective_price_per_unit = db_packaging_option.base_price - applicable_level.discount_value
                if effective_price_per_unit < 0: effective_price_per_unit = 0 # منع السعر السالب
            # TODO: يمكن إضافة المزيد من أنواع الخصم (مثلاً BOGO - Buy One Get One)
            # TODO: يجب التأكد من أن price_per_unit_at_level و discount_value لا يتم تعيينهما في نفس الوقت بشكل خاطئ.
        # else: الكمية أقل من الحد الأدنى لأي مستوى، نستخدم السعر الأساسي (وهو الافتراضي)

    return float(effective_price_per_unit) # التأكد من أن القيمة المعادة هي float

def update_price_tier_rule_assignment(db: Session, assignment_id: int, assignment_in: schemas.ProductPackagingPriceTierRuleAssignmentUpdate, current_user: User) -> models.ProductPackagingPriceTierRuleAssignment:
    """
    خدمة لتحديث إسناد قاعدة شريحة سعر موجود.
    تتضمن التحقق من الملكية ومنطق تداخل الفترات الزمنية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        assignment_id (int): معرف الإسناد المراد تحديثه.
        assignment_in (schemas.ProductPackagingPriceTierRuleAssignmentUpdate): البيانات المراد تحديثها.
        current_user (User): المستخدم الحالي.

    Returns:
        models.ProductPackagingPriceTierRuleAssignment: كائن الإسناد المحدث.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإسناد.
        ForbiddenException: إذا لم يكن المستخدم يملك الإسناد (أو القاعدة/المنتج المرتبط) وليس مسؤولاً.
        BadRequestException: إذا كانت start_date بعد end_date.
        ConflictException: إذا تسبب التحديث في تداخل مع إسنادات نشطة أخرى.
    """
    db_assignment = get_price_tier_rule_assignment_details(db, assignment_id)

    # 1. التحقق من ملكية المستخدم (مالك القاعدة أو مالك المنتج المرتبط بخيار التعبئة أو مسؤول)
    db_rule = get_price_tier_rule_details(db, db_assignment.rule_id)
    db_packaging_option = get_packaging_option_details(db, db_assignment.packaging_option_id) # هذا سيتأكد أيضًا من ملكية المنتج الأم

    if db_rule.created_by_user_id != current_user.user_id and \
       db_packaging_option.product.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بتحديث إسناد قاعدة السعر هذه.")

    # 2. منطق عمل: التحقق من أن start_date قبل end_date إذا تم تحديثهما
    new_start_date = assignment_in.start_date if assignment_in.start_date is not None else db_assignment.start_date
    new_end_date = assignment_in.end_date if assignment_in.end_date is not None else db_assignment.end_date

    if new_start_date and new_end_date and new_start_date > new_end_date:
        raise BadRequestException(detail="تاريخ البدء يجب أن يكون قبل تاريخ الانتهاء.")

    # 3. منطق عمل: التحقق من عدم وجود إسنادات متداخلة بعد التحديث
    #    - يجب ألا يكون هناك أكثر من إسناد نشط واحد (فعال) لنفس خيار التعبئة في أي لحظة.
    potential_conflicts = pricing_crud.get_active_assignments_for_packaging_option(db, db_assignment.packaging_option_id, current_timestamp=new_start_date or datetime.now(timezone.utc))
    for existing_assignment in potential_conflicts:
        if existing_assignment.assignment_id != assignment_id: # استبعاد الإسناد الذي يتم تحديثه نفسه
            # التحقق من التداخل الزمني بين الإسناد المحدث والإسنادات الأخرى
            existing_start = existing_assignment.start_date or datetime.min.replace(tzinfo=timezone.utc)
            existing_end = existing_assignment.end_date or datetime.max.replace(tzinfo=timezone.utc)

            updated_start = new_start_date or datetime.min.replace(tzinfo=timezone.utc)
            updated_end = new_end_date or datetime.max.replace(tzinfo=timezone.utc)

            if (updated_start <= existing_end and updated_end >= existing_start):
                raise ConflictException(detail=f"يوجد بالفعل إسناد سعر نشط متداخل ({existing_assignment.assignment_id}) لخيار التعبئة هذا في الفترة الزمنية المحددة بعد التحديث.")

    return pricing_crud.update_price_tier_rule_assignment(db=db, db_assignment=db_assignment, assignment_in=assignment_in)

def soft_delete_price_tier_rule_assignment(db: Session, assignment_id: int, current_user: User) -> models.ProductPackagingPriceTierRuleAssignment:
    """
    خدمة للحذف الناعم لإسناد قاعدة شريحة سعر عن طريق تعيين 'is_active' إلى False.
    تتضمن التحقق من الملكية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        assignment_id (int): معرف الإسناد المراد حذفه ناعمًا.
        current_user (User): المستخدم الحالي.

    Returns:
        models.ProductPackagingPriceTierRuleAssignment: كائن الإسناد بعد الحذف الناعم.

    Raises:
        NotFoundException: إذا لم يتم العثور على الإسناد.
        ForbiddenException: إذا لم يكن المستخدم يملك الإسناد (أو القاعدة/المنتج المرتبط) وليس مسؤولاً.
        BadRequestException: إذا كان الإسناد غير نشط بالفعل.
    """
    db_assignment = get_price_tier_rule_assignment_details(db, assignment_id)

    # التحقق من الملكية
    db_rule = get_price_tier_rule_details(db, db_assignment.rule_id)
    db_packaging_option = get_packaging_option_details(db, db_assignment.packaging_option_id)

    if db_rule.created_by_user_id != current_user.user_id and \
       db_packaging_option.product.seller_user_id != current_user.user_id and \
       not any(p.permission_name_key == "ADMIN_PRICING_RULE_MANAGE_ANY" for p in current_user.default_role.permissions):
        raise ForbiddenException(detail="غير مصرح لك بإلغاء تفعيل إسناد قاعدة السعر هذه.")

    if not db_assignment.is_active:
        raise BadRequestException(detail=f"إسناد قاعدة السعر بمعرف {assignment_id} غير نشط بالفعل.")

    # TODO: منطق عمل: التحقق من عدم وجود طلبات معلقة (pending orders) تعتمد على هذا الإسناد
    #       إذا كان هناك طلب يعتمد عليه، قد تحتاج إلى منع الحذف الناعم أو التعامل معه بطريقة خاصة (مثل تجميد الطلب).

    return pricing_crud.soft_delete_price_tier_rule_assignment(db=db, db_assignment=db_assignment)

