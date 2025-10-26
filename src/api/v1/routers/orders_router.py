# backend\src\api\v1\routers\orders_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين والطلبات

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User # مودل المستخدم، للتحقق من الصلاحيات

# استيراد Schemas (هياكل البيانات) الخاصة بالطلبات
from src.market.schemas import order_schemas as schemas

# استيراد الخدمات (منطق العمل) المتعلقة بالطلبات
from src.market.services import orders_service

# تعريف الراوتر الرئيسي لوحدة إدارة الطلبات.
# هذا الراوتر سيتعامل مع نقاط الوصول المتعلقة بالطلبات المباشرة للمشترين والبائعين.
router = APIRouter(
    prefix="/orders", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/orders)
    tags=["Market - Orders Management"] # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
)

# ================================================================
# --- نقاط الوصول للطلبات (Order) ---
#    (تتطلب صلاحية ORDER_CREATE_DIRECT للمشتري، وصلاحيات VIEW/UPDATE_OWN للمشترين والبائعين)
# ================================================================

@router.post(
    "/",
    response_model=schemas.OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Buyer] إنشاء طلب شراء مباشر جديد",
    description="""
    يسمح للمشتري بإنشاء طلب شراء مباشر جديد من المنتجات المعروضة.
    تتضمن العملية التحقق من المخزون وحساب الأسعار وتعيين الحالة الأولية.
    يتطلب صلاحية 'ORDER_CREATE_DIRECT'.
    """,
)
async def create_new_order_endpoint(
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_CREATE_DIRECT"))
):
    """نقطة وصول لإنشاء طلب شراء مباشر جديد."""
    return orders_service.create_new_order(db=db, order_in=order_in, current_user=current_user)

@router.get(
    "/me",
    response_model=List[schemas.OrderRead],
    summary="[Buyer/Seller] جلب جميع طلباتي (كمشتري أو بائع)",
    description="""
    يجلب قائمة بجميع الطلبات التي يكون المستخدم الحالي طرفًا فيها، سواء كمشترٍ (أنشأ الطلب) أو كبائع (لبنود داخل الطلب).
    يتطلب صلاحية 'ORDER_VIEW_OWN'.
    """,
)
async def get_my_orders_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_VIEW_OWN")),
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب جميع الطلبات الخاصة بالمستخدم الحالي."""
    return orders_service.get_my_orders(db=db, current_user=current_user, skip=skip, limit=limit)

@router.get(
    "/{order_id}",
    response_model=schemas.OrderRead,
    summary="[Buyer/Seller] جلب تفاصيل طلب واحد",
    description="""
    يجلب التفاصيل الكاملة لطلب محدد بالـ ID الخاص به.
    يتطلب صلاحية 'ORDER_VIEW_OWN' ويتم التحقق من أن المستخدم هو المشتري أو البائع لأحد بنود الطلب أو مسؤول.
    """,
)
async def get_order_details_endpoint(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_VIEW_OWN"))
):
    """نقطة وصول لجلب تفاصيل طلب محدد."""
    return orders_service.get_order_details(db=db, order_id=order_id, current_user=current_user)

@router.patch(
    "/{order_id}",
    response_model=schemas.OrderRead,
    summary="[Seller/Admin] تحديث طلب",
    description="""
    يسمح للبائع أو المسؤول بتحديث تفاصيل طلب موجود (مثل تحديث حالة الطلب أو الملاحظات).
    يتطلب صلاحية 'ORDER_UPDATE_OWN_STATUS' للبائع أو صلاحية إدارية عامة.
    """,
)
async def update_order_endpoint(
    order_id: UUID,
    order_in: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_UPDATE_OWN_STATUS"))
):
    """نقطة وصول لتحديث طلب محدد."""
    return orders_service.update_order(db=db, order_id=order_id, order_in=order_in, current_user=current_user)

@router.patch(
    "/{order_id}/status",
    response_model=schemas.OrderRead,
    summary="[Seller/Admin] تحديث حالة الطلب",
    description="""
    يسمح للبائع أو المسؤول بتحديث حالة طلب محدد مباشرة.
    يتطلب صلاحية 'ORDER_UPDATE_OWN_STATUS' للبائع أو صلاحية إدارية عامة.
    يُفضل استخدام هذا لعمليات تغيير الحالة المباشرة.
    """,
)
async def update_order_status_endpoint(
    order_id: UUID,
    status_update: schemas.OrderUpdate, # يمكن أن تحتوي على order_status_id فقط
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_UPDATE_OWN_STATUS"))
):
    """نقطة وصول لتحديث حالة طلب محدد."""
    if status_update.order_status_id is None:
        raise BadRequestException(detail="يجب توفير معرف الحالة الجديدة (order_status_id).")
    return orders_service.update_order_status(db=db, order_id=order_id, new_status_id=status_update.order_status_id, current_user=current_user)


@router.delete(
    "/{order_id}",
    response_model=schemas.OrderRead, # ترجع الكائن بعد تحديث حالته إلى "ملغى"
    summary="[Buyer/Seller/Admin] إلغاء طلب",
    description="""
    يسمح للمشتري أو البائع أو المسؤول بإلغاء طلب معين (يعادل الحذف الناعم).
    يتم التحقق من صلاحيات المستخدم ومرحلة الطلب قبل الإلغاء.
    تؤدي العملية إلى تحديث حالة الطلب، عكس حجوزات المخزون، وبدء استرداد المدفوعات.
    يتطلب صلاحية 'ORDER_CANCEL_OWN'.
    """,
)
async def cancel_order_endpoint(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_CANCEL_OWN")),
    reason: Optional[str] = None # سبب الإلغاء
):
    """نقطة وصول لإلغاء (حذف ناعم) طلب محدد."""
    return orders_service.cancel_order(db=db, order_id=order_id, current_user=current_user, reason=reason)