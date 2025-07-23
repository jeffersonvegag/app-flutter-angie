# app/schemas/project.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ProjectBase(BaseModel):
    title: str
    description: str
    budget: float
    area: str
    deadline: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    skills_required: Optional[List[str]] = []

class ProjectUpdate(ProjectBase):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    area: Optional[str] = None

class Project(ProjectBase):
    id: int
    client_id: int
    freelancer_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    credits_held: float
    is_paid: bool
    skills_required: List[str] = []

    class Config:
        from_attributes = True

class ProjectDetail(Project):
    client_name: Optional[str] = None
    freelancer_name: Optional[str] = None