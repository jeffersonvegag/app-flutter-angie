# app/schemas/application.py
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ProjectApplicationBase(BaseModel):
    message: Optional[str] = None

class ProjectApplicationCreate(ProjectApplicationBase):
    pass

class ProjectApplicationUpdate(BaseModel):
    status: Optional[str] = None

class ProjectApplication(ProjectApplicationBase):
    id: int
    project_id: int
    freelancer_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ProjectApplicationDetail(ProjectApplicationBase):
    id: int
    project_id: int
    freelancer_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Datos del freelancer
    freelancer_username: str
    freelancer_email: str
    freelancer_full_name: Optional[str] = None
    freelancer_experience_years: Optional[float] = None
    freelancer_hourly_rate: Optional[float] = None
    freelancer_rating: float = 0.0
    freelancer_area_expertise: Optional[str] = None
    freelancer_skills: list[str] = []
    
    # Datos del proyecto
    project_title: str
    
    class Config:
        orm_mode = True
