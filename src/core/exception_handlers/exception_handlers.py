# backend\src\core\exception_handlers\exception_handlers.py

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Union, Dict, Any

# معالج استثناءات HTTP العام
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    معالج استثناءات FastAPI الافتراضي HTTPExceptions.
    يعيد استجابة JSON موحدة للأخطاء.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# معالج استثناءات التحقق من صحة Pydantic
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    معالج استثناءات Pydantic ValidationError.
    يعيد تفاصيل أخطاء التحقق من الصحة بشكل منظم.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "خطأ في التحقق من صحة البيانات المدخلة.", "errors": exc.errors()},
    )

# معالج استثناءات عام للمشروع (يمكن توسيعه لاحقًا)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    معالج عام لأي استثناءات غير متوقعة.
    """
    # TODO: يمكن إضافة تسجيل للخطأ هنا لأغراض المراقبة (monitoring/logging).
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "حدث خطأ غير متوقع في الخادم."},
    )