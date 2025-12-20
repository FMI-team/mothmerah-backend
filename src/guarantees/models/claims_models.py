from datetime import datetime
from sqlalchemy import (
    Integer, String, Text,  BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey#, CheckConstraint # ,Boolean , SmallInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base_class import Base

from uuid import uuid4

class GGClaim(Base):
    """(10.1) جدول مطالبات الضمان الذهبي."""
    __tablename__ = 'gg_claims'
    gg_claim_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    related_order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.order_id'), nullable=False)
    buyer_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    seller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    claim_submission_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    problem_description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_quantity_description: Mapped[str] = mapped_column(Text, nullable=True)
    gg_claim_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('gg_claim_statuses.gg_claim_status_id'), nullable=False)
    resolution_details: Mapped[str] = mapped_column(Text, nullable=True)
    resolution_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class GGClaimItem(Base):
    """(10.2) جدول البنود المتأثرة في مطالبة الضمان الذهبي."""
    __tablename__ = 'gg_claim_items'
    gg_claim_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gg_claim_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('gg_claims.gg_claim_id'), nullable=False)
    order_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('order_items.order_item_id'), nullable=False)
    affected_quantity: Mapped[float] = mapped_column(Numeric, nullable=False)
    item_problem_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class GGClaimStatusHistory(Base):
    """(10.5) جدول سجل تغييرات حالة مطالبة الضمان الذهبي."""
    __tablename__ = 'gg_claim_status_history'
    history_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gg_claim_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('gg_claims.gg_claim_id'), nullable=False)
    old_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('gg_claim_statuses.gg_claim_status_id'), nullable=True)
    new_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('gg_claim_statuses.gg_claim_status_id'), nullable=False)
    change_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    changed_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class GGClaimEvidence(Base):
    """(10.6) جدول الأدلة المرفقة بمطالبة الضمان الذهبي."""
    __tablename__ = 'gg_claim_evidences'
    evidence_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gg_claim_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('gg_claims.gg_claim_id'), nullable=False)
    evidence_file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=True)
    upload_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    uploaded_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class GGClaimResolution(Base):
    """(10.9) جدول سجل حلول مطالبات الضمان الذهبي."""
    __tablename__ = 'gg_claim_resolutions'
    resolution_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gg_claim_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('gg_claims.gg_claim_id'), nullable=False)
    gg_resolution_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('gg_resolution_types.gg_resolution_type_id'), nullable=False)
    resolution_notes: Mapped[str] = mapped_column(Text, nullable=True)
    refund_amount_approved: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    replacement_order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.order_id'), nullable=True)
    resolution_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    resolved_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())