from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from fastapi import HTTPException

from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate

def get_payment(db: Session, payment_id: int):
    return db.query(Payment).filter(Payment.id == payment_id).first()

def get_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Payment).offset(skip).limit(limit).all()

def get_payments_by_project(db: Session, project_id: int):
    return db.query(Payment).filter(Payment.project_id == project_id).all()

def get_payments_by_user(db: Session, user_id: int, as_receiver: bool = False):
    if as_receiver:
        return db.query(Payment).filter(Payment.receiver_id == user_id).all()
    else:
        return db.query(Payment).filter(Payment.payer_id == user_id).all()

def create_payment(db: Session, payment: PaymentCreate, payer_id: int):
    db_payment = Payment(
        amount=payment.amount,
        project_id=payment.project_id,
        payer_id=payer_id,
        receiver_id=payment.receiver_id,
        status=PaymentStatus.PENDING
    )
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def update_payment_status(db: Session, payment_id: int, status: PaymentStatus):
    db_payment = get_payment(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    db_payment.status = status
    db_payment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_payment)
    return db_payment