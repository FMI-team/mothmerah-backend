# backend\src\community\schemas\reviews_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

# استيراد Schemas المطلوبة للعلاقات المتداخلة
# ActivityTypeRead, SecurityEventTypeRead, SystemEventTypeRead, EntityTypeForReviewOrImageRead تستورد من src.lookups.schemas
from src.lookups.schemas import (
    ReviewStatusRead,
    ReviewReportReasonRead,
    ReviewCriterionRead,
    EntityTypeForReviewOrImageRead
)

# استيراد OrderRead (لـ Review.related_order)
if TYPE_CHECKING: # <-- هذا الاستيراد يتم فقط لفحص الأنواع، لا يتم تنفيذه في وقت التشغيل
    from src.market.schemas.order_schemas import OrderRead
    # TODO: ProductRead, AuctionRead, AuctionLotRead إذا تم تقييمها مباشرة
    # from src.products.schemas.product_schemas import ProductRead
    # from src.auctions.schemas.auction_schemas import AuctionRead, AuctionLotRead
    
    # استيراد Schemas المطلوبة للعلاقات المتداخلة
    # UserRead تستورد من src.users.schemas.core_schemas
    from src.users.schemas.core_schemas import UserRead # <-- تم نقل استيراد UserRead إلى هنا


# ==========================================================
# --- Schemas للمراجعات (Reviews) ---
#    (المودلات من backend\src\community\models\reviews_models.py)
# ==========================================================
class ReviewBase(BaseModel):
    """النموذج الأساسي لبيانات المراجعة."""
    reviewer_user_id: UUID = Field(..., description="معرف المستخدم الذي قدم المراجعة.")
    reviewed_entity_id: str = Field(..., description="معرف الكيان الذي تم تقييمه (UUID أو Integer).")
    reviewed_entity_type: str = Field(..., max_length=50, description="نوع الكيان الذي تم تقييمه (مثل 'Product', 'Seller', 'Order').")
    related_order_id: Optional[UUID] = Field(None, description="معرف الطلب المرتبط (إذا كانت المراجعة جزءاً من طلب).")
    rating_overall: int = Field(..., ge=1, le=5, description="التقييم الإجمالي (من 1 إلى 5 نجوم).")
    review_title: Optional[str] = Field(None, max_length=255)
    review_text: Optional[str] = Field(None)
    review_status_id: int = Field(..., description="حالة المراجعة (مثلاً: 'قيد المراجعة', 'موافق عليها').")
    # submission_timestamp, publication_timestamp, created_at, updated_at تدار تلقائياً

class ReviewCreate(ReviewBase):
    """نموذج لإنشاء مراجعة جديدة."""
    # لا نطلب submission_timestamp, publication_timestamp هنا
    pass

class ReviewUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث مراجعة موجودة."""
    rating_overall: Optional[int] = Field(None, ge=1, le=5)
    review_title: Optional[str] = Field(None, max_length=255)
    review_text: Optional[str] = Field(None)
    review_status_id: Optional[int] = Field(None) # للمسؤولين

class ReviewRead(ReviewBase):
    """نموذج لقراءة وعرض تفاصيل المراجعة."""
    review_id: int
    submission_timestamp: datetime
    publication_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # الكائنات المرتبطة بشكل متداخل
    # reviewer_user: UserRead
    reviewer_user: "UserRead" # <-- تم التعديل هنا: وضع "UserRead" كسلسلة نصية
    review_status: ReviewStatusRead
    reviewed_entity_type_obj: EntityTypeForReviewOrImageRead
    related_order: Optional["OrderRead"] = None # <-- مرجع أمامي

    # علاقات عكسية متداخلة
    ratings_by_criteria: List["ReviewRatingByCriterionRead"] = [] # <-- مرجع أمامي
    responses: List["ReviewResponseRead"] = [] # <-- مرجع أمامي
    reports: List["ReviewReportRead"] = [] # <-- مرجع أمامي


# ==========================================================
# --- Schemas لتقييمات المراجعة حسب المعايير (ReviewRatingByCriterion) ---
#    (المودلات من backend\src\community\models\reviews_models.py)
# ==========================================================
class ReviewRatingByCriterionBase(BaseModel):
    """النموذج الأساسي لبيانات التقييم حسب المعيار."""
    review_id: int = Field(..., description="معرف المراجعة الأم.")
    criteria_id: int = Field(..., description="معرف معيار التقييم.")
    rating_value: int = Field(..., ge=1, le=5, description="قيمة التقييم لهذا المعيار (1-5).")

class ReviewRatingByCriterionCreate(ReviewRatingByCriterionBase):
    """نموذج لإنشاء تقييم جديد حسب المعيار."""
    pass

class ReviewRatingByCriterionUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث تقييم حسب المعيار موجود."""
    rating_value: Optional[int] = Field(None, ge=1, le=5)

class ReviewRatingByCriterionRead(ReviewRatingByCriterionBase):
    """نموذج لقراءة وعرض تفاصيل التقييم حسب المعيار."""
    rating_by_criteria_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # الكائنات المرتبطة بشكل متداخل
    review_criterion: ReviewCriterionRead
    # TODO: review: "ReviewRead" # <-- مرجع أمامي


# ==========================================================
# --- Schemas للردود على المراجعات (ReviewResponse) ---
#    (المودلات من backend\src\community\models\reviews_models.py)
# ==========================================================
class ReviewResponseBase(BaseModel):
    """النموذج الأساسي لبيانات الرد على المراجعة."""
    review_id: int = Field(..., description="معرف المراجعة التي يتم الرد عليها.")
    responder_user_id: UUID = Field(..., description="معرف المستخدم الذي قدم الرد.")
    response_text: str = Field(..., description="نص الرد.")
    is_approved: Optional[bool] = Field(None, description="هل الرد موافق عليه للنشر؟")
    approved_by_user_id: Optional[UUID] = Field(None, description="معرف المسؤول الذي وافق على الرد.")

class ReviewResponseCreate(ReviewResponseBase):
    """نموذج لإنشاء رد جديد على مراجعة."""
    pass

class ReviewResponseUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث رد على مراجعة موجود."""
    response_text: Optional[str] = Field(None)
    is_approved: Optional[bool] = Field(None)
    approved_by_user_id: Optional[UUID] = Field(None)

class ReviewResponseRead(ReviewResponseBase):
    """نموذج لقراءة وعرض تفاصيل الرد على المراجعة."""
    response_id: int
    response_timestamp: datetime
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # الكائنات المرتبطة بشكل متداخل
    # TODO: review: "ReviewRead" # <-- مرجع أمامي
    # responder_user: UserRead
    # approved_by_user: Optional[UserRead] = None
    responder_user: "UserRead" # <-- تم التعديل هنا: وضع "UserRead" كسلسلة نصية
    approved_by_user: Optional["UserRead"] = None # <-- تم التعديل هنا: وضع "UserRead" كسلسلة نصية
    


# ==========================================================
# --- Schemas للإبلاغات عن المراجعات المخالفة (ReviewReport) ---
#    (المودلات من backend\src\community\models\reviews_models.py)
# ==========================================================
class ReviewReportBase(BaseModel):
    """النموذج الأساسي لبيانات الإبلاغ عن المراجعات."""
    review_id: int = Field(..., description="معرف المراجعة المبلغ عنها.")
    reporter_user_id: UUID = Field(..., description="معرف المستخدم الذي قدم البلاغ.")
    report_reason_id: Optional[int] = Field(None, description="معرف سبب الإبلاغ (من جدول review_report_reasons).")
    custom_report_reason: Optional[str] = Field(None, description="سبب بلاغ مخصص (إذا لم يكن من الأسباب المحددة).")
    report_status: str = Field("PENDING_REVIEW", max_length=50, description="حالة معالجة البلاغ (مثلاً: 'قيد المراجعة', 'تم الحل').")
    action_taken: Optional[str] = Field(None, description="الإجراء الذي اتخذه المسؤول.")
    resolved_by_user_id: Optional[UUID] = Field(None, description="معرف المسؤول الذي حل البلاغ.")
    resolved_timestamp: Optional[datetime] = Field(None)

class ReviewReportCreate(ReviewReportBase):
    """نموذج لإنشاء بلاغ جديد عن مراجعة."""
    pass

class ReviewReportUpdate(BaseModel): # ترث من BaseModel
    """نموذج لتحديث بلاغ عن مراجعة موجود."""
    report_reason_id: Optional[int] = Field(None)
    custom_report_reason: Optional[str] = Field(None)
    report_status: Optional[str] = Field(None, max_length=50)
    action_taken: Optional[str] = Field(None)
    resolved_by_user_id: Optional[UUID] = Field(None)
    resolved_timestamp: Optional[datetime] = Field(None)

class ReviewReportRead(ReviewReportBase):
    """نموذج لقراءة وعرض تفاصيل الإبلاغ عن مراجعة."""
    report_id: int
    report_timestamp: datetime
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # الكائنات المرتبطة بشكل متداخل
    # TODO: review: "ReviewRead" # <-- مرجع أمامي
    # reporter_user: UserRead
    # report_reason: Optional[ReviewReportReasonRead] = None
    # resolved_by_user: Optional[UserRead] = None
    reporter_user: "UserRead" # <-- تم التعديل هنا: وضع "UserRead" كسلسلة نصية
    report_reason: Optional[ReviewReportReasonRead] = None
    resolved_by_user: Optional["UserRead"] = None # <-- تم التعديل هنا: وضع "UserRead" كسلسلة نصية

# TODO: إضافة استدعاءات update_forward_refs() في __init__.py للحزمة
# لا توجد هنا استدعاءات لـ update_forward_refs() في نهاية الملفات الفردية.
# سيتم استدعاؤها في __init__.py للحزمة، مما يسمح بحل المراجع الأمامية.