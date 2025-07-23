from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class PaymentBase(BaseModel):
    amount: float
    project_id: int
    
class PaymentCreate(PaymentBase):
    receiver_id: int

class Payment(PaymentBase):
    id: int
    payer_id: int
    receiver_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True