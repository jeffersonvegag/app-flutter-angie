from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.project import (
    get_project, get_projects, get_projects_by_client, get_projects_by_freelancer,
    get_open_projects, create_project, update_project, assign_project
)
from app.crud.user import get_freelancers
from app.crud import transaction as crud_transaction
from app.crud.application import (
    create_application, get_applications_by_project, get_application_by_project_and_freelancer
)
from app.ml.recommender import FreelancerRecommender
from app.models.models import User, Project as ProjectModel, ProjectStatus
from app.schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectDetail
from app.schemas.user import User as UserSchema
from app.schemas.application import ProjectApplicationCreate, ProjectApplication, ProjectApplicationDetail

router = APIRouter()

def convert_project_to_dict(project: ProjectModel) -> dict:
    """Helper function to convert SQLAlchemy Project to dict"""
    skills_list = [skill.name for skill in project.skills_required]
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "client_id": project.client_id,
        "freelancer_id": project.freelancer_id,
        "status": project.status,
        "budget": project.budget,
        "deadline": project.deadline,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "area": project.area,
        "credits_held": project.credits_held,
        "is_paid": project.is_paid,
        "skills_required": skills_list
    }

@router.get("/", response_model=List[Project])
def read_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve projects.
    """
    projects = get_projects(db, skip=skip, limit=limit)
    return [convert_project_to_dict(p) for p in projects]

@router.get("/open", response_model=List[Project])
def read_open_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve open projects.
    """
    projects = get_open_projects(db, skip=skip, limit=limit)
    return [convert_project_to_dict(p) for p in projects]

@router.get("/client/in-progress", response_model=List[Project])
def read_client_in_progress_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve projects in progress created by the current user (client).
    """
    if not current_user.is_client:
        raise HTTPException(status_code=400, detail="Not a client")
    
    projects = db.query(ProjectModel).filter(
        ProjectModel.client_id == current_user.id,
        ProjectModel.status.in_(["assigned", "in_progress", "completed"])
    ).order_by(
        ProjectModel.updated_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [convert_project_to_dict(p) for p in projects]

@router.get("/client", response_model=List[Project])
def read_client_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve projects created by the current user (client).
    """
    if not current_user.is_client:
        raise HTTPException(status_code=400, detail="Not a client")
    
    projects = get_projects_by_client(
        db=db, client_id=current_user.id, skip=skip, limit=limit
    )
    return [convert_project_to_dict(p) for p in projects]

@router.get("/freelancer", response_model=List[Project])
def read_freelancer_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve projects assigned to the current user (freelancer).
    """
    if not current_user.is_freelancer:
        raise HTTPException(status_code=400, detail="Not a freelancer")
    
    projects = get_projects_by_freelancer(
        db=db, freelancer_id=current_user.id, skip=skip, limit=limit
    )
    return [convert_project_to_dict(p) for p in projects]

@router.post("/", response_model=Project)
def create_project_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new project.
    """
    if not current_user.is_client:
        raise HTTPException(status_code=400, detail="Not a client")
    
    project = create_project(db=db, project=project_in, client_id=current_user.id)
    return convert_project_to_dict(project)

@router.post("/{project_id}/apply", response_model=ProjectApplication)
def apply_to_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    application_data: ProjectApplicationCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Apply to a project as a freelancer.
    """
    # Verificar que el usuario sea freelancer
    if not current_user.is_freelancer:
        raise HTTPException(status_code=400, detail="Only freelancers can apply to projects")
    
    # Verificar que el proyecto existe
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verificar que el proyecto esté abierto
    if project.status != ProjectStatus.OPEN.value:
        raise HTTPException(status_code=400, detail="Project is not open for applications")
    
    # Verificar que no sea el cliente del proyecto
    if project.client_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot apply to your own project")
    
    # Verificar si ya aplicó anteriormente
    existing_application = get_application_by_project_and_freelancer(
        db=db, project_id=project_id, freelancer_id=current_user.id
    )
    if existing_application:
        # Si ya aplicó, retornar la aplicación existente en lugar de error
        return existing_application
    
    try:
        application = create_application(
            db=db, 
            application=application_data, 
            project_id=project_id, 
            freelancer_id=current_user.id
        )
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}/applications", response_model=List[ProjectApplicationDetail])
def get_project_applications(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get all applications for a project (client only).
    """
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Solo el cliente del proyecto puede ver las aplicaciones
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    applications = get_applications_by_project(db=db, project_id=project_id)
    return applications

@router.delete("/{project_id}/unapply")
def unapply_from_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Remove application from a project (freelancer only).
    """
    # Verificar que el usuario sea freelancer
    if not current_user.is_freelancer:
        raise HTTPException(status_code=400, detail="Only freelancers can unapply from projects")
    
    # Verificar que el proyecto existe
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Buscar la aplicación del freelancer para este proyecto
    application = get_application_by_project_and_freelancer(
        db=db, project_id=project_id, freelancer_id=current_user.id
    )
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Solo se puede desaplicar si la aplicación está pendiente
    if application.status != "pending":
        raise HTTPException(
            status_code=400, 
            detail="Cannot unapply from a project with non-pending application"
        )
    
    # Eliminar la aplicación
    try:
        db.delete(application)
        db.commit()
        
        return {
            "message": "Application removed successfully",
            "project_id": project_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing application: {str(e)}")

@router.get("/{project_id}/my-application", response_model=ProjectApplication)
def get_my_application(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's application for a project (freelancer only).
    """
    if not current_user.is_freelancer:
        raise HTTPException(status_code=400, detail="Only freelancers can check applications")
    
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    application = get_application_by_project_and_freelancer(
        db=db, project_id=project_id, freelancer_id=current_user.id
    )
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application

@router.get("/recommendations/{project_id}", response_model=List[UserSchema])
def get_freelancer_recommendations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get freelancer recommendations for a project.
    """
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Solo el cliente del proyecto puede ver recomendaciones
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Obtener freelancers
        freelancers = get_freelancers(db=db)
        
        # Preparar datos para el recomendador
        project_dict = {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "budget": project.budget,
            "area": project.area,
            "skills_required": [skill.name for skill in project.skills_required]
        }
        
        freelancer_list = []
        for f in freelancers:
            freelancer_list.append({
                "id": f.id,
                "username": f.username,
                "experience_years": f.experience_years,
                "hourly_rate": f.hourly_rate,
                "rating": f.rating,
                "area_expertise": f.area_expertise,
                "skills": [skill.name for skill in f.skills]
            })
        
        # Obtener recomendaciones
        recommender = FreelancerRecommender()
        recommendations = recommender.recommend_freelancers(
            project=project_dict, 
            freelancers=freelancer_list, 
            top_n=5
        )
        
        # Extraer IDs de freelancers recomendados
        recommended_ids = [rec['freelancer']['id'] for rec in recommendations]
        
        # Convertir freelancers a diccionarios compatibles con UserSchema
        result = []
        for f in freelancers:
            if f.id in recommended_ids:
                result.append({
                    "id": f.id,
                    "email": f.email,
                    "username": f.username,
                    "full_name": f.full_name,
                    "is_active": f.is_active,
                    "is_freelancer": f.is_freelancer,
                    "is_client": f.is_client,
                    "experience_years": f.experience_years,
                    "hourly_rate": f.hourly_rate,
                    "rating": f.rating,
                    "area_expertise": f.area_expertise,
                    "credits_balance": f.credits_balance,
                    "skills": [skill.name for skill in f.skills]
                })
        
        # Ordenar por el orden de las recomendaciones
        sorted_result = []
        for rec_id in recommended_ids:
            for freelancer_dict in result:
                if freelancer_dict["id"] == rec_id:
                    sorted_result.append(freelancer_dict)
                    break
        
        return sorted_result
        
    except Exception as e:
        # En caso de error, retornar lista vacía
        print(f"Error in recommendations: {e}")
        return []

@router.get("/{project_id}", response_model=ProjectDetail)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get project by ID.
    """
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=Project)
def update_project_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a project.
    """
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Solo el cliente del proyecto puede actualizarlo
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    project = update_project(db=db, project_id=project_id, project_data=project_in)
    return convert_project_to_dict(project)

@router.delete("/{project_id}")
def delete_project_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a project (only if it's open and belongs to current user).
    """
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Solo el cliente del proyecto puede eliminarlo
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Solo se puede eliminar si está abierto
    if project.status != "open":
        raise HTTPException(status_code=400, detail="Cannot delete project that is not open")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}

@router.post("/{project_id}/assign/{freelancer_id}", response_model=Project)
def assign_project_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    freelancer_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Assign a freelancer to a project and hold credits.
    """
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Solo el cliente del proyecto puede asignar freelancers
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verificar que el cliente tenga suficientes créditos
    try:
        crud_transaction.hold_credits_for_project(db=db, project_id=project_id, amount=project.budget)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    project = assign_project(db=db, project_id=project_id, freelancer_id=freelancer_id)
    return convert_project_to_dict(project)

@router.post("/{project_id}/complete", response_model=Project)
def complete_project_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Mark project as completed and transfer credits to freelancer (client only).
    """
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Solo el cliente del proyecto puede finalizarlo
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the client can complete the project")
    
    # Verificar que el proyecto esté en progreso o asignado
    if project.status not in [ProjectStatus.IN_PROGRESS.value, ProjectStatus.ASSIGNED.value]:
        raise HTTPException(status_code=400, detail="Project must be assigned or in progress to be completed")
    
    # Verificar que tenga un freelancer asignado
    if not project.freelancer_id:
        raise HTTPException(status_code=400, detail="Project must have an assigned freelancer")
    
    try:
        # Transferir créditos del proyecto al freelancer
        crud_transaction.complete_project_payment(db=db, project_id=project_id)
        
        # Actualizar status a completado
        project.status = ProjectStatus.COMPLETED.value
        project.is_paid = True
        db.commit()
        db.refresh(project)
        
        return convert_project_to_dict(project)
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error completing project: {str(e)}")

@router.post("/{project_id}/mark-completed", response_model=Project)
def mark_project_completed(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Mark project as completed by freelancer (without payment).
    """
    project = get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Solo el freelancer asignado puede marcar como completado
    if project.freelancer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned freelancer can mark as completed")
    
    # Verificar que el proyecto esté en progreso
    if project.status != ProjectStatus.IN_PROGRESS.value:
        raise HTTPException(status_code=400, detail="Project must be in progress to be marked as completed")
    
    # Actualizar status a completado (sin transferir créditos)
    project.status = ProjectStatus.COMPLETED.value
    db.commit()
    db.refresh(project)
    
    return convert_project_to_dict(project)
