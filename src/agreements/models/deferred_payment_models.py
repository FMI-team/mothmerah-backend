from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey, Date
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base_class import Base

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class DeferredPaymentAgreement(Base):
    """(9.1) جدول اتفاقيات الدفع الآجل."""
    __tablename__ = 'deferred_payment_agreements'
    deferred_payment_agreement_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    related_order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.order_id'), nullable=True)
    related_auction_settlement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('auction_settlements.settlement_id'), nullable=True)
    seller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    buyer_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    total_agreement_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    agreement_terms_text: Mapped[str] = mapped_column(Text, nullable=True)
    number_of_installments: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    first_installment_due_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    installment_frequency_days: Mapped[int] = mapped_column(Integer, nullable=True)
    agreement_creation_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    deferred_payment_agreement_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('deferred_payment_agreement_statuses.deferred_payment_agreement_status_id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)

class DeferredPaymentInstallment(Base):
    """(9.4) جدول الأقساط المستحقة لاتفاقيات الدفع الآجل."""
    __tablename__ = 'deferred_payment_installments'
    installment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    deferred_payment_agreement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('deferred_payment_agreements.deferred_payment_agreement_id'), nullable=False)
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    amount_due: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0.00"))
    installment_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('installment_statuses.installment_status_id'), nullable=False)
    last_payment_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class InstallmentPaymentRecord(Base):
    """(9.7) جدول سجلات مدفوعات الأقساط."""
    __tablename__ = 'installment_payment_records'
    payment_record_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    installment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('deferred_payment_installments.installment_id'), nullable=False)
    payment_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    payment_method_key: Mapped[str] = mapped_column(String(50), nullable=True)
    transaction_reference: Mapped[str] = mapped_column(String(255), nullable=True)
    recorded_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class DeferredPaymentAgreementDocument(Base):
    """(9.8) جدول وثائق اتفاقيات الدفع الآجل."""
    __tablename__ = 'deferred_payment_agreement_documents'
    document_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    deferred_payment_agreement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('deferred_payment_agreements.deferred_payment_agreement_id'), nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type_key: Mapped[str] = mapped_column(String(50), nullable=True)
    document_url: Mapped[str] = mapped_column(String(512), nullable=False)
    upload_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    uploaded_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())