# backend\src\api\exception_handlers.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from datetime import datetime, timezone

# Optional: يمكنك استيراد الاستثناءات المخصصة هنا إذا أردت استخدامها لـ Type Hinting
# أو لإضافة منطق خاص بها في المستقبل، ولكن معالج HTTPException العام سيلتقطها
# from src.exceptions import NotFoundException, ConflictException, BadRequestException, ForbiddenException

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    معالج استثناءات عام لجميع استثناءات HTTPException (بما في ذلك الاستثناءات المخصصة).
    يوفر استجابة خطأ JSON موحدة.
    """
    error_response = {
        "message": exc.detail,
        "status_code": exc.status_code,
        "error_type": exc.__class__.__name__, # يعرض اسم الكلاس الخاص بالاستثناء (مثل "NotFoundException")
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=exc.headers # تضمين الهيدرات الأصلية لـ HTTPException (مثل WWW-Authenticate لـ 401)
    )

# ملاحظة: يمكنك إضافة معالجات استثناءات أخرى هنا إذا كنت بحاجة إلى معالجة أنواع مختلفة من الأخطاء
# بطرق مختلفة، على سبيل المثال:
# from fastapi.exceptions import RequestValidationError
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content={"message": "Validation error", "errors": exc.errors()},
#     )