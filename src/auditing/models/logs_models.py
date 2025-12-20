# backend\src\auditing\models\logs_models.py

from datetime import datetime
from sqlalchemy import (JSON, Integer, String, Text, BigInteger, SmallInteger, func, TIMESTAMP, text, ForeignKey)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING # تأكد من استيراد Optional و TYPE_CHECKING

from src.db.base_class import Base

from uuid import uuid4
from sqlalchemy import String

# يمنع الأخطاء الناتجة عن الاستيراد الدائري لأغراض Type Checking
if TYPE_CHECKING:
    # من المجموعة 1 (المستخدمون)
    from src.users.models.core_models import User
    from src.users.models.security_models import UserSession # لـ user_sessions.session_id
    # من المجموعة 12 (Lookups العامة)
    from src.lookups.models.lookups_models import ActivityType, SecurityEventType, EntityTypeForReviewOrImage, SystemEventType # تم إضافة SystemEventType

# =================================================================
# المجموعة 13: سجلات التدقيق والأنشطة العامة (General Audit & Activity Logs)
# =================================================================

class SystemAuditLog(Base):
    """(13.1) جدول سجلات تدقيق النظام العامة."""
    __tablename__ = 'system_audit_logs'
    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True) # تم إضافة autoincrement
    event_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    # ملاحظة: event_type_id يشير إلى system_event_types، وليس security_event_types
    event_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('system_event_types.event_type_id'), nullable=True) # يجب أن يكون NOT NULL حسب الـ BRD
    event_description: Mapped[str] = mapped_column(Text, nullable=False) # BRD: NOT NULL
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True) # INET هو نوع بيانات PostgreSQL للـ IP
    target_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # To accommodate UUIDs and BigInts
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # BRD: JSON
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) # BRD: NOT NULL

    # علاقات:
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], lazy="selectin", back_populates="system_audit_logs")
    event_type: Mapped[Optional["SystemEventType"]] = relationship("SystemEventType", foreign_keys=[event_type_id], lazy="selectin", back_populates="system_audit_logs")

class UserActivityLog(Base):
    """(13.2) جدول سجلات نشاط المستخدم."""
    __tablename__ = 'user_activity_logs'
    activity_log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True) # تم إضافة autoincrement
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    session_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('user_sessions.session_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    activity_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('activity_types.activity_type_id'), nullable=False)
    activity_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) # BRD: NOT NULL
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # BRD: VARCHAR(50)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # To accommodate UUIDs and BigInts
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # BRD: JSON
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) # BRD: NOT NULL

    # علاقات:
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin", back_populates="user_activity_logs")
    session: Mapped[Optional["UserSession"]] = relationship("UserSession", foreign_keys=[session_id], lazy="selectin")
    activity_type: Mapped["ActivityType"] = relationship("ActivityType", foreign_keys=[activity_type_id], lazy="selectin", back_populates="user_activity_logs")
    # TODO: علاقة بـ EntityTypeForReviewOrImage.entity_type_code


class SearchLog(Base):
    """(13.3) جدول سجلات البحث."""
    __tablename__ = 'search_logs'
    search_log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True) # تم إضافة autoincrement
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    session_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('user_sessions.session_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    search_query: Mapped[str] = mapped_column(Text, nullable=False)
    search_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) # BRD: NOT NULL
    number_of_results_returned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # BRD: number_of_results_returned
    filters_applied: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # BRD: filters_applied
    clicked_result_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    clicked_result_entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) # BRD: NOT NULL

    # علاقات:
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], lazy="selectin", back_populates="search_logs")
    session: Mapped[Optional["UserSession"]] = relationship("UserSession", foreign_keys=[session_id], lazy="selectin")

class SecurityEventLog(Base):
    """(13.4) جدول سجلات أحداث الأمان."""
    __tablename__ = 'security_event_logs'
    security_event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True) # تم إضافة autoincrement
    event_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) # BRD: NOT NULL
    security_event_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('security_event_types.security_event_type_id'), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    target_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True) # BRD: target_user_id
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # BRD: details (TEXT)
    severity_level: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) # BRD: NOT NULL

    # علاقات:
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], lazy="selectin", back_populates="security_event_logs")
    target_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[target_user_id], lazy="selectin")
    event_type: Mapped["SecurityEventType"] = relationship("SecurityEventType", foreign_keys=[security_event_type_id], lazy="selectin", back_populates="security_event_logs")

class DataChangeAuditLog(Base):
    """(13.5) جدول سجلات تدقيق تغييرات البيانات (متقدم)."""
    __tablename__ = 'data_change_audit_logs'
    change_log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True) # تم إضافة autoincrement
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    column_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # BRD: column_name
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) # BRD: NOT NULL
    changed_by_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False) # BRD: change_type
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) # BRD: NOT NULL

    # علاقات:
    changed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[changed_by_user_id], lazy="selectin", back_populates="data_change_audit_logs")
