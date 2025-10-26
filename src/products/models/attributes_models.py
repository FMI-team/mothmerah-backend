from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger,
    func, TIMESTAMP, text, ForeignKey )
from sqlalchemy.orm import Mapped, mapped_column,relationship
from typing import List
from src.db.base_class import Base

class Attribute(Base):
    """(2.ب.1) جدول السمات العامة (لون، حجم، جودة...)."""
    __tablename__ = 'attributes'
    attribute_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    attribute_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    attribute_description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    is_filterable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), comment="هل يمكن استخدامها كفلتر في البحث؟")
    is_variant_defining: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), comment="هل تساهم في تعريف صنف مختلف؟")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    # relation
    values: Mapped[List["AttributeValue"]] = relationship(back_populates="attribute", cascade="all, delete-orphan")

class AttributeTranslation(Base):
    """(2.ب.2) جدول ترجمات السمات العامة."""
    __tablename__ = 'attribute_translations'
    # attribute_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    attribute_id: Mapped[int] = mapped_column(Integer, ForeignKey('attributes.attribute_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_attribute_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_attribute_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class AttributeValue(Base):
    """(2.ب.3) جدول قيم السمات الممكنة (أحمر، أخضر، كبير، صغير...)."""
    __tablename__ = 'attribute_values'
    attribute_value_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    attribute_id: Mapped[int] = mapped_column(Integer, ForeignKey('attributes.attribute_id'), nullable=False)
    attribute_value_key: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    # relation
    attribute: Mapped["Attribute"] = relationship(back_populates="values")

class AttributeValueTranslation(Base):
    """(2.ب.4) جدول ترجمات قيم السمات."""
    __tablename__ = 'attribute_value_translations'
    # attribute_value_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    attribute_value_id: Mapped[int] = mapped_column(Integer, ForeignKey('attribute_values.attribute_value_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_value_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ProductVarietyAttribute(Base):
    """(2.ب.5) جدول يربط كل صنف من المنتج بقيم السمات الخاصة به."""
    __tablename__ = 'product_variety_attributes'
    product_variety_attribute_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    product_variety_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('product_varieties.variety_id'), nullable=False)
    attribute_id: Mapped[int] = mapped_column(Integer, ForeignKey('attributes.attribute_id'), nullable=False)
    attribute_value_id: Mapped[int] = mapped_column(Integer, ForeignKey('attribute_values.attribute_value_id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())