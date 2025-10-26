# backend\src\market\models\shipments_models.py
from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey, Date
)
from sqlalchemy.orm import Mapped, mapped_column, relationship 
from typing import List, Optional

from src.db.base_class import Base

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class Shipment(Base):
    """(4.د.1) جدول الشحنات المرتبطة بالطلبات."""
    __tablename__ = 'shipments'
    shipment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.order_id'), nullable=False)
    shipping_carrier_name: Mapped[str] = mapped_column(String(255), nullable=True)
    tracking_number: Mapped[str] = mapped_column(String(100), nullable=True)
    shipment_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('shipment_statuses.shipment_status_id'), nullable=False)
    estimated_shipping_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    actual_shipping_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    estimated_delivery_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    shipping_address_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('addresses.address_id'), nullable=True)
    shipping_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    shipping_notes: Mapped[str] = mapped_column(Text, nullable=True)
    shipped_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    # علاقات مع مودلات من مجموعات أخرى أو مودلات لم تُستورد مباشرةً:
    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id], lazy="selectin") # علاقة بالطلب الأب
    shipment_status: Mapped["ShipmentStatus"] = relationship("ShipmentStatus", foreign_keys=[shipment_status_id], lazy="selectin") # علاقة بحالة الشحن
    shipping_address: Mapped[Optional["Address"]] = relationship("Address", foreign_keys=[shipping_address_id], lazy="selectin") # علاقة بعنوان الشحن
    shipped_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[shipped_by_user_id], lazy="selectin") # علاقة بالمستخدم الذي قام بالشحن

    # علاقة ببنود الشحنة (Shipment Items)
    items: Mapped[List["ShipmentItem"]] = relationship(back_populates="shipment", cascade="all, delete-orphan") # علاقة ببنود الشحنة

class ShipmentItem(Base):
    """(4.د.4) جدول بنود الشحنة (للشحنات الجزئية)."""
    __tablename__ = 'shipment_items'
    shipment_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('shipments.shipment_id'), nullable=False)
    order_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('order_items.order_item_id'), nullable=False)
    quantity_shipped: Mapped[float] = mapped_column(Numeric, nullable=False)
    item_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- SQLAlchemy Relationships ---
    # علاقة بالشحنة الأب
    shipment: Mapped["Shipment"] = relationship(back_populates="items")

    # علاقة ببنود الطلب الأب (لربط بنود الشحنة بالبنود الأصلية في الطلب)
    order_item: Mapped["OrderItem"] = relationship("OrderItem", foreign_keys=[order_item_id], lazy="selectin")
