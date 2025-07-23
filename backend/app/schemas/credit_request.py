# app/schemas/credit_request.py
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class CreditRequestBase(BaseModel):
    amount: float
    description: Optional[str] = None

class CreditRequestCreate(CreditRequestBase):
    pass

class CreditRequestUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None

class CreditRequest(CreditRequestBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    class Config:
        orm_mode = True

class CreditRequestDetail(CreditRequest):
    # Información del usuario que solicita
    user_username: str
    user_full_name: Optional[str] = None
    user_email: str
    user_credits_balance: float
    
    # Información del admin que revisó (si aplica)
    reviewer_username: Optional[str] = None
    reviewer_full_name: Optional[str] = None
    
    class Config:
        orm_mode = True
