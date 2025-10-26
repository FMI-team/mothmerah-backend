# backend\src\auctions\schemas\settlement_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID # لمعرفات المستخدمين والمزادات

# استيراد Schemas المطلوبة للعلاقات المتداخلة من ملفات Schemas أخرى
# AuctionSettlementStatusRead تستورد الآن من src.lookups.schemas
from src.lookups.schemas import AuctionSettlementStatusRead # <-- تم التعديل هنا

# TODO: تأكد من أن AuctionRead, BidRead, UserRead موجودة ومستوردة
# from src.auctions.schemas.auction_schemas import AuctionRead
# from src.auctions.schemas.bidding_schemas import BidRead
# from src.users.schemas.core_schemas import UserRead

# ==========================================================
# --- Schemas لحالات تسوية المزاد (Auction Settlement Statuses) ---
#    (هذه Schemas لم تعد موجودة هنا، بل في lookups_schemas.py)

# ==========================================================
# --- Schemas لتسويات المزادات (Auction Settlements) ---
#    (المودلات من backend\src\auctions\models\settlements_models.py)
# ==========================================================
class AuctionSettlementBase(BaseModel):
    """النموذج الأساسي لتسوية المزاد: يوثق النتائج المالية للمزاد."""
    auction_id: UUID = Field(..., description="معرف المزاد الذي تمت تسويته.")
    winning_bid_id: int = Field(..., description="معرف المزايدة الفائزة (Bid ID).")
    winner_user_id: UUID = Field(..., description="معرف المستخدم الفائز بالمزاد.")
    seller_user_id: UUID = Field(..., description="معرف البائع الذي عرض المزاد.")
    final_winning_price_per_unit: float = Field(..., gt=0, description="السعر النهائي الفائز لكل وحدة.")
    quantity_won: float = Field(..., gt=0, description="الكمية التي فاز بها المشتري.")
    total_settlement_amount: float = Field(..., gt=0, description="إجمالي المبلغ المستحق للتسوية (السعر الفائز × الكمية الفائز بها).")
    # platform_commission_id و payment_transaction_id و payout_transaction_id سيتم تعيينها لاحقاً في الخدمة
    net_amount_to_seller: float = Field(..., description="المبلغ الصافي الذي سيتم تسويته للبائع بعد خصم العمولة.")
    settlement_status_id: Optional[int] = Field(None, description="حالة التسوية (مثلاً: 'قيد الدفع', 'تم الدفع').")
    settlement_timestamp: datetime = Field(None, description="تاريخ ووقت إتمام التسوية.") # سيتم تعيينه تلقائياً
    notes: Optional[str] = Field(None, description="ملاحظات إضافية حول التسوية.")

class AuctionSettlementCreate(AuctionSettlementBase):
    """نموذج لإنشاء تسوية مزاد جديدة."""
    pass

class AuctionSettlementUpdate(BaseModel):
    """نموذج لتحديث تسوية مزاد موجودة (يمكن للمسؤول تحديث حالتها أو ملاحظاتها)."""
    # لا يمكن تغيير المعرفات الرئيسية أو المبالغ المالية الأساسية بعد الإنشاء.
    settlement_status_id: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    
class AuctionSettlementRead(AuctionSettlementBase):
    """نموذج لقراءة وعرض تفاصيل تسوية المزاد بشكل كامل."""
    settlement_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات المزاد (AuctionRead), المزايدة الفائزة (BidRead), المستخدمين (UserRead), حالة التسوية (AuctionSettlementStatusRead) بشكل متداخل.
    # auction: AuctionRead
    # winning_bid: BidRead
    # winner_user: UserRead
    # seller_user: UserRead
    settlement_status: AuctionSettlementStatusRead # حالة التسوية
    # TODO: علاقات مع PlatformCommissionRead و WalletTransactionRead
