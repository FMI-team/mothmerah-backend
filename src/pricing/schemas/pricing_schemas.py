# backend\src\products\schemas\pricing_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID # لـ product_packaging_option_id

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas أخرى
# LanguageRead تستورد الآن من src.lookups.schemas
from src.lookups.schemas import LanguageRead # <-- تم التعديل هنا

# TODO: تأكد من أن ProductPackagingOptionRead موجودة ومستوردة
# from src.products.schemas.packaging_schemas import ProductPackagingOptionRead

# ==========================================================
# --- Schemas لقواعد شرائح الأسعار (PriceTierRule) ---
#    (جدول: price_tier_rules)
# ==========================================================
class PriceTierRuleBase(BaseModel):
    """
    النموذج الأساسي لبيانات قاعدة شريحة السعر.
    يحدد الحقول الأساسية التي تصف بها القاعدة (مثل اسم القاعدة، الوصف، ونوع الخصم).
    """
    rule_name_key: str = Field(..., max_length=100, description="مفتاح فريد لاسم القاعدة يُستخدم للترجمة.")
    description_key: Optional[str] = Field(None, max_length=255, description="مفتاح لوصف القاعدة يُستخدم للترجمة.")
    discount_type: Optional[str] = Field(
        None,
        max_length=20,
        description="نوع الخصم الذي تطبقه هذه القاعدة (مثلاً: 'PERCENTAGE' نسبة مئوية، 'FIXED_AMOUNT' مبلغ ثابت، 'NEW_PRICE' سعر جديد مباشر لكل وحدة)."
    )
    # created_by_user_id و created_at و updated_at تُدار تلقائيًا بواسطة النظام أو في طبقة الخدمة.

class PriceTierRuleCreate(PriceTierRuleBase):
    """
    نموذج بيانات لإنشاء قاعدة شريحة سعر جديدة.
    يتضمن الحقول الأساسية بالإضافة إلى إمكانية تضمين الترجمات الأولية والمستويات السعرية مباشرة عند الإنشاء.
    """
    translations: Optional[List["PriceTierRuleTranslationCreate"]] = Field(
        [],
        description="قائمة بالترجمات الأولية لاسم القاعدة ووصفها. يجب توفير ترجمة افتراضية."
    )
    levels: Optional[List["PriceTierRuleLevelCreate"]] = Field(
        [],
        description="قائمة بالمستويات السعرية الأولية لهذه القاعدة (مثلاً: حد أدنى للكمية وسعر مقابل)."
    )
    # TODO: منطق عمل: في طبقة الخدمة، يجب التحقق من أن:
    # 1. translations تحتوي على ترجمة افتراضية (مثلاً العربية) إذا كانت القاعدة تُعرض للمستخدم.
    # 2. levels (المستويات) لا تتداخل فيما بينها من حيث الكميات.
    # 3. levels مرتبة تصاعديًا بناءً على minimum_quantity.
    # 4. discount_type متوافق مع الحقول المعبأة في PriceTierRuleLevelCreate (مثلاً إذا كان 'NEW_PRICE' يجب أن يكون price_per_unit_at_level موجودًا).

class PriceTierRuleUpdate(BaseModel):
    """
    نموذج بيانات لتحديث قاعدة شريحة سعر موجودة.
    جميع الحقول اختيارية، مما يسمح بتحديث جزئي لخصائص القاعدة.
    """
    rule_name_key: Optional[str] = Field(None, max_length=100, description="تحديث مفتاح اسم القاعدة.")
    description_key: Optional[str] = Field(None, max_length=255, description="تحديث مفتاح وصف القاعدة.")
    discount_type: Optional[str] = Field(None, max_length=20, description="تحديث نوع الخصم.")
    # TODO: منطق عمل: في طبقة الخدمة، عند تحديث discount_type، يجب التحقق من أن المستويات الحالية متوافقة
    # أو مطالبة البائع بتحديث المستويات.

class PriceTierRuleRead(PriceTierRuleBase):
    """
    نموذج بيانات لقراءة وعرض تفاصيل قاعدة شريحة السعر.
    يتضمن معرف القاعدة، منشئها، الطوابع الزمنية، والترجمات والمستويات المدمجة.
    """
    rule_id: int = Field(..., description="المعرف الفريد لقاعدة شريحة السعر.")
    created_by_user_id: Optional[UUID] = Field(None, description="معرف المستخدم الذي أنشأ القاعدة.")
    created_at: datetime = Field(..., description="تاريخ ووقت إنشاء القاعدة.")
    updated_at: datetime = Field(..., description="تاريخ ووقت آخر تحديث للقاعدة.")
    translations: List["PriceTierRuleTranslationRead"] = Field(
        [],
        description="قائمة بالترجمات المتاحة لاسم القاعدة ووصفها."
    )
    levels: List["PriceTierRuleLevelRead"] = Field(
        [],
        description="قائمة بالمستويات السعرية المرتبطة بهذه القاعدة."
    )
    model_config = ConfigDict(from_attributes=True) # لتمكين التحويل من كائن SQLAlchemy إلى Pydantic.


# ==========================================================
# --- Schemas لترجمات قواعد شرائح الأسعار (PriceTierRuleTranslation) ---
#    (جدول: price_tier_rule_translations)
# ==========================================================
class PriceTierRuleTranslationBase(BaseModel):
    """
    النموذج الأساسي لبيانات ترجمة قاعدة شريحة السعر.
    """
    language_code: str = Field(..., max_length=10, description="رمز اللغة للترجمة (مثلاً: 'ar', 'en').")
    translated_rule_name: str = Field(..., max_length=150, description="الاسم المترجم للقاعدة في هذه اللغة.")
    translated_description: Optional[str] = Field(None, description="الوصف المترجم للقاعدة في هذه اللغة.")

class PriceTierRuleTranslationCreate(PriceTierRuleTranslationBase):
    """
    نموذج بيانات لإنشاء ترجمة جديدة لقاعدة شريحة سعر.
    """
    pass

class PriceTierRuleTranslationUpdate(BaseModel):
    """
    نموذج بيانات لتحديث ترجمة قاعدة شريحة سعر موجودة.
    جميع الحقول اختيارية، مما يسمح بتحديث جزئي للترجمة.
    """
    translated_rule_name: Optional[str] = Field(None, max_length=150)
    translated_description: Optional[str] = Field(None)

class PriceTierRuleTranslationRead(PriceTierRuleTranslationBase):
    """
    نموذج بيانات لقراءة وعرض ترجمة قاعدة شريحة سعر.
    """
    rule_id: int = Field(..., description="معرف القاعدة الأم المرتبطة بهذه الترجمة.")
    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# --- Schemas لمستويات/درجات قاعدة شريحة السعر (PriceTierRuleLevel) ---
#    (جدول: price_tier_rule_levels)
# ==========================================================
class PriceTierRuleLevelBase(BaseModel):
    """
    النموذج الأساسي لبيانات مستوى/درجة قاعدة شريحة السعر.
    يحدد الحد الأدنى للكمية والسعر/الخصم المرتبط بهذا المستوى.
    """
    minimum_quantity: float = Field(
        ...,
        gt=0, # يجب أن تكون الكمية الدنيا أكبر من صفر.
        description="الحد الأدنى للكمية المطلوبة لتطبيق هذا المستوى السعري (مثلاً: 10 كرتون)."
    )
    price_per_unit_at_level: Optional[float] = Field(
        None,
        ge=0, # السعر يجب أن يكون أكبر من أو يساوي صفر.
        description="السعر الجديد للوحدة عند تطبيق هذا المستوى (يُستخدم إذا كان نوع الخصم للقاعدة الأم هو 'NEW_PRICE')."
    )
    discount_value: Optional[float] = Field(
        None,
        ge=0, # قيمة الخصم يجب أن تكون أكبر من أو تساوي صفر.
        description="قيمة الخصم (مبلغ أو نسبة مئوية، تُستخدم إذا كان نوع الخصم للقاعدة الأم هو 'PERCENTAGE' أو 'FIXED_AMOUNT')."
    )
    level_description_key: Optional[str] = Field(
        None,
        max_length=255,
        description="مفتاح لوصف المستوى (مثلاً: 'خصم 10-19 وحدة') يُستخدم للترجمة."
    )
    # TODO: منطق عمل: في طبقة الخدمة، يجب التحقق من أن:
    # 1. أحد الحقلين (price_per_unit_at_level أو discount_value) موجود بناءً على discount_type للقاعدة الأم.
    # 2. ليس كلاهما موجودًا في نفس الوقت، أو يتم تحديد أولوية واضحة.
    # 3. minimum_quantity لهذا المستوى أكبر من minimum_quantity للمستوى السابق في نفس القاعدة (إذا كان هناك ترتيب).

class PriceTierRuleLevelCreate(PriceTierRuleLevelBase):
    """
    نموذج بيانات لإنشاء مستوى/درجة سعر جديدة لقاعدة معينة.
    """
    rule_id: int = Field(..., description="معرف القاعدة التي ينتمي إليها هذا المستوى السعري.")

class PriceTierRuleLevelUpdate(BaseModel):
    """
    نموذج بيانات لتحديث مستوى/درجة سعر موجودة.
    جميع الحقول اختيارية، مما يسمح بالتحديث الجزئي.
    """
    minimum_quantity: Optional[float] = Field(None, gt=0)
    price_per_unit_at_level: Optional[float] = Field(None, ge=0)
    discount_value: Optional[float] = Field(None, ge=0)
    level_description_key: Optional[str] = Field(None, max_length=255)
    # TODO: منطق عمل: في طبقة الخدمة، عند تحديث مستوى، يجب التحقق من عدم تداخل الكميات مع مستويات أخرى في نفس القاعدة
    # وأن الترتيب المنطقي للكميات الدنيا لم يعد مختلاً.

class PriceTierRuleLevelRead(PriceTierRuleLevelBase):
    """
    نموذج بيانات لقراءة وعرض تفاصيل مستوى/درجة قاعدة شريحة السعر.
    يتضمن المعرف الفريد للمستوى، معرف القاعدة الأم، والطوابع الزمنية.
    """
    level_id: int
    rule_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لإسناد قواعد شرائح الأسعار لخيارات التعبئة (ProductPackagingPriceTierRuleAssignment) ---
#    (جدول: product_packaging_price_tier_rule_assignments)
# ==========================================================
class ProductPackagingPriceTierRuleAssignmentBase(BaseModel):
    """
    النموذج الأساسي لبيانات إسناد قاعدة سعر متدرج لخيار تعبئة.
    هذا الإسناد هو الذي يربط قاعدة التسعير الديناميكي بمنتج معين.
    """
    packaging_option_id: int = Field(
        ...,
        description="معرف خيار التعبئة والتغليف المرتبط بهذه القاعدة (من المجموعة 2.ج)."
    )
    rule_id: int = Field(
        ...,
        description="معرف قاعدة شريحة السعر المرتبطة."
    )
    start_date: Optional[datetime] = Field(
        None,
        description="تاريخ ووقت بداية تفعيل هذا الإسناد (للعروض المؤقتة أو الموسمية)."
    )
    end_date: Optional[datetime] = Field(
        None,
        description="تاريخ ووقت نهاية تفعيل هذا الإسناد."
    )
    is_active: bool = Field(
        True,
        description="هل هذا الإسناد نشط حاليًا؟ يُستخدم للحذف الناعم أو لتفعيل/إلغاء تفعيل مؤقت."
    )
    # TODO: منطق عمل: في طبقة الخدمة، يجب التحقق من أن:
    # 1. start_date يأتي قبل end_date إذا كان كلاهما موجودًا.
    # 2. لا توجد إسنادات متداخلة لنفس packaging_option_id في نفس الفترة الزمنية (إذا كانت قواعد التداخل ممنوعة).

class ProductPackagingPriceTierRuleAssignmentCreate(ProductPackagingPriceTierRuleAssignmentBase):
    """
    نموذج بيانات لإنشاء إسناد قاعدة سعر متدرج جديد لخيار تعبئة.
    """
    pass

class ProductPackagingPriceTierRuleAssignmentUpdate(BaseModel):
    """
    نموذج بيانات لتحديث إسناد قاعدة سعر متدرج موجود.
    جميع الحقول اختيارية. لا يمكن تغيير 'packaging_option_id' أو 'rule_id' بعد الإنشاء.
    """
    start_date: Optional[datetime] = Field(None, description="تحديث تاريخ بداية التفعيل.")
    end_date: Optional[datetime] = Field(None, description="تحديث تاريخ نهاية التفعيل.")
    is_active: Optional[bool] = Field(None, description="تحديث حالة تفعيل الإسناد.")
    # TODO: منطق عمل: في طبقة الخدمة، عند إلغاء تفعيل إسناد، يجب التحقق من عدم وجود طلبات معلقة تعتمد على هذا الإسناد.

class ProductPackagingPriceTierRuleAssignmentRead(ProductPackagingPriceTierRuleAssignmentBase):
    """
    نموذج بيانات لقراءة وعرض تفاصيل إسناد قاعدة سعر متدرج لخيار تعبئة.
    يتضمن المعرف الفريد للإسناد، والطوابع الزمنية.
    """
    assignment_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
