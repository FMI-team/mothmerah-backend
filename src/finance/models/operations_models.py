from datetime import datetime
from sqlalchemy import (Integer, String, Text, BigInteger, Numeric, func, TIMESTAMP, text, ForeignKey, JSON)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base_class import Base

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class PaymentRecord(Base):
    """(8.ب.2) سجلات عمليات الدفع عبر البوابات."""
    __tablename__ = 'payment_records'
    payment_record_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    wallet_transaction_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('wallet_transactions.wallet_transaction_id'), nullable=True)
    order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.order_id'), nullable=True)
    gateway_id: Mapped[int] = mapped_column(Integer, ForeignKey('payment_gateways.gateway_id'), nullable=False)
    gateway_transaction_reference: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payment_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('currencies.currency_code'), nullable=False)
    payment_status_from_gateway: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_method_used: Mapped[str] = mapped_column(String(50), nullable=True)
    payment_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    gateway_response_payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class WithdrawalRequest(Base):
    """(8.ب.3) طلبات سحب الرصيد من المحفظة."""
    __tablename__ = 'withdrawal_requests'
    withdrawal_request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    wallet_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('wallets.wallet_id'), nullable=False)
    amount_requested: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('currencies.currency_code'), nullable=False)
    beneficiary_bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    beneficiary_iban: Mapped[str] = mapped_column(String(34), nullable=False)
    beneficiary_account_name: Mapped[str] = mapped_column(String(150), nullable=False)
    request_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    withdrawal_request_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('withdrawal_request_statuses.withdrawal_request_status_id'), nullable=False)
    admin_notes: Mapped[str] = mapped_column(Text, nullable=True)
    processed_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    processed_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    transaction_reference: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())