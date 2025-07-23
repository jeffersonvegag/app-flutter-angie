# app/crud/transaction.py
from sqlalchemy.orm import Session
from typing import List
from app.models.models import Transaction, User, Project, TransactionType
from app.schemas.transaction import CreditPurchase, WithdrawalRequest

def purchase_credits(db: Session, user_id: int, credit_purchase: CreditPurchase) -> Transaction:
    """Comprar créditos"""
    # Crear transacción
    transaction = Transaction(
        user_id=user_id,
        transaction_type=TransactionType.CREDIT_PURCHASE.value,
        amount=credit_purchase.amount,
        description=credit_purchase.description
    )
    db.add(transaction)
    
    # Actualizar balance del usuario
    user = db.query(User).filter(User.id == user_id).first()
    user.credits_balance += credit_purchase.amount
    
    db.commit()
    db.refresh(transaction)
    return transaction

def hold_credits_for_project(db: Session, project_id: int, amount: float):
    """Retener créditos para un proyecto"""
    project = db.query(Project).filter(Project.id == project_id).first()
    client = db.query(User).filter(User.id == project.client_id).first()
    
    if client.credits_balance < amount:
        raise ValueError("Insufficient credits")
    
    # Restar créditos del cliente y retenerlos en el proyecto
    client.credits_balance -= amount
    project.credits_held = amount
    
    db.commit()

def release_payment(db: Session, project_id: int) -> Transaction:
    """Liberar pago al freelancer cuando el proyecto se completa"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if project.credits_held <= 0:
        raise ValueError("No credits held for this project")
    
    # Transferir créditos al freelancer
    freelancer = db.query(User).filter(User.id == project.freelancer_id).first()
    freelancer.credits_balance += project.credits_held
    
    # Crear transacción de pago
    transaction = Transaction(
        user_id=freelancer.id,
        project_id=project_id,
        transaction_type=TransactionType.PROJECT_PAYMENT.value,
        amount=project.credits_held,
        description=f"Payment for project: {project.title}"
    )
    db.add(transaction)
    
    # Marcar proyecto como pagado y limpiar créditos retenidos
    project.is_paid = True
    project.credits_held = 0.0
    
    db.commit()
    db.refresh(transaction)
    return transaction

def request_withdrawal(db: Session, user_id: int, withdrawal: WithdrawalRequest) -> Transaction:
    """Solicitar retiro de créditos"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if user.credits_balance < withdrawal.amount:
        raise ValueError("Insufficient credits")
    
    # Crear transacción de retiro
    transaction = Transaction(
        user_id=user_id,
        transaction_type=TransactionType.WITHDRAWAL_REQUEST.value,
        amount=-withdrawal.amount,  # Negativo para indicar salida
        description=withdrawal.description
    )
    db.add(transaction)
    
    # Restar del balance (en una implementación real, esto se haría después de procesar el retiro)
    user.credits_balance -= withdrawal.amount
    
    db.commit()
    db.refresh(transaction)
    return transaction

def get_user_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
    """Obtener transacciones del usuario"""
    return db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

def complete_project_payment(db: Session, project_id: int) -> Transaction:
    """Completar pago del proyecto: transferir créditos retenidos al freelancer"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise ValueError("Project not found")
    
    if project.is_paid:
        raise ValueError("Project is already paid")
    
    if project.credits_held <= 0:
        raise ValueError("No credits held for this project")
    
    if not project.freelancer_id:
        raise ValueError("No freelancer assigned to this project")
    
    # Transferir créditos al freelancer
    freelancer = db.query(User).filter(User.id == project.freelancer_id).first()
    if not freelancer:
        raise ValueError("Freelancer not found")
    
    freelancer.credits_balance += project.credits_held
    
    # Crear transacción de pago
    transaction = Transaction(
        user_id=freelancer.id,
        project_id=project_id,
        transaction_type=TransactionType.PROJECT_PAYMENT.value,
        amount=project.credits_held,
        description=f"Payment for project: {project.title}"
    )
    db.add(transaction)
    
    # Marcar proyecto como pagado y limpiar créditos retenidos
    project.is_paid = True
    amount_transferred = project.credits_held
    project.credits_held = 0.0
    
    db.commit()
    db.refresh(transaction)
    
    print(f"✅ Project payment completed: ${amount_transferred} transferred to freelancer {freelancer.username}")
    return transaction

def get_user_balance(db: Session, user_id: int) -> float:
    """Obtener balance de créditos del usuario"""
    user = db.query(User).filter(User.id == user_id).first()
    return user.credits_balance if user else 0.0