# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_freelancer: bool = False
    is_client: bool = False
    is_admin: bool = False
    experience_years: Optional[float] = None
    hourly_rate: Optional[float] = None
    area_expertise: Optional[str] = None

class UserCreate(UserBase):
    password: str
    skills: Optional[List[str]] = []

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    rating: float
    credits_balance: float
    skills: List[str] = []

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str