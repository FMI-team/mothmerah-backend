from datetime import datetime
from sqlalchemy import (Integer, String, Text, BigInteger, Numeric, func, TIMESTAMP, text, ForeignKey, JSON)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base_class import Base

from uuid import uuid4

class Wallet(Base):
    """(8.أ.1) محافظ المستخدمين."""
    __tablename__ = 'wallets'
    wallet_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), unique=True, nullable=False)
    current_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0.00"))
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('currencies.currency_code'), nullable=False)
    wallet_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('wallet_statuses.wallet_status_id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class WalletTransaction(Base):
    """(8.أ.2) معاملات المحفظة."""
    __tablename__ = 'wallet_transactions'
    wallet_transaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    wallet_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('wallets.wallet_id'), nullable=False)
    transaction_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('transaction_types.transaction_type_id'), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('currencies.currency_code'), nullable=False)
    transaction_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    current_balance_after_transaction: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    related_order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.order_id'), nullable=True)
    related_auction_settlement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('auction_settlements.settlement_id'), nullable=True)
    related_payment_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('payment_records.payment_record_id'), nullable=True)
    related_withdrawal_request_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('withdrawal_requests.withdrawal_request_id'), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'COMPLETED'"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())