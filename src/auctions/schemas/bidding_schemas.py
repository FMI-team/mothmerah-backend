# backend\src\auctions\schemas\bidding_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID # لمعرفات المستخدمين والمزادات

# TODO: تأكد من أن UserRead, AuctionRead, AuctionLotRead موجودة ومستوردة
# من schemas.auction_schemas import AuctionRead, AuctionLotRead
# من schemas.core_schemas import UserRead

# ==========================================================
# --- Schemas للمشاركين في المزاد (Auction Participants) ---
#    (المودلات من backend\src\auctions\models\bidding_models.py)
# ==========================================================
class AuctionParticipantBase(BaseModel):
    """النموذج الأساسي للمشاركين في المزاد."""
    auction_id: UUID = Field(..., description="معرف المزاد.")
    user_id: UUID = Field(..., description="معرف المستخدم المشارك.")
    participation_status: Optional[str] = Field(
        None,
        max_length=50,
        description="حالة المشاركة (مثلاً: 'REGISTERED', 'APPROVED_TO_BID', 'BLOCKED')."
    )
    # TODO: منطق عمل: التأكد من أن المستخدم ليس هو بائع المزاد.
    # TODO: منطق عمل: التحقق من أهلية المستخدم للمشاركة (مثل تعبئة رصيد المحفظة).

class AuctionParticipantCreate(AuctionParticipantBase):
    """نموذج لإنشاء مشارك مزاد جديد."""
    pass

class AuctionParticipantUpdate(BaseModel):
    """نموذج لتحديث مشارك مزاد موجود. يُستخدم لتغيير حالة المشاركة."""
    participation_status: Optional[str] = Field(None, max_length=50)

class AuctionParticipantRead(AuctionParticipantBase):
    """نموذج لقراءة وعرض تفاصيل مشارك المزاد."""
    auction_participant_id: int
    participation_timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات المستخدم (UserRead) ومعلومات المزاد (AuctionRead) بشكل متداخل.
    # auction: AuctionRead
    # user: UserRead

# ==========================================================
# --- Schemas للمزايدات (Bids) ---
#    (المودلات من backend\src\auctions\models\bidding_models.py)
# ==========================================================
class BidBase(BaseModel):
    """النموذج الأساسي للمزايدة."""
    auction_id: UUID = Field(..., description="معرف المزاد الذي تُقدم عليه المزايدة.")
    lot_id: Optional[UUID] = Field(None, description="معرف اللوت إذا كانت المزايدة على لوت محدد.")
    bidder_user_id: UUID = Field(..., description="معرف المستخدم الذي قدم المزايدة.")
    bid_amount_per_unit: float = Field(..., gt=0, description="قيمة المزايدة لكل وحدة من المنتج.")
    is_auto_bid: Optional[bool] = Field(False, description="هل هذه المزايدة أتت من نظام المزايدة الآلية؟")
    # bid_timestamp و bid_status تدار بواسطة النظام.

class BidCreate(BidBase):
    """نموذج لإنشاء مزايدة جديدة."""
    # TODO: منطق عمل: التحقق من أن bid_amount_per_unit أكبر من السعر الحالي للمزاد وأكبر من minimum_bid_increment.
    # TODO: منطق عمل: التحقق من أن المزايد لديه رصيد كافٍ في المحفظة لتغطية المزايدة.
    # TODO: منطق عمل: إذا كانت المزايدة الآلية مفعلة للمزايد، يجب أن يتم التعامل معها في الخدمة.

class BidRead(BidBase):
    """نموذج لقراءة وعرض تفاصيل المزايدة."""
    bid_id: int
    bid_timestamp: datetime
    bid_status: Optional[str] = Field(None, description="حالة المزايدة (مثلاً: 'ACTIVE_HIGHEST', 'OUTBID', 'WINNING_BID').")
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات المزاد (AuctionRead) واللوت (AuctionLotRead) والمزايد (UserRead) بشكل متداخل.
    # auction: AuctionRead
    # lot: AuctionLotRead
    # bidder: UserRead

# ==========================================================
# --- Schemas لإعدادات المزايدة الآلية (Auto Bid Settings) ---
#    (المودلات من backend\src\auctions\models\bidding_models.py)
# ==========================================================
class AutoBidSettingBase(BaseModel):
    """النموذج الأساسي لإعدادات المزايدة الآلية."""
    auction_id: UUID = Field(..., description="معرف المزاد الذي تنطبق عليه الإعدادات.")
    user_id: UUID = Field(..., description="معرف المستخدم الذي قام بتعيين الإعدادات.")
    max_bid_amount_per_unit: float = Field(..., gt=0, description="أقصى مبلغ للمزايدة لكل وحدة يرغب المستخدم في دفعه تلقائيًا.")
    increment_amount: Optional[float] = Field(None, gt=0, description="مقدار الزيادة في المزايدة التلقائية (إذا كان مختلفًا عن الزيادة الدنيا للمزاد).")
    is_active: Optional[bool] = Field(True, description="هل إعداد المزايدة الآلية نشط حاليًا؟")
    # TODO: منطق عمل: التحقق من أن (auction_id, user_id) فريد.
    # TODO: منطق عمل: التأكد من أن max_bid_amount_per_unit أعلى من السعر الحالي للمزاد.

class AutoBidSettingCreate(AutoBidSettingBase):
    """نموذج لإنشاء إعداد مزايدة آلية جديد."""
    pass

class AutoBidSettingUpdate(BaseModel):
    """نموذج لتحديث إعداد مزايدة آلية موجود."""
    max_bid_amount_per_unit: Optional[float] = Field(None, gt=0)
    increment_amount: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = Field(None)

class AutoBidSettingRead(AutoBidSettingBase):
    """نموذج لقراءة وعرض تفاصيل إعداد المزايدة الآلية."""
    auto_bid_setting_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات المزاد (AuctionRead) والمستخدم (UserRead) بشكل متداخل.
    # auction: AuctionRead
    # user: UserRead

# ==========================================================
# --- Schemas لقوائم مراقبة المزادات (Auction Watchlists) ---
#    (المودلات من backend\src\auctions\models\bidding_models.py)
# ==========================================================
class AuctionWatchlistBase(BaseModel):
    """النموذج الأساسي لقائمة مراقبة المزاد."""
    user_id: UUID = Field(..., description="معرف المستخدم الذي يراقب المزاد.")
    auction_id: UUID = Field(..., description="معرف المزاد الذي تتم مراقبته.")

class AuctionWatchlistCreate(AuctionWatchlistBase):
    """نموذج لإنشاء إدخال جديد في قائمة مراقبة المزادات."""
    # TODO: منطق عمل: التحقق من أن (user_id, auction_id) فريد.
    pass

class AuctionWatchlistRead(AuctionWatchlistBase):
    """نموذج لقراءة وعرض تفاصيل إدخال قائمة مراقبة المزاد."""
    watchlist_entry_id: int
    added_timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
    # TODO: يمكن تضمين معلومات المستخدم (UserRead) والمزاد (AuctionRead) بشكل متداخل.
    # user: UserRead
    # auction: AuctionRead
