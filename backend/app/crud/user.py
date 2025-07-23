# app/crud/user.py
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.models import User, Skill
from app.schemas.user import UserCreate, UserUpdate

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, *, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, *, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()

def get_freelancers(db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).filter(User.is_freelancer == True).offset(skip).limit(limit).all()

def create_user(db: Session, *, user: UserCreate) -> User:
    # Crear usuario
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        is_freelancer=user.is_freelancer,
        is_client=user.is_client,
        is_admin=user.is_admin,
        experience_years=user.experience_years,
        hourly_rate=user.hourly_rate,
        area_expertise=user.area_expertise,
        credits_balance=0.0
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Agregar habilidades si las hay
    if user.skills:
        for skill_name in user.skills:
            # Buscar o crear la habilidad
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.add(skill)
                db.commit()
                db.refresh(skill)
            
            # Asociar habilidad al usuario
            if skill not in db_user.skills:
                db_user.skills.append(skill)
        
        db.commit()
        db.refresh(db_user)
    
    return db_user

def get_user_with_skills(db: Session, user_id: int) -> Optional[dict]:
    """Obtener usuario con skills formateadas para la respuesta de la API"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_freelancer": user.is_freelancer,
        "is_client": user.is_client,
        "is_admin": user.is_admin,
        "experience_years": user.experience_years,
        "hourly_rate": user.hourly_rate,
        "rating": user.rating,
        "area_expertise": user.area_expertise,
        "credits_balance": user.credits_balance,
        "skills": [skill.name for skill in user.skills] if user.skills else []
    }

def update_user(db: Session, *, db_user: User, user_in: UserUpdate) -> User:
    update_data = user_in.dict(exclude_unset=True)
    
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user