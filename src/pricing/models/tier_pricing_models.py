# backend\src\pricing\models\tier_pricing_models.py
from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey, Date)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column,relationship
from src.db.base_class import Base

from uuid import uuid4

class PriceTierRule(Base):
    """(3.1) جدول قواعد شرائح الأسعار - جدول مرجعي."""
    __tablename__ = 'price_tier_rules'
    rule_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=True, comment="e.g., 'PERCENTAGE', 'FIXED_AMOUNT', 'NEW_PRICE'")
    created_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # price_rule_assignments: Mapped[list["ProductPackagingPriceTierRuleAssignment"]] = relationship(back_populates="packaging_option")
    assignments: Mapped[list["ProductPackagingPriceTierRuleAssignment"]] = relationship(back_populates="rule")
    levels: Mapped[list["PriceTierRuleLevel"]] = relationship(cascade="all, delete-orphan")

class PriceTierRuleTranslation(Base):
    """(3.2) جدول ترجمات قواعد شرائح الأسعار."""
    __tablename__ = 'price_tier_rule_translations'
    # rule_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey('price_tier_rules.rule_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_rule_name: Mapped[str] = mapped_column(String(150), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class PriceTierRuleLevel(Base):
    """(3.3) جدول مستويات قاعدة شريحة السعر."""
    __tablename__ = 'price_tier_rule_levels'
    level_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey('price_tier_rules.rule_id'), nullable=False)
    minimum_quantity: Mapped[float] = mapped_column(Numeric, nullable=False)
    price_per_unit_at_level: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    discount_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    level_description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ProductPackagingPriceTierRuleAssignment(Base):
    """(3.4) جدول يربط قواعد الأسعار بخيارات التعبئة للمنتجات."""
    __tablename__ = 'product_packaging_price_tier_rule_assignments'
    assignment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    packaging_option_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('product_packaging_options.packaging_option_id'), nullable=False)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey('price_tier_rules.rule_id'), nullable=False)
    start_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    end_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقة مع خيار التغليف، back_populates يجب أن يطابق اسم العلاقة في ProductPackagingOption
    packaging_option: Mapped["ProductPackagingOption"] = relationship(back_populates="price_rule_assignments")
    # علاقة مع قاعدة التسعير، back_populates يجب أن يطابق اسم العلاقة في PriceTierRule
    rule: Mapped["PriceTierRule"] = relationship(back_populates="assignments")
