from datetime import datetime
from sqlalchemy import (Integer, String, Text, Boolean, BigInteger, Numeric, func, TIMESTAMP, text, ForeignKey, JSON)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base_class import Base

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class Product(Base):
    """(2.أ.3) جدول المنتجات الأساسية."""
    __tablename__ = 'products'

    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    seller_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('product_categories.category_id'), nullable=False)
    base_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, comment="السعر الأساسي قبل أي تسعير ديناميكي")
    unit_of_measure_id: Mapped[int] = mapped_column(Integer, ForeignKey('units_of_measure.unit_id'), nullable=False)
    country_of_origin_code: Mapped[str] = mapped_column(String(2), ForeignKey('countries.country_code'), nullable=True)
    is_organic: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_local_saudi_product: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    product_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('product_statuses.product_status_id'), nullable=False)
    main_image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, nullable=True, comment="لتسهيل البحث والتصنيف")
    updated_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    # هذا يخبر SQLAlchemy بكيفية جلب الكائنات المرتبطة
    category: Mapped["ProductCategory"] = relationship(lazy="selectin")
    unit_of_measure: Mapped["UnitOfMeasure"] = relationship(lazy="selectin")
    seller: Mapped["User"] = relationship(foreign_keys=[seller_user_id], back_populates="products_sold")
    updater: Mapped["User"] = relationship(foreign_keys=[updated_by_user_id], back_populates="products_updated")
    translations: Mapped[list["ProductTranslation"]] = relationship(cascade="all, delete-orphan")
    packaging_options: Mapped[list["ProductPackagingOption"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    status: Mapped["ProductStatus"] = relationship("ProductStatus", foreign_keys=[product_status_id], lazy="selectin") # استخدام "ProductStatus" كسلسلة

class ProductTranslation(Base):
    """(2.أ.4) جدول ترجمات المنتجات."""
    __tablename__ = 'product_translations'
    product_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), nullable=False)
    translated_product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    translated_short_description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ProductVariety(Base):
    """(2.أ.5) جدول أصناف المنتج (مثل: طماطم شيري، طماطم كرزي)."""
    __tablename__ = 'product_varieties'
    variety_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=False)
    variety_name_key: Mapped[str] = mapped_column(String(100), nullable=False, comment="مفتاح لاسم الصنف للترجمة")
    sku_variant: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ProductVarietyTranslation(Base):
    """(2.أ.6) جدول ترجمات أصناف المنتج."""
    __tablename__ = 'product_variety_translations'
    # variety_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    variety_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('product_varieties.variety_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_variety_name: Mapped[str] = mapped_column(String(150), nullable=False)
    translated_variety_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())