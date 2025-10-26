# backend\src\lookups\models.py

from datetime import datetime, date
from sqlalchemy import (JSON, Integer, String, Boolean, Text, Date, SmallInteger, BigInteger, func, TIMESTAMP, text, ForeignKey)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING 

from src.db.base_class import Base

# يمنع الأخطاء الناتجة عن الاستيراد الدائري لأغراض Type Checking
# سنحدد هنا فقط المودلات التي تستخدم هذه الـ lookups العامة،
# وليس العكس لتجنب أي تعقيد.
if TYPE_CHECKING:
    # من المجموعة 1 (المستخدمين)
    from src.users.models.core_models import User # إذا كانت Audit Logs تستخدم User
    # من المجموعة 4 (عمليات السوق)
    from src.market.models.orders_models import Order # لاستخدام Order.currency_code
    # من المجموعة 6 (المراجعات)
    from src.community.models.reviews_models import Review, ReviewRatingByCriterion, ReviewResponse, ReviewReport # <-- أضف هذا
    # من المجموعة 8 (المحفظة)
    from src.wallet.models.wallet_models import WalletTransaction, WithdrawalRequest # لاستخدام WalletTransaction.currency_code, WithdrawalRequest.status
    from src.wallet.models.payment_models import PaymentGateway # لبوابات الدفع
    # من المجموعة 9 (الدفع الآجل)
    from src.deferred_payments.models.deferred_payment_models import DeferredPaymentAgreement, DeferredPaymentInstallment # للدفع الآجل
    # من المجموعة 10 (الضمان الذهبي)
    from src.golden_guarantee.models.gg_models import GGClaim, GGResolution # للضمان الذهبي
    # من المجموعة 13 (سجلات التدقيق)
    from src.auditing.models.logs_models import UserActivityLog, SecurityEventLog, SystemAuditLog # لسجلات التدقيق
    # من المجموعة 2 (المنتجات)
    from src.products.models.products_models import Product # لاستخدام Product.product_status
    from src.products.models.inventory_models import InventoryItem, InventoryTransaction # للمخزون
    from src.products.models.future_offerings_models import ExpectedCrop # للمحاصيل المتوقعة
    # من المجموعة 3 (التسعير)
    from src.pricing.models.pricing_models import PriceTierRule # لقواعد التسعير
    # من المجموعة 5 (المزادات)
    from src.auctions.models.auctions_models import Auction # للمزادات
    # من المجموعة 11 (الإشعارات)
    from src.notifications.models.notifications_models import Notification, NotificationDelivery # للإشعارات
else:
    import src.auditing.models.logs_models as logs_models

    SecurityEventLog = logs_models.SecurityEventLog
    UserActivityLog = logs_models.UserActivityLog
    SystemAuditLog = logs_models.SystemAuditLog



# =================================================================
# المجموعة 12: الجداول المرجعية العامة وأنواع الكيانات (فقط المودلات الأساسية للمجموعة 12)
# =================================================================

class Currency(Base):
    """(12.1) جدول العملات: يحتوي على العملات المدعومة في النظام."""
    __tablename__ = 'currencies'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    currency_code: Mapped[str] = mapped_column(String(3), primary_key=True)
    currency_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(5), nullable=False)
    decimal_places: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("2"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["CurrencyTranslation"]] = relationship(back_populates="currency", cascade="all, delete-orphan")
    # علاقات عكسية من جداول أخرى تستخدم العملة (مثلاً Orders, WalletTransactions)
    orders: Mapped[List["Order"]] = relationship("Order", foreign_keys="[Order.currency_code]", back_populates="currency")
    # TODO: wallet_transactions: Mapped[List["WalletTransaction"]] = relationship("WalletTransaction", foreign_keys="[WalletTransaction.currency_code]", back_populates="currency") # تفعيلها عند تعريف WalletTransaction
    # TODO: shipments: Mapped[List["Shipment"]] = relationship("Shipment", foreign_keys="[Shipment.currency_code]", back_populates="currency")
    # TODO: auction_settlements: Mapped[List["AuctionSettlement"]] = relationship("AuctionSettlement", foreign_keys="[AuctionSettlement.currency_code]", back_populates="currency")


class CurrencyTranslation(Base):
    """(12.2) جدول ترجمات أسماء العملات."""
    __tablename__ = 'currency_translations'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('currencies.currency_code', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_currency_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    currency: Mapped["Currency"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")


class DimDate(Base):
    """(12.3) جدول الأبعاد الزمنية: يحتوي على تفاصيل كل يوم لتسهيل الاستعلامات."""
    __tablename__ = 'dim_dates'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    date_id: Mapped[date] = mapped_column(Date, primary_key=True)
    day_number_in_week: Mapped[int] = mapped_column(SmallInteger)
    day_name_key: Mapped[str] = mapped_column(String(20))
    day_number_in_month: Mapped[int] = mapped_column(SmallInteger)
    month_number_in_year: Mapped[int] = mapped_column(SmallInteger)
    month_name_key: Mapped[str] = mapped_column(String(20))
    calendar_quarter: Mapped[int] = mapped_column(SmallInteger)
    calendar_year: Mapped[int] = mapped_column(SmallInteger)
    is_weekend_ksa: Mapped[bool] = mapped_column(Boolean)
    is_official_holiday_ksa: Mapped[bool] = mapped_column(Boolean)
    hijri_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # لا توجد علاقات من هذا الجدول عادة


class DayOfWeekTranslation(Base):
    """(12.4) جدول ترجمات أسماء أيام الأسبوع."""
    __tablename__ = 'day_of_week_translations'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    # المفتاح المركب (day_name_key, language_code)
    day_name_key: Mapped[str] = mapped_column(String(20), primary_key=True, comment="الربط مع dim_dates يتم عبر هذه القيمة")
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_day_name: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات:
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")


class MonthTranslation(Base):
    """(12.5) جدول ترجمات أسماء الشهور."""
    __tablename__ = 'month_translations'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    # المفتاح المركب (month_name_key, language_code)
    month_name_key: Mapped[str] = mapped_column(String(20), primary_key=True, comment="الربط مع dim_dates يتم عبر هذه القيمة")
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_month_name: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات:
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")


class ActivityType(Base):
    """(12.6) جدول أنواع الأنشطة التي يمكن تسجيلها في النظام."""
    __tablename__ = 'activity_types'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    activity_type_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    activity_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات:
    translations: Mapped[List["ActivityTypeTranslation"]] = relationship(back_populates="activity_type", cascade="all, delete-orphan")
    user_activity_logs: Mapped[List["UserActivityLog"]] = relationship("UserActivityLog", foreign_keys="[UserActivityLog.activity_type_id]", back_populates="activity_type") # من المجموعة 13


class ActivityTypeTranslation(Base):
    """(12.7) جدول ترجمات أنواع الأنشطة."""
    __tablename__ = 'activity_type_translations'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    activity_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('activity_types.activity_type_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_activity_name: Mapped[str] = mapped_column(String(150), nullable=False)
    translated_activity_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات:
    activity_type: Mapped["ActivityType"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")


class SecurityEventType(Base):
    """(12.8) جدول أنواع أحداث الأمان."""
    __tablename__ = 'security_event_types'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    security_event_type_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    event_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    severity_level: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True, comment="مثل 1-5 لخطورة الحدث")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات:
    translations: Mapped[List["SecurityEventTypeTranslation"]] = relationship(back_populates="security_event_type", cascade="all, delete-orphan")
    security_event_logs: Mapped[List["SecurityEventLog"]] = relationship("SecurityEventLog", foreign_keys=lambda: [SecurityEventLog.security_event_type_id], back_populates="event_type") # من المجموعة 13


class SecurityEventTypeTranslation(Base):
    """(12.9) جدول ترجمات أنواع أحداث الأمان."""
    __tablename__ = 'security_event_type_translations'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    security_event_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('security_event_types.security_event_type_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_event_name: Mapped[str] = mapped_column(String(150), nullable=False)
    translated_event_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات:
    security_event_type: Mapped["SecurityEventType"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")


class Language(Base):
    """(12.10) جدول اللغات: يحتوي على اللغات التي يدعمها النظام وخصائصها."""
    __tablename__ = 'languages'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    language_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    language_name_native: Mapped[str] = mapped_column(String(50), nullable=False, comment="اسم اللغة بلغتها الأصلية")
    language_name_en: Mapped[str] = mapped_column(String(50), nullable=False, comment="اسم اللغة بالإنجليزية كمرجع")
    text_direction: Mapped[str] = mapped_column(String(3), nullable=False, comment="'LTR' أو 'RTL'")
    is_active_for_interface: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    sort_order: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True, comment="لترتيب عرض اللغات في القوائم")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات عكسية مع جداول الترجمة (من المجموعة 12)
    currency_translations: Mapped[List["CurrencyTranslation"]] = relationship("CurrencyTranslation", back_populates="language")
    day_of_week_translations: Mapped[List["DayOfWeekTranslation"]] = relationship("DayOfWeekTranslation", back_populates="language")
    month_translations: Mapped[List["MonthTranslation"]] = relationship("MonthTranslation", back_populates="language")
    activity_type_translations: Mapped[List["ActivityTypeTranslation"]] = relationship("ActivityTypeTranslation", back_populates="language")
    security_event_type_translations: Mapped[List["SecurityEventTypeTranslation"]] = relationship("SecurityEventTypeTranslation", back_populates="language")
    entity_type_translations: Mapped[List["EntityTypeTranslation"]] = relationship("EntityTypeTranslation", back_populates="language")
    users: Mapped[List["User"]] = relationship("User", back_populates="preferred_language")
    
    # علاقات عكسية مع جداول الترجمة من مجموعات أخرى (هنا تضاف فقط للمراجعة الشاملة، كل مودل ترجمة يعرف علاقته العكسية)
    # TODO: UserTypeTranslation.language_code (من المجموعة 1.أ)
    # TODO: AccountStatusTranslation.language_code (من المجموعة 1.أ)
    # TODO: RoleTranslation.language_code (من المجموعة 1.ب)
    # TODO: LicenseTypeTranslation.language_code (من المجموعة 1.ج)
    # TODO: IssuingAuthorityTranslation.language_code (من المجموعة 1.ج)
    # TODO: UserVerificationStatusTranslation.language_code (من المجموعة 1.ج)
    # TODO: LicenseVerificationStatusTranslation.language_code (من المجموعة 1.ج)
    # TODO: AddressTypeTranslation.language_code (من المجموعة 1.د)
    # TODO: CountryTranslation.language_code (من المجموعة 1.د)
    # TODO: GovernorateTranslation.language_code (من المجموعة 1.د)
    # TODO: CityTranslation.language_code (من المجموعة 1.د)
    # TODO: DistrictTranslation.language_code (من المجموعة 1.د)
    # TODO: ProductStatusTranslation.language_code (من المجموعة 2.أ)
    # TODO: ProductCategoryTranslation.language_code (من المجموعة 2.أ)
    # TODO: ProductTranslation.language_code (من المجموعة 2.أ)
    # TODO: ProductVarietyTranslation.language_code (من المجموعة 2.أ)
    # TODO: AttributeTranslation.language_code (من المجموعة 2.ب)
    # TODO: AttributeValueTranslation.language_code (من المجموعة 2.ب)
    # TODO: UnitOfMeasureTranslation.language_code (من المجموعة 2.ج)
    # TODO: ProductPackagingOptionTranslation.language_code (من المجموعة 2.ج)
    # TODO: InventoryItemStatusTranslation.language_code (من المجموعة 2.د)
    # TODO: InventoryTransactionTypeTranslation.language_code (من المجموعة 2.د)
    # TODO: ExpectedCropStatusTranslation.language_code (من المجموعة 2.هـ)
    # TODO: PriceTierRuleTranslation.language_code (من المجموعة 3)
    # TODO: OrderStatusTranslation.language_code (من المجموعة 4.أ)
    # TODO: PaymentStatusTranslation.language_code (من المجموعة 4.أ)
    # TODO: OrderItemStatusTranslation.language_code (من المجموعة 4.أ)
    # TODO: RfqStatusTranslation.language_code (من المجموعة 4.ب)
    # TODO: QuoteStatusTranslation.language_code (من المجموعة 4.ج)
    # TODO: ShipmentStatusTranslation.language_code (من المجموعة 4.د)
    # TODO: AuctionStatusTranslation.language_code (من المجموعة 5.أ)
    # TODO: AuctionTypeTranslation.language_code (من المجموعة 5.أ)
    # TODO: AuctionLotTranslation.language_code (من المجموعة 5.أ)
    # TODO: AuctionSettlementStatusTranslation.language_code (من المجموعة 5.ج)
    # TODO: ReviewStatusTranslation.language_code (من المجموعة 6)
    # TODO: ReviewReportReasonTranslation.language_code (من المجموعة 6)
    # TODO: ReviewCriterionTranslation.language_code (من المجموعة 6)
    # TODO: ResellerSalesOfferTranslation.language_code (من المجموعة 7)
    # TODO: WalletStatusTranslation.language_code (من المجموعة 8.أ)
    # TODO: TransactionTypeTranslation.language_code (من المجموعة 8.أ)
    # TODO: WithdrawalRequestStatusTranslation.language_code (من المجموعة 8.ب)
    # TODO: DeferredPaymentAgreementStatusTranslation.language_code (من المجموعة 9)
    # TODO: InstallmentStatusTranslation.language_code (من المجموعة 9)
    # TODO: GGClaimStatusTranslation.language_code (من المجموعة 10)
    # TODO: GGResolutionTypeTranslation.language_code (من المجموعة 10)
    # TODO: NotificationTemplateTranslation.language_code (من المجموعة 11)
    # TODO: NotificationChannelTranslation.language_code (من المجموعة 11)
    # TODO: NotificationDeliveryStatusTranslation.language_code (من المجموعة 11)
    # TODO: NotificationTypeTranslation.language_code (من المجموعة 11)
    # TODO: SystemEventTypeTranslation.language_code (من المجموعة 13)
    # TODO: ApplicationSettingTranslation.language_code (من المجموعة 14)


class EntityTypeForReviewOrImage(Base):
    """(12.11) جدول أنواع الكيانات التي يمكن أن ترتبط بها مراجعة أو صورة."""
    __tablename__ = 'entity_types_for_reviews_or_images'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    entity_type_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_type_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات:
    translations: Mapped[List["EntityTypeTranslation"]] = relationship(back_populates="entity_type", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", foreign_keys="[Review.reviewed_entity_type]", back_populates="reviewed_entity_type_obj") # <-- أضف هذا السطر
    review_criteria: Mapped[List["ReviewCriterion"]] = relationship("ReviewCriterion", foreign_keys="[ReviewCriterion.applicable_entity_type_code]", back_populates="applicable_entity_type") # <-- أضف هذا السطر

class EntityTypeTranslation(Base):
    """(12.12) جدول ترجمات أنواع الكيانات."""
    __tablename__ = 'entity_type_translations'
    # __table_args__ = {'extend_existing': True} # تم إزالة هذا المعامل بناءً على طلبك

    entity_type_code: Mapped[str] = mapped_column(String(50), ForeignKey('entity_types_for_reviews_or_images.entity_type_code', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_entity_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_entity_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # علاقات:
    entity_type: Mapped["EntityTypeForReviewOrImage"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")


# =================================================================
# جداول Lookups أخرى من مجموعات مختلفة (ليست جزءاً من المجموعة 12 الأساسية، ولكنها جداول مرجعية)
# يجب أن تكون هذه المودلات موجودة في ملفات المودلز الخاصة بمجموعاتها الأصلية.
# هذه المودلات هنا هي فقط لغرض التجميع والمراجعة، لكنها لا تُعرف هنا فعلياً.
#
# هذا التعليق يوضح أن المودلات التالية ليست جزءاً من lookups/models.py
# بل هي من ملفات المودلز الأخرى الخاصة بمجموعاتها (products, market, reviews, wallet, deferred_payments, gg, notifications)
#
# =================================================================
# المجموعة 2: إدارة كتالوج المنتجات والمخزون الأساسي (Product Catalog & Primary Inventory Management)
# 2.أ. المجموعة الفرعية: إدارة المنتجات وفئاتها وأصنافها
# =================================================================
# class ProductStatus(Base): ... (من src.products.models.products_models)
# class ProductStatusTranslation(Base): ... (من src.products.models.products_models)

# =================================================================
# المجموعة 2: إدارة كتالوج المنتجات والمخزون الأساسي (Product Catalog & Primary Inventory Management)
# 2.د. المجموعة الفرعية: إدارة المخزون الأساسي وحركاته
# =================================================================
# class InventoryItemStatus(Base): ... (من src.products.models.inventory_models)
# class InventoryItemStatusTranslation(Base): ... (من src.products.models.inventory_models)
# class InventoryTransactionType(Base): ... (من src.products.models.inventory_models)
# class InventoryTransactionTypeTranslation(Base): ... (من src.products.models.inventory_models)


# =================================================================
# المجموعة 2: إدارة كتالوج المنتجات والمخزون الأساسي (Product Catalog & Primary Inventory Management)
# 2.هـ. المجموعة الفرعية: إدارة العروض المستقبلية وتتبع الأسعار
# =================================================================
# class ExpectedCropStatus(Base): ... (من src.products.models.future_offerings_models)
# class ExpectedCropStatusTranslation(Base): ... (من src.products.models.future_offerings_models)


# =================================================================
# المجموعة 4: إدارة عمليات السوق (الطلبات، طلبات عروض الأسعار، عروض الأسعار) (Market Operations Management - Orders, RFQs, Quotes)
# 4.أ. المجموعة الفرعية: إدارة الطلبات المباشرة
# =================================================================
# class OrderStatus(Base): ... (من src.market.models.orders_models)
# class OrderStatusTranslation(Base): ... (من src.market.models.orders_models)
# class PaymentStatus(Base): ... (من src.market.models.orders_models)
# class PaymentStatusTranslation(Base): ... (من src.market.models.orders_models)
# class OrderItemStatus(Base): ... (من src.market.models.orders_models)
# class OrderItemStatusTranslation(Base): ... (من src.market.models.orders_models)

# =================================================================
# المجموعة 4: إدارة عمليات السوق (الطلبات، طلبات عروض الأسعار، عروض الأسعار) (Market Operations Management - Orders, RFQs, Quotes)
# 4.ب. المجموعة الفرعية: إدارة طلبات عروض الأسعار (RFQs)
# =================================================================
# class RfqStatus(Base): ... (من src.market.models.rfqs_models)
# class RfqStatusTranslation(Base): ... (من src.market.models.rfqs_models)

# =================================================================
# المجموعة 4: إدارة عمليات السوق (الطلبات، طلبات عروض الأسعار، عروض الأسعار) (Market Operations Management - Orders, RFQs, Quotes)
# 4.ج. المجموعة الفرعية: إدارة عروض الأسعار (Quotes)
# =================================================================
# class QuoteStatus(Base): ... (من src.market.models.quotes_models)
# class QuoteStatusTranslation(Base): ... (من src.market.models.quotes_models)

# =================================================================
# المجموعة 4: إدارة عمليات السوق (الطلبات، طلبات عروض الأسعار، عروض الأسعار) (Market Operations Management - Orders, RFQs, Quotes)
# 4.د. المجموعة الفرعية: إدارة الشحنات (مبدئي)
# =================================================================
# class ShipmentStatus(Base): ... (من src.market.models.shipments_models)
# class ShipmentStatusTranslation(Base): ... (من src.market.models.shipments_models)


# =================================================================
# المجموعة 6: إدارة المراجعات والتقييمات (Reviews & Ratings Management)
# =================================================================
# class ReviewStatus(Base): ... (من src.reviews.models.reviews_models)
# class ReviewStatusTranslation(Base): ... (من src.reviews.models.reviews_models)
# class ReviewReportReason(Base): ... (من src.reviews.models.reviews_models)
# class ReviewReportReasonTranslation(Base): ... (من src.reviews.models.reviews_models)
# class ReviewCriterion(Base): ... (من src.reviews.models.reviews_models)
# class ReviewCriterionTranslation(Base): ... (من src.reviews.models.reviews_models)


# ==========================================================
# المجموعة 8: إدارة المحفظة والمدفوعات (Wallet & Payment Management)
# ==========================================================
# class WalletStatus(Base): ... (من src.wallet.models.wallet_models)
# class WalletStatusTranslation(Base): ... (من src.wallet.models.wallet_models)
# class TransactionType(Base): ... (من src.wallet.models.wallet_models)
# class TransactionTypeTranslation(Base): ... (من src.wallet.models.wallet_models)
# class PaymentGateway(Base): ... (من src.wallet.models.wallet_models)
# class WithdrawalRequestStatus(Base): ... (من src.wallet.models.wallet_models)
# class WithdrawalRequestStatusTranslation(Base): ... (من src.wallet.models.wallet_models)


# =================================================================
# المجموعة 9: إدارة اتفاقيات الدفع الآجل (Seller-Managed Deferred Payment Agreements)
# =================================================================
# class DeferredPaymentAgreementStatus(Base): ... (من src.deferred_payments.models.deferred_payment_models)
# class DeferredPaymentAgreementStatusTranslation(Base): ... (من src.deferred_payments.models.deferred_payment_models)
# class InstallmentStatus(Base): ... (من src.deferred_payments.models.deferred_payment_models)
# class InstallmentStatusTranslation(Base): ... (من src.deferred_payments.models.deferred_payment_models)


# =================================================================
# المجموعة 10: إدارة الضمان الذهبي (Golden Guarantee Management)
# =================================================================
# class GGClaimStatus(Base): ... (من src.golden_guarantee.models.gg_models)
# class GGClaimStatusTranslation(Base): ... (من src.golden_guarantee.models.gg_models)
# class GGResolutionType(Base): ... (من src.golden_guarantee.models.gg_models)
# class GGResolutionTypeTranslation(Base): ... (من src.golden_guarantee.models.gg_models)


# =================================================================
# المجموعة 11: نظام الإشعارات والاتصالات (Notification & Communication System)
# =================================================================
# class NotificationType(Base): ... (من src.notifications.models.notifications_models)
# class NotificationTypeTranslation(Base): ... (من src.notifications.models.notifications_models)
# class NotificationChannel(Base): ... (من src.notifications.models.notifications_models)
# class NotificationChannelTranslation(Base): ... (من src.notifications.models.notifications_models)
# class NotificationDeliveryStatus(Base): ... (من src.notifications.models.notifications_models)
# class NotificationDeliveryStatusTranslation(Base): ... (من src.notifications.models.notifications_models)


# =================================================================
# المجموعة 13: سجلات التدقيق والأنشطة العامة (General Audit & Activity Logs)
# =================================================================
# class SystemEventType(Base): ... (من src.audit.models.audit_models)
# class SystemEventTypeTranslation(Base): ... (من src.audit.models.audit_models)




# =================================================================
# المجموعة 2: إدارة كتالوج المنتجات والمخزون الأساسي (Product Catalog & Primary Inventory Management)
# 2.أ. المجموعة الفرعية: إدارة المنتجات وفئاتها وأصنافها
# =================================================================

class ProductStatus(Base):
    """(من 2.أ) جدول حالات المنتج (نشط، غير نشط، مسودة...)."""
    __tablename__ = 'product_statuses'
    product_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    translations: Mapped[List["ProductStatusTranslation"]] = relationship(back_populates="product_status", cascade="all, delete-orphan")

class ProductStatusTranslation(Base):
    """(من 2.أ) جدول ترجمات حالات المنتج."""
    __tablename__ = 'product_status_translations'
    # product_status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('product_statuses.product_status_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    product_status: Mapped["ProductStatus"] = relationship(back_populates="translations")

# =================================================================
# المجموعة 2: إدارة كتالوج المنتجات والمخزون الأساسي (Product Catalog & Primary Inventory Management)
# 2.د. المجموعة الفرعية: إدارة المخزون الأساسي وحركاته
# =================================================================


class InventoryItemStatus(Base):
    """(من 2.د) جدول حالات عنصر المخزون (متاح، محجوز، تالف...)."""
    __tablename__ = 'inventory_item_statuses'
    inventory_item_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class InventoryItemStatusTranslation(Base):
    """(من 2.د) جدول ترجمات حالات عنصر المخزون."""
    __tablename__ = 'inventory_item_status_translations'
    # status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    inventory_item_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('inventory_item_statuses.inventory_item_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_status_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class InventoryTransactionType(Base):
    """(من 2.د) جدول أنواع حركات المخزون (إضافة، بيع، إتلاف...)."""
    __tablename__ = 'inventory_transaction_types'
    transaction_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_type_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class InventoryTransactionTypeTranslation(Base):
    """(من 2.د) جدول ترجمات أنواع حركات المخزون."""
    __tablename__ = 'inventory_transaction_type_translations'
    # transaction_type_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    transaction_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('inventory_transaction_types.transaction_type_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_transaction_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_transaction_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


# =================================================================
# المجموعة 2: إدارة كتالوج المنتجات والمخزون الأساسي (Product Catalog & Primary Inventory Management)
# 2.هـ. المجموعة الفرعية: إدارة العروض المستقبلية وتتبع الأسعار
# =================================================================

class ExpectedCropStatus(Base):
    """(من 2.هـ) جدول حالات المحاصيل المتوقعة (معروض، محجوز...)."""
    __tablename__ = 'expected_crop_statuses'
    status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class ExpectedCropStatusTranslation(Base):
    """(من 2.هـ) جدول ترجمات حالات المحاصيل المتوقعة."""
    __tablename__ = 'expected_crop_status_translations'
    # translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    status_id: Mapped[int] = mapped_column(Integer, ForeignKey('expected_crop_statuses.status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True) # حقل الوصف المضاف بناءً على طلبك
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


# =================================================================
# المجموعة 4: إدارة عمليات السوق (الطلبات، طلبات عروض الأسعار، عروض الأسعار) (Market Operations Management - Orders, RFQs, Quotes)
# 4.أ. المجموعة الفرعية: إدارة الطلبات المباشرة
# =================================================================

class OrderStatus(Base):
    """(من 4.أ) جدول حالات الطلب (قيد المراجعة، مؤكد، تم الشحن...)."""
    __tablename__ = 'order_statuses'
    order_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status_description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class OrderStatusTranslation(Base):
    """(من 4.أ) جدول ترجمات حالات الطلب."""
    __tablename__ = 'order_status_translations'
    # status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('order_statuses.order_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_status_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class PaymentStatus(Base):
    """(من 4.أ) جدول حالات الدفع (بانتظار الدفع، تم الدفع، فشل...)."""
    __tablename__ = 'payment_statuses'
    payment_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class PaymentStatusTranslation(Base):
    """(من 4.أ) جدول ترجمات حالات الدفع."""
    __tablename__ = 'payment_status_translations'
    # payment_status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    payment_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('payment_statuses.payment_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class OrderItemStatus(Base):
    """(من 4.أ) جدول حالات بنود الطلب (قيد التجهيز، تم الشحن...)."""
    __tablename__ = 'order_item_statuses'
    item_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class OrderItemStatusTranslation(Base):
    """(من 4.أ) جدول ترجمات حالات بنود الطلب."""
    __tablename__ = 'order_item_status_translations'
    # item_status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    item_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('order_item_statuses.item_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

# =================================================================
# المجموعة 4: إدارة عمليات السوق (الطلبات، طلبات عروض الأسعار، عروض الأسعار) (Market Operations Management - Orders, RFQs, Quotes)
# 4.ب. المجموعة الفرعية: إدارة طلبات عروض الأسعار (RFQs)
# =================================================================

class RfqStatus(Base):
    """(من 4.ب) جدول حالات طلب عرض السعر (مفتوح، مغلق، ملغى...)."""
    __tablename__ = 'rfq_statuses'
    rfq_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class RfqStatusTranslation(Base):
    """(من 4.ب) جدول ترجمات حالات طلب عرض السعر."""
    __tablename__ = 'rfq_status_translations'
    # status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rfq_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('rfq_statuses.rfq_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

# =================================================================
# المجموعة 4: إدارة عمليات السوق (الطلبات، طلبات عروض الأسعار، عروض الأسعار) (Market Operations Management - Orders, RFQs, Quotes)
# 4.ج. المجموعة الفرعية: إدارة عروض الأسعار (Quotes)
# =================================================================

class QuoteStatus(Base):
    """(من 4.ج) جدول حالات عرض السعر (مقدم، مقبول، مرفوض...)."""
    __tablename__ = 'quote_statuses'
    quote_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class QuoteStatusTranslation(Base):
    """(من 4.ج) جدول ترجمات حالات عرض السعر."""
    __tablename__ = 'quote_status_translations'
    # status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    quote_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('quote_statuses.quote_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


# =================================================================
# المجموعة 4: إدارة عمليات السوق (الطلبات، طلبات عروض الأسعار، عروض الأسعار) (Market Operations Management - Orders, RFQs, Quotes)
# 4.د. المجموعة الفرعية: إدارة الشحنات (مبدئي)
# =================================================================

class ShipmentStatus(Base):
    """(من 4.د) جدول حالات الشحن (قيد التجهيز، تم التسليم...)."""
    __tablename__ = 'shipment_statuses'
    shipment_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class ShipmentStatusTranslation(Base):
    """(من 4.د) جدول ترجمات حالات الشحن."""
    __tablename__ = 'shipment_status_translations'
    # status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    shipment_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('shipment_statuses.shipment_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


# =================================================================
# المجموعة 6: إدارة المراجعات والتقييمات (Reviews & Ratings Management)
# =================================================================

class ReviewStatus(Base):
    """(6.9) جدول حالات المراجعة (بانتظار الموافقة، منشورة، مرفوضة)."""
    __tablename__ = 'review_statuses'
    status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    translations: Mapped[List["ReviewStatusTranslation"]] = relationship(back_populates="review_status", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", foreign_keys="[Review.review_status_id]", back_populates="review_status") 

class ReviewStatusTranslation(Base):
    """(6.10) جدول ترجمات حالات المراجعة."""
    __tablename__ = 'review_status_translations'
    status_id: Mapped[int] = mapped_column(Integer, ForeignKey('review_statuses.status_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    review_status: Mapped["ReviewStatus"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")

class ReviewReportReason(Base):
    """(6.7) جدول أسباب الإبلاغ عن المراجعات."""
    __tablename__ = 'review_report_reasons'
    reason_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reason_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    translations: Mapped[List["ReviewReportReasonTranslation"]] = relationship(back_populates="review_report_reason", cascade="all, delete-orphan")
    review_reports: Mapped[List["ReviewReport"]] = relationship("ReviewReport", foreign_keys="[ReviewReport.report_reason_id]", back_populates="report_reason") # <-- أضف هذا السطر

# ==========================================================
# --- مودلز أسباب الإبلاغ عن المراجعات (Review Report Reasons) ---
#    (من المجموعة 6، تم نقلها إلى هنا لأنها جداول Lookup)
# ==========================================================

class ReviewReportReasonTranslation(Base):
    """(6.8) جدول ترجمات أسباب الإبلاغ."""
    __tablename__ = 'review_report_reason_translations'
    reason_id: Mapped[int] = mapped_column(Integer, ForeignKey('review_report_reasons.reason_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_reason_text: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    review_report_reason: Mapped["ReviewReportReason"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")

# ==========================================================
# --- مودلز معايير التقييم (Review Criteria) ---
#    (من المجموعة 6، تم نقلها إلى هنا لأنها جداول Lookup)
# ==========================================================

class ReviewCriterion(Base):
    __tablename__ = 'review_criteria'
    
    criteria_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    criteria_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    applicable_entity_type_code: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey('entity_types_for_reviews_or_images.entity_type_code'), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    translations: Mapped[List["ReviewCriterionTranslation"]] = relationship(back_populates="review_criterion", cascade="all, delete-orphan")
    
    applicable_entity_type: Mapped[Optional["EntityTypeForReviewOrImage"]] = relationship(
        "EntityTypeForReviewOrImage", 
        foreign_keys=[applicable_entity_type_code],  # refer to the mapped column attribute
        lazy="selectin", 
        back_populates="review_criteria"
    )
    
    review_ratings_by_criteria: Mapped[List["ReviewRatingByCriterion"]] = relationship(
        "ReviewRatingByCriterion", 
        foreign_keys="[ReviewRatingByCriterion.criteria_id]", 
        back_populates="review_criterion"
    )
 # هذا السطر صحيح لأنه يشير لعمود في مودل آخر

class ReviewCriterionTranslation(Base):
    """(6.3) جدول ترجمات معايير التقييم."""
    __tablename__ = 'review_criteria_translations'
    criteria_id: Mapped[int] = mapped_column(Integer, ForeignKey('review_criteria.criteria_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    translated_criteria_name: Mapped[str] = mapped_column(String(150), nullable=False)
    translated_criteria_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    review_criterion: Mapped["ReviewCriterion"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship("Language", foreign_keys=[language_code], lazy="selectin")

# =================================================================
# المجموعة 8: إدارة المحفظة والمدفوعات (Wallet & Payment Management)
# =================================================================

class WalletStatus(Base):
    """(8.أ.5) حالات المحفظة (نشطة، مجمدة...)."""
    __tablename__ = 'wallet_statuses'
    wallet_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class WalletStatusTranslation(Base):
    """(8.أ.6) ترجمات حالات المحفظة."""
    __tablename__ = 'wallet_status_translations'
    # wallet_status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    wallet_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('wallet_statuses.wallet_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_wallet_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_wallet_status_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class TransactionType(Base):
    """(8.أ.3) أنواع معاملات المحفظة (إيداع، سحب، شراء...)."""
    __tablename__ = 'transaction_types'
    transaction_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_type_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description_key: Mapped[str] = mapped_column(String(255), nullable=True)
    is_credit: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="هل المعاملة تضيف رصيدًا أم تخصم")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class TransactionTypeTranslation(Base):
    """(8.أ.4) ترجمات أنواع معاملات المحفظة."""
    __tablename__ = 'transaction_type_translations'
    # type_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    transaction_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('transaction_types.transaction_type_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_transaction_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class PaymentGateway(Base):
    """(8.ب.1) بوابات الدفع المعتمدة."""
    __tablename__ = 'payment_gateways'
    gateway_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gateway_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    gateway_display_name_key: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    configuration_details: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class WithdrawalRequestStatus(Base):
    """(8.ب.4) حالات طلبات سحب الرصيد."""
    __tablename__ = 'withdrawal_request_statuses'
    withdrawal_request_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class WithdrawalRequestStatusTranslation(Base):
    """(8.ب.5) ترجمات حالات طلبات سحب الرصيد."""
    __tablename__ = 'withdrawal_request_status_translations'
    # status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    withdrawal_request_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('withdrawal_request_statuses.withdrawal_request_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_status_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

# =================================================================
# المجموعة 9: إدارة اتفاقيات الدفع الآجل (Seller-Managed Deferred Payment Agreements)
# =================================================================

class DeferredPaymentAgreementStatus(Base):
    """(من 9) حالات اتفاقيات الدفع الآجل (نشطة، مكتملة، متعثرة...)."""
    __tablename__ = 'deferred_payment_agreement_statuses'
    deferred_payment_agreement_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class DeferredPaymentAgreementStatusTranslation(Base):
    """(من 9) ترجمات حالات اتفاقيات الدفع الآجل."""
    __tablename__ = 'deferred_payment_agreement_status_translations'
    # status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    deferred_payment_agreement_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('deferred_payment_agreement_statuses.deferred_payment_agreement_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class InstallmentStatus(Base):
    """(من 9) حالات الأقساط (مستحق، مدفوع، متأخر...)."""
    __tablename__ = 'installment_statuses'
    installment_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class InstallmentStatusTranslation(Base):
    """(من 9) ترجمات حالات الأقساط."""
    __tablename__ = 'installment_status_translations'
    # status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    installment_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('installment_statuses.installment_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

# =================================================================
# المجموعة 10: إدارة الضمان الذهبي (Golden Guarantee Management)
# =================================================================

class GGClaimStatus(Base):
    """(من 3 10) جدول حالات مطالبات الضمان الذهبي."""
    __tablename__ = 'gg_claim_statuses'
    gg_claim_status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class GGClaimStatusTranslation(Base):
    """(4 من 10) جدول ترجمات حالات مطالبات الضمان الذهبي."""
    __tablename__ = 'gg_claim_status_translations'
    # status_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gg_claim_status_id: Mapped[int] = mapped_column(Integer, ForeignKey('gg_claim_statuses.gg_claim_status_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class GGResolutionType(Base):
    """(7 من 10) جدول أنواع حلول مطالبات الضمان الذهبي."""
    __tablename__ = 'gg_resolution_types'
    gg_resolution_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resolution_type_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class GGResolutionTypeTranslation(Base):
    """(8 من 10) جدول ترجمات أنواع حلول مطالبات الضمان الذهبي."""
    __tablename__ = 'gg_resolution_type_translations'
    # resolution_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gg_resolution_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('gg_resolution_types.gg_resolution_type_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_resolution_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


# =================================================================
# المجموعة 13: سجلات التدقيق والأنشطة العامة (General Audit & Activity Logs)
# =================================================================

class SystemEventType(Base):
    """(من 13) جدول أنواع أحداث النظام العامة."""
    __tablename__ = 'system_event_types'
    event_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    system_audit_logs: Mapped[List["SystemAuditLog"]] = relationship(
        "SystemAuditLog",
        back_populates="event_type",
        lazy="selectin"
    )

class SystemEventTypeTranslation(Base):
    """(من 13) جدول ترجمات أنواع أحداث النظام العامة."""
    __tablename__ = 'system_event_type_translations'
    # event_type_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('system_event_types.event_type_id'), primary_key=True) # nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_event_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())






class AuctionStatus(Base):
    """
    (5.أ.2) جدول حالات المزاد: يحدد الحالات المختلفة التي يمكن أن يمر بها المزاد.
    مثلاً: 'مجدول', 'نشط', 'مغلق ببيع', 'ملغى'.
    """
    __tablename__ = 'auction_statuses'
    auction_status_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    status_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="مفتاح فريد لاسم الحالة للترجمة.")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات الترجمة
    translations: Mapped[List["AuctionStatusTranslation"]] = relationship(
        back_populates="auction_status", cascade="all, delete-orphan" # علاقة بترجمات الحالة
    )
    # المزادات التي تحمل هذه الحالة (علاقة عكسية)
    auctions: Mapped[List["Auction"]] = relationship("Auction", back_populates="auction_status")
    # لوطات المزادات التي تحمل هذه الحالة (علاقة عكسية)
    auction_lots: Mapped[List["AuctionLot"]] = relationship("AuctionLot", back_populates="lot_status")



class AuctionStatusTranslation(Base):
    """
    (5.أ.3) جدول ترجمات حالات المزاد.
    """
    __tablename__ = 'auction_status_translations'
    auction_status_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('auction_statuses.auction_status_id', ondelete="CASCADE"), primary_key=True
    )
    language_code: Mapped[str] = mapped_column(
        String(10), ForeignKey('languages.language_code'), primary_key=True
    )
    translated_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # وصف مطول للحالة
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    auction_status: Mapped["AuctionStatus"] = relationship(back_populates="translations") # علاقة بحالة المزاد الأب


class AuctionType(Base):
    """
    (5.أ.4) جدول أنواع المزادات: يحدد أنواع المزادات المختلفة التي قد تدعمها المنصة.
    مثلاً: 'مزاد عادي', 'مزاد ما قبل الوصول', 'مزاد صامت'.
    """
    __tablename__ = 'auction_types'
    auction_type_id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL
    type_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="مفتاح فريد لاسم النوع للترجمة.")
    description_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="مفتاح لوصف النوع للترجمة.")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["AuctionTypeTranslation"]] = relationship(
        back_populates="auction_type", cascade="all, delete-orphan" # علاقة بترجمات نوع المزاد
    )
    # المزادات من هذا النوع (علاقة عكسية)
    auctions: Mapped[List["Auction"]] = relationship("Auction", back_populates="auction_type")

class AuctionTypeTranslation(Base):
    """
    (5.أ.5) جدول ترجمات أنواع المزادات.
    """
    __tablename__ = 'auction_type_translations'
    auction_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('auction_types.auction_type_id', ondelete="CASCADE"), primary_key=True
    )
    language_code: Mapped[str] = mapped_column(
        String(10), ForeignKey('languages.language_code'), primary_key=True
    )
    translated_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_type_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    auction_type: Mapped["AuctionType"] = relationship(back_populates="translations") # علاقة بنوع المزاد الأب
