# app/crud/credit_request.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.models import CreditRequest, CreditRequestStatus, User
from app.schemas.credit_request import CreditRequestCreate, CreditRequestUpdate
from datetime import datetime

def get_credit_request(db: Session, request_id: int) -> Optional[CreditRequest]:
    return db.query(CreditRequest).filter(CreditRequest.id == request_id).first()

def get_credit_requests_by_user(db: Session, user_id: int) -> List[CreditRequest]:
    return db.query(CreditRequest).filter(
        CreditRequest.user_id == user_id
    ).order_by(desc(CreditRequest.created_at)).all()

def get_all_credit_requests(db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
    """Obtener todas las solicitudes con información del usuario"""
    requests = db.query(
        CreditRequest,
        User.username,
        User.full_name,
        User.email,
        User.credits_balance
    ).join(
        User, CreditRequest.user_id == User.id
    ).order_by(
        desc(CreditRequest.created_at)
    ).offset(skip).limit(limit).all()
    
    result = []
    for req, username, full_name, email, credits_balance in requests:
        # Obtener información del reviewer si existe
        reviewer_info = None
        if req.reviewed_by:
            reviewer = db.query(User).filter(User.id == req.reviewed_by).first()
            if reviewer:
                reviewer_info = {
                    "username": reviewer.username,
                    "full_name": reviewer.full_name
                }
        
        result.append({
            "id": req.id,
            "user_id": req.user_id,
            "amount": req.amount,
            "description": req.description,
            "status": req.status,
            "created_at": req.created_at,
            "updated_at": req.updated_at,
            "reviewed_by": req.reviewed_by,
            "reviewed_at": req.reviewed_at,
            "rejection_reason": req.rejection_reason,
            "user_username": username,
            "user_full_name": full_name,
            "user_email": email,
            "user_credits_balance": credits_balance,
            "reviewer_username": reviewer_info["username"] if reviewer_info else None,
            "reviewer_full_name": reviewer_info["full_name"] if reviewer_info else None,
        })
    
    return result

def get_pending_credit_requests(db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
    """Obtener solicitudes pendientes para el admin"""
    requests = db.query(
        CreditRequest,
        User.username,
        User.full_name,
        User.email,
        User.credits_balance
    ).join(
        User, CreditRequest.user_id == User.id
    ).filter(
        CreditRequest.status == CreditRequestStatus.PENDING.value
    ).order_by(
        desc(CreditRequest.created_at)
    ).offset(skip).limit(limit).all()
    
    result = []
    for req, username, full_name, email, credits_balance in requests:
        result.append({
            "id": req.id,
            "user_id": req.user_id,
            "amount": req.amount,
            "description": req.description,
            "status": req.status,
            "created_at": req.created_at,
            "updated_at": req.updated_at,
            "user_username": username,
            "user_full_name": full_name,
            "user_email": email,
            "user_credits_balance": credits_balance,
        })
    
    return result

def create_credit_request(
    db: Session, 
    credit_request: CreditRequestCreate, 
    user_id: int
) -> CreditRequest:
    """Crear una nueva solicitud de créditos"""
    db_request = CreditRequest(
        user_id=user_id,
        amount=credit_request.amount,
        description=credit_request.description,
        status=CreditRequestStatus.PENDING.value
    )
    
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    return db_request

def approve_credit_request(
    db: Session, 
    request_id: int, 
    admin_id: int
) -> Optional[CreditRequest]:
    """Aprobar una solicitud de créditos"""
    credit_request = db.query(CreditRequest).filter(CreditRequest.id == request_id).first()
    if not credit_request:
        return None
    
    if credit_request.status != CreditRequestStatus.PENDING.value:
        raise ValueError("Credit request is not pending")
    
    # Actualizar la solicitud
    credit_request.status = CreditRequestStatus.APPROVED.value
    credit_request.reviewed_by = admin_id
    credit_request.reviewed_at = datetime.utcnow()
    
    # Agregar créditos al usuario
    user = db.query(User).filter(User.id == credit_request.user_id).first()
    if user:
        user.credits_balance += credit_request.amount
    
    db.commit()
    db.refresh(credit_request)
    
    return credit_request

def reject_credit_request(
    db: Session, 
    request_id: int, 
    admin_id: int, 
    rejection_reason: str = None
) -> Optional[CreditRequest]:
    """Rechazar una solicitud de créditos"""
    credit_request = db.query(CreditRequest).filter(CreditRequest.id == request_id).first()
    if not credit_request:
        return None
    
    if credit_request.status != CreditRequestStatus.PENDING.value:
        raise ValueError("Credit request is not pending")
    
    # Actualizar la solicitud
    credit_request.status = CreditRequestStatus.REJECTED.value
    credit_request.reviewed_by = admin_id
    credit_request.reviewed_at = datetime.utcnow()
    credit_request.rejection_reason = rejection_reason
    
    db.commit()
    db.refresh(credit_request)
    
    return credit_request

def delete_credit_request(db: Session, request_id: int) -> bool:
    """Eliminar una solicitud de créditos (solo si está pendiente)"""
    credit_request = db.query(CreditRequest).filter(CreditRequest.id == request_id).first()
    if not credit_request:
        return False
    
    if credit_request.status != CreditRequestStatus.PENDING.value:
        return False
    
    db.delete(credit_request)
    db.commit()
    return True
