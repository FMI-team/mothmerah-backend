from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column,relationship
from typing import List, Optional

from src.db.base_class import Base

from uuid import uuid4

class Auction(Base):
    """(5.أ.1) الجدول الرئيسي للمزادات."""
    __tablename__ = 'auctions'
    auction_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    seller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=False)
    auction_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('auction_types.auction_type_id'), nullable=False)
    auction_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('auction_statuses.auction_status_id'), nullable=False)
    auction_title_key: Mapped[str] = mapped_column(String(255), nullable=True)
    custom_auction_title: Mapped[str] = mapped_column(Text, nullable=True)
    auction_description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    custom_auction_description: Mapped[str] = mapped_column(Text, nullable=True)
    start_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    end_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    starting_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    minimum_bid_increment: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reserve_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    quantity_offered: Mapped[float] = mapped_column(Numeric, nullable=False)
    unit_of_measure_id_for_quantity: Mapped[int] = mapped_column(Integer, ForeignKey('units_of_measure.unit_id'), nullable=False)
    current_highest_bid_amount_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    current_highest_bidder_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    total_bids_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_private_auction: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    pre_arrival_shipping_info: Mapped[str] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    # علاقات مع مودلات من مجموعات أخرى
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_user_id], lazy="selectin")
    product: Mapped["Product"] = relationship("Product", foreign_keys=[product_id], lazy="selectin")
    unit_of_measure: Mapped["UnitOfMeasure"] = relationship("UnitOfMeasure", foreign_keys=[unit_of_measure_id_for_quantity], lazy="selectin") # علاقة بوحدة القياس
    auction_type: Mapped["AuctionType"] = relationship("AuctionType", foreign_keys=[auction_type_id], back_populates="auctions", lazy="selectin")
    auction_status: Mapped["AuctionStatus"] = relationship("AuctionStatus", foreign_keys=[auction_status_id], back_populates="auctions", lazy="selectin")
    current_highest_bidder: Mapped[Optional["User"]] = relationship("User", foreign_keys=[current_highest_bidder_user_id], lazy="selectin")

    # علاقات المزادات بكياناتها الفرعية (لوطات، مشاركين، مزايدات، إعدادات، قوائم مراقبة، تسويات)
    lots: Mapped[List["AuctionLot"]] = relationship(back_populates="auction", cascade="all, delete-orphan")
    # TODO: علاقات مع Participants, Bids, AutoBidSettings, AuctionWatchlists من ملف Bidding Models
    participants: Mapped[List["AuctionParticipant"]] = relationship("AuctionParticipant", foreign_keys="[AuctionParticipant.auction_id]", back_populates="auction", cascade="all, delete-orphan")
    bids: Mapped[List["Bid"]] = relationship("Bid", foreign_keys="[Bid.auction_id]", back_populates="auction", cascade="all, delete-orphan")
    auto_bid_settings: Mapped[List["AutoBidSetting"]] = relationship("AutoBidSetting", foreign_keys="[AutoBidSetting.auction_id]", back_populates="auction", cascade="all, delete-orphan")
    watchlists: Mapped[List["AuctionWatchlist"]] = relationship("AuctionWatchlist", foreign_keys="[AuctionWatchlist.auction_id]", back_populates="auction", cascade="all, delete-orphan")
    # TODO: علاقة مع Settlements من ملف Settlements Models
    settlements: Mapped[List["AuctionSettlement"]] = relationship("AuctionSettlement", foreign_keys="[AuctionSettlement.auction_id]", back_populates="auction", cascade="all, delete-orphan")

class AuctionLot(Base):
    """(5.أ.6) جدول لوطات/دفعات المزاد."""
    __tablename__ = 'auction_lots'
    lot_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    auction_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auctions.auction_id'), nullable=False)
    lot_title_key: Mapped[str] = mapped_column(String(255), nullable=True)
    custom_lot_title: Mapped[str] = mapped_column(Text, nullable=True)
    lot_description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    custom_lot_description: Mapped[str] = mapped_column(Text, nullable=True)
    quantity_in_lot: Mapped[float] = mapped_column(Numeric, nullable=True)
    lot_starting_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    lot_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('auction_statuses.auction_status_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


    # --- SQLAlchemy Relationships ---
    auction: Mapped["Auction"] = relationship(back_populates="lots")
    lot_status: Mapped[Optional["AuctionStatus"]] = relationship("AuctionStatus", foreign_keys=[lot_status_id], lazy="selectin")

    # علاقات بكيانات اللوت الفرعية
    translations: Mapped[List["AuctionLotTranslation"]] = relationship(back_populates="auction_lot", cascade="all, delete-orphan")
    products_in_lot: Mapped[List["LotProduct"]] = relationship(back_populates="auction_lot", cascade="all, delete-orphan")
    images: Mapped[List["LotImage"]] = relationship(back_populates="auction_lot", cascade="all, delete-orphan")
    # TODO: علاقة مع Bids من ملف Bidding Models
    bids: Mapped[List["Bid"]] = relationship(
        "Bid",
        foreign_keys="[Bid.lot_id]",
        back_populates="lot",
        cascade="all, delete-orphan"
    )

class AuctionLotTranslation(Base):
    """(5.أ.7) جدول ترجمات لوطات المزاد."""
    __tablename__ = 'auction_lot_translations'
    lot_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lot_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auction_lots.lot_id'), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), nullable=False)
    translated_lot_title: Mapped[str] = mapped_column(String(255), nullable=True)
    translated_lot_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    auction_lot: Mapped["AuctionLot"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")

class LotProduct(Base):
    """(5.أ.8) جدول منتجات اللوت (للّوطات المجمعة)."""
    __tablename__ = 'lot_products'
    lot_product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lot_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auction_lots.lot_id'), nullable=False)
    packaging_option_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('product_packaging_options.packaging_option_id'), nullable=False)
    quantity_in_lot: Mapped[float] = mapped_column(Numeric, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- SQLAlchemy Relationships ---
    auction_lot: Mapped["AuctionLot"] = relationship(back_populates="products_in_lot") # علاقة بلوت المزاد الأب
    # علاقة بـ ProductPackagingOption من المجموعة 2
    packaging_option: Mapped["ProductPackagingOption"] = relationship("ProductPackagingOption", foreign_keys=[packaging_option_id], lazy="selectin")

class LotImage(Base):
    """(5.أ.9) جدول صور اللوت."""
    __tablename__ = 'lot_images'
    lot_image_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lot_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('auction_lots.lot_id'), nullable=False)
    image_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('images.image_id'), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- SQLAlchemy Relationships ---
    auction_lot: Mapped["AuctionLot"] = relationship(back_populates="images") # علاقة بلوت المزاد الأب
    # علاقة بـ Image من المجموعة 2
    image: Mapped["Image"] = relationship("Image", foreign_keys=[image_id], lazy="selectin")

