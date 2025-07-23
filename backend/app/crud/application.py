# app/crud/application.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import ProjectApplication, ApplicationStatus, User, Project, Skill
from app.schemas.application import ProjectApplicationCreate

def get_application(db: Session, application_id: int) -> Optional[ProjectApplication]:
    return db.query(ProjectApplication).filter(ProjectApplication.id == application_id).first()

def get_applications_by_project(db: Session, project_id: int) -> List[dict]:
    """Get applications with freelancer details"""
    from app.models.models import user_skills
    from sqlalchemy import func
    
    applications = db.query(
        ProjectApplication,
        User.username,
        User.email,
        User.full_name,
        User.experience_years,
        User.hourly_rate,
        User.rating,
        User.area_expertise,
        Project.title
    ).join(
        User, ProjectApplication.freelancer_id == User.id
    ).join(
        Project, ProjectApplication.project_id == Project.id
    ).filter(
        ProjectApplication.project_id == project_id
    ).all()
    
    result = []
    for app, username, email, full_name, exp_years, hourly_rate, rating, area_expertise, project_title in applications:
        # Obtener skills del freelancer
        freelancer_skills = db.query(Skill.name).join(
            user_skills, Skill.id == user_skills.c.skill_id
        ).filter(
            user_skills.c.user_id == app.freelancer_id
        ).all()
        
        skills_list = [skill.name for skill in freelancer_skills]
        
        result.append({
            "id": app.id,
            "project_id": app.project_id,
            "freelancer_id": app.freelancer_id,
            "message": app.message,
            "status": app.status,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
            "freelancer_username": username,
            "freelancer_email": email,
            "freelancer_full_name": full_name,
            "freelancer_experience_years": exp_years,
            "freelancer_hourly_rate": hourly_rate,
            "freelancer_rating": rating,
            "freelancer_area_expertise": area_expertise,
            "freelancer_skills": skills_list,
            "project_title": project_title
        })
    
    return result

def get_applications_by_freelancer(db: Session, freelancer_id: int) -> List[ProjectApplication]:
    return db.query(ProjectApplication).filter(ProjectApplication.freelancer_id == freelancer_id).all()

def get_application_by_project_and_freelancer(db: Session, project_id: int, freelancer_id: int) -> Optional[ProjectApplication]:
    return db.query(ProjectApplication).filter(
        and_(
            ProjectApplication.project_id == project_id,
            ProjectApplication.freelancer_id == freelancer_id
        )
    ).first()

def create_application(db: Session, application: ProjectApplicationCreate, project_id: int, freelancer_id: int) -> ProjectApplication:
    # Verificar si ya existe una aplicación
    existing_application = get_application_by_project_and_freelancer(db, project_id, freelancer_id)
    if existing_application:
        raise ValueError("You have already applied to this project")
    
    db_application = ProjectApplication(
        project_id=project_id,
        freelancer_id=freelancer_id,
        message=application.message,
        status=ApplicationStatus.PENDING.value
    )
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    
    return db_application

def update_application_status(db: Session, application_id: int, status: str) -> Optional[ProjectApplication]:
    db_application = db.query(ProjectApplication).filter(ProjectApplication.id == application_id).first()
    if not db_application:
        return None
    
    db_application.status = status
    db.commit()
    db.refresh(db_application)
    
    return db_application

def delete_application(db: Session, application_id: int) -> bool:
    db_application = db.query(ProjectApplication).filter(ProjectApplication.id == application_id).first()
    if not db_application:
        return False
    
    db.delete(db_application)
    db.commit()
    return True
