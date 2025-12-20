# backend/src/users/models/roles_models.py
from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger,
    func, TIMESTAMP, text, ForeignKey )
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List,Optional
from src.db.base_class import Base
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from .core_models import User
from uuid import uuid4

class Role(Base):
    """(1.ب.1) جدول الأدوار: يحدد الأدوار الوظيفية في النظام."""
    __tablename__ = 'roles'
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    role_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())   

    # هذه العلاقة تربط Role بجدول RolePermission (جدول الربط)
    permission_associations: Mapped[List["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")
    # هذه الخاصية الافتراضية تتيح لنا الوصول المباشر إلى الصلاحيات عبر جدول الربط
    permissions: AssociationProxy[List["Permission"]] = association_proxy(
        "permission_associations", "permission",
        creator=lambda permission_obj: RolePermission(permission=permission_obj) # لتمكين الإضافة المباشرة للصلاحيات
    )

    # علاقة بترجمات الدور
    translations: Mapped[List["RoleTranslation"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )

    # علاقة عكسية بالمستخدمين الذين لديهم هذا الدور كدور افتراضي (من جدول User)
    users_with_default_role: Mapped[List["User"]] = relationship("User", foreign_keys="[User.default_user_role_id]", back_populates="default_role", lazy="selectin")
    
    # علاقة مع جدول UserRole (جدول الربط) للمستخدمين الذين لديهم هذا الدور كدور إضافي
    user_role_associations: Mapped[List["UserRole"]] = relationship(back_populates="role", cascade="all, delete-orphan")
    # هذه الخاصية الافتراضية تتيح لنا الوصول المباشر إلى المستخدمين الذين لديهم هذا الدور (افتراضي أو إضافي)
    users: AssociationProxy[List["User"]] = association_proxy(
        "user_role_associations", "user",
        creator=lambda user_obj: UserRole(user=user_obj) # لتمكين الإضافة المباشرة للمستخدمين للدور
    )

class RoleTranslation(Base):
    """(1.ب.2) جدول ترجمات الأدوار."""
    __tablename__ = 'role_translations'
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.role_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    role: Mapped["Role"] = relationship(back_populates="translations") # علاقة بالدور الأب

class Permission(Base):
    """(1.ب.3) جدول الصلاحيات: يمثل كل إجراء يمكن التحكم فيه داخل النظام."""
    __tablename__ = 'permissions'
    permission_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    permission_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    module_group: Mapped[str] = mapped_column(String(50), nullable=True, comment="الوحدة التي تنتمي إليها الصلاحية")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # هذه العلاقة تربط Permission بجدول RolePermission (جدول الربط)
    role_associations: Mapped[List["RolePermission"]] = relationship(back_populates="permission", cascade="all, delete-orphan")
    # هذه الخاصية الافتراضية تتيح لنا الوصول المباشر إلى الأدوار التي تحتوي على هذه الصلاحية
    roles: AssociationProxy[List["Role"]] = association_proxy(
        "role_associations", "role",
        creator=lambda role_obj: RolePermission(role=role_obj) # لتمكين الإضافة المباشرة للأدوار للصلاحية
    )

class RolePermission(Base):
    """(1.ب.4.أ) جدول ربط الأدوار بالصلاحيات (Many-to-Many)."""
    __tablename__ = 'role_permissions'
    role_permission_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.role_id', ondelete='CASCADE'), nullable=False)
    permission_id: Mapped[int] = mapped_column(Integer, ForeignKey('permissions.permission_id', ondelete='CASCADE'), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- العلاقات مع الجدولين الرئيسيين ---
    # هذه العلاقات تخبر SQLAlchemy بكيفية الربط بين الدور والصلاحية
    role: Mapped["Role"] = relationship(back_populates="permission_associations")
    permission: Mapped["Permission"] = relationship(back_populates="role_associations")

class UserRole(Base):
    """(1.ب.4.ب) جدول ربط المستخدمين بالأدوار (Many-to-Many)."""
    __tablename__ = 'user_roles'
    user_role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.role_id', ondelete='RESTRICT'), nullable=False)
    assigned_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # --- العلاقات مع الجدولين الرئيسيين ---
    # هذه العلاقات تخبر SQLAlchemy بكيفية الربط بين المستخدم والدور
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_roles") # علاقة بالمستخدم
    role: Mapped["Role"] = relationship("Role", foreign_keys=[role_id], back_populates="user_role_associations") # علاقة بالدور
    assigned_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by_user_id], remote_side=[User.user_id], lazy="selectin") # علاقة بالمستخدم المسؤول عن الإسناد
