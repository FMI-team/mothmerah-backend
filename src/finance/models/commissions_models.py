from datetime import datetime
from sqlalchemy import (Integer, String, Text, BigInteger, Numeric, func, TIMESTAMP, text, ForeignKey)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base_class import Base

from uuid import uuid4

class PlatformCommission(Base):
    """(8.ج.1) عمولات المنصة المحتسبة."""
    __tablename__ = 'platform_commissions'
    commission_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    transaction_entity_id: Mapped[str] = mapped_column(String, nullable=False) # UUID or BigInt as String
    transaction_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    seller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    commission_basis_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    commission_rate_applied: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    commission_amount_calculated: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('currencies.currency_code'), nullable=False)
    calculation_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    commission_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'CALCULATED'"))
    related_payment_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('payment_records.payment_record_id'), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())