from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey, Date
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base_class import Base

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class ResellerInventoryItem(Base):
    """(7.1) جدول بنود مخزون المندوب لإعادة البيع."""
    __tablename__ = 'reseller_inventory_items'
    reseller_inventory_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reseller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    source_product_packaging_option_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('product_packaging_options.packaging_option_id'), nullable=False)
    source_purchase_order_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('order_items.order_item_id'), nullable=True)
    quantity_purchased: Mapped[float] = mapped_column(Numeric, nullable=False)
    available_quantity_for_resale: Mapped[float] = mapped_column(Numeric, nullable=False)
    cost_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    acquisition_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=True, comment="e.g., 'AVAILABLE', 'SOLD_OUT'")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ResellerSalesOffer(Base):
    """(7.2) جدول عروض البيع التي يقدمها المندوبون لعملائهم."""
    __tablename__ = 'reseller_sales_offers'
    sales_offer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reseller_inventory_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('reseller_inventory_items.reseller_inventory_item_id'), nullable=False)
    resale_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    resale_unit_of_measure_id: Mapped[int] = mapped_column(Integer, ForeignKey('units_of_measure.unit_id'), nullable=True)
    minimum_order_quantity: Mapped[float] = mapped_column(Numeric, nullable=True)
    custom_offer_title_key: Mapped[str] = mapped_column(String(255), nullable=True)
    custom_offer_description_key: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    available_from_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    available_until_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ResellerSalesOfferTranslation(Base):
    """(7.3) جدول ترجمات عروض بيع المندوبين."""
    __tablename__ = 'reseller_sales_offer_translations'
    # offer_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sales_offer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('reseller_sales_offers.sales_offer_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_offer_title: Mapped[str] = mapped_column(String(255), nullable=False)
    translated_offer_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ResellerCustomerOrder(Base):
    """(7.5) جدول طلبات عملاء المندوبين."""
    __tablename__ = 'reseller_customer_orders'
    customer_order_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reseller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    end_customer_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    customer_address_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('addresses.address_id'), nullable=True)
    order_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    order_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('order_statuses.order_status_id'), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(50), nullable=True, comment="e.g., 'PAID', 'UNPAID'")
    delivery_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ResellerCustomerOrderItem(Base):
    """(7.6) جدول بنود طلبات عملاء المندوبين."""
    __tablename__ = 'reseller_customer_order_items'
    customer_order_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('reseller_customer_orders.customer_order_id'), nullable=False)
    reseller_sales_offer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('reseller_sales_offers.sales_offer_id'), nullable=False)
    quantity_ordered: Mapped[float] = mapped_column(Numeric, nullable=False)
    price_per_unit_charged: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_item_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ResellerInventoryTransaction(Base):
    """(7.4) جدول حركات مخزون المندوبين لإعادة البيع."""
    __tablename__ = 'reseller_inventory_transactions'
    reseller_inv_transaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reseller_inventory_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('reseller_inventory_items.reseller_inventory_item_id'), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_changed: Mapped[float] = mapped_column(Numeric, nullable=False)
    transaction_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    related_customer_order_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('reseller_customer_order_items.customer_order_item_id'), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())