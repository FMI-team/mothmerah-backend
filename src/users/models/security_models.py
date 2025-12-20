from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, SmallInteger,
    func, TIMESTAMP, text, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base_class import Base
from uuid import uuid4
from sqlalchemy import String

class PasswordResetToken(Base):
    """(1.هـ.1) جدول رموز إعادة تعيين كلمة المرور المؤقتة."""
    __tablename__ = 'password_reset_tokens'
    token_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expiry_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- SQLAlchemy Relationships ---
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="password_reset_tokens", lazy="selectin") # علاقة بالمستخدم الأب

class PhoneChangeRequest(Base):
    """(1.هـ.2) جدول إدارة طلبات تغيير رقم الجوال بشكل آمن."""
    __tablename__ = 'phone_change_requests'
    request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    old_phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    new_phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    old_phone_otp_code: Mapped[str] = mapped_column(String(10), nullable=True)
    new_phone_otp_code: Mapped[str] = mapped_column(String(10), nullable=True)
    request_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'PENDING_OLD_PHONE_VERIFICATION'"))
    request_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    verification_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    last_attempt_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="phone_change_requests", lazy="selectin") # علاقة بالمستخدم الأب

class UserSession(Base):
    """(1.هـ.3) جدول جلسات المستخدمين النشطة."""
    __tablename__ = 'user_sessions'
    session_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    device_identifier: Mapped[str] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    login_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    last_activity_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    expiry_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    logout_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_sessions", lazy="selectin") # علاقة بالمستخدم الأب
