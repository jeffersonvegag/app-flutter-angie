# app/api/v1/endpoints/transactions.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import transaction as crud_transaction
from app.models.models import User, Project
from app.schemas.transaction import (
    Transaction, CreditPurchase, ProjectPayment, 
    WithdrawalRequest, UserBalance
)

router = APIRouter()

@router.post("/purchase-credits", response_model=Transaction)
def purchase_credits(
    *,
    db: Session = Depends(deps.get_db),
    credit_purchase: CreditPurchase,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Purchase credits.
    """
    if not current_user.is_client:
        raise HTTPException(status_code=400, detail="Only clients can purchase credits")
    
    transaction = crud_transaction.purchase_credits(
        db=db, user_id=current_user.id, credit_purchase=credit_purchase
    )
    return transaction

@router.post("/pay-project", response_model=Transaction)
def pay_project(
    *,
    db: Session = Depends(deps.get_db),
    payment: ProjectPayment,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Complete project payment to freelancer.
    """
    project = db.query(Project).filter(Project.id == payment.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if project.status != "completed":
        raise HTTPException(status_code=400, detail="Project must be completed first")
    
    try:
        transaction = crud_transaction.release_payment(db=db, project_id=payment.project_id)
        return transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/hold-credits/{project_id}")
def hold_credits(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Hold credits for a project when freelancer is assigned.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        crud_transaction.hold_credits_for_project(db=db, project_id=project_id, amount=project.budget)
        return {"message": "Credits held successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/request-withdrawal", response_model=Transaction)
def request_withdrawal(
    *,
    db: Session = Depends(deps.get_db),
    withdrawal: WithdrawalRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Request withdrawal of credits.
    """
    if not current_user.is_freelancer:
        raise HTTPException(status_code=400, detail="Only freelancers can request withdrawals")
    
    try:
        transaction = crud_transaction.request_withdrawal(
            db=db, user_id=current_user.id, withdrawal=withdrawal
        )
        return transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/balance", response_model=UserBalance)
def get_balance(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get user's credit balance and transaction history.
    """
    balance = crud_transaction.get_user_balance(db=db, user_id=current_user.id)
    transactions = crud_transaction.get_user_transactions(db=db, user_id=current_user.id)
    
    return UserBalance(
        credits_balance=balance,
        transactions=transactions
    )

@router.get("/transactions", response_model=List[Transaction])
def get_transactions(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get user's transaction history.
    """
    transactions = crud_transaction.get_user_transactions(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return transactions