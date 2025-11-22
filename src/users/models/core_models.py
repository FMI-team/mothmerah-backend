# backend/src/users/models/core_models.py
from datetime import datetime
from sqlalchemy import (Integer, String, Text, Boolean, BigInteger, func, TIMESTAMP, text, ForeignKey, CheckConstraint, JSON)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base_class import Base
from typing import List, Optional, TYPE_CHECKING # تأكد من استيراد Optional
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

# يمنع الأخطاء الناتجة عن الاستيراد الدائري (ممارسة جيدة)
if TYPE_CHECKING:
    from .addresses_models import Address
    from .roles_models import Role, RolePermission, UserRole, Permission, RoleTranslation # Added RoleTranslation
    from .security_models import PasswordResetToken, PhoneChangeRequest, UserSession
    from .verification_models import License, LicenseType, IssuingAuthority, UserVerificationStatus, LicenseVerificationStatus, UserVerificationHistory, ManualVerificationLog, LicenseTypeTranslation, IssuingAuthorityTranslation, UserVerificationStatusTranslation, LicenseVerificationStatusTranslation # Added translations
    from src.products.models.products_models import Product # Assuming Product is in products_models
    from src.market.models.orders_models import Order, OrderItem # Assuming Order and OrderItem are in orders_models
    from src.market.models.rfqs_models import Rfq, RfqItem # Assuming Rfq and RfqItem are in rfqs_models
    from src.market.models.quotes_models import Quote, QuoteItem # Assuming Quote and QuoteItem are in quotes_models
    from src.community.models.reviews_models import ReviewReport, ReviewResponse # Assuming Quote and QuoteItem are in quotes_models
    from src.market.models.shipments_models import Shipment, ShipmentItem # Assuming Shipment and ShipmentItem are in shipments_models
    from src.auctions.models.auctions_models import Auction, AuctionLot, AuctionLotTranslation, LotProduct, LotImage # Assuming Auction models
    from src.auctions.models.bidding_models import AuctionParticipant, Bid, AutoBidSetting, AuctionWatchlist # Assuming Bidding models
    from src.auctions.models.settlements_models import AuctionSettlement, AuctionSettlementStatus, AuctionSettlementStatusTranslation # Assuming Settlements models
    from src.lookups.models import Language # Assuming Language is in lookups_models
else:
    import src.market.models.quotes_models as quotes_models
    import src.community.models.reviews_models as reviews_models
    import src.products.models.products_models as products_models
    import src.market.models.orders_models as orders_models
    import src.market.models.rfqs_models as rfqs_models
    import src.market.models.shipments_models as shipments_models
    import src.auctions.models.auctions_models as auctions_models
    import src.auctions.models.bidding_models as bidding_models
    import src.auctions.models.settlements_models as settlements_models

    Quote = quotes_models.Quote

    ReviewReport = reviews_models.ReviewReport
    ReviewResponse = reviews_models.ReviewResponse

    Product = products_models.Product

    Order = orders_models.Order
    OrderItem = orders_models.OrderItem

    Rfq = rfqs_models.Rfq
    RfqItem = rfqs_models.RfqItem

    Shipment = shipments_models.Shipment
    ShipmentItem = shipments_models.ShipmentItem

    Auction = auctions_models.Auction
    AuctionLotTranslation = auctions_models.AuctionLotTranslation
    AuctionLot = auctions_models.AuctionLot
    LotProduct = auctions_models.LotProduct
    LotImage = auctions_models.LotImage
    AuctionParticipant = bidding_models.AuctionParticipant

    Bid = bidding_models.Bid

    AutoBidSetting = bidding_models.AutoBidSetting
    AuctionWatchlist = bidding_models.AuctionWatchlist
    AuctionSettlement = settlements_models.AuctionSettlement
    AuctionSettlementStatus = settlements_models.AuctionSettlementStatus
    AuctionSettlementStatusTranslation = settlements_models.AuctionSettlementStatusTranslation


class User(Base):
    """(1.أ.1) الجدول المحوري للمستخدمين بالبنية النهائية الكاملة."""
    __tablename__ = 'users'
    # user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    reviews_given: Mapped[List["Review"]] = relationship("Review", back_populates="reviewer_user", lazy="select")
    review_responses_given: Mapped[List["ReviewResponse"]] = relationship(
        "ReviewResponse",
        back_populates="responder_user",
        foreign_keys=[ReviewResponse.responder_user_id],
        lazy="selectin"
    )
    review_responses_approved: Mapped[List["ReviewResponse"]] = relationship(
        "ReviewResponse",
        back_populates="approved_by_user",
        foreign_keys=[ReviewResponse.approved_by_user_id],
        lazy="selectin"
    )

    review_reports_made: Mapped[List["ReviewReport"]] = relationship(
        "ReviewReport",
        back_populates="reporter_user",
        foreign_keys=[ReviewReport.reporter_user_id],
        lazy="selectin"
    )

    review_reports_resolved: Mapped[List["ReviewReport"]] = relationship(
        "ReviewReport",
        back_populates="resolved_by_user",
        foreign_keys=[ReviewReport.resolved_by_user_id],
        lazy="selectin"
    )

    system_audit_logs: Mapped[List["SystemAuditLog"]] = relationship(
        "SystemAuditLog",
        back_populates="user",
        lazy="selectin"
    )

    user_activity_logs: Mapped[List["UserActivityLog"]] = relationship("UserActivityLog", back_populates="user", lazy="selectin")
    search_logs: Mapped[List["SearchLog"]] = relationship("SearchLog", back_populates="user", lazy="selectin")
    security_event_logs: Mapped[List["SecurityEventLog"]] = relationship(
        "SecurityEventLog",
        back_populates="user",
        lazy="selectin",
        foreign_keys="[SecurityEventLog.user_id]"
    )
# Optionally, add this if you want a reverse relation for target_user_id:
    targeted_security_event_logs: Mapped[List["SecurityEventLog"]] = relationship(
        "SecurityEventLog",
        foreign_keys="[SecurityEventLog.target_user_id]",
        lazy="selectin",
        overlaps="target_user"
    )
    data_change_audit_logs: Mapped[List["DataChangeAuditLog"]] = relationship("DataChangeAuditLog", back_populates="changed_by_user", lazy="selectin")



    # --- Foreign Keys to dependency tables ---
    # هذه هي الأعمدة التي كانت مفقودة ويجب إضافتها!
    default_user_role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('roles.role_id'), nullable=True)
    user_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_types.user_type_id'), nullable=False)
    account_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('account_statuses.account_status_id'), nullable=False)
    user_verification_status_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('user_verification_statuses.user_verification_status_id'), nullable=True)
    preferred_language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), nullable=False, server_default=text("'ar'"))
    
    last_login_timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_activity_timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    additional_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # --- العلاقات مع تفعيل التحميل الفوري ---
    # علاقات مع مودلات من جداول lookups و roles و user_types
    account_status: Mapped["AccountStatus"] = relationship("AccountStatus", back_populates="users", foreign_keys=[account_status_id], lazy="selectin") # <-- تم التعديل هنا
    user_type: Mapped["UserType"] = relationship("UserType", back_populates="users", foreign_keys=[user_type_id], lazy="selectin") # <-- تم التعديل هنا
    default_role: Mapped[Optional["Role"]] = relationship("Role", foreign_keys=[default_user_role_id], back_populates="users_with_default_role", lazy="selectin") # <-- تم التعديل هنا
    user_verification_status: Mapped[Optional["UserVerificationStatus"]] = relationship("UserVerificationStatus", back_populates="users", foreign_keys=[user_verification_status_id], lazy="selectin") # <-- تم التعديل هنا
    preferred_language: Mapped["Language"] = relationship("Language", back_populates="users", foreign_keys=[preferred_language_code], lazy="selectin") # <-- تم التعديل هنا
    updater: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id], remote_side=lambda: User.user_id, lazy="selectin") # <-- تم التعديل هنا: remote_side أيضاً يصبح نصياً

    # علاقات عكسية مع مودلات من مجموعات أخرى (Products, Market, Auctions)
    products_sold: Mapped[List["Product"]] = relationship("Product", foreign_keys=lambda: [Product.seller_user_id], back_populates="seller")
    products_updated: Mapped[List["Product"]] = relationship("Product", foreign_keys=lambda: [Product.updated_by_user_id], back_populates="updater")
    
    # علاقات مع مودلات من Market (orders_models, rfqs_models, quotes_models, shipments_models)
    orders_as_buyer: Mapped[List["Order"]] = relationship("Order", back_populates="buyer", foreign_keys=lambda: [Order.buyer_user_id])
    orders_as_seller: Mapped[List["Order"]] = relationship("Order", back_populates="seller", foreign_keys=lambda: [Order.seller_user_id])
    rfqs_as_buyer: Mapped[List["Rfq"]] = relationship("Rfq", back_populates="buyer", foreign_keys=lambda: [Rfq.buyer_user_id])
    # quotes_as_seller: Mapped[List["Quote"]] = relationship("Quote", back_populates="seller_user", foreign_keys="[Quote.seller_user_id]")
    # quotes_as_seller: Mapped[List["Quote"]] = relationship("Quote", back_populates="seller_user", foreign_keys="[Quote.seller_user_id]")
    quotes_as_seller: Mapped[List["Quote"]] = relationship("Quote", back_populates="seller_user", foreign_keys=lambda: [Quote.seller_user_id], overlaps="seller")
    shipments_as_shipper: Mapped[List["Shipment"]] = relationship("Shipment", back_populates="shipped_by_user", foreign_keys=lambda: [Shipment.shipped_by_user_id])
    
    # علاقات مع مودلات من Auction
    auctions_as_seller: Mapped[List["Auction"]] = relationship("Auction", back_populates="seller", foreign_keys=lambda: [Auction.seller_user_id])
    current_highest_bids: Mapped[List["Auction"]] = relationship("Auction", back_populates="current_highest_bidder", foreign_keys=lambda: [Auction.current_highest_bidder_user_id])
    bids_as_bidder: Mapped[List["Bid"]] = relationship("Bid", back_populates="bidder", foreign_keys=lambda: [Bid.bidder_user_id])
    auction_participants: Mapped[List["AuctionParticipant"]] = relationship("AuctionParticipant", back_populates="user", foreign_keys=lambda: [AuctionParticipant.user_id])
    auto_bid_settings: Mapped[List["AutoBidSetting"]] = relationship("AutoBidSetting", back_populates="user", foreign_keys=lambda: [AutoBidSetting.user_id])
    auction_watchlists: Mapped[List["AuctionWatchlist"]] = relationship("AuctionWatchlist", back_populates="user", foreign_keys=lambda: [AuctionWatchlist.user_id])
    auction_settlements_as_winner: Mapped[List["AuctionSettlement"]] = relationship("AuctionSettlement", back_populates="winner_user", foreign_keys=lambda: [AuctionSettlement.winner_user_id])
    auction_settlements_as_seller: Mapped[List["AuctionSettlement"]] = relationship("AuctionSettlement", back_populates="seller_user", foreign_keys=lambda: [AuctionSettlement.seller_user_id])

    # علاقات مع مودلات من Group 1 (Users module)
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    phone_change_requests: Mapped[List["PhoneChangeRequest"]] = relationship("PhoneChangeRequest", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    user_sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    licenses: Mapped[List["License"]] = relationship("License", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    user_verification_history: Mapped[List["UserVerificationHistory"]] = relationship(
        "UserVerificationHistory",
        back_populates="user",
        foreign_keys=lambda: [__import__('src.users.models.verification_models', fromlist=['UserVerificationHistory']).UserVerificationHistory.user_id],# Explicitly specify the FK here
        lazy="selectin"
    )
# <-- تم التعديل هنا
    manual_verification_logs_as_reviewer: Mapped[List["ManualVerificationLog"]] = relationship(
        "ManualVerificationLog",
        foreign_keys=lambda: [__import__('src.users.models.verification_models', fromlist=['ManualVerificationLog']).ManualVerificationLog.reviewer_user_id],
        back_populates="reviewer_user", lazy="selectin") # <-- تم التعديل هنا
    
    # علاقات RBAC (إدارة الأدوار والصلاحيات)
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys=lambda: [__import__('src.users.models.roles_models', fromlist=['UserRole']).UserRole.user_id]
    )

    account_status_history: Mapped[List["AccountStatusHistory"]] = relationship(
        "AccountStatusHistory",
        back_populates="user",
        foreign_keys=lambda: [AccountStatusHistory.user_id],
        lazy="selectin"
    )

    user_preferences: Mapped[List["UserPreference"]] = relationship(
        "UserPreference",
        back_populates="user",
        foreign_keys=lambda: [UserPreference.user_id],
        lazy="selectin"
    )


    # TODO: association_proxy للأدوار: permissions: AssociationProxy[List["Permission"]] = association_proxy("permission_associations", "permission")
    # هذا يتطلب استيراد AssociationProxy في هذا الملف


    __table_args__ = (
        CheckConstraint("phone_number ~ '^\\+9665[0-9]{8}$'", name='chk_sa_phone_number'),
        CheckConstraint("email IS NULL OR email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'", name='chk_valid_email'),
    )

class AccountStatusHistory(Base):
    """(1.أ.6) جدول سجل تغييرات حالة الحساب لغرض التدقيق والمتابعة."""
    __tablename__ = 'account_status_history'
    account_status_history_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    old_account_status_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('account_statuses.account_status_id'), nullable=True)
    new_account_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('account_statuses.account_status_id'), nullable=False)
    change_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    changed_by_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    reason_for_change: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    additional_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="account_status_history", lazy="selectin")
    old_account_status: Mapped[Optional["AccountStatus"]] = relationship("AccountStatus", foreign_keys=[old_account_status_id], lazy="selectin", post_update=True)
    new_account_status: Mapped["AccountStatus"] = relationship("AccountStatus", foreign_keys=[new_account_status_id], lazy="selectin")
    changed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[changed_by_user_id], remote_side=lambda: User.user_id, lazy="selectin")

class UserPreference(Base):
    """(1.أ.7) جدول تفضيلات المستخدمين بنظام المفتاح والقيمة."""
    __tablename__ = 'user_preferences'
    user_preference_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    preference_key: Mapped[str] = mapped_column(String(100), nullable=False)
    preference_value: Mapped[str] = mapped_column(Text, nullable=True) # Using Text for flexibility
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_preferences", lazy="selectin")

class UserType(Base):
    """(1.أ.2) جدول أنواع المستخدمين (تاجر جملة، أسرة منتجة، مندوب...)."""
    __tablename__ = 'user_types'
    user_type_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    user_type_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    users: Mapped[List["User"]] = relationship("User", back_populates="user_type", foreign_keys=lambda: [User.user_type_id])
    translations: Mapped[List["UserTypeTranslation"]] = relationship(back_populates="user_type", cascade="all, delete-orphan")

class UserTypeTranslation(Base):
    """(1.أ.3) جدول ترجمات أنواع المستخدمين."""
    __tablename__ = 'user_type_translations'
    # user_type_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # BIGSERIAL
    user_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_types.user_type_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_user_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- SQLAlchemy Relationships ---
    user_type: Mapped["UserType"] = relationship(back_populates="translations")

class AccountStatus(Base):
    """(1.أ.4) جدول حالات الحساب التشغيلية (نشط، موقوف، بانتظار التفعيل...)."""
    __tablename__ = 'account_statuses'
    account_status_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), comment="هل هذه الحالة نهائية لا يمكن الخروج منها؟ (مثل محذوف)")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # --- Bidirectional relationship ---
    users: Mapped[List["User"]] = relationship("User", back_populates="account_status", foreign_keys=lambda: [User.account_status_id], lazy="select")
    translations: Mapped[List["AccountStatusTranslation"]] = relationship(
        back_populates="status", cascade="all, delete-orphan" # ترجمات حالة الحساب
    )
    account_status_history_old_status: Mapped[List["AccountStatusHistory"]] = relationship("AccountStatusHistory", foreign_keys=lambda: [AccountStatusHistory.old_account_status_id], lazy="selectin", overlaps="old_account_status")
    account_status_history_new_status: Mapped[List["AccountStatusHistory"]] = relationship("AccountStatusHistory", foreign_keys=lambda: [AccountStatusHistory.new_account_status_id], lazy="selectin", overlaps="new_account_status")

class AccountStatusTranslation(Base):
    """(1.أ.5) جدول ترجمات حالات الحساب التشغيلية."""
    __tablename__ = 'account_status_translations'
    # account_status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    account_status_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('account_statuses.account_status_id', ondelete="CASCADE"), 
        primary_key=True
    )
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_status_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # ---   العلاقة العكسية ---
    status: Mapped["AccountStatus"] = relationship(back_populates="translations")