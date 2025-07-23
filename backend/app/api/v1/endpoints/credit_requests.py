# app/api/v1/endpoints/credit_requests.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.credit_request import (
    get_credit_requests_by_user, get_all_credit_requests, get_pending_credit_requests,
    create_credit_request, approve_credit_request, reject_credit_request,
    delete_credit_request, get_credit_request
)
from app.models.models import User
from app.schemas.credit_request import CreditRequest, CreditRequestCreate, CreditRequestDetail

router = APIRouter()

@router.post("/", response_model=CreditRequest)
def create_credit_request_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    credit_request_in: CreditRequestCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new credit request (client only).
    """
    if not current_user.is_client:
        raise HTTPException(status_code=400, detail="Only clients can request credits")
    
    if credit_request_in.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    if credit_request_in.amount > 10000:  # Límite máximo
        raise HTTPException(status_code=400, detail="Maximum credit request is $10,000")
    
    try:
        credit_request = create_credit_request(
            db=db, 
            credit_request=credit_request_in, 
            user_id=current_user.id
        )
        return credit_request
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating credit request: {str(e)}")

@router.get("/my-requests", response_model=List[CreditRequest])
def get_my_credit_requests(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's credit requests.
    """
    if not current_user.is_client:
        raise HTTPException(status_code=400, detail="Only clients can view credit requests")
    
    return get_credit_requests_by_user(db=db, user_id=current_user.id)

@router.delete("/{request_id}")
def delete_my_credit_request(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a pending credit request (user can only delete their own).
    """
    credit_request = get_credit_request(db=db, request_id=request_id)
    if not credit_request:
        raise HTTPException(status_code=404, detail="Credit request not found")
    
    if credit_request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = delete_credit_request(db=db, request_id=request_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete non-pending credit request")
    
    return {"message": "Credit request deleted successfully"}

# === ADMIN ENDPOINTS ===

@router.get("/admin/all", response_model=List[CreditRequestDetail])
def get_all_credit_requests_admin(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get all credit requests (admin only).
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return get_all_credit_requests(db=db, skip=skip, limit=limit)

@router.get("/admin/pending", response_model=List[CreditRequestDetail])
def get_pending_credit_requests_admin(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get pending credit requests (admin only).
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return get_pending_credit_requests(db=db, skip=skip, limit=limit)

@router.post("/{request_id}/approve")
def approve_credit_request_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Approve a credit request (admin only).
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        credit_request = approve_credit_request(
            db=db, 
            request_id=request_id, 
            admin_id=current_user.id
        )
        
        if not credit_request:
            raise HTTPException(status_code=404, detail="Credit request not found")
        
        return {
            "message": "Credit request approved successfully",
            "request_id": request_id,
            "amount": credit_request.amount,
            "user_id": credit_request.user_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving credit request: {str(e)}")

@router.post("/{request_id}/reject")
def reject_credit_request_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    rejection_reason: str = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Reject a credit request (admin only).
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        credit_request = reject_credit_request(
            db=db, 
            request_id=request_id, 
            admin_id=current_user.id,
            rejection_reason=rejection_reason
        )
        
        if not credit_request:
            raise HTTPException(status_code=404, detail="Credit request not found")
        
        return {
            "message": "Credit request rejected successfully",
            "request_id": request_id,
            "rejection_reason": rejection_reason
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rejecting credit request: {str(e)}")
