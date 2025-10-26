# backend\src\auctions\models\settlements_models.py

from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional # تأكد من استيراد List و Optional

from src.db.base_class import Base

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

# =================================================================
# المجموعة 5.3: جداول المجموعة 5.ج (تسويات المزادات)
# =================================================================

class AuctionSettlementStatus(Base):
    """
    (5.ج.2) جدول حالات تسوية المزاد: يحدد الحالات المختلفة التي يمكن أن تمر بها عملية تسوية المزاد.
    مثلاً: 'قيد الدفع', 'تم الدفع', 'تم التسوية للبائع', 'فشل الدفع'.
    """
    __tablename__ = 'auction_settlement_statuses'
    settlement_status_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="مفتاح فريد لاسم الحالة للترجمة.")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["AuctionSettlementStatusTranslation"]] = relationship(
        back_populates="auction_settlement_status", cascade="all, delete-orphan" # علاقة بترجمات الحالة
    )
    # التسويات التي تحمل هذه الحالة (علاقة عكسية)
    settlements: Mapped[List["AuctionSettlement"]] = relationship("AuctionSettlement", back_populates="settlement_status")


class AuctionSettlementStatusTranslation(Base):
    """
    (5.ج.3) جدول ترجمات حالات تسوية المزاد.
    """
    __tablename__ = 'auction_settlement_status_translations'
    settlement_status_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('auction_settlement_statuses.settlement_status_id', ondelete="CASCADE"), primary_key=True
    )
    language_code: Mapped[str] = mapped_column(
        String(10), ForeignKey('languages.language_code'), primary_key=True
    )
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # وصف مطول للحالة
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    auction_settlement_status: Mapped["AuctionSettlementStatus"] = relationship(back_populates="translations") # علاقة بحالة التسوية الأب


class AuctionSettlement(Base):
    """(5.ج.1) جدول تسويات المزاد لتوثيق النتائج المالية."""
    __tablename__ = 'auction_settlements'
    settlement_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auction_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auctions.auction_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    winning_bid_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('bids.bid_id', ondelete='RESTRICT', onupdate='CASCADE'), unique=True, nullable=False)
    winner_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    seller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    final_winning_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_won: Mapped[float] = mapped_column(Numeric, nullable=False)
    total_settlement_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    net_amount_to_seller: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    settlement_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('auction_settlement_statuses.settlement_status_id'), nullable=False)
    settlement_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # الأعمدة التالية سيتم تفعيل علاقاتها (Foreign Keys) بعد إنشاء المجموعة 8
    # ...
    platform_commission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('platform_commissions.commission_id', ondelete='SET NULL'), nullable=True)
    payment_transaction_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('wallet_transactions.wallet_transaction_id'), nullable=True)
    payout_transaction_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('wallet_transactions.wallet_transaction_id'), nullable=True)
    # ...
    
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
 
     # --- SQLAlchemy Relationships ---
    # علاقات مع مودلات من مجموعات أخرى أو مودلات لم تُستورد مباشرةً:
    auction: Mapped["Auction"] = relationship("Auction", foreign_keys=[auction_id], lazy="selectin") # المزاد الذي تمت التسوية له
    winning_bid: Mapped["Bid"] = relationship("Bid", foreign_keys=[winning_bid_id], lazy="selectin") # المزايدة الفائزة
    winner_user: Mapped["User"] = relationship("User", foreign_keys=[winner_user_id], lazy="selectin") # المستخدم الفائز
    seller_user: Mapped["User"] = relationship("User", foreign_keys=[seller_user_id], lazy="selectin") # البائع
    settlement_status: Mapped["AuctionSettlementStatus"] = relationship("AuctionSettlementStatus", foreign_keys=[settlement_status_id], back_populates="settlements", lazy="selectin") # حالة التسوية
    
    # العلاقات مع مودلات من المجموعة 8 (المحفظة والمدفوعات)
    # TODO: platform_commission: Mapped[Optional["PlatformCommission"]] = relationship("PlatformCommission", foreign_keys=[AuctionSettlement.platform_commission_id], lazy="selectin")
    # TODO: payment_transaction: Mapped[Optional["WalletTransaction"]] = relationship("WalletTransaction", foreign_keys=[AuctionSettlement.payment_transaction_id], lazy="selectin")
    # TODO: payout_transaction: Mapped[Optional["WalletTransaction"]] = relationship("WalletTransaction", foreign_keys=[AuctionSettlement.payout_transaction_id], lazy="selectin")

