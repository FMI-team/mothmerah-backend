from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger,
    func, TIMESTAMP, text, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base_class import Base

from uuid import uuid4


# =================================================================
# المجموعة 11: نظام الإشعارات والاتصالات (Notification & Communication System)
# =================================================================


class NotificationTemplate(Base):
    """(11.1) جدول قوالب الإشعارات."""
    __tablename__ = 'notification_templates'
    template_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    default_language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class NotificationTemplateTranslation(Base):
    """(11.2) جدول ترجمات قوالب الإشعارات."""
    __tablename__ = 'notification_template_translations'
    template_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_templates.template_id'), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), nullable=False)
    translated_subject: Mapped[str] = mapped_column(String(255), nullable=True)
    translated_body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class NotificationChannel(Base):
    """(11.3) جدول قنوات إرسال الإشعارات (SMS, EMAIL...)."""
    __tablename__ = 'notification_channels'
    channel_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class NotificationChannelTranslation(Base):
    """(11.4) جدول ترجمات أسماء قنوات الإشعارات."""
    __tablename__ = 'notification_channel_translations'
    channel_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_channels.channel_id'), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), nullable=False)
    translated_channel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class NotificationDeliveryStatus(Base):
    """(11.6) جدول حالات تسليم الإشعارات (SENT, DELIVERED, FAILED...)."""
    __tablename__ = 'notification_delivery_statuses'
    delivery_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class NotificationDeliveryStatusTranslation(Base):
    """(11.7) جدول ترجمات حالات تسليم الإشعارات."""
    __tablename__ = 'notification_delivery_status_translations'
    status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    delivery_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_delivery_statuses.delivery_status_id'), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class NotificationType(Base):
    """(11.9) جدول أنواع الإشعارات (تحديث طلب، تنبيه مزاد...)."""
    __tablename__ = 'notification_types'
    notification_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    default_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    can_user_disable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class NotificationTypeTranslation(Base):
    """(11.10) جدول ترجمات أنواع الإشعارات."""
    __tablename__ = 'notification_type_translations'
    type_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    notification_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_types.notification_type_id'), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), nullable=False)
    translated_type_name: Mapped[str] = mapped_column(String(150), nullable=False)
    translated_type_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class NotificationLog(Base):
    """(11.5) جدول سجل الإشعارات المرسلة."""
    __tablename__ = 'notification_logs'
    notification_log_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_templates.template_id'), nullable=True)
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_channels.channel_id'), nullable=False)
    recipient_address: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_rendered: Mapped[str] = mapped_column(String(255), nullable=True)
    body_rendered: Mapped[str] = mapped_column(Text, nullable=False)
    sent_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    delivery_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_delivery_statuses.delivery_status_id'), nullable=False)
    gateway_response: Mapped[str] = mapped_column(Text, nullable=True)
    related_entity_type: Mapped[str] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[str] = mapped_column(String, nullable=True) # To accommodate UUIDs and BigInts
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class UserNotificationPreference(Base):
    """(11.8) جدول تفضيلات إشعارات المستخدم."""
    __tablename__ = 'user_notification_preferences'
    preference_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    notification_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_types.notification_type_id'), nullable=False)
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey('notification_channels.channel_id'), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'notification_type_id', 'channel_id', name='uq_user_notification_preference'),
    )