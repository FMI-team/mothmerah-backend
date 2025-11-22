from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger,
    func, TIMESTAMP, text, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from src.db.base_class import Base

class ProductCategory(Base):
    """(2.أ.1) جدول فئات المنتجات (خضروات، فواكه، تمور)."""
    __tablename__ = 'product_categories'
    category_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    category_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # علاقة ذاتية لتكوين هيكل شجري للفئات (فئة رئيسية وفئات فرعية)
    parent_category_id: Mapped[int] = mapped_column(Integer, ForeignKey('product_categories.category_id'), nullable=True)
    category_image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    translations: Mapped[List["ProductCategoryTranslation"]] = relationship(
        "ProductCategoryTranslation",
        back_populates="category",
        cascade="all, delete-orphan"
    )

class ProductCategoryTranslation(Base):
    """(2.أ.2) جدول ترجمات فئات المنتجات."""
    __tablename__ = 'product_category_translations'
    # category_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('product_categories.category_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_category_name: Mapped[str] = mapped_column(String(150), nullable=False)
    translated_category_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category: Mapped["ProductCategory"] = relationship("ProductCategory", back_populates="translations")