# backend\src\community\models\reviews_models.py

from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, SmallInteger,
    func, TIMESTAMP, text, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING # تأكد من استيراد Optional و TYPE_CHECKING

from src.db.base_class import Base

from uuid import uuid4

# يمنع الأخطاء الناتجة عن الاستيراد الدائري لأغراض Type Checking
if TYPE_CHECKING:
    # من المجموعة 1 (المستخدمون)
    from src.users.models.core_models import User
    # من المجموعة 12 (Lookups العامة)
    from src.lookups.models.lookups_models import ReviewStatus, ReviewReportReason, ReviewCriterion, EntityTypeForReviewOrImage, Language
    # من المجموعة 4 (عمليات السوق)
    from src.market.models.orders_models import Order
    # من المجموعة 2 (المنتجات)
    from src.products.models.products_models import Product # إذا كان يتم تقييم المنتج
    # من المجموعة 5 (المزادات)
    from src.auctions.models.auctions_models import Auction, AuctionLot # إذا كان يتم تقييم المزاد/لوط المزاد


class Review(Base):
    """(6.1) الجدول الرئيسي للمراجعات والتقييمات."""
    __tablename__ = 'reviews'
    review_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reviewer_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    reviewed_entity_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="معرف الكيان (UUID أو Integer) - يجب أن يكون VARCHAR ليتسع لمعرفات مختلفة")
    reviewed_entity_type: Mapped[str] = mapped_column(String(50), ForeignKey('entity_types_for_reviews_or_images.entity_type_code'), nullable=False)
    related_order_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.order_id', ondelete='SET NULL'), nullable=True)
    rating_overall: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    review_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('review_statuses.status_id'), nullable=False)
    submission_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    publication_timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    reviewer_user: Mapped["User"] = relationship("User", foreign_keys=[reviewer_user_id], back_populates="reviews_given", lazy="selectin")
    review_status: Mapped["ReviewStatus"] = relationship("ReviewStatus", foreign_keys=[review_status_id], lazy="selectin", back_populates="reviews")
    reviewed_entity_type_obj: Mapped["EntityTypeForReviewOrImage"] = relationship("EntityTypeForReviewOrImage", foreign_keys=[reviewed_entity_type], lazy="selectin", back_populates="reviews") # back_populates جديد
    related_order: Mapped[Optional["Order"]] = relationship("Order", foreign_keys=[related_order_id], lazy="selectin", back_populates="reviews")

    # علاقات عكسية
    ratings_by_criteria: Mapped[List["ReviewRatingByCriterion"]] = relationship(back_populates="review", cascade="all, delete-orphan")
    responses: Mapped[List["ReviewResponse"]] = relationship(back_populates="review", cascade="all, delete-orphan")
    reports: Mapped[List["ReviewReport"]] = relationship(back_populates="review", cascade="all, delete-orphan")

    __table_args__ = (CheckConstraint('rating_overall >= 1 AND rating_overall <= 5', name='chk_rating_overall_range'),)


class ReviewRatingByCriterion(Base):
    """(6.4) جدول تقييمات المراجعة حسب المعايير التفصيلية."""
    __tablename__ = 'review_ratings_by_criteria'
    rating_by_criteria_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('reviews.review_id', ondelete="CASCADE"), nullable=False)
    criteria_id: Mapped[int] = mapped_column(Integer, ForeignKey('review_criteria.criteria_id'), nullable=False)
    rating_value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات:
    review: Mapped["Review"] = relationship(back_populates="ratings_by_criteria")
    review_criterion: Mapped["ReviewCriterion"] = relationship("ReviewCriterion", foreign_keys=[criteria_id], lazy="selectin", back_populates="review_ratings_by_criteria")

    __table_args__ = (CheckConstraint('rating_value >= 1 AND rating_value <= 5', name='chk_rating_value_range'),)


class ReviewResponse(Base):
    """(6.5) جدول الردود على المراجعات (عادة من البائع)."""
    __tablename__ = 'review_responses'
    response_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('reviews.review_id', ondelete="CASCADE"), nullable=False, unique=True)
    responder_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    is_approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, server_default=text("true"))
    approved_by_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    review: Mapped["Review"] = relationship(back_populates="responses")
    responder_user: Mapped["User"] = relationship("User", foreign_keys=[responder_user_id], lazy="selectin", back_populates="review_responses_given")
    approved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_user_id], lazy="selectin", back_populates="review_responses_approved")


class ReviewReport(Base):
    """(6.6) جدول الإبلاغات عن المراجعات المخالفة."""
    __tablename__ = 'review_reports'
    report_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('reviews.review_id', ondelete="CASCADE"), nullable=False)
    reporter_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=False)
    report_reason_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('review_report_reasons.reason_id'), nullable=True)
    custom_report_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    report_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'PENDING_REVIEW'"))
    action_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    resolved_timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True) # تم التأكيد على Optional
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    review: Mapped["Review"] = relationship(back_populates="reports")
    reporter_user: Mapped["User"] = relationship("User", foreign_keys=[reporter_user_id], lazy="selectin", back_populates="review_reports_made")
    report_reason: Mapped[Optional["ReviewReportReason"]] = relationship("ReviewReportReason", foreign_keys=[report_reason_id], lazy="selectin", back_populates="review_reports") # back_populates جديد
    resolved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by_user_id], lazy="selectin", back_populates="review_reports_resolved")