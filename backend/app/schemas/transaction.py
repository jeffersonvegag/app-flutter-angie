# app/schemas/transaction.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionBase(BaseModel):
    amount: float
    description: str

class CreditPurchase(TransactionBase):
    pass

class ProjectPayment(BaseModel):
    project_id: int

class WithdrawalRequest(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    user_id: int
    project_id: Optional[int]
    transaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserBalance(BaseModel):
    credits_balance: float
    transactions: list[Transaction]