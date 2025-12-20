from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey, Date )
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from src.db.base_class import Base

from uuid import uuid4

class ExpectedCrop(Base):
    """(2.هـ.1) جدول المحاصيل المتوقعة التي يعرضها المنتجون."""
    __tablename__ = 'expected_crops'
    expected_crop_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    producer_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=True)
    custom_product_name_key: Mapped[str] = mapped_column(String(255), nullable=True)
    expected_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_of_measure_id: Mapped[int] = mapped_column(Integer, ForeignKey('units_of_measure.unit_id'), nullable=False)
    expected_harvest_start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    expected_harvest_end_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    offering_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('expected_crop_statuses.status_id'), nullable=False)
    cultivation_notes_key: Mapped[str] = mapped_column(Text, nullable=True)
    asking_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    is_organic: Mapped[bool] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # status: Mapped["ExpectedCropStatus"] = relationship(foreign_keys=[offering_status_id], lazy="selectin")
    status: Mapped["ExpectedCropStatus"] = relationship("ExpectedCropStatus", foreign_keys=[offering_status_id], lazy="selectin") # <-- أضف "ExpectedCropStatus" كأول معامل
    translations: Mapped[list["ExpectedCropTranslation"]] = relationship(cascade="all, delete-orphan")

class ExpectedCropTranslation(Base):
    """(2.هـ.2) جدول ترجمات المحاصيل المتوقعة."""
    __tablename__ = 'expected_crop_translations'
    # translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    expected_crop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('expected_crops.expected_crop_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_product_name: Mapped[str] = mapped_column(String(255), nullable=True)
    translated_cultivation_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ProductPriceHistory(Base):
    """(2.هـ.3) جدول سجل أسعار المنتج لتتبع التغيرات."""
    __tablename__ = 'product_price_history'
    price_history_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_packaging_option_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('product_packaging_options.packaging_option_id'), nullable=False)
    old_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    new_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_change_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    changed_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    change_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())