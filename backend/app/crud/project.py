# app/crud/project.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Project, ProjectStatus, Skill
from app.schemas.project import ProjectCreate, ProjectUpdate

def get_project(db: Session, project_id: int) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    return db.query(Project).offset(skip).limit(limit).all()

def get_projects_by_client(db: Session, client_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
    return db.query(Project).filter(Project.client_id == client_id).offset(skip).limit(limit).all()

def get_projects_by_freelancer(db: Session, freelancer_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
    """Get all projects assigned to a freelancer (assigned, in_progress, completed)"""
    return db.query(Project).filter(
        Project.freelancer_id == freelancer_id
    ).order_by(
        Project.updated_at.desc()
    ).offset(skip).limit(limit).all()

def get_open_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    return db.query(Project).filter(Project.status == ProjectStatus.OPEN.value).offset(skip).limit(limit).all()

def create_project(db: Session, project: ProjectCreate, client_id: int) -> Project:
    # Crear proyecto
    db_project = Project(
        title=project.title,
        description=project.description,
        client_id=client_id,
        budget=project.budget,
        deadline=project.deadline,
        area=project.area,
        status=ProjectStatus.OPEN.value
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Agregar habilidades requeridas si las hay
    if project.skills_required:
        for skill_name in project.skills_required:
            # Buscar o crear la habilidad
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.add(skill)
                db.commit()
                db.refresh(skill)
            
            # Asociar habilidad al proyecto
            if skill not in db_project.skills_required:
                db_project.skills_required.append(skill)
        
        db.commit()
        db.refresh(db_project)
    
    return db_project

def update_project(db: Session, project_id: int, project_data: ProjectUpdate) -> Optional[Project]:
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        return None
    
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def assign_project(db: Session, project_id: int, freelancer_id: int) -> Optional[Project]:
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        return None
    
    db_project.freelancer_id = freelancer_id
    db_project.status = ProjectStatus.ASSIGNED.value
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project