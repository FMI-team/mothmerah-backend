# backend\src\market\models\rfqs_models.py
from datetime import datetime
from sqlalchemy import (JSON, Integer, String, Text, Boolean, BigInteger, Numeric, func, TIMESTAMP, text, ForeignKey, Date)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from src.db.base_class import Base

from uuid import uuid4

class Rfq(Base):
    """(4.ب.1) جدول طلبات عروض الأسعار - Request For Quotations."""
    __tablename__ = 'rfqs'
    rfq_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    buyer_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    rfq_reference_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    submission_deadline: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    delivery_deadline: Mapped[datetime] = mapped_column(Date, nullable=True)
    delivery_address_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('addresses.address_id'), nullable=True)
    payment_terms_preference: Mapped[str] = mapped_column(Text, nullable=True)
    rfq_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('rfq_statuses.rfq_status_id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # --- SQLAlchemy Relationships ---
    # علاقات مع مودلات من مجموعات أخرى أو مودلات لم تُستورد مباشرةً:
    # buyer: Mapped["User"] = relationship("User", foreign_keys=[Rfq.buyer_user_id], lazy="selectin") # علاقة بالمشتري
    buyer: Mapped["User"] = relationship("User", foreign_keys=[buyer_user_id], lazy="selectin") # علاقة بالمشتري
    delivery_address: Mapped[Optional["Address"]] = relationship("Address", foreign_keys=[delivery_address_id], lazy="selectin") # علاقة بعنوان التسليم
    rfq_status: Mapped["RfqStatus"] = relationship("RfqStatus", foreign_keys=[rfq_status_id], lazy="selectin") # علاقة بحالة طلب عرض الأسعار

    # علاقة ببنود طلب عرض الأسعار (RfQ Items)
    items: Mapped[list["RfqItem"]] = relationship(back_populates="rfq", cascade="all, delete-orphan") # علاقة ببنود الـ RFQ

    # علاقة بعروض الأسعار المرتبطة بهذا الـ RFQ
    quotes: Mapped[list["Quote"]] = relationship("Quote", back_populates="rfq", cascade="all, delete-orphan") # علاقة بعروض الأسعار

class RfqItem(Base):
    """(4.ب.2) جدول بنود طلب عرض السعر."""
    __tablename__ = 'rfq_items'
    rfq_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rfq_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('rfqs.rfq_id'), nullable=False)
    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=True)
    custom_product_description: Mapped[str] = mapped_column(Text, nullable=True)
    quantity_requested: Mapped[float] = mapped_column(Numeric, nullable=False)
    unit_of_measure_id: Mapped[int] = mapped_column(Integer, ForeignKey('units_of_measure.unit_id'), nullable=False)
    required_specifications: Mapped[dict] = mapped_column(JSON, nullable=True)
    target_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # --- SQLAlchemy Relationships ---
    # علاقة بطلب عرض الأسعار الأب
    rfq: Mapped["Rfq"] = relationship(back_populates="items")

    # علاقات مع مودلات من مجموعات أخرى:
    product: Mapped[Optional["Product"]] = relationship("Product", foreign_keys=[product_id], lazy="selectin") # علاقة بالمنتج (إذا كان موجوداً بالكتالوج)
    unit_of_measure: Mapped["UnitOfMeasure"] = relationship("UnitOfMeasure", foreign_keys=[unit_of_measure_id], lazy="selectin") # علاقة بوحدة القياس
