from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.users.schemas import security_schemas
from src.users.services import security_service

router = APIRouter()

@router.post("/request")
def request_password_reset_endpoint(request: security_schemas.PasswordResetRequestSchema, db: Session = Depends(get_db)):
    return security_service.request_password_reset(db=db, phone_number=request.phone_number)

@router.post("/confirm")
def confirm_password_reset_endpoint(request: security_schemas.PasswordResetConfirmSchema, db: Session = Depends(get_db)):
    return security_service.confirm_password_reset(db=db, phone_number=request.phone_number, token=request.token, new_password=request.new_password)