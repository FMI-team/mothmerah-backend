# backend\src\market\models\quotes_models.py
from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column,relationship

from src.db.base_class import Base

from uuid import uuid4

class Quote(Base):
    """(4.ج.1) جدول عروض الأسعار المقدمة ردًا على RFQ."""
    __tablename__ = 'quotes'
    quote_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rfq_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('rfqs.rfq_id'), nullable=False)
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    seller_user: Mapped["User"] = relationship(
        "User",
        back_populates="quotes_as_seller",
        foreign_keys=[seller_user_id]
    )
    submission_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    total_quote_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_terms_key: Mapped[str] = mapped_column(String(255), nullable=True)
    delivery_terms_key: Mapped[str] = mapped_column(String(255), nullable=True)
    validity_period_days: Mapped[int] = mapped_column(Integer, nullable=True)
    expiry_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    quote_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('quote_statuses.quote_status_id'), nullable=False)
    seller_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # --- SQLAlchemy Relationships ---
    # علاقات مع مودلات من مجموعات أخرى أو مودلات لم تُستورد مباشرةً:
    rfq: Mapped["Rfq"] = relationship("Rfq", foreign_keys=[rfq_id], back_populates="quotes", lazy="selectin") # علاقة بطلب عرض الأسعار الأب
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_user_id], lazy="selectin", overlaps="seller_user") # علاقة بالبائع مقدم العرض
    quote_status: Mapped["QuoteStatus"] = relationship("QuoteStatus", foreign_keys=[quote_status_id], lazy="selectin") # علاقة بحالة عرض السعر

    # علاقة ببنود عرض السعر (Quote Items)
    items: Mapped[list["QuoteItem"]] = relationship(back_populates="quote", cascade="all, delete-orphan") # علاقة ببنود العرض

class QuoteItem(Base):
    """(4.ج.2) جدول بنود عرض السعر."""
    __tablename__ = 'quote_items'
    quote_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    quote_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('quotes.quote_id'), nullable=False)
    rfq_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('rfq_items.rfq_item_id'), nullable=False)
    offered_product_description: Mapped[str] = mapped_column(Text, nullable=True)
    offered_quantity: Mapped[float] = mapped_column(Numeric, nullable=False)
    unit_price_offered: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_item_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    item_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # --- SQLAlchemy Relationships ---
    # علاقة بعرض السعر الأب
    quote: Mapped["Quote"] = relationship(back_populates="items")

    # علاقة ببنود طلب عرض الأسعار الأب (لربط العرض بالطلب الأصلي)
    rfq_item: Mapped["RfqItem"] = relationship("RfqItem", foreign_keys=[rfq_item_id], lazy="selectin")
