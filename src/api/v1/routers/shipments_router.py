# backend\src\api\v1\routers\shipments_router.py

from fastapi import APIRouter, Depends, status, HTTPException # استيراد المكونات الأساسية لـ FastAPI
from sqlalchemy.orm import Session # لاستخدام جلسة قاعدة البيانات
from typing import List, Optional # لتعريف أنواع البيانات في Python
from uuid import UUID # لمعالجة معرفات المستخدمين والطلبات
from datetime import datetime, date # لاستخدام التواريخ

# استيراد المكونات المشتركة للمشروع
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات
from src.api.v1 import dependencies # لتبعية الصلاحيات والمستخدم الحالي
from src.users.models.core_models import User # مودل المستخدم، للتحقق من الصلاحيات

# استيراد Schemas (هياكل البيانات) الخاصة بالشحنات
from src.market.schemas import shipment_schemas as schemas

# استيراد الخدمات (منطق العمل) المتعلقة بالشحنات
from src.market.services import shipments_service
from src.lookups.schemas import lookups_schemas 

# تعريف الراوتر الرئيسي لوحدة إدارة الشحنات.
# هذا الراوتر سيتعامل مع نقاط الوصول المتعلقة بالشحنات للبائعين والمشترين.
router = APIRouter(
    prefix="/shipments", # المسار الأساسي لجميع نقاط الوصول في هذا الراوتر (مثال: /api/v1/shipments)
    tags=["Market - Shipments Management"] # الوسوم التي تظهر في وثائق OpenAPI (Swagger UI)
)

# ================================================================
# --- نقاط الوصول للشحنات (Shipment) ---
#    (تتطلب صلاحيات لإنشاء وتتبع وتحديث الشحن)
# ================================================================

@router.post(
    "/",
    response_model=schemas.ShipmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Seller/Admin] إنشاء سجل شحنة جديد",
    description="""
    يسمح للبائع أو المسؤول بإنشاء سجل جديد لشحنة مرتبطة بطلب معين.
    يتضمن تفاصيل شركة الشحن، رقم التتبع، وتفاصيل بنود الشحنة.
    يتطلب صلاحية 'SHIPMENT_CREATE_OWN' (للبائع) أو 'ADMIN_ORDER_MANAGE_ANY' (للمسؤول).
    """,
)
async def create_new_shipment_endpoint(
    shipment_in: schemas.ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("SHIPMENT_CREATE_OWN"))
):
    """نقطة وصول لإنشاء سجل شحنة جديد."""
    return shipments_service.create_new_shipment(db=db, shipment_in=shipment_in, current_user=current_user)

@router.get(
    "/for-order/{order_id}",
    response_model=List[schemas.ShipmentRead],
    summary="[Buyer/Seller/Admin] جلب شحنات طلب معين",
    description="""
    يجلب قائمة بجميع الشحنات المتعلقة بطلب معين.
    يتطلب صلاحية 'ORDER_VIEW_OWN' (للمشتري/البائع) أو 'ADMIN_ORDER_VIEW_ANY' (للمسؤول).
    """,
)
async def get_shipments_for_order_endpoint(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_VIEW_OWN")),
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب جميع الشحنات لطلب معين."""
    return shipments_service.get_all_shipments_for_order(db=db, order_id=order_id, current_user=current_user, skip=skip, limit=limit)

@router.get(
    "/me",
    response_model=List[schemas.ShipmentRead],
    summary="[Buyer/Seller] جلب شحناتي",
    description="""
    يجلب قائمة بجميع الشحنات التي تخص المستخدم الحالي، سواء كان هو المشتري للطلب أو البائع الذي قام بالشحن.
    يتطلب صلاحية 'ORDER_VIEW_OWN' (للمشتري/البائع).
    """,
)
async def get_my_shipments_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_VIEW_OWN")),
    skip: int = 0,
    limit: int = 100
):
    """نقطة وصول لجلب جميع الشحنات الخاصة بالمستخدم الحالي."""
    return shipments_service.get_my_shipments(db=db, current_user=current_user, skip=skip, limit=limit)

@router.get(
    "/{shipment_id}",
    response_model=schemas.ShipmentRead,
    summary="[Buyer/Seller/Admin] جلب تفاصيل شحنة واحدة",
    description="""
    يجلب التفاصيل الكاملة لشحنة محددة بالـ ID الخاص بها.
    يتطلب صلاحية 'ORDER_VIEW_OWN' (للمشتري/البائع) أو صلاحية إدارية.
    """,
)
async def get_shipment_details_endpoint(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_VIEW_OWN"))
):
    """نقطة وصول لجلب تفاصيل شحنة محددة."""
    return shipments_service.get_shipment_details(db=db, shipment_id=shipment_id, current_user=current_user)

@router.patch(
    "/{shipment_id}",
    response_model=schemas.ShipmentRead,
    summary="[Seller/Admin] تحديث شحنة",
    description="""
    يسمح للبائع أو المسؤول بتحديث تفاصيل شحنة موجودة (مثل رقم التتبع، تواريخ الشحن/التسليم).
    يتطلب صلاحية 'ORDER_UPDATE_OWN_STATUS' (للبائع) أو صلاحية إدارية.
    """,
)
async def update_shipment_endpoint(
    shipment_id: int,
    shipment_in: schemas.ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_UPDATE_OWN_STATUS")) # TODO: صلاحية SHIPMENT_UPDATE_OWN
):
    """نقطة وصول لتحديث شحنة محددة."""
    return shipments_service.update_shipment(db=db, shipment_id=shipment_id, shipment_in=shipment_in, current_user=current_user)

@router.patch(
    "/{shipment_id}/status",
    response_model=schemas.ShipmentRead,
    summary="[Seller/Admin] تحديث حالة الشحنة",
    description="""
    يسمح للبائع أو المسؤول بتحديث حالة شحنة محددة مباشرة (مثلاً إلى 'تم الشحن', 'تم التسليم').
    يتطلب صلاحية 'ORDER_UPDATE_OWN_STATUS' (للبائع) أو صلاحية إدارية.
    """,
)
async def update_shipment_status_endpoint(
    shipment_id: int,
    status_update: schemas.ShipmentUpdate, # يمكن أن تحتوي على shipment_status_id فقط
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_UPDATE_OWN_STATUS")) # TODO: صلاحية SHIPMENT_UPDATE_OWN
):
    """نقطة وصول لتحديث حالة شحنة محددة."""
    if status_update.shipment_status_id is None:
        raise BadRequestException(detail="يجب توفير معرف الحالة الجديدة (shipment_status_id).")
    return shipments_service.update_shipment_status(db=db, shipment_id=shipment_id, new_status_id=status_update.shipment_status_id, current_user=current_user)


@router.delete(
    "/{shipment_id}",
    response_model=schemas.ShipmentRead, # ترجع الكائن بعد تحديث حالته إلى "ملغى"
    summary="[Seller/Admin] إلغاء شحنة",
    description="""
    يسمح للبائع أو المسؤول بإلغاء شحنة معينة (يعادل الحذف الناعم) عن طريق تغيير حالتها إلى "ملغاة".
    يتم التحقق من صلاحيات المستخدم ومرحلة الشحنة قبل الإلغاء.
    يتطلب صلاحية 'ORDER_UPDATE_OWN_STATUS' (للبائع) أو صلاحية إدارية.
    """,
)
async def cancel_shipment_endpoint(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.has_permission("ORDER_UPDATE_OWN_STATUS")) # TODO: صلاحية SHIPMENT_CANCEL_OWN
):
    """نقطة وصول لإلغاء (حذف ناعم) شحنة محددة."""
    return shipments_service.cancel_shipment(db=db, shipment_id=shipment_id, current_user=current_user)


# ================================================================
# --- نقاط الوصول لحالات الشحن (ShipmentStatus) ---
#    (هذه عادةً ما تُدار بواسطة المسؤولين، ولكن يمكن تضمين نقاط وصول عرض هنا)
# ================================================================

@router.get(
    "/statuses",
    response_model=List[lookups_schemas.ShipmentStatusRead],
    summary="[Public] جلب جميع حالات الشحن",
    description="""
    يجلب قائمة بجميع الحالات المرجعية للشحن في النظام.
    متاح للعامة لغرض العرض.
    """,
)
async def get_all_shipment_statuses_endpoint(db: Session = Depends(get_db)):
    """نقطة وصول لجلب جميع حالات الشحن."""
    return shipments_service.get_all_shipment_statuses_service(db=db)

# TODO: نقاط وصول إدارة حالات الشحن (POST, PATCH, DELETE) ستكون في product_admin_router.py

# ================================================================
# --- نقاط الوصول لترجمات حالات الشحن (ShipmentStatusTranslation) ---
# ================================================================

@router.get(
    "/statuses/{shipment_status_id}/translations/{language_code}",
    response_model=lookups_schemas.ShipmentStatusTranslationRead,
    summary="[Public] جلب ترجمة محددة لحالة شحن",
    description="""
    يجلب ترجمة محددة لحالة شحن بلغة معينة.
    متاح للعامة لغرض العرض.
    """,
)
async def get_shipment_status_translation_details_endpoint(
    shipment_status_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """نقطة وصول لجلب ترجمة محددة لحالة شحن."""
    return shipments_service.get_shipment_status_translation_details_service(db=db, shipment_status_id=shipment_status_id, language_code=language_code)

# TODO: نقاط وصول إدارة ترجمات حالات الشحن (POST, PATCH, DELETE) ستكون في product_admin_router.py