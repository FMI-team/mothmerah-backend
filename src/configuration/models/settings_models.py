# backend\src\system_settings\models\system_settings_models.py

from datetime import datetime
from sqlalchemy import (JSON, Integer, String, Text, Boolean, BigInteger, func, TIMESTAMP, text, ForeignKey)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING # تأكد من استيراد Optional و TYPE_CHECKING

from src.db.base_class import Base

from uuid import uuid4

# يمنع الأخطاء الناتجة عن الاستيراد الدائري لأغراض Type Checking
if TYPE_CHECKING:
    # من المجموعة 1 (المستخدمون)
    from src.users.models.core_models import User
    # من المجموعة 12 (Lookups العامة)
    from src.lookups.models.lookups_models import Language


# =================================================================
# المجموعة 14: إدارة إعدادات وتكوينات النظام (System Settings & Configuration Management)
# =================================================================

class ApplicationSetting(Base):
    """(14.1) جدول إعدادات التطبيق العامة."""
    __tablename__ = 'application_settings'
    setting_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True) # تم إضافة autoincrement
    setting_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    setting_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # تم التأكيد على Optional
    setting_datatype: Mapped[str] = mapped_column(String(50), nullable=False, comment="e.g., 'INTEGER', 'STRING', 'BOOLEAN', 'JSON', 'TEXT'")
    description_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # تم التأكيد على Optional
    module_scope: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="e.g., 'AUCTIONS', 'PAYMENTS'") # NEW field, added Optional
    is_editable_by_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True) # تم إضافة ondelete

    # علاقات:
    translations: Mapped[List["ApplicationSettingTranslation"]] = relationship(back_populates="application_setting", cascade="all, delete-orphan")
    last_updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id], lazy="selectin", back_populates="application_settings_updated")


class ApplicationSettingTranslation(Base):
    """(14.2) جدول ترجمات قيم إعدادات التطبيق."""
    __tablename__ = 'application_setting_translations'
    
    setting_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    setting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('application_settings.setting_id', ondelete="CASCADE"), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), nullable=False)
    translated_setting_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    translated_setting_description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # علاقات:
    application_setting: Mapped["ApplicationSetting"] = relationship(back_populates="translations")
    
    # ✅ FIXED: Use string reference instead of direct class reference
    language: Mapped["Language"] = relationship(
        "Language", 
        foreign_keys="[ApplicationSettingTranslation.language_code]",  # Changed to string
        lazy="selectin"
    )


class FeatureFlag(Base):
    """(14.3) جدول أعلام تفعيل الميزات (Feature Flags)."""
    __tablename__ = 'feature_flags'
    flag_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # SERIAL / autoincrement
    flag_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # تم التأكيد على Optional
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    activation_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="e.g., enable for specific user IDs, or a percentage of users") # تم التأكيد على Optional
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True) # تم إضافة ondelete

    # علاقات:
    last_updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id], lazy="selectin", back_populates="feature_flags_updated")


class SystemMaintenanceSchedule(Base):
    """(14.4) جدول صيانة النظام."""
    __tablename__ = 'system_maintenance_schedule'
    maintenance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # SERIAL / autoincrement
    start_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    end_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    maintenance_message_key: Mapped[str] = mapped_column(String(255), nullable=False) # BRD: NOT NULL
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True) # تم إضافة ondelete

    # علاقات:
    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id], lazy="selectin", back_populates="maintenance_schedules_created")