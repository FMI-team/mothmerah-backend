from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, BigInteger,
    func, TIMESTAMP, text, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from src.db.base_class import Base

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class InventoryItem(Base):
    """(2.د.1) جدول عناصر المخزون الفعلية للبائعين."""
    __tablename__ = 'inventory_items'
    inventory_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_packaging_option_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('product_packaging_options.packaging_option_id'), nullable=False)
    seller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    on_hand_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    inventory_item_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('inventory_item_statuses.inventory_item_status_id'), nullable=False)
    last_restock_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    location_identifier: Mapped[str] = mapped_column(String(100), nullable=True, comment="لتحديد موقع المخزون في مستودع البائع")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('available_quantity >= 0', name='chk_available_quantity_positive'),
        CheckConstraint('reserved_quantity >= 0', name='chk_reserved_quantity_positive'),
        CheckConstraint('on_hand_quantity >= 0', name='chk_on_hand_quantity_positive'),
    )

    # ...
    status: Mapped["InventoryItemStatus"] = relationship("InventoryItemStatus", foreign_keys=[inventory_item_status_id], lazy="selectin")
    transactions: Mapped[list["InventoryTransaction"]] = relationship(
        "InventoryTransaction", back_populates="inventory_item", cascade="all, delete-orphan"
    )
    # ...


class InventoryTransaction(Base):
    """(2.د.4) جدول حركات المخزون (سجل تدقيق لكل تغيير)."""
    __tablename__ = 'inventory_transactions'
    transaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('inventory_items.inventory_item_id'), nullable=False)
    transaction_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('inventory_transaction_types.transaction_type_id'), nullable=False)
    quantity_changed: Mapped[int] = mapped_column(Integer, nullable=False, comment="قيمة موجبة للإضافة، سالبة للخصم")
    balance_after_transaction: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    related_order_id: Mapped[int] = mapped_column(BigInteger, nullable=True) # سيتم ربطه لاحقًا بجدول الطلبات
    related_auction_id: Mapped[int] = mapped_column(BigInteger, nullable=True) # سيتم ربطه لاحقًا بجدول المزادات
    reason_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    inventory_item: Mapped["InventoryItem"] = relationship(
        "InventoryItem", back_populates="transactions"
    )