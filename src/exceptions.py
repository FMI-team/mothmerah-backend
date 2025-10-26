# backend\src\exceptions.py

from fastapi import HTTPException, status

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found."):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ConflictException(HTTPException):
    def __init__(self, detail: str = "Resource conflict. It may already exist or cannot be modified due to its current state."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request. The request could not be understood or was invalid."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Forbidden. You do not have permission to perform this action."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

# ملاحظة:
# Unauthorized (401) يتم التعامل معها عادة بواسطة FastAPI dependencies (مثل OAuth2PasswordBearer)
# عندما لا يتم توفير التوكن أو يكون غير صالح، لذا لا نحتاج لتعريفها كاستثناء مخصص هنا عادةً.