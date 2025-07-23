# app/api/v1/endpoints/auth.py
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.crud.user import get_user_by_email, get_user_by_username, create_user, get_user_with_skills
from app.models.models import User
from app.schemas.user import UserCreate, User as UserSchema
from app.schemas.token import Token

router = APIRouter()

@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserSchema)
def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    # Verificar si el email ya existe
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un usuario con este email"
        )
    
    # Verificar si el username ya existe
    user = get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un usuario con este username"
        )
    
    # Si se intenta crear un admin, verificar que no exista otro
    if user_in.is_admin:
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        if existing_admin:
            raise HTTPException(
                status_code=400,
                detail="Ya existe un usuario administrador en el sistema"
            )
    
    # Crear el usuario
    db_user = create_user(db, user=user_in)
    
    # Retornar el usuario en formato API
    user_response = get_user_with_skills(db, db_user.id)
    return user_response

@router.get("/admin-exists")
def check_admin_exists(
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Verificar si ya existe un usuario administrador en el sistema
    """
    try:
        # Buscar si existe algún usuario con is_admin = True
        admin_user = db.query(User).filter(User.is_admin == True).first()
        
        return {
            "admin_exists": admin_user is not None,
            "message": "Admin exists" if admin_user else "No admin found"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking admin existence: {str(e)}"
        )

@router.post("/make-first-admin")
def make_first_admin(
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Convertir al primer usuario en administrador si no existe ningún admin
    """
    try:
        # Verificar si ya existe un admin
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        if existing_admin:
            return {
                "message": "Ya existe un administrador",
                "admin_username": existing_admin.username
            }
        
        # Obtener el primer usuario creado (ID más bajo)
        first_user = db.query(User).order_by(User.id.asc()).first()
        if not first_user:
            raise HTTPException(status_code=404, detail="No hay usuarios en el sistema")
        
        # Convertir al primer usuario en admin
        first_user.is_admin = True
        db.commit()
        db.refresh(first_user)
        
        return {
            "message": f"Usuario '{first_user.username}' convertido en administrador",
            "admin_username": first_user.username,
            "admin_id": first_user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error making first admin: {str(e)}"
        )