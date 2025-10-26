# backend\src\pricing\crud\pricing_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز (بناءً على التسمية الجديدة للملف)
from src.pricing.models import tier_pricing_models as models
# استيراد الـ Schemas (بناءً على التسمية الجديدة للملف)
from src.pricing.schemas import pricing_schemas as schemas


# ==========================================================
# --- CRUD Functions for PriceTierRule (قواعد شرائح الأسعار) ---
# ==========================================================

def create_price_tier_rule(db: Session, rule_in: schemas.PriceTierRuleCreate, created_by_user_id: Optional[UUID] = None) -> models.PriceTierRule:
    """
    ينشئ قاعدة شريحة سعر جديدة في قاعدة البيانات.
    يقوم أيضًا بإنشاء الترجمات والمستويات السعرية المضمنة في الـ schema (إذا وجدت).

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_in (schemas.PriceTierRuleCreate): بيانات القاعدة للإنشاء، بما في ذلك الترجمات والمستويات.
        created_by_user_id (Optional[UUID]): معرف المستخدم الذي أنشأ القاعدة.

    Returns:
        models.PriceTierRule: كائن القاعدة الذي تم إنشاؤه.
    """
    db_rule = models.PriceTierRule(
        rule_name_key=rule_in.rule_name_key,
        description_key=rule_in.description_key,
        discount_type=rule_in.discount_type,
        created_by_user_id=created_by_user_id
    )
    db.add(db_rule)
    db.flush() # ضروري للحصول على rule_id قبل حفظ الترجمات والمستويات المرتبطة.

    # إضافة الترجمات المضمنة (nested translations)
    if rule_in.translations:
        for trans_in in rule_in.translations:
            db_translation = models.PriceTierRuleTranslation(
                rule_id=db_rule.rule_id,
                language_code=trans_in.language_code,
                translated_rule_name=trans_in.translated_rule_name,
                translated_description=trans_in.translated_description
            )
            db.add(db_translation)

    # إضافة المستويات السعرية المضمنة (nested levels)
    if rule_in.levels:
        for level_in in rule_in.levels:
            db_level = models.PriceTierRuleLevel(
                rule_id=db_rule.rule_id,
                minimum_quantity=level_in.minimum_quantity,
                price_per_unit_at_level=level_in.price_per_unit_at_level,
                discount_value=level_in.discount_value,
                level_description_key=level_in.level_description_key
            )
            db.add(db_level)
            
    db.commit() # حفظ التغييرات بالكامل (القاعدة والترجمات والمستويات).
    db.refresh(db_rule) # تحديث الكائن ليعكس البيانات من قاعدة البيانات.
    return db_rule

def get_price_tier_rule(db: Session, rule_id: int) -> Optional[models.PriceTierRule]:
    """
    يجلب قاعدة شريحة سعر واحدة بالـ ID الخاص بها.
    يتضمن جلب ترجماتها ومستوياتها لتقليل استعلامات قاعدة البيانات (N+1 problem).

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة المطلوب.

    Returns:
        Optional[models.PriceTierRule]: كائن القاعدة أو None إذا لم يتم العثور عليه.
    """
    return db.query(models.PriceTierRule).options(
        joinedload(models.PriceTierRule.translations), # تحميل الترجمات المرتبطة.
        joinedload(models.PriceTierRule.levels) # تحميل المستويات المرتبطة.
    ).filter(models.PriceTierRule.rule_id == rule_id).first()

def get_all_price_tier_rules(db: Session, skip: int = 0, limit: int = 100) -> List[models.PriceTierRule]:
    """
    يجلب قائمة بجميع قواعد شرائح الأسعار الموجودة في النظام.

    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات المراد تخطيها (للترقيم).
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها (للترقيم).

    Returns:
        List[models.PriceTierRule]: قائمة بكائنات قواعد شرائح الأسعار.
    """
    return db.query(models.PriceTierRule).options(
        joinedload(models.PriceTierRule.translations),
        joinedload(models.PriceTierRule.levels)
    ).offset(skip).limit(limit).all()

def update_price_tier_rule(db: Session, db_rule: models.PriceTierRule, rule_in: schemas.PriceTierRuleUpdate) -> models.PriceTierRule:
    """
    يحدث بيانات قاعدة شريحة سعر موجودة.
    يتم تحديث فقط الحقول المتوفرة في 'rule_in'.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_rule (models.PriceTierRule): كائن القاعدة من قاعدة البيانات المراد تحديثه.
        rule_in (schemas.PriceTierRuleUpdate): البيانات المراد تحديثها.

    Returns:
        models.PriceTierRule: كائن القاعدة المحدث.
    """
    update_data = rule_in.model_dump(exclude_unset=True) # استبعاد الحقول غير المحددة (None) من التحديث.
    for key, value in update_data.items():
        setattr(db_rule, key, value) # تحديث كل حقل.
    db.add(db_rule) # إضافة الكائن إلى الجلسة لتتبع التغييرات.
    db.commit() # حفظ التغييرات في قاعدة البيانات.
    db.refresh(db_rule) # تحديث الكائن ليعكس البيانات من قاعدة البيانات بعد التغيير.
    return db_rule

def delete_price_tier_rule(db: Session, db_rule: models.PriceTierRule):
    """
    يحذف قاعدة شريحة سعر معينة (حذف صارم).
    TODO: التحقق من عدم وجود إسنادات نشطة (ProductPackagingPriceTierRuleAssignment) أو مستويات (PriceTierRuleLevel) مرتبطة بهذه القاعدة سيتم في طبقة الخدمة لمنع مشاكل سلامة البيانات.
    """
    db.delete(db_rule) # حذف الكائن من قاعدة البيانات.
    db.commit() # تأكيد الحذف.
    return

# ==========================================================
# --- CRUD Functions for PriceTierRuleTranslation (ترجمات قواعد شرائح الأسعار) ---
# ==========================================================

def create_price_tier_rule_translation(db: Session, rule_id: int, trans_in: schemas.PriceTierRuleTranslationCreate) -> models.PriceTierRuleTranslation:
    """
    ينشئ ترجمة جديدة لقاعدة شريحة سعر معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة الأم التي تنتمي إليها هذه الترجمة.
        trans_in (schemas.PriceTierRuleTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.PriceTierRuleTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models.PriceTierRuleTranslation(
        rule_id=rule_id,
        language_code=trans_in.language_code,
        translated_rule_name=trans_in.translated_rule_name,
        translated_description=trans_in.translated_description
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_price_tier_rule_translation(db: Session, rule_id: int, language_code: str) -> Optional[models.PriceTierRuleTranslation]:
    """
    يجلب ترجمة قاعدة شريحة سعر محددة بالـ ID الخاص بالقاعدة ورمز اللغة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة.
        language_code (str): رمز اللغة (مثلاً: 'ar', 'en').

    Returns:
        Optional[models.PriceTierRuleTranslation]: كائن الترجمة أو None إذا لم يتم العثور عليها.
    """
    return db.query(models.PriceTierRuleTranslation).filter(
        and_(
            models.PriceTierRuleTranslation.rule_id == rule_id,
            models.PriceTierRuleTranslation.language_code == language_code
        )
    ).first()

def update_price_tier_rule_translation(db: Session, db_translation: models.PriceTierRuleTranslation, trans_in: schemas.PriceTierRuleTranslationUpdate) -> models.PriceTierRuleTranslation:
    """
    يحدث ترجمة قاعدة شريحة سعر موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.PriceTierRuleTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.PriceTierRuleTranslationUpdate): البيانات المراد تحديثها للترجمة.

    Returns:
        models.PriceTierRuleTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_price_tier_rule_translation(db: Session, db_translation: models.PriceTierRuleTranslation):
    """
    يحذف ترجمة قاعدة شريحة سعر معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.PriceTierRuleTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for PriceTierRuleLevel (مستويات/درجات قاعدة شريحة السعر) ---
# ==========================================================

def create_price_tier_rule_level(db: Session, level_in: schemas.PriceTierRuleLevelCreate) -> models.PriceTierRuleLevel:
    """
    ينشئ مستوى جديد لقاعدة شريحة سعر معينة في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        level_in (schemas.PriceTierRuleLevelCreate): بيانات المستوى الجديد للإنشاء، بما في ذلك rule_id.

    Returns:
        models.PriceTierRuleLevel: كائن المستوى الذي تم إنشاؤه.
    """
    db_level = models.PriceTierRuleLevel(
        rule_id=level_in.rule_id,
        minimum_quantity=level_in.minimum_quantity,
        price_per_unit_at_level=level_in.price_per_unit_at_level,
        discount_value=level_in.discount_value,
        level_description_key=level_in.level_description_key
    )
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    return db_level

def get_price_tier_rule_level(db: Session, level_id: int) -> Optional[models.PriceTierRuleLevel]:
    """
    يجلب مستوى قاعدة شريحة سعر واحد بالـ ID الخاص به.

    Args:
        db (Session): جلسة قاعدة البيانات.
        level_id (int): معرف المستوى المطلوب.

    Returns:
        Optional[models.PriceTierRuleLevel]: كائن المستوى أو None إذا لم يتم العثور عليه.
    """
    return db.query(models.PriceTierRuleLevel).filter(models.PriceTierRuleLevel.level_id == level_id).first()

def get_all_price_tier_rule_levels_for_rule(db: Session, rule_id: int) -> List[models.PriceTierRuleLevel]:
    """
    يجلب جميع المستويات السعرية المرتبطة بقاعدة شريحة سعر معينة.
    يتم ترتيب المستويات تصاعديًا حسب الحد الأدنى للكمية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        rule_id (int): معرف القاعدة التي تنتمي إليها المستويات.

    Returns:
        List[models.PriceTierRuleLevel]: قائمة بكائنات المستويات.
    """
    return db.query(models.PriceTierRuleLevel).filter(models.PriceTierRuleLevel.rule_id == rule_id).order_by(models.PriceTierRuleLevel.minimum_quantity).all()

def update_price_tier_rule_level(db: Session, db_level: models.PriceTierRuleLevel, level_in: schemas.PriceTierRuleLevelUpdate) -> models.PriceTierRuleLevel:
    """
    يحدث بيانات مستوى قاعدة شريحة سعر موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_level (models.PriceTierRuleLevel): كائن المستوى من قاعدة البيانات المراد تحديثه.
        level_in (schemas.PriceTierRuleLevelUpdate): البيانات المراد تحديثها.

    Returns:
        models.PriceTierRuleLevel: كائن المستوى المحدث.
    """
    update_data = level_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_level, key, value)
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    return db_level

def delete_price_tier_rule_level(db: Session, db_level: models.PriceTierRuleLevel):
    """
    يحذف مستوى قاعدة شريحة سعر معينة (حذف صارم).
    TODO: التحقق من عدم وجود ارتباطات حيوية (لا يتوقع أن تكون هناك بشكل مباشر من جداول العمليات) سيتم في طبقة الخدمة.
          قد تكون هذه المستويات مرتبطة منطقيًا بأسعار تم تطبيقها في طلبات سابقة، ولكن السعر النهائي يُحفظ في سجل الطلب.
    """
    db.delete(db_level)
    db.commit()
    return

# ==========================================================
# --- CRUD Functions for ProductPackagingPriceTierRuleAssignment (إسناد القواعد لخيارات التعبئة) ---
# ==========================================================

def create_price_tier_rule_assignment(db: Session, assignment_in: schemas.ProductPackagingPriceTierRuleAssignmentCreate) -> models.ProductPackagingPriceTierRuleAssignment:
    """
    ينشئ إسنادًا جديدًا لقاعدة شريحة سعر إلى خيار تعبئة في قاعدة البيانات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        assignment_in (schemas.ProductPackagingPriceTierRuleAssignmentCreate): بيانات الإسناد للإنشاء.

    Returns:
        models.ProductPackagingPriceTierRuleAssignment: كائن الإسناد الذي تم إنشاؤه.
    """
    db_assignment = models.ProductPackagingPriceTierRuleAssignment(
        packaging_option_id=assignment_in.packaging_option_id,
        rule_id=assignment_in.rule_id,
        start_date=assignment_in.start_date,
        end_date=assignment_in.end_date,
        is_active=assignment_in.is_active
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

def get_price_tier_rule_assignment(db: Session, assignment_id: int) -> Optional[models.ProductPackagingPriceTierRuleAssignment]:
    """
    يجلب إسناد قاعدة شريحة سعر واحد بالـ ID الخاص به.
    يتضمن جلب القاعدة وخيار التعبئة المرتبطين لتحسين الأداء.

    Args:
        db (Session): جلسة قاعدة البيانات.
        assignment_id (int): معرف الإسناد المطلوب.

    Returns:
        Optional[models.ProductPackagingPriceTierRuleAssignment]: كائن الإسناد أو None إذا لم يتم العثور عليه.
    """
    return db.query(models.ProductPackagingPriceTierRuleAssignment).options(
        joinedload(models.ProductPackagingPriceTierRuleAssignment.rule), # تحميل القاعدة
        joinedload(models.ProductPackagingPriceTierRuleAssignment.packaging_option) # تحميل خيار التعبئة
    ).filter(models.ProductPackagingPriceTierRuleAssignment.assignment_id == assignment_id).first()

def get_active_assignments_for_packaging_option(db: Session, packaging_option_id: int, current_timestamp: Optional[datetime] = None) -> List[models.ProductPackagingPriceTierRuleAssignment]:
    """
    يجلب جميع الإسنادات النشطة حاليًا لخيار تعبئة معين.
    يتم تحديد النشاط بناءً على حقل 'is_active' وتواريخ البدء والانتهاء.

    Args:
        db (Session): جلسة قاعدة البيانات.
        packaging_option_id (int): معرف خيار التعبئة.
        current_timestamp (Optional[datetime]): الطابع الزمني الحالي للاعتبار (افتراضيًا الوقت الحالي).

    Returns:
        List[models.ProductPackagingPriceTierRuleAssignment]: قائمة بكائنات الإسنادات النشطة.
    """
    if current_timestamp is None:
        current_timestamp = datetime.now(datetime.timezone.utc) # استخدام الوقت العالمي المنسق

    query = db.query(models.ProductPackagingPriceTierRuleAssignment).options(
        joinedload(models.ProductPackagingPriceTierRuleAssignment.rule).joinedload(models.PriceTierRule.levels) # تحميل القاعدة ومستوياتها لسهولة الوصول إليها
    ).filter(
        models.ProductPackagingPriceTierRuleAssignment.packaging_option_id == packaging_option_id,
        models.ProductPackagingPriceTierRuleAssignment.is_active == True,
        models.ProductPackagingPriceTierRuleAssignment.start_date <= current_timestamp # تاريخ البدء قبل أو يساوي الوقت الحالي
    )
    # إذا كان هناك تاريخ انتهاء، يجب أن يكون الوقت الحالي قبله أو يساويه
    query = query.filter(
        (models.ProductPackagingPriceTierRuleAssignment.end_date == None) | # أو لا يوجد تاريخ انتهاء
        (models.ProductPackagingPriceTierRuleAssignment.end_date >= current_timestamp)
    )
    return query.all()

def update_price_tier_rule_assignment(db: Session, db_assignment: models.ProductPackagingPriceTierRuleAssignment, assignment_in: schemas.ProductPackagingPriceTierRuleAssignmentUpdate) -> models.ProductPackagingPriceTierRuleAssignment:
    """
    يحدث بيانات إسناد قاعدة شريحة سعر موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_assignment (models.ProductPackagingPriceTierRuleAssignment): كائن الإسناد من قاعدة البيانات المراد تحديثه.
        assignment_in (schemas.ProductPackagingPriceTierRuleAssignmentUpdate): البيانات المراد تحديثها.

    Returns:
        models.ProductPackagingPriceTierRuleAssignment: كائن الإسناد المحدث.
    """
    update_data = assignment_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_assignment, key, value)
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

def soft_delete_price_tier_rule_assignment(db: Session, db_assignment: models.ProductPackagingPriceTierRuleAssignment) -> models.ProductPackagingPriceTierRuleAssignment:
    """
    يقوم بالحذف الناعم لإسناد قاعدة شريحة سعر عن طريق تعيين 'is_active' إلى False.
    TODO: التحقق من عدم وجود طلبات معلقة (pending orders) تعتمد على هذا الإسناد قبل إلغاء تفعيله.
    """
    db_assignment.is_active = False
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment
