# backend\src\core\schemas_bootstrap.py

# هذا الملف يقوم بضمان أن جميع نماذج Pydantic (خاصة تلك التي تحتوي على مراجع أمامية)
# يتم إعادة بنائها وحلها بشكل صحيح بعد تحميل جميع الوحدات (modules) في النظام.
# يتم استدعاء دالة rebuild_all_schemas() مرة واحدة عند بدء تشغيل التطبيق.

# استيراد Schemas من جميع المجموعات الموجودة في هيكل مشروعك
# يتم الاستيراد هنا لضمان تحميل جميع تعريفات Schemas في ذاكرة Python
# (يفضل استخدام aliases لتقليل تضارب الأسماء ولزيادة الوضوح)

# Schemas من المجموعة 1 (إدارة المستخدمين)
import src.users.schemas.core_schemas as users_core_schemas
import src.users.schemas.address_schemas as users_address_schemas
import src.users.schemas.rbac_schemas as users_rbac_schemas
import src.users.schemas.license_schemas as users_license_schemas
import src.users.schemas.management_schemas as users_management_schemas
import src.users.schemas.security_schemas as users_security_schemas
import src.users.schemas.verification_lookups_schemas as users_verification_lookups_schemas

# Schemas من المجموعة 2 (كتالوج المنتجات)
import src.products.schemas.product_schemas as products_product_schemas
import src.products.schemas.attribute_schemas as products_attribute_schemas
import src.products.schemas.category_schemas as products_category_schemas
import src.products.schemas.units_schemas as products_units_schemas
import src.products.schemas.packaging_schemas as products_packaging_schemas
import src.products.schemas.inventory_schemas as products_inventory_schemas
import src.products.schemas.future_offerings_schemas as products_future_offerings_schemas
import src.products.schemas.product_lookups_schemas as products_product_lookups_schemas
# import src.products.schemas.pricing_schemas as products_pricing_schemas

# Schemas من المجموعة 3 (التسعير)
import src.pricing.schemas.pricing_schemas as pricing_pricing_schemas

# Schemas من المجموعة 4 (عمليات السوق)
import src.market.schemas.order_schemas as market_order_schemas
import src.market.schemas.rfq_schemas as market_rfq_schemas
import src.market.schemas.quote_schemas as market_quote_schemas
import src.market.schemas.shipment_schemas as market_shipment_schemas

# Schemas من المجموعة 5 (المزادات)
import src.auctions.schemas.auction_schemas as auctions_auction_schemas
import src.auctions.schemas.bidding_schemas as auctions_bidding_schemas
import src.auctions.schemas.settlement_schemas as auctions_settlement_schemas

# Schemas من المجموعة 6 (المراجعات - Community)
import src.community.schemas.reviews_schemas as community_reviews_schemas

# Schemas من المجموعة 8 (المحفظة والمدفوعات - Finance) - TODO: تأكد من هذه المسارات والأسماء عند بناء المجموعة
# import src.finance.schemas.wallets_schemas as finance_wallets_schemas
# import src.finance.schemas.operations_schemas as finance_operations_schemas
# import src.finance.schemas.commissions_schemas as finance_commissions_schemas

# Schemas من المجموعة 9 (اتفاقيات الدفع الآجل - Agreements)
# TODO: تأكد من هذه المسارات والأسماء عند بناء المجموعة
# import src.agreements.schemas.deferred_payment_schemas as agreements_deferred_payment_schemas

# Schemas من المجموعة 10 (الضمان الذهبي - Guarantees)
# TODO: تأكد من هذه المسارات والأسماء عند بناء المجموعة
# import src.guarantees.schemas.claims_schemas as guarantees_claims_schemas

# Schemas من المجموعة 11 (الإشعارات والاتصالات - Communications)
# TODO: تأكد من هذه المسارات والأسماء عند بناء المجموعة
# import src.communications.schemas.notifications_schemas as communications_notifications_schemas

# Schemas من المجموعة 12 (Lookups العامة)
import src.lookups.schemas.lookups_schemas as lookups_lookups_schemas

# Schemas من المجموعة 13 (سجلات التدقيق - Auditing)
import src.auditing.schemas.audit_schemas as auditing_audit_schemas

# Schemas من المجموعة 14 (إعدادات النظام - Configuration)
import src.configuration.schemas.settings_schemas as configuration_settings_schemas


def rebuild_all_schemas():
    """
    يقوم بإعادة بناء جميع نماذج Pydantic التي تحتوي على مراجع أمامية.
    يجب استدعاء هذه الدالة مرة واحدة عند بدء تشغيل التطبيق.
    الترتيب هنا مهم جداً لحل التبعيات المعقدة.
    """
    print("Rebuilding Pydantic schemas (ordered by dependency)...")

    # =====================================================================
    # 1. المرحلة الأولى: إعادة بناء Schemas الأساسية جداً والتي لا تعتمد على الكثير
    #    أو التي تسبب مشاكل الاستيراد الدائرية العميقة (مثل UserRead)
    # =====================================================================

    # إعادة بناء UserRead مبكراً لجعله متاحاً للآخرين (سيتم إعادة بنائه مرة أخرى لاحقاً)
    # هذا يساعد في كسر حلقة التبعية العميقة.
    users_core_schemas.UserRead.model_rebuild()
    # يمكن إضافة بعض تبعيات UserRead المباشرة هنا إذا كانت تسبب مشاكل مبكرة
    # users_core_schemas.AccountStatusRead.model_rebuild()
    # users_core_schemas.UserTypeRead.model_rebuild()
    # users_rbac_schemas.RoleRead.model_rebuild()


    # =====================================================================
    # 2. إعادة بناء Schemas Lookups العامة (المجموعة 12)
    #    هذه يجب أن تكون هي الأساس لأن الكثير يعتمد عليها.
    # =====================================================================
    lookups_lookups_schemas.CurrencyRead.model_rebuild()
    lookups_lookups_schemas.LanguageRead.model_rebuild()
    lookups_lookups_schemas.DimDateRead.model_rebuild()
    lookups_lookups_schemas.DayOfWeekTranslationRead.model_rebuild()
    lookups_lookups_schemas.MonthTranslationRead.model_rebuild()
    lookups_lookups_schemas.ActivityTypeRead.model_rebuild()
    lookups_lookups_schemas.ActivityTypeTranslationRead.model_rebuild()
    lookups_lookups_schemas.SecurityEventTypeRead.model_rebuild()
    lookups_lookups_schemas.SecurityEventTypeTranslationRead.model_rebuild()
    lookups_lookups_schemas.EntityTypeForReviewOrImageRead.model_rebuild()
    lookups_lookups_schemas.EntityTypeTranslationRead.model_rebuild()
    lookups_lookups_schemas.ProductStatusRead.model_rebuild()
    lookups_lookups_schemas.ProductStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.InventoryItemStatusRead.model_rebuild()
    lookups_lookups_schemas.InventoryItemStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.InventoryTransactionTypeRead.model_rebuild()
    lookups_lookups_schemas.InventoryTransactionTypeTranslationRead.model_rebuild()
    lookups_lookups_schemas.ExpectedCropStatusRead.model_rebuild()
    lookups_lookups_schemas.ExpectedCropStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.OrderStatusRead.model_rebuild()
    lookups_lookups_schemas.OrderStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.PaymentStatusRead.model_rebuild()
    lookups_lookups_schemas.PaymentStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.OrderItemStatusRead.model_rebuild()
    lookups_lookups_schemas.OrderItemStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.RfqStatusRead.model_rebuild()
    lookups_lookups_schemas.RfqStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.QuoteStatusRead.model_rebuild()
    lookups_lookups_schemas.QuoteStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.ShipmentStatusRead.model_rebuild()
    lookups_lookups_schemas.ShipmentStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.ReviewStatusRead.model_rebuild()
    lookups_lookups_schemas.ReviewStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.ReviewReportReasonRead.model_rebuild()
    lookups_lookups_schemas.ReviewReportReasonTranslationRead.model_rebuild()
    lookups_lookups_schemas.ReviewCriterionRead.model_rebuild()
    lookups_lookups_schemas.ReviewCriterionTranslationRead.model_rebuild()
    lookups_lookups_schemas.WalletStatusRead.model_rebuild()
    lookups_lookups_schemas.WalletStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.TransactionTypeRead.model_rebuild()
    lookups_lookups_schemas.TransactionTypeTranslationRead.model_rebuild()
    lookups_lookups_schemas.PaymentGatewayRead.model_rebuild()
    lookups_lookups_schemas.WithdrawalRequestStatusRead.model_rebuild()
    lookups_lookups_schemas.WithdrawalRequestStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.DeferredPaymentAgreementStatusRead.model_rebuild()
    lookups_lookups_schemas.DeferredPaymentAgreementStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.InstallmentStatusRead.model_rebuild()
    lookups_lookups_schemas.InstallmentStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.GGClaimStatusRead.model_rebuild()
    lookups_lookups_schemas.GGClaimStatusTranslationRead.model_rebuild()
    lookups_lookups_schemas.GGResolutionTypeRead.model_rebuild()
    lookups_lookups_schemas.GGResolutionTypeTranslationRead.model_rebuild()
    lookups_lookups_schemas.SystemEventTypeRead.model_rebuild()
    lookups_lookups_schemas.SystemEventTypeTranslationRead.model_rebuild()

    # # =====================================================================
    # # 3. إعادة بناء Schemas الوحدات الأساسية التي تعتمد على Lookups (وليس UserRead بعد)
    # # =====================================================================

    # # المجموعة 13 (سجلات التدقيق) - تعتمد على Lookups فقط (SystemEventType, ActivityType, SecurityEventType)
    # auditing_audit_schemas.SystemAuditLogRead.model_rebuild()
    # auditing_audit_schemas.UserActivityLogRead.model_rebuild()
    # auditing_audit_schemas.SearchLogRead.model_rebuild()
    # auditing_audit_schemas.SecurityEventLogRead.model_rebuild()
    # auditing_audit_schemas.DataChangeAuditLogRead.model_rebuild()

    # # المجموعة 14 (إعدادات النظام) - تعتمد على Lookups
    # configuration_settings_schemas.ApplicationSettingRead.model_rebuild()
    # configuration_settings_schemas.ApplicationSettingTranslationRead.model_rebuild()
    # configuration_settings_schemas.FeatureFlagRead.model_rebuild()
    # configuration_settings_schemas.SystemMaintenanceScheduleRead.model_rebuild()

    # # Schemas الأساسية لوحدة المستخدمين (بدون UserRead بعد)
    # users_core_schemas.UserTypeRead.model_rebuild()
    # users_core_schemas.AccountStatusRead.model_rebuild()
    # users_core_schemas.AccountStatusHistoryRead.model_rebuild()
    # users_core_schemas.UserPreferenceRead.model_rebuild()
    # users_core_schemas.UserCreate.model_rebuild()
    # users_core_schemas.UserUpdate.model_rebuild()
    # users_core_schemas.UserChangePassword.model_rebuild()
    # users_core_schemas.Token.model_rebuild()
    
    # users_address_schemas.AddressTypeRead.model_rebuild()
    # users_address_schemas.AddressTypeTranslationRead.model_rebuild()
    # users_address_schemas.CountryRead.model_rebuild()
    # users_address_schemas.CountryTranslationRead.model_rebuild()
    # users_address_schemas.GovernorateRead.model_rebuild()
    # users_address_schemas.GovernorateTranslationRead.model_rebuild()
    # users_address_schemas.CityRead.model_rebuild()
    # users_address_schemas.CityTranslationRead.model_rebuild()
    # users_address_schemas.DistrictRead.model_rebuild()
    # users_address_schemas.DistrictTranslationRead.model_rebuild()
    # users_address_schemas.AddressRead.model_rebuild()

    # users_rbac_schemas.RoleRead.model_rebuild()
    # users_rbac_schemas.RoleWithPermissionsRead.model_rebuild()
    # users_rbac_schemas.PermissionRead.model_rebuild()
    # users_rbac_schemas.GroupedPermissionRead.model_rebuild()
    # users_rbac_schemas.RoleTranslationRead.model_rebuild()
    # users_rbac_schemas.UserRoleRead.model_rebuild()

    # users_license_schemas.LicenseRead.model_rebuild()
    # users_management_schemas.AdminUserStatusUpdate.model_rebuild()
    # users_security_schemas.UserSessionRead.model_rebuild()
    # users_security_schemas.PhoneChangeRequestRead.model_rebuild()
    # users_security_schemas.PasswordResetTokenRead.model_rebuild()
    # users_security_schemas.PasswordResetRequestSchema.model_rebuild()
    # users_security_schemas.PasswordResetConfirmSchema.model_rebuild()
    # users_security_schemas.PhoneChangeRequestCreate.model_rebuild()
    # users_security_schemas.PhoneChangeVerify.model_rebuild()
    # users_security_schemas.TokenPayload.model_rebuild()
    # users_verification_lookups_schemas.LicenseTypeRead.model_rebuild()
    # users_verification_lookups_schemas.LicenseTypeTranslationRead.model_rebuild()
    # users_verification_lookups_schemas.IssuingAuthorityRead.model_rebuild()
    # users_verification_lookups_schemas.IssuingAuthorityTranslationRead.model_rebuild()
    # users_verification_lookups_schemas.UserVerificationStatusRead.model_rebuild()
    # users_verification_lookups_schemas.UserVerificationStatusTranslationRead.model_rebuild()
    # users_verification_lookups_schemas.LicenseVerificationStatusRead.model_rebuild()
    # users_verification_lookups_schemas.LicenseVerificationStatusTranslationRead.model_rebuild()
    # users_verification_lookups_schemas.UserVerificationHistoryRead.model_rebuild()
    # users_verification_lookups_schemas.ManualVerificationLogRead.model_rebuild()

    # # المجموعة 2 (كتالوج المنتجات) - تعتمد على UserRead و Lookups
    # products_product_schemas.ProductRead.model_rebuild()
    # products_product_schemas.ProductTranslationRead.model_rebuild()
    # products_product_schemas.ProductVarietyRead.model_rebuild()
    # products_product_schemas.ProductVarietyTranslationRead.model_rebuild()
    # products_product_schemas.LotProductRead.model_rebuild()
    # products_product_schemas.LotImageRead.model_rebuild()
    # products_product_schemas.AuctionLotRead.model_rebuild()
    # products_product_schemas.AuctionLotTranslationRead.model_rebuild()

    # products_attribute_schemas.AttributeRead.model_rebuild()
    # products_attribute_schemas.AttributeTranslationRead.model_rebuild()
    # products_attribute_schemas.AttributeValueRead.model_rebuild()
    # products_attribute_schemas.AttributeValueTranslationRead.model_rebuild()
    # products_attribute_schemas.ProductVarietyAttributeRead.model_rebuild()

    # products_category_schemas.ProductCategoryRead.model_rebuild()
    # products_category_schemas.ProductCategoryTranslationRead.model_rebuild()

    # products_units_schemas.UnitOfMeasureRead.model_rebuild()
    # products_units_schemas.UnitOfMeasureTranslationRead.model_rebuild()
    # products_packaging_schemas.ProductPackagingOptionRead.model_rebuild()
    # products_packaging_schemas.ProductPackagingOptionTranslationRead.model_rebuild()
    # products_inventory_schemas.InventoryItemRead.model_rebuild()
    # products_inventory_schemas.InventoryTransactionRead.model_rebuild()
    # products_future_offerings_schemas.ExpectedCropRead.model_rebuild()
    # products_pricing_schemas.PriceTierRuleRead.model_rebuild()
    # products_pricing_schemas.PriceTierRuleLevelRead.model_rebuild()
    # products_pricing_schemas.ProductPackagingPriceTierRuleAssignmentRead.model_rebuild()


    # # المجموعة 3 (التسعير)
    # pricing_pricing_schemas.PriceTierRuleRead.model_rebuild()
    # pricing_pricing_schemas.PriceTierRuleTranslationRead.model_rebuild()
    # pricing_pricing_schemas.PriceTierRuleLevelRead.model_rebuild()
    # pricing_pricing_schemas.ProductPackagingPriceTierRuleAssignmentRead.model_rebuild()


    # # المجموعة 4 (عمليات السوق) - تعتمد على UserRead, ProductRead, Lookups
    # market_order_schemas.OrderRead.model_rebuild()
    # market_order_schemas.OrderItemRead.model_rebuild()
    # market_order_schemas.OrderStatusHistoryRead.model_rebuild()
    # market_rfq_schemas.RfqRead.model_rebuild()
    # market_rfq_schemas.RfqItemRead.model_rebuild()
    # market_quote_schemas.QuoteRead.model_rebuild()
    # market_quote_schemas.QuoteItemRead.model_rebuild()
    # market_shipment_schemas.ShipmentRead.model_rebuild()
    # market_shipment_schemas.ShipmentItemRead.model_rebuild()


    # # المجموعة 5 (المزادات) - تعتمد على UserRead, ProductRead, Lookups, Market Schemas
    # auctions_auction_schemas.AuctionRead.model_rebuild()
    # auctions_auction_schemas.AuctionLotRead.model_rebuild()
    # auctions_auction_schemas.AuctionLotTranslationRead.model_rebuild()
    # auctions_auction_schemas.LotProductRead.model_rebuild()
    # auctions_auction_schemas.LotImageRead.model_rebuild()

    # auctions_bidding_schemas.AuctionParticipantRead.model_rebuild()
    # auctions_bidding_schemas.BidRead.model_rebuild()
    # auctions_bidding_schemas.AutoBidSettingRead.model_rebuild()
    # auctions_bidding_schemas.AuctionWatchlistRead.model_rebuild()

    # auctions_settlement_schemas.AuctionSettlementRead.model_rebuild()
    # auctions_settlement_schemas.AuctionSettlementStatusRead.model_rebuild()
    # auctions_settlement_schemas.AuctionSettlementStatusTranslationRead.model_rebuild()


    # # المجموعة 8 (المحفظة والمدفوعات - Finance) - TODO: تأكد من هذه المسارات والأسماء عند بناء المجموعة
    # # if 'finance_wallets_schemas' in globals() and hasattr(finance_wallets_schemas, 'WalletRead'):
    # #     finance_wallets_schemas.WalletRead.model_rebuild()
    # # if 'finance_operations_schemas' in globals() and hasattr(finance_operations_schemas, 'PaymentRecordRead'):
    # #     finance_operations_schemas.PaymentRecordRead.model_rebuild()
    # # if 'finance_commissions_schemas' in globals() and hasattr(finance_commissions_schemas, 'PlatformCommissionRead'):
    # #     finance_commissions_schemas.PlatformCommissionRead.model_rebuild()


    # # المجموعة 9 (اتفاقيات الدفع الآجل - Agreements) - TODO: تأكد من هذه المسارات والأسماء عند بناء المجموعة
    # # if 'agreements_deferred_payment_models' in globals() and hasattr(agreements_deferred_payment_models, 'DeferredPaymentAgreementRead'):
    # #     agreements_deferred_payment_models.DeferredPaymentAgreementRead.model_rebuild()


    # # المجموعة 10 (الضمان الذهبي - Guarantees) - TODO: تأكد من هذه المسارات والأسماء عند بناء المجموعة
    # # if 'guarantees_claims_schemas' in globals() and hasattr(guarantees_claims_schemas, 'GGClaimRead'):
    # #     guarantees_claims_schemas.GGClaimRead.model_rebuild()


    # # المجموعة 11 (الإشعارات والاتصالات - Communications) - TODO: تأكد من هذه المسارات والأسماء عند بناء المجموعة
    # # if 'communications_notifications_schemas' in globals() and hasattr(communications_notifications_schemas, 'NotificationRead'):
    # #     communications_notifications_schemas.NotificationRead.model_rebuild()

    # # =====================================================================
    # # 4. إعادة بناء UserRead أخيراً (بعد أن تكون جميع تبعياته قد تم بناؤها)
    # # =====================================================================
    # users_core_schemas.UserRead.model_rebuild()


    print("Pydantic schemas rebuilt successfully!")