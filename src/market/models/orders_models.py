# backend\src\market\models\orders_models.py
from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey, CheckConstraint 
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column  ,relationship 
from typing import List, Optional
from uuid import uuid4

from src.db.base_class import Base

# TODO: يمكن استيراد المودلز المرتبطة مباشرة هنا إذا لزم الأمر
# لضمان Type Hinting صحيح في العلاقات، لكن ليس ضرورياً لعمل SQLAlchemy
# from src.users.models.core_models import User
# from src.products.models.units_models import ProductPackagingOption
# from src.lookups.models import OrderStatus, OrderItemStatus, Currency, Address

class Order(Base):
    """(4.أ.1) جدول الطلبات العادية."""
    __tablename__ = 'orders'
    # order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4) # SQLite compatible
    buyer_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    seller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    order_reference_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    order_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    order_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('order_statuses.order_status_id'), nullable=False)
    total_amount_before_discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True, server_default=text("0.00"))
    total_amount_after_discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    vat_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True, server_default=text("0.00"))
    final_total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('currencies.currency_code'), nullable=False)
    shipping_address_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('addresses.address_id'), nullable=True)
    billing_address_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('addresses.address_id'), nullable=True)
    payment_method_id: Mapped[int] = mapped_column(Integer, nullable=True)
    payment_status_id: Mapped[int] = mapped_column(Integer, ForeignKey("payment_statuses.payment_status_id"), nullable=True)
    source_of_order: Mapped[str] = mapped_column(String(50), nullable=True)
    related_quote_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("quotes.quote_id"), nullable=True)
    related_auction_settlement_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    notes_from_buyer: Mapped[str] = mapped_column(Text, nullable=True)
    notes_from_seller: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    # items: Mapped[list["OrderItem"]] = relationship(cascade="all, delete-orphan")
    items: Mapped[list["OrderItem"]] = relationship(cascade="all, delete-orphan", back_populates="order") # علاقة بالبنود
    # استخدام اسم المودل كسلسلة نصية "ModelName"
    buyer: Mapped["User"] = relationship("User", foreign_keys=[buyer_user_id], lazy="selectin") # علاقة بالمشتري
    seller: Mapped[Optional["User"]] = relationship("User", foreign_keys=[seller_user_id], lazy="selectin") # علاقة بالبائع
    status: Mapped["OrderStatus"] = relationship("OrderStatus", foreign_keys=[order_status_id], lazy="selectin") # علاقة بحالة الطلب
    currency: Mapped["Currency"] = relationship("Currency", foreign_keys=[currency_code], lazy="selectin") # علاقة بالعملة
    shipping_address: Mapped[Optional["Address"]] = relationship("Address", foreign_keys=[shipping_address_id], lazy="selectin") # علاقة بعنوان الشحن
    billing_address: Mapped[Optional["Address"]] = relationship("Address", foreign_keys=[billing_address_id], lazy="selectin") # علاقة بعنوان الفوترة
    payment_status: Mapped[Optional["PaymentStatus"]] = relationship("PaymentStatus", foreign_keys=[payment_status_id], lazy="selectin") # علاقة بحالة الدفع
    related_quote: Mapped[Optional["Quote"]] = relationship("Quote", foreign_keys=[related_quote_id], lazy="selectin") # علاقة بعرض السعر المرتبط
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="related_order", lazy="selectin")
    # TODO: related_auction_settlement: Mapped[Optional["AuctionSettlement"]] = relationship("AuctionSettlement", foreign_keys=[related_auction_settlement_id], lazy="selectin") # علاقة بتسوية المزاد (إذا تم تعريف AuctionSettlement)

    history: Mapped[List["OrderStatusHistory"]] = relationship(back_populates="order", cascade="all, delete-orphan") # علاقة بسجل تغييرات الحالة

class OrderItem(Base):
    """(4.أ.2) جدول بنود الطلب."""
    __tablename__ = 'order_items'
    order_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.order_id', ondelete="CASCADE"))
    product_packaging_option_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('product_packaging_options.packaging_option_id'), nullable=False)
    seller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    # quantity_ordered: Mapped[float] = mapped_column(Numeric, nullable=False)
    quantity_ordered: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price_at_purchase: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_price_for_item: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    # item_status_id: Mapped[int] = mapped_column(Integer, nullable=True)
    item_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('order_item_statuses.item_status_id'), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (CheckConstraint('quantity_ordered > 0', name='chk_quantity_ordered_positive'),)

    # --- SQLAlchemy Relationships ---
    order: Mapped["Order"] = relationship(back_populates="items") # علاقة بالطلب الأب
    # العلاقات مع مودلات من مجموعات أخرى
    packaging_option: Mapped["ProductPackagingOption"] = relationship("ProductPackagingOption", foreign_keys=[product_packaging_option_id], lazy="selectin") # علاقة بخيار التعبئة
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_user_id], lazy="selectin") # علاقة بالبائع (لهذا البند)
    item_status: Mapped[Optional["OrderItemStatus"]] = relationship("OrderItemStatus", foreign_keys=[item_status_id], lazy="selectin") # علاقة بحالة البند

class OrderStatusHistory(Base):
    """(4.أ.5) جدول سجل تغييرات حالة الطلب."""
    __tablename__ = 'order_status_history'
    order_status_history_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.order_id'), nullable=False)
    old_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('order_statuses.order_status_id'), nullable=True)
    new_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('order_statuses.order_status_id'), nullable=False)
    change_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    changed_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- SQLAlchemy Relationships ---
    order: Mapped["Order"] = relationship(back_populates="history") # علاقة بالطلب الأب
    # العلاقات مع مودلات من جداول lookups (حالات الطلب) ومودل المستخدم
    old_status: Mapped[Optional["OrderStatus"]] = relationship("OrderStatus", foreign_keys=[old_status_id], lazy="selectin", post_update=True) # العلاقة بالحالة القديمة (post_update لتجنب Circular Cascade)
    new_status: Mapped["OrderStatus"] = relationship("OrderStatus", foreign_keys=[new_status_id], lazy="selectin") # العلاقة بالحالة الجديدة
    changed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[changed_by_user_id], lazy="selectin") # علاقة بالمستخدم الذي أجرى التغيير (قد يكون NULL للنظام)
