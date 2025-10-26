# backend\src\users\schemas\core_schemas.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING 

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas الأخرى
# TODO: تأكد من أن هذه الملفات موجودة وأن Schemas المطلوبة معرفة فيها.
from src.users.schemas.rbac_schemas import RoleRead # للدور الأساسي
# تم استيراد UserVerificationStatusRead من verification_lookups_schemas.py
from src.users.schemas.verification_lookups_schemas import UserVerificationStatusRead
# تم استيراد AdminUserStatusUpdate من management_schemas.py
from src.users.schemas.management_schemas import AdminUserStatusUpdate
from src.lookups.schemas import LanguageRead # <--  للغة المفضلة

# استيرادات لفحص الأنواع فقط (TYPE_CHECKING) لتجنب الاستيرادات الدائرية في وقت التشغيل
if TYPE_CHECKING:
    from src.users.schemas.core_schemas import UserRead as _UserRead # لـ updated_by_user (مرجع ذاتي)

    from src.auditing.schemas.audit_schemas import SystemAuditLogRead, UserActivityLogRead, SearchLogRead, SecurityEventLogRead, DataChangeAuditLogRead # لسجلات التدقيق المرتبطة بـ User
    from src.configuration.schemas.settings_schemas import ApplicationSettingRead, FeatureFlagRead, SystemMaintenanceScheduleRead # لإعدادات النظام المرتبطة بـ User
    from src.community.schemas.reviews_schemas import ReviewRead, ReviewResponseRead, ReviewReportRead # للمراجعات المرتبطة بـ User
    from src.market.schemas.orders_models import Order # TODO: إذا كانت هناك علاقات عكسية من Order إلى User (مثل buyer, seller)
    from src.market.schemas.orders_schemas import OrderRead # لـ Review.related_order إذا كانت مدمجة في UserRead
    # TODO: المزيد من استيرادات Schemas الأخرى إذا كانت UserRead ستتضمنها مباشرة في future_offerings, pricing, etc.
    from src.products.schemas.product_schemas import ProductRead # للمنتجات التي يملكها User
    from src.market.schemas.rfq_schemas import RfqRead # لـ RFQs التي يملكها User
    from src.market.schemas.quotes_schemas import QuoteRead # لـ Quotes التي يملكها User
    from src.market.schemas.shipment_schemas import ShipmentRead # لـ Shipments التي يملكها User
    from src.auctions.schemas.auction_schemas import AuctionRead # للمزادات التي يملكها User
    from src.auctions.schemas.bidding_schemas import BidRead, AutoBidSettingRead, AuctionWatchlistRead, AuctionParticipantRead # للمزايدات
    from src.auctions.schemas.settlement_schemas import AuctionSettlementRead # لتسويات المزادات

# ==========================================================
# --- Schemas لأنواع المستخدمين (User Types) ---
#    (المودلات من backend\src\users\models\core_models.py)
# ==========================================================
class UserTypeTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة نوع المستخدم."""
    language_code: str = Field(..., max_length=10, description="رمز اللغة للترجمة (مثلاً: 'ar-SA').")
    translated_user_type_name: str = Field(..., max_length=100, description="الاسم المترجم لنوع المستخدم (مثلاً: 'بائع', 'مشترٍ').")
    translated_description: Optional[str] = Field(None, description="الوصف المترجم لنوع المستخدم.")

class UserTypeTranslationCreate(UserTypeTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لنوع مستخدم."""
    pass

class UserTypeTranslationUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث ترجمة نوع مستخدم موجودة."""
    translated_user_type_name: Optional[str] = Field(None, max_length=100)
    translated_description: Optional[str] = Field(None)

class UserTypeTranslationRead(UserTypeTranslationBase):
    """نموذج لقراءة وعرض ترجمة نوع المستخدم."""
    user_type_id: int # معرف النوع الأم
    model_config = ConfigDict(from_attributes=True)

class UserTypeBase(BaseModel):
    """النموذج الأساسي لنوع المستخدم."""
    user_type_name_key: str = Field(..., max_length=50, description="مفتاح نصي فريد لنوع المستخدم (مثلاً: 'SELLER', 'BUYER').")

class UserTypeCreate(UserTypeBase):
    """نموذج لإنشاء نوع مستخدم جديد، يتضمن ترجماته الأولية."""
    password: str = Field(..., min_length=8, description="كلمة المرور للمستخدم الجديد.") # تم إضافة هذا الحقل ليكون هنا
    user_type_key: str = Field(..., description="مفتاح نوع المستخدم الذي يختاره المستخدم (مثلاً: 'BUYER', 'SELLER').")
    default_role_key: Optional[str] = Field("BASE_USER", description="مفتاح الدور الأساسي الافتراضي الذي سيتم تعيينه.")

    translations: Optional[List[UserTypeTranslationCreate]] = Field([], description="الترجمات الأولية لنوع المستخدم.") # أعد هذا السطر هنا إذا كان هذا ينطبق على Create

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('كلمة المرور يجب أن لا تقل عن 8 أحرف.')
        return v

class UserTypeUpdate(BaseModel): # ترث من BaseModel للسماح بجميع الحقول اختيارية
    """نموذج لتحديث بيانات نوع مستخدم أساسية."""
    user_type_name_key: Optional[str] = Field(None, max_length=50)

class UserTypeRead(UserTypeBase):
    """نموذج لقراءة وعرض تفاصيل نوع المستخدم، يتضمن ترجماته ومعرفه."""
    user_type_id: int
    translations: List[UserTypeTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لحالات الحساب التشغيلية (Account Statuses) ---
#    (المودلات من backend\src\users\models\core_models.py)
# ==========================================================
class AccountStatusTranslationBase(BaseModel):
    """النموذج الأساسي لترجمة حالة الحساب."""
    language_code: str = Field(..., max_length=10)
    translated_status_name: str = Field(..., max_length=100)
    translated_status_description: Optional[str] = Field(None)

class AccountStatusTranslationCreate(AccountStatusTranslationBase):
    """نموذج لإنشاء ترجمة جديدة لحالة حساب."""
    pass

class AccountStatusTranslationUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث ترجمة حالة حساب موجودة."""
    translated_status_name: Optional[str] = Field(None, max_length=100)
    translated_status_description: Optional[str] = Field(None)

class AccountStatusTranslationRead(AccountStatusTranslationBase):
    """نموذج لقراءة وعرض ترجمة حالة الحساب."""
    account_status_id: int # معرف الحالة الأم
    model_config = ConfigDict(from_attributes=True)

class AccountStatusBase(BaseModel):
    """النموذج الأساسي لحالة الحساب: يحدد الخصائص المشتركة بين الإنشاء والتحديث."""
    status_name_key: str = Field(..., max_length=50, description="مفتاح فريد لاسم الحالة (مثلاً: 'ACTIVE', 'SUSPENDED').")
    is_terminal: Optional[bool] = Field(False, description="هل هذه الحالة نهائية لا يمكن الخروج منها؟")

class AccountStatusCreate(AccountStatusBase):
    """نموذج لإنشاء حالة حساب جديدة، يتضمن ترجماتها الأولية."""
    translations: Optional[List[AccountStatusTranslationCreate]] = Field([], description="الترجمات الأولية لحالة الحساب.")

class AccountStatusUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث حالة حساب موجودة."""
    status_name_key: Optional[str] = Field(None, max_length=50)
    is_terminal: Optional[bool] = None

class AccountStatusRead(AccountStatusBase):
    """نموذج لقراءة وعرض تفاصيل حالة الحساب، يتضمن ترجماتها ومعرفها."""
    account_status_id: int
    translations: List[AccountStatusTranslationRead] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لتفضيلات المستخدمين (User Preferences) ---
#    (المودلات من backend\src\users\models\core_models.py)
# ==========================================================
class UserPreferenceBase(BaseModel):
    """النموذج الأساسي لتفضيلات المستخدمين: يخزن تفضيل واحد بنظام المفتاح-القيمة."""
    preference_key: str = Field(..., max_length=100, description="مفتاح نصي فريد للتفضيل (مثلاً: 'theme', 'notification_email').")
    preference_value: str = Field(..., description="قيمة التفضيل التي حددها المستخدم (يمكن أن تكون JSON نصيًا).")

class UserPreferenceCreate(UserPreferenceBase):
    """نموذج لإنشاء تفضيل مستخدم جديد."""
    # user_id سيتم تعيينه في طبقة الخدمة.
    pass

class UserPreferenceUpdate(BaseModel):
    """نموذج لتحديث تفضيل مستخدم موجود. عادةً ما يتم تحديث القيمة فقط."""
    preference_value: Optional[str] = Field(None, description="تحديث قيمة التفضيل.")

class UserPreferenceRead(UserPreferenceBase):
    """نموذج لقراءة وعرض تفاصيل تفضيل المستخدم."""
    user_preference_id: int
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# --- Schemas لسجل تغييرات حالة الحساب (Account Status History) ---
#    (المودلات من backend\src\users\models\core_models.py)
#    هذا الجدول يُنشأ تلقائياً ولا يُعدّل أو يُحذف مباشرةً عبر API.
# ==========================================================
class AccountStatusHistoryRead(BaseModel):
    """نموذج لقراءة وعرض تفاصيل سجل تغييرات حالة الحساب.
    يُستخدم لتتبع مسار التغييرات التي طرأت على حالة حساب المستخدم بمرور الوقت.
    """
    account_status_history_id: int
    user_id: UUID
    old_account_status_id: Optional[int] = Field(None, description="معرف الحالة القديمة للحساب.")
    new_account_status_id: int = Field(..., description="معرف الحالة الجديدة للحساب.")
    change_timestamp: datetime = Field(..., description="تاريخ ووقت تغيير الحالة.")
    changed_by_user_id: Optional[UUID] = Field(None, description="معرف المستخدم الذي أجرى التغيير (إذا لم يكن النظام).")
    reason_for_change: Optional[str] = Field(None, description="وصف نصي أو رمز يشير إلى سبب تغيير الحالة.")
    additional_notes: Optional[str] = Field(None, description="ملاحظات إضافية حول سبب التغيير.")
    created_at: datetime # هذا الحقل سيكون مطابقًا لـ change_timestamp في هذا السياق
    updated_at: datetime # (نادراً ما يُحدث سجل تاريخي)
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين AccountStatusRead لـ old_account_status و new_account_status
    # old_account_status: AccountStatusRead # موجود في هذا الملف
    # new_account_status: AccountStatusRead # موجود في هذا الملف
    # TODO: يمكن تضمين UserRead لـ changed_by_user (يتطلب استيراد UserRead)


# ==========================================================
# --- Schemas للمستخدمين (User) ---
#    (المودلات من backend\src\users\models\core_models.py)
# ==========================================================
class UserBase(BaseModel):
    """النموذج الأساسي للمستخدم: يصف الخصائص الأساسية للمستخدم."""
    phone_number: str = Field(..., examples=["+966500000000"], description="رقم الجوال الأساسي للمستخدم.")
    email: Optional[EmailStr] = Field(None, description="عنوان البريد الإلكتروني للمستخدم.") # EmailStr للتحقق من التنسيق
    first_name: str = Field(..., description="الاسم الأول للمستخدم.")
    last_name: str = Field(..., description="اسم العائلة للمستخدم.")
    profile_picture_url: Optional[str] = Field(None, description="رابط صورة الملف الشخصي للمستخدم.")
    # user_type_id: int = Field(..., description="معرف نوع المستخدم (مثلاً: بائع، مشترٍ).")
    default_user_role_id: Optional[int] = Field(None, description="معرف الدور الأساسي للمستخدم.")
    user_verification_status_id: Optional[int] = Field(None, description="معرف حالة التحقق العامة للمستخدم.")
    preferred_language_code: str = Field("ar", max_length=10, description="رمز اللغة المفضلة للمستخدم.")

    # حقول تُدار بواسطة النظام أو آليات أمنية:
    # password_hash: لا يتم تمريره مباشرة في Schemas (يُجزأ في الخدمة)
    # phone_verified_at, email_verified_at, last_login_timestamp, last_activity_timestamp, is_deleted, updated_by_user_id, additional_data

# class UserCreate(UserBase):
#     """نموذج لإنشاء مستخدم جديد. يتطلب كلمة مرور."""
#     password: str = Field(..., min_length=8, description="كلمة المرور للمستخدم الجديد.")
#     # user_type_id: int # هذا الحقل كان هنا، لكنه جزء من UserBase الآن.
    
#     # هذه الحقول كانت معاملات منفصلة، والآن أصبحت جزءًا من الـ Schema
#     user_type_key: str = Field(..., description="مفتاح نوع المستخدم الذي يختاره المستخدم (مثلاً: 'BUYER', 'SELLER').") # <-- إضافة هذا
#     default_role_key: Optional[str] = Field("BASE_USER", description="مفتاح الدور الأساسي الافتراضي الذي سيتم تعيينه.") # <-- إضافة هذا


#     @field_validator('password')
#     @classmethod
#     def validate_password_complexity(cls, v: str) -> str:
#         # هنا يمكن إضافة نفس منطق التحقق من تعقيد كلمة المرور الموجود في security.py
#         if len(v) < 8:
#             raise ValueError('كلمة المرور يجب أن لا تقل عن 8 أحرف.')
#         return v
class UserCreate(UserBase):
    """نموذج لإنشاء مستخدم جديد. يتطلب كلمة مرور."""
    password: str = Field(..., min_length=8, description="كلمة المرور للمستخدم الجديد.")
    user_type_key: str = Field(..., description="مفتاح نوع المستخدم الذي يختاره المستخدم (مثلاً: 'BUYER', 'SELLER').")
    default_role_key: Optional[str] = Field("BASE_USER", description="مفتاح الدور الأساسي الافتراضي الذي سيتم تعيينه.")

    translations: Optional[List[UserTypeTranslationCreate]] = Field([], description="الترجمات الأولية لنوع المستخدم.")

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('كلمة المرور يجب أن لا تقل عن 8 أحرف.')
        return v


class UserUpdate(BaseModel):
    """نموذج لتحديث الملف الشخصي للمستخدم. جميع الحقول اختيارية."""
    phone_number: Optional[str] = Field(None, examples=["+9665XXXXXXXXX"])
    email: Optional[EmailStr] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    profile_picture_url: Optional[str] = Field(None)
    user_type_id: Optional[int] = Field(None, description="تحديث نوع المستخدم.") # قد يكون متاحًا فقط للمسؤولين
    default_user_role_id: Optional[int] = Field(None, description="تحديث الدور الأساسي.") # قد يكون متاحًا فقط للمسؤولين
    user_verification_status_id: Optional[int] = Field(None, description="تحديث حالة التحقق.") # قد يكون متاحًا فقط للمسؤولين
    preferred_language_code: Optional[str] = Field(None, max_length=10)
    is_deleted: Optional[bool] = Field(None, description="لتطبيق الحذف الناعم للحساب (فقط للمسؤول).")
    additional_data: Optional[dict] = Field(None)

class UserRead(UserBase):
    """نموذج لقراءة وعرض تفاصيل المستخدم بشكل كامل، بما في ذلك معرفه والطوابع الزمنية،
    بالإضافة إلى الكائنات المرتبطة بشكل متداخل لتحسين العرض والصلاحيات.
    """
    user_id: UUID
    phone_verified_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    last_login_timestamp: Optional[datetime] = None
    last_activity_timestamp: Optional[datetime] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    updated_by_user_id: Optional[UUID] = None
    additional_data: Optional[dict] = None
    
    # الكائنات المرتبطة بشكل متداخل (Nested Relationships)
    account_status: "AccountStatusRead" # <-- استخدام سلسلة نصية
    user_type: UserTypeRead
    default_role: Optional["RoleRead"] = None # <-- استخدام سلسلة نصية
    user_verification_status: Optional[UserVerificationStatusRead] = None
    preferred_language: Optional["LanguageRead"] = None # <-- استخدام سلسلة نصية

    # # علاقات عكسية (Lazy-loaded, often not directly included in Read unless specific endpoint)
    # # ولكن يمكن وضعها كـ "forward references" هنا لـ OpenAPI
    # system_audit_logs: List["SystemAuditLogRead"] = Field([]) # <-- استخدام سلسلة نصية
    # user_activity_logs: List["UserActivityLogRead"] = Field([]) # <-- استخدام سلسلة نصية
    # search_logs: List["SearchLogRead"] = Field([]) # <-- استخدام سلسلة نصية
    # security_event_logs: List["SecurityEventLogRead"] = Field([]) # <-- استخدام سلسلة نصية
    # data_change_audit_logs: List["DataChangeAuditLogRead"] = Field([]) # <-- استخدام سلسلة نصية
    # application_settings_updated: List["ApplicationSettingRead"] = Field([]) # <-- استخدام سلسلة نصية
    # feature_flags_updated: List["FeatureFlagRead"] = Field([]) # <-- استخدام سلسلة نصية
    # maintenance_schedules_created: List["SystemMaintenanceScheduleRead"] = Field([]) # <-- استخدام سلسلة نصية
    
    # reviews_given: List["ReviewRead"] = Field([]) # <-- استخدام سلسلة نصية
    # review_responses_given: List["ReviewResponseRead"] = Field([]) # <-- استخدام سلسلة نصية
    # review_responses_approved: List["ReviewResponseRead"] = Field([]) # <-- استخدام سلسلة نصية
    # review_reports_made: List["ReviewReportRead"] = Field([]) # <-- استخدام سلسلة نصية
    # review_reports_resolved: List["ReviewReportRead"] = Field([]) # <-- استخدام سلسلة نصية
    
    # # TODO: علاقات عكسية أخرى من Market, Products, Auctions
    # orders_as_buyer: List["OrderRead"] = Field([]) # <-- استخدام سلسلة نصية
    # orders_as_seller: List["OrderRead"] = Field([]) # <-- استخدام سلسلة نصية
    # products_sold: List["ProductRead"] = Field([]) # <-- استخدام سلسلة نصية
    # products_updated: List["ProductRead"] = Field([]) # <-- استخدام سلسلة نصية
    # rfqs_as_buyer: List["RfqRead"] = Field([]) # <-- استخدام سلسلة نصية
    # quotes_as_seller: List["QuoteRead"] = Field([]) # <-- استخدام سلسلة نصية
    # shipments_as_shipper: List["ShipmentRead"] = Field([]) # <-- استخدام سلسلة نصية
    # auctions_as_seller: List["AuctionRead"] = Field([]) # <-- استخدام سلسلة نصية
    # current_highest_bids: List["AuctionRead"] = Field([]) # <-- استخدام سلسلة نصية
    # bids_as_bidder: List["BidRead"] = Field([]) # <-- استخدام سلسلة نصية
    # auction_participants: List["AuctionParticipantRead"] = Field([]) # <-- استخدام سلسلة نصية
    # auto_bid_settings: List["AutoBidSettingRead"] = Field([]) # <-- استخدام سلسلة نصية
    # auction_watchlists: List["AuctionWatchlistRead"] = Field([]) # <-- استخدام سلسلة نصية
    # auction_settlements_as_winner: List["AuctionSettlementRead"] = Field([]) # <-- استخدام سلسلة نصية
    # auction_settlements_as_seller: List["AuctionSettlementRead"] = Field([]) # <-- استخدام سلسلة نصية

    model_config = ConfigDict(from_attributes=True)


class UserChangePassword(BaseModel):
    """نموذج لتغيير كلمة مرور المستخدم (للمستخدم المسجل دخوله)."""
    current_password: str = Field(..., description="كلمة المرور الحالية للمستخدم.")
    new_password: str = Field(..., description="كلمة المرور الجديدة.")
    confirm_new_password: str = Field(..., description="تأكيد كلمة المرور الجديدة.")

    @field_validator('new_password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('كلمة المرور يجب أن لا تقل عن 8 أحرف.')
        return v

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserChangePassword':
        if self.new_password is not None and self.new_password != self.confirm_new_password:
            raise ValueError('كلمتا المرور الجديدتان غير متطابقتين.')
        return self

class Token(BaseModel):
    """
    [نسخة محسنة]
    نموذج لتمثيل استجابة المصادقة الكاملة.
    """
    access_token: str
    refresh_token: str # <<< إضافة حقل الـ Refresh Token
    token_type: str = "bearer"

# UserRead.model_rebuild()
