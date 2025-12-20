from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Date,
    func, TIMESTAMP, text, ForeignKey )
from sqlalchemy.dialects.postgresql import UUID
from typing import List,Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base_class import Base
from .core_models import User
from uuid import uuid4

class LicenseType(Base):
    """(1.ج.1) جدول أنواع التراخيص والوثائق (سجل تجاري، عمل حر...)."""
    __tablename__ = 'license_types'
    license_type_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    license_type_name_key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    is_mandatory_for_role: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- علاقات ---
    translations: Mapped[List["LicenseTypeTranslation"]] = relationship(
        back_populates="license_type", cascade="all, delete-orphan" # علاقة بترجمات نوع الترخيص
    )
    # التراخيص التي تحمل هذا النوع (علاقة عكسية)
    licenses: Mapped[List["License"]] = relationship("License", back_populates="license_type")

class LicenseTypeTranslation(Base):
    """(1.ج.2) جدول ترجمات أنواع التراخيص."""
    __tablename__ = 'license_type_translations'
    # type_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    license_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('license_types.license_type_id', ondelete="CASCADE"), primary_key=True)    
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_license_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- العلاقة العكسية ---
    license_type: Mapped["LicenseType"] = relationship(back_populates="translations") # علاقة بنوع الترخيص الأب

class IssuingAuthority(Base):
    """(1.ج.3) جدول الجهات المصدرة للتراخيص (وزارة التجارة...)."""
    __tablename__ = 'issuing_authorities'
    authority_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    authority_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), ForeignKey('countries.country_code'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["IssuingAuthorityTranslation"]] = relationship(
        back_populates="issuing_authority", cascade="all, delete-orphan" # علاقة بترجمات الجهة المصدرة
    )
    # التراخيص الصادرة من هذه الجهة (علاقة عكسية)
    licenses: Mapped[List["License"]] = relationship("License", back_populates="issuing_authority")
    # علاقة بـ Country من المجموعة 1.د
    country: Mapped["Country"] = relationship("Country", foreign_keys=[country_code], lazy="selectin")

class IssuingAuthorityTranslation(Base):
    """(1.ج.4) جدول ترجمات الجهات المصدرة للتراخيص."""
    __tablename__ = 'issuing_authority_translations'
    authority_id: Mapped[int] = mapped_column(Integer, ForeignKey('issuing_authorities.authority_id', ondelete="CASCADE"), primary_key=True)    
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_authority_name: Mapped[str] = mapped_column(String(150), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    issuing_authority: Mapped["IssuingAuthority"] = relationship(back_populates="translations") # علاقة بالجهة المصدرة الأب

class UserVerificationStatus(Base):
    """(1.ج.6) جدول حالات التحقق من المستخدم (لم يتم التحقق، قيد المراجعة، تم التحقق)."""
    __tablename__ = 'user_verification_statuses'
    user_verification_status_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["UserVerificationStatusTranslation"]] = relationship(
        back_populates="user_verification_status", cascade="all, delete-orphan" # علاقة بترجمات حالة التحقق
    )
    # المستخدمون الذين لديهم حالة التحقق هذه (علاقة عكسية)
    users: Mapped[List["User"]] = relationship("User", back_populates="user_verification_status", foreign_keys="[User.user_verification_status_id]") # استخدام foreign_keys هنا للتأكيد
    # سجلات تاريخ تحقق المستخدم التي تشير إلى هذه الحالة (علاقة عكسية)
    user_verification_history_old_status: Mapped[List["UserVerificationHistory"]] = relationship("UserVerificationHistory", foreign_keys="[UserVerificationHistory.old_user_verification_status_id]", lazy="selectin", back_populates="old_user_verification_status") # back_populates
    user_verification_history_new_status: Mapped[List["UserVerificationHistory"]] = relationship("UserVerificationHistory", foreign_keys="[UserVerificationHistory.new_user_verification_status_id]", lazy="selectin", back_populates="new_user_verification_status") # back_populates

class UserVerificationStatusTranslation(Base):
    """(1.ج.7) جدول ترجمات حالات التحقق من المستخدم."""
    __tablename__ = 'user_verification_status_translations'
    user_verification_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_verification_statuses.user_verification_status_id', ondelete="CASCADE"), primary_key=True)    
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    user_verification_status: Mapped["UserVerificationStatus"] = relationship(back_populates="translations") # علاقة بحالة التحقق الأب

class LicenseVerificationStatus(Base):
    """(1.ج.8) جدول حالات التحقق من التراخيص (مقبول، مرفوض، منتهي الصلاحية...)."""
    __tablename__ = 'license_verification_statuses'
    license_verification_status_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["LicenseVerificationStatusTranslation"]] = relationship(
        back_populates="license_verification_status", cascade="all, delete-orphan" # علاقة بترجمات حالة التحقق
    )
    # التراخيص التي تحمل حالة التحقق هذه (علاقة عكسية)
    licenses: Mapped[List["License"]] = relationship("License", back_populates="verification_status")

class LicenseVerificationStatusTranslation(Base):
    """(1.ج.9) جدول ترجمات حالات التحقق من التراخيص."""
    __tablename__ = 'license_verification_status_translations'
    # license_verification_status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    license_verification_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('license_verification_statuses.license_verification_status_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    license_verification_status: Mapped["LicenseVerificationStatus"] = relationship(back_populates="translations") # علاقة بحالة التحقق الأب

class License(Base):
    """(1.ج.5) جدول تراخيص ووثائق المستخدمين."""
    __tablename__ = 'licenses'
    license_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    license_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('license_types.license_type_id', ondelete='RESTRICT'), nullable=False)
    issuing_authority_id: Mapped[int] = mapped_column(Integer, ForeignKey('issuing_authorities.authority_id', ondelete='RESTRICT'), nullable=True)
    file_storage_key: Mapped[str] = mapped_column(String(255), nullable=False, comment="يربط السجل بالملف الفعلي المخزن على الخدمة السحابية")
    license_number: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    verification_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('license_verification_statuses.license_verification_status_id', ondelete='RESTRICT'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="licenses", lazy="selectin") # المستخدم صاحب الترخيص
    license_type: Mapped["LicenseType"] = relationship("LicenseType", foreign_keys=[license_type_id], back_populates="licenses", lazy="selectin") # نوع الترخيص
    issuing_authority: Mapped[Optional["IssuingAuthority"]] = relationship("IssuingAuthority", foreign_keys=[issuing_authority_id], back_populates="licenses", lazy="selectin") # الجهة المصدرة
    verification_status: Mapped["LicenseVerificationStatus"] = relationship("LicenseVerificationStatus", foreign_keys=[verification_status_id], back_populates="licenses", lazy="selectin") # حالة التحقق من الترخيص

class UserVerificationHistory(Base):
    """(1.ج.10) جدول سجل تغييرات حالة التحقق للمستخدم."""
    __tablename__ = 'user_verification_history'
    history_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    changed_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    old_user_verification_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_verification_statuses.user_verification_status_id', ondelete='RESTRICT'), nullable=True)
    new_user_verification_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_verification_statuses.user_verification_status_id', ondelete='RESTRICT'), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- SQLAlchemy Relationships ---
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_verification_history",
        foreign_keys=[user_id]
    ) # المستخدم الذي تغيرت حالته
    changed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[changed_by_user_id], remote_side=[User.user_id], lazy="selectin") # المستخدم الذي أجرى التغيير (قد يكون النظام)
    old_user_verification_status: Mapped[Optional["UserVerificationStatus"]] = relationship("UserVerificationStatus", foreign_keys=[old_user_verification_status_id], lazy="selectin", back_populates="user_verification_history_old_status") # الحالة القديمة
    new_user_verification_status: Mapped["UserVerificationStatus"] = relationship("UserVerificationStatus", foreign_keys=[new_user_verification_status_id], lazy="selectin", back_populates="user_verification_history_new_status") # الحالة الجديدة

class ManualVerificationLog(Base):
    """(1.ج.11) جدول سجل المراجعة اليدوية للوثائق أو الحسابات."""
    __tablename__ = 'manual_verification_log'
    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    reviewer_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="نوع الكيان الذي تمت مراجعته (e.g., 'LICENSE')")
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="معرف الكيان الذي تمت مراجعته (e.g., license_id)")
    action_taken: Mapped[str] = mapped_column(String(50), nullable=False, comment="الإجراء المتخذ (e.g., 'APPROVED', 'REJECTED')")
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- SQLAlchemy Relationships ---
    reviewer_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewer_user_id], back_populates="manual_verification_logs_as_reviewer", lazy="selectin") # المستخدم المراجع
    # TODO: علاقة مع entity_type و entity_id (قد تتطلب Polymorphic relationships أو منطق خاص في الخدمة)
    #       هذه العلاقات ليست Foreign Key مباشرة في قاعدة البيانات، ويتم ربطها منطقياً في التطبيق.
