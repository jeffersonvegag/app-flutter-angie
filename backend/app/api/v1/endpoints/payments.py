from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.payment import (
    get_payment, get_payments, get_payments_by_project, get_payments_by_user,
    create_payment, update_payment_status
)
from app.models.user import User
from app.models.payment import PaymentStatus
from app.schemas.payment import Payment, PaymentCreate

router = APIRouter()

@router.get("/", response_model=List[Payment])
def read_payments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve payments.
    """
    payments = get_payments(db, skip=skip, limit=limit)
    return payments

@router.get("/received", response_model=List[Payment])
def read_received_payments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve payments received by the current user.
    """
    payments = get_payments_by_user(db, user_id=current_user.id, as_receiver=True)
    return payments

@router.get("/sent", response_model=List[Payment])
def read_sent_payments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve payments sent by the current user.
    """
    payments = get_payments_by_user(db, user_id=current_user.id, as_receiver=False)
    return payments

@router.get("/project/{project_id}", response_model=List[Payment])
def read_project_payments(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve payments for a specific project.
    """
    payments = get_payments_by_project(db, project_id=project_id)
    return payments

@router.post("/", response_model=Payment)
def create_payment_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    payment_in: PaymentCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new payment.
    """
    payment = create_payment(db=db, payment=payment_in, payer_id=current_user.id)
    return payment

@router.get("/{payment_id}", response_model=Payment)
def read_payment(
    payment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get payment by ID.
    """
    payment = get_payment(db=db, payment_id=payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.post("/{payment_id}/complete", response_model=Payment)
def complete_payment(
    payment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Mark a payment as completed.
    """
    payment = get_payment(db=db, payment_id=payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")