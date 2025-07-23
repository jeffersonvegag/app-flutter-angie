# app/api/v1/endpoints/applications.py
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.application import get_application, update_application_status
from app.crud.project import get_project, assign_project
from app.crud import transaction as crud_transaction
from app.models.models import User, ApplicationStatus, ProjectApplication as ProjectApplicationModel
from app.schemas.application import ProjectApplication

router = APIRouter()

@router.post("/{application_id}/accept")
def accept_application(
    *,
    db: Session = Depends(deps.get_db),
    application_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Accept a project application (client only).
    """
    try:
        print(f"DEBUG: Intentando aceptar aplicación {application_id} por usuario {current_user.id}")
        
        # Verificar que la aplicación existe
        application = get_application(db=db, application_id=application_id)
        if not application:
            print(f"DEBUG: Aplicación {application_id} no encontrada")
            raise HTTPException(status_code=404, detail="Application not found")
        
        print(f"DEBUG: Aplicación encontrada - Estado: {application.status}, Proyecto: {application.project_id}")
        
        # Verificar que el proyecto existe
        project = get_project(db=db, project_id=application.project_id)
        if not project:
            print(f"DEBUG: Proyecto {application.project_id} no encontrado")
            raise HTTPException(status_code=404, detail="Project not found")
        
        print(f"DEBUG: Proyecto encontrado - Estado: {project.status}, Cliente: {project.client_id}")
        
        # Solo el cliente del proyecto puede aceptar aplicaciones
        if project.client_id != current_user.id:
            print(f"DEBUG: Usuario {current_user.id} no es el cliente del proyecto {project.client_id}")
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verificar que la aplicación esté pendiente
        if application.status != ApplicationStatus.PENDING.value:
            print(f"DEBUG: Aplicación no está pendiente - Estado actual: {application.status}")
            raise HTTPException(status_code=400, detail=f"Application is not pending (current status: {application.status})")
        
        # Verificar que el proyecto esté abierto
        if project.status != "open":
            print(f"DEBUG: Proyecto no está abierto - Estado actual: {project.status}")
            raise HTTPException(status_code=400, detail=f"Project is not open (current status: {project.status})")
        
        # Verificar que el cliente tenga suficientes créditos
        print(f"DEBUG: Créditos del cliente: {current_user.credits_balance}, Presupuesto del proyecto: {project.budget}")
        if current_user.credits_balance < project.budget:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient credits (have: {current_user.credits_balance}, need: {project.budget})"
            )
        
        print(f"DEBUG: Todas las validaciones pasaron, procediendo a aceptar")
        
        # 1. Actualizar el estado de la aplicación
        application.status = ApplicationStatus.ACCEPTED.value
        
        # 2. Asignar el proyecto al freelancer
        project.freelancer_id = application.freelancer_id
        project.status = "in_progress"
        project.credits_held = project.budget
        
        # 3. Sostener los créditos del cliente
        current_user.credits_balance -= project.budget
        
        # 4. Rechazar todas las demás aplicaciones para este proyecto
        other_applications = db.query(ProjectApplicationModel).filter(
            ProjectApplicationModel.project_id == project.id,
            ProjectApplicationModel.id != application_id,
            ProjectApplicationModel.status == ApplicationStatus.PENDING.value
        ).all()
        
        print(f"DEBUG: Rechazando {len(other_applications)} aplicaciones adicionales")
        
        for other_app in other_applications:
            other_app.status = ApplicationStatus.REJECTED.value
        
        # Guardar todos los cambios
        db.commit()
        db.refresh(application)
        
        print(f"DEBUG: Aplicación aceptada exitosamente")
        
        # Retornar respuesta simple
        return {
            "message": "Application accepted successfully",
            "application_id": application.id,
            "project_id": project.id,
            "status": application.status
        }
        
    except HTTPException as e:
        print(f"DEBUG: HTTPException: {e.detail}")
        raise
    except Exception as e:
        print(f"DEBUG: Error inesperado: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error accepting application: {str(e)}")

@router.post("/{application_id}/reject", response_model=ProjectApplication)
def reject_application(
    *,
    db: Session = Depends(deps.get_db),
    application_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Reject a project application (client only).
    """
    # Verificar que la aplicación existe
    application = get_application(db=db, application_id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Verificar que el proyecto existe
    project = get_project(db=db, project_id=application.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Solo el cliente del proyecto puede rechazar aplicaciones
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verificar que la aplicación esté pendiente
    if application.status != ApplicationStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Application is not pending")
    
    # Actualizar el estado de la aplicación
    updated_application = update_application_status(
        db=db, 
        application_id=application_id, 
        status=ApplicationStatus.REJECTED.value
    )
    
    if not updated_application:
        raise HTTPException(status_code=500, detail="Failed to update application status")
    
    return updated_application
