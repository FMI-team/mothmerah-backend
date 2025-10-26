# backend\src\products\schemas\future_offerings_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID # لاستخدام UUID لـ product_id و user_id

# ==========================================================
# --- Schemas للمحاصيل المتوقعة (Expected Crops) ---
#    (جدول: expected_crops)
# ==========================================================
class ExpectedCropBase(BaseModel):
    """
    النموذج الأساسي لبيانات المحصول المتوقع المشتركة بين الإنشاء والتحديث.
    يحدد الحقول الأساسية التي يصف بها المنتج محصوله المستقبلي.
    """
    # يمكن للمحصول أن يرتبط بمنتج معرف مسبقًا في الكتالوج، أو يكون منتجًا مخصصًا جديدًا.
    # TODO: منطق عمل: يجب أن يكون أحد الحقلين (product_id أو custom_product_name_key) موجودًا وليس كلاهما. سيتم التحقق من ذلك في طبقة الخدمة.
    product_id: Optional[UUID] = Field(
        None,
        description="معرف المنتج الموجود في الكتالوج الذي يتوافق معه هذا المحصول المتوقع (إذا كان موجودًا)."     )
    custom_product_name_key: Optional[str] = Field(
        None,
        max_length=255,
        description="مفتاح نصي لاسم مخصص للمحصول إذا لم يكن مرتبطًا بمنتج موجود في الكتالوج، يستخدم للترجمة."     )
    
    expected_quantity: float = Field(
        ...,
        gt=0, # يجب أن تكون الكمية المتوقعة أكبر من صفر.
        description="الكمية المتوقعة من المحصول (مثلاً: 1000 كيلوغرام)."     )
    unit_of_measure_id: int = Field(
        ...,
        description="معرف وحدة القياس لهذا المحصول (مثل: كيلوغرام، صندوق). يُربط بجدول units_of_measure."     )
    expected_harvest_start_date: date = Field(
        ...,
        description="تاريخ البدء المتوقع لحصاد المحصول. حيوي للتخطيط المستقبلي للمشترين."     )
    expected_harvest_end_date: Optional[date] = Field(
        None,
        description="تاريخ الانتهاء المتوقع لحصاد المحصول. يمكن أن يكون المحصول متاحًا لفترة."     )
    
    asking_price_per_unit: Optional[float] = Field(
        None,
        gt=0, # السعر يجب أن يكون أكبر من صفر إذا تم تحديده.
        description="السعر المبدئي الذي يطلبه المنتج لكل وحدة من المحصول المتوقع."     )
    cultivation_notes_key: Optional[str] = Field(
        None,
        description="مفتاح نصي لملاحظات حول زراعة المحصول (مثل: طريقة الري، خصائص التربة)، يستخدم للترجمة. يمكن أن يوفر معلومات قيمة للمشترين التجاريين."     )
    is_organic: Optional[bool] = Field(
        False,
        description="هل المحصول عضوي؟"     )

class ExpectedCropCreate(ExpectedCropBase):
    """
    نموذج بيانات لإنشاء سجل محصول متوقع جديد.
    يتضمن الحقول الأساسية بالإضافة إلى إمكانية تضمين الترجمات الأولية.
    """
    translations: Optional[List["ExpectedCropTranslationCreate"]] = Field(
        [],
        description="قائمة بالترجمات الأولية لاسم المحصول المخصص وملاحظات الزراعة."     )
    # TODO: منطق عمل: يجب أن تكون الترجمة الافتراضية (مثلاً العربية) موجودة دائمًا عند الإنشاء إذا تم استخدام custom_product_name_key.

class ExpectedCropUpdate(BaseModel):
    """
    نموذج بيانات لتحديث سجل محصول متوقع موجود.
    جميع الحقول اختيارية، مما يسمح بالتحديث الجزئي.
    """
    product_id: Optional[UUID] = Field(None, description="تحديث معرف المنتج المرتبط.")
    custom_product_name_key: Optional[str] = Field(None, max_length=255, description="تحديث مفتاح الاسم المخصص للمحصول.")
    expected_quantity: Optional[float] = Field(None, gt=0, description="تحديث الكمية المتوقعة.")
    unit_of_measure_id: Optional[int] = Field(None, description="تحديث وحدة القياس.")
    expected_harvest_start_date: Optional[date] = Field(None, description="تحديث تاريخ بدء الحصاد المتوقع.")
    expected_harvest_end_date: Optional[date] = Field(None, description="تحديث تاريخ انتهاء الحصاد المتوقع.")
    asking_price_per_unit: Optional[float] = Field(None, gt=0, description="تحديث السعر المبدئي المطلوب.")
    cultivation_notes_key: Optional[str] = Field(None, description="تحديث مفتاح ملاحظات الزراعة.")
    is_organic: Optional[bool] = None # تحديث ما إذا كان المحصول عضويًا.
    offering_status_id: Optional[int] = Field(
        None,
        description="معرف الحالة الجديدة للعرض (مثل: ملغى، مكتمل، قيد الحجز). يستخدم للحذف الناعم."     )
    # TODO: منطق عمل: عند تحديث الحالة إلى 'ملغى' أو 'مكتمل'، يجب التحقق من عدم وجود حجوزات نشطة لهذا المحصول.
    # TODO: الذكاء الاصطناعي: يمكن استخدام تحديثات الكمية والسعر لتدريب نماذج التنبؤ بالأسعار والطلب.

class ExpectedCropRead(ExpectedCropBase):
    """
    نموذج بيانات لقراءة وعرض سجل محصول متوقع.
    يتضمن جميع الحقول الأساسية، بالإضافة إلى معرفات النظام والطوابع الزمنية والترجمات المدمجة.
    """
    expected_crop_id: int = Field(..., description="معرف المحصول المتوقع الفريد.")
    producer_user_id: UUID = Field(..., description="معرف المستخدم (المنتج/المزارع) الذي أضاف هذا المحصول المتوقع.")
    offering_status_id: int = Field(..., description="معرف الحالة الحالية لعرض المحصول المتوقع.")
    created_at: datetime = Field(..., description="تاريخ ووقت إنشاء سجل المحصول المتوقع.")
    updated_at: datetime = Field(..., description="تاريخ ووقت آخر تحديث لسجل المحصول المتوقع.")
    translations: List["ExpectedCropTranslationRead"] = Field(
        [],
        description="قائمة بالترجمات المتاحة لاسم المحصول المخصص وملاحظات الزراعة."     )
    model_config = ConfigDict(from_attributes=True) # لتمكين التحويل من كائن SQLAlchemy إلى Pydantic.

# ==========================================================
# --- Schemas لترجمات المحاصيل المتوقعة (Expected Crop Translations) ---
#    (جدول: expected_crop_translations)
# ==========================================================
class ExpectedCropTranslationBase(BaseModel):
    """
    النموذج الأساسي لبيانات ترجمة المحصول المتوقع.
    """
    language_code: str = Field(..., max_length=10, description="رمز اللغة للترجمة (مثلاً: 'ar', 'en').")
    translated_product_name: Optional[str] = Field(
        None,
        max_length=255,
        description="الاسم المترجم للمحصول إذا كان custom_product_name_key مستخدماً."     )
    translated_cultivation_notes: Optional[str] = Field(
        None,
        description="الملاحظات المترجمة حول زراعة المحصول."     )

class ExpectedCropTranslationCreate(ExpectedCropTranslationBase):
    """
    نموذج بيانات لإنشاء ترجمة جديدة لمحصول متوقع.
    """
    pass

class ExpectedCropTranslationUpdate(BaseModel):
    """
    نموذج بيانات لتحديث ترجمة محصول متوقع موجودة.
    جميع الحقول اختيارية للسماح بالتحديث الجزئي.
    """
    translated_product_name: Optional[str] = Field(None, max_length=255)
    translated_cultivation_notes: Optional[str] = Field(None)

class ExpectedCropTranslationRead(ExpectedCropTranslationBase):
    """
    نموذج بيانات لقراءة وعرض ترجمة محصول متوقع.
    """
    expected_crop_id: int = Field(..., description="معرف المحصول المتوقع المرتبط بهذه الترجمة.")
    model_config = ConfigDict(from_attributes=True) # لتمكين التحويل من كائن SQLAlchemy إلى Pydantic.

# ==========================================================
# --- Schemas لسجل أسعار المنتج (Product Price History) ---
#    (جدول: product_price_history)
#    ملاحظة: هذا الجدول للسجلات التاريخية فقط (immutable)
# ==========================================================
class ProductPriceHistoryCreate(BaseModel):
    """
    نموذج بيانات لإنشاء سجل جديد لتاريخ أسعار المنتج.
    يُستخدم لتسجيل التغييرات في سعر خيار تعبئة منتج معين.
    عادة ما يتم إنشاء هذا السجل تلقائيًا عند تحديث سعر المنتج، وقد يتم إنشاؤه يدويًا من قبل المسؤولين.
    """
    product_packaging_option_id: int = Field(
        ...,
        description="معرف خيار التعبئة (Packaging Option) الذي تغير سعره. يُربط بجدول product_packaging_options (من المجموعة 2.ج)."     )
    old_price_per_unit: Optional[float] = Field(
        None,
        ge=0, # يجب أن يكون السعر أكبر من أو يساوي صفر.
        description="السعر القديم للوحدة قبل التغيير. يكون NULL إذا كان هذا هو أول سعر مسجل."     )
    new_price_per_unit: float = Field(
        ...,
        gt=0, # يجب أن يكون السعر الجديد أكبر من صفر.
        description="السعر الجديد للوحدة بعد التغيير."     )
    change_reason: Optional[str] = Field(
        None,
        max_length=255,
        description="سبب تغيير السعر (مثلاً: 'عرض ترويجي', 'تغيير موسمي', 'تعديل يدوي')."     )
    # ملاحظات على الحقول التي لا يتم تضمينها هنا ولكنها في المودل:
    # - changed_by_user_id: يتم تعيينه في طبقة الخدمة بناءً على المستخدم الحالي أو النظام.
    # - price_change_timestamp: يتم تعيينه تلقائيًا في قاعدة البيانات.

class ProductPriceHistoryRead(BaseModel):
    """
    نموذج بيانات لقراءة وعرض سجل واحد من تاريخ أسعار المنتج.
    يوفر رؤية تاريخية حول تقلبات الأسعار.
    """
    price_history_id: int = Field(..., description="المعرف الفريد لسجل تغيير السعر.")
    product_packaging_option_id: int = Field(
        ...,
        description="معرف خيار التعبئة المرتبط بهذا التغيير في السعر."     )
    old_price_per_unit: Optional[float] = Field(None, description="السعر القديم للوحدة.")
    new_price_per_unit: float = Field(..., description="السعر الجديد للوحدة.")
    price_change_timestamp: datetime = Field(
        ...,
        description="تاريخ ووقت حدوث تغيير السعر."     )
    changed_by_user_id: Optional[UUID] = Field(
        None,
        description="معرف المستخدم الذي أجرى تغيير السعر (إذا كان يدويًا أو مسؤولاً)."     )
    change_reason: Optional[str] = Field(None, description="سبب تغيير السعر.")
    model_config = ConfigDict(from_attributes=True) # لتمكين التحويل من كائن SQLAlchemy إلى Pydantic.

    # TODO: الذكاء الاصطناعي: بيانات هذا الجدول حيوية جدًا!
    # - يمكن استخدامها لتدريب نماذج التنبؤ بالأسعار المستقبلية (Price Forecasting Models).
    # - تحليل الاتجاهات الموسمية للأسعار (Seasonal Price Trends).
    # - فهم مرونة الطلب السعرية (Price Elasticity of Demand).
    # - اكتشاف الحالات الشاذة في الأسعار (Price Anomalies) التي قد تشير إلى مشاكل في السوق.
    # - توليد تقارير أداء المنتجات من حيث التسعير.

# ==========================================================
# --- Schemas لحالات المحاصيل المتوقعة (Expected Crop Statuses) ---
#    (جدول: expected_crop_statuses)
# ==========================================================
class ExpectedCropStatusBase(BaseModel):
    """
    النموذج الأساسي لبيانات حالة المحصول المتوقع.
    يُستخدم لتعريف الحالات الممكنة لعروض المحاصيل (مثل 'معروض', 'تم الحجز', 'ملغى').
    """
    status_name_key: str = Field(
        ...,
        max_length=50,
        description="مفتاح نصي فريد للحالة (مثلاً: 'AVAILABLE_FOR_BOOKING', 'CANCELED')."
    )

class ExpectedCropStatusCreate(ExpectedCropStatusBase):
    """
    نموذج بيانات لإنشاء حالة جديدة للمحصول المتوقع.
    يتضمن الحقول الأساسية بالإضافة إلى إمكانية تضمين الترجمات الأولية.
    """
    translations: Optional[List["ExpectedCropStatusTranslationCreate"]] = Field(
        [],
        description="قائمة بالترجمات الأولية لاسم الحالة ووصفها."
    )
    # TODO: منطق عمل: التأكد من وجود ترجمة افتراضية (مثل العربية) عند الإنشاء.

class ExpectedCropStatusUpdate(ExpectedCropStatusBase):
    """
    نموذج بيانات لتحديث حالة محصول متوقع موجودة.
    جميع الحقول اختيارية، مما يسمح بالتحديث الجزئي.
    """
    pass # في هذا التصميم، يمكن تحديث status_name_key فقط من خلال ExpectedCropStatusBase

class ExpectedCropStatusRead(ExpectedCropStatusBase):
    """
    نموذج بيانات لقراءة وعرض حالة محصول متوقع.
    يتضمن معرف الحالة والترجمات المدمجة.
    """
    status_id: int = Field(..., description="المعرف الفريد للحالة.")
    translations: List["ExpectedCropStatusTranslationRead"] = Field(
        [],
        description="قائمة بالترجمات المتاحة لاسم الحالة ووصفها."
    )
    model_config = ConfigDict(from_attributes=True) # لتمكين التحويل من كائن SQLAlchemy إلى Pydantic.

# ==========================================================
# --- Schemas لترجمات حالات المحاصيل المتوقعة (Expected Crop Status Translations) ---
#    (جدول: expected_crop_status_translations)
# ==========================================================
class ExpectedCropStatusTranslationBase(BaseModel):
    """
    النموذج الأساسي لبيانات ترجمة حالة المحصول المتوقع.
    """
    language_code: str = Field(..., max_length=10, description="رمز اللغة للترجمة (مثلاً: 'ar', 'en').")
    translated_status_name: str = Field(
        ...,
        max_length=100,
        description="الاسم المترجم للحالة (مثلاً: 'متاح للحجز')."
    )
    translated_description: Optional[str] = Field(
        None,
        description="الوصف المترجم للحالة (يساعد في توضيح معنى الحالة)."
    )

class ExpectedCropStatusTranslationCreate(ExpectedCropStatusTranslationBase):
    """
    نموذج بيانات لإنشاء ترجمة جديدة لحالة محصول متوقع.
    """
    pass

class ExpectedCropStatusTranslationUpdate(BaseModel):
    """
    نموذج بيانات لتحديث ترجمة حالة محصول متوقع موجودة.
    جميع الحقول اختيارية للسماح بالتحديث الجزئي.
    """
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class ExpectedCropStatusTranslationRead(ExpectedCropStatusTranslationBase):
    """
    نموذج بيانات لقراءة وعرض ترجمة حالة محصول متوقع.
    """
    status_id: int = Field(..., description="معرف حالة المحصول المتوقع المرتبطة بهذه الترجمة.")
    model_config = ConfigDict(from_attributes=True) # لتمكين التحويل من كائن SQLAlchemy إلى Pydantic.

