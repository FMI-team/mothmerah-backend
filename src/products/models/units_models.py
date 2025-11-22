from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey )
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base_class import Base

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

# =================================================================
# المجموعة 2.3: 2.ج. المجموعة الفرعية: إدارة وحدات القياس وخيارات التعبئة والصور
# =================================================================

class UnitOfMeasure(Base):
    """(2.ج.1) جدول وحدات القياس (كيلو، صندوق، حبة...)."""
    __tablename__ = 'units_of_measure'
    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    unit_abbreviation_key: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    is_base_unit_for_type: Mapped[bool] = mapped_column(Boolean, nullable=True)
    conversion_factor_to_base: Mapped[float] = mapped_column(Numeric, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class UnitOfMeasureTranslation(Base):
    """(2.ج.2) جدول ترجمات وحدات القياس."""
    __tablename__ = 'unit_of_measure_translations'
    # unit_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey('units_of_measure.unit_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_unit_name: Mapped[str] = mapped_column(String(50), nullable=False)
    translated_unit_abbreviation: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class Image(Base):
    """(2.ج.5) جدول عام لإدارة جميع الصور في النظام بطريقة مرنة."""
    __tablename__ = 'images'
    image_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # استخدام علاقة متعددة الأشكال (Polymorphic) لربط الصورة بأي كيان في النظام
    entity_id: Mapped[str] = mapped_column(String, nullable=False, comment="معرف الكيان الذي ترتبط به الصورة (UUID أو Integer)")
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="نوع الكيان من جدول entity_types_for_reviews_or_images")
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    alt_text_key: Mapped[str] = mapped_column(String(255), nullable=True)
    is_primary_image: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    uploaded_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # ملاحظة: تم تعريف entity_id كـ String لاستيعاب أنواع مختلفة من المعرفات (UUID للمستخدمين والمنتجات, Integer للجداول الأخرى)


class ProductPackagingOption(Base):
    """(2.ج.3) جدول خيارات التعبئة والبيع للمنتجات (صندوق كرتون 5 كيلو...)."""
    __tablename__ = 'product_packaging_options'
    packaging_option_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=False)
    packaging_option_name_key: Mapped[str] = mapped_column(String(100), nullable=True)
    custom_packaging_description: Mapped[str] = mapped_column(Text, nullable=True)
    quantity_in_packaging: Mapped[float] = mapped_column(Numeric, nullable=False)
    unit_of_measure_id_for_quantity: Mapped[int] = mapped_column(Integer, ForeignKey('units_of_measure.unit_id'), nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    barcode: Mapped[str] = mapped_column(String(100), nullable=True)
    is_default_option: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    product: Mapped["Product"] = relationship(back_populates="packaging_options")
    unit_of_measure: Mapped["UnitOfMeasure"] = relationship("UnitOfMeasure", foreign_keys=[unit_of_measure_id_for_quantity], lazy="selectin")
    translations: Mapped[list["ProductPackagingOptionTranslation"]] = relationship("ProductPackagingOptionTranslation", back_populates="packaging_option", cascade="all, delete-orphan")
    # يجب أن يكون اسم العلاقة "price_rule_assignments"
    price_rule_assignments: Mapped[list["ProductPackagingPriceTierRuleAssignment"]] = relationship(back_populates="packaging_option")

class ProductPackagingOptionTranslation(Base):
    """(2.ج.4) جدول ترجمات خيارات التعبئة والبيع."""
    __tablename__ = 'product_packaging_option_translations'
    # packaging_option_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    packaging_option_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('product_packaging_options.packaging_option_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_packaging_option_name: Mapped[str] = mapped_column(String(150), nullable=False)
    translated_custom_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    packaging_option: Mapped["ProductPackagingOption"] = relationship("ProductPackagingOption", back_populates="translations")