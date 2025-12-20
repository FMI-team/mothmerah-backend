from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column,relationship
from typing import List, Optional

from src.db.base_class import Base

from uuid import uuid4

class AuctionParticipant(Base):
    """(5.ب.1) جدول المشاركين في المزاد."""
    __tablename__ = 'auction_participants'
    auction_participant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auction_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auctions.auction_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    participation_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    participation_status: Mapped[str] = mapped_column(String(50), nullable=True, comment="e.g., 'REGISTERED', 'APPROVED_TO_BID', 'BLOCKED'")

    # --- SQLAlchemy Relationships ---
    auction: Mapped["Auction"] = relationship("Auction", back_populates="participants", foreign_keys=[auction_id], lazy="selectin") # علاقة بالمزاد الأب
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin") # علاقة بالمستخدم المشارك


class Bid(Base):
    """(5.ب.2) جدول المزايدات التي تتم على المزادات أو لوطاتها."""
    __tablename__ = 'bids'
    bid_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auction_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auctions.auction_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    lot_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auction_lots.lot_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    bidder_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    bid_amount_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    bid_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    bid_status: Mapped[str] = mapped_column(String(50), nullable=True, comment="e.g., 'ACTIVE_HIGHEST', 'OUTBID', 'WINNING_BID'")
    is_auto_bid: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    # --- SQLAlchemy Relationships ---
    auction: Mapped["Auction"] = relationship("Auction", back_populates="bids", foreign_keys=[auction_id], lazy="selectin") # علاقة بالمزاد الأب
    lot: Mapped[Optional["AuctionLot"]] = relationship("AuctionLot", back_populates="bids", foreign_keys=[lot_id], lazy="selectin") # علاقة باللوت (إذا كانت المزايدة على لوت)
    bidder: Mapped["User"] = relationship("User", foreign_keys=[bidder_user_id], lazy="selectin") # علاقة بالمستخدم المزايد

class AutoBidSetting(Base):
    """(5.ب.3) جدول إعدادات المزايدة الآلية للمستخدم في مزاد معين."""
    __tablename__ = 'auto_bid_settings'
    auto_bid_setting_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auction_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auctions.auction_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    max_bid_amount_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    increment_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('auction_id', 'user_id', name='uq_user_auction_auto_bid'),
    )

    # --- SQLAlchemy Relationships ---
    auction: Mapped["Auction"] = relationship("Auction", back_populates="auto_bid_settings", foreign_keys=[auction_id], lazy="selectin") # علاقة بالمزاد الأب
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin") # علاقة بالمستخدم صاحب الإعداد

class AuctionWatchlist(Base):
    """(5.ب.4) جدول قوائم مراقبة المزادات للمستخدمين."""
    __tablename__ = 'auction_watchlists'
    watchlist_entry_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    auction_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auctions.auction_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    added_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'auction_id', name='uq_user_auction_watchlist'),
    )

    # --- SQLAlchemy Relationships ---
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin") # علاقة بالمستخدم صاحب قائمة المراقبة
    auction: Mapped["Auction"] = relationship("Auction", back_populates="watchlists", foreign_keys=[auction_id], lazy="selectin") # علاقة بالمزاد الذي يتم مراقبته
