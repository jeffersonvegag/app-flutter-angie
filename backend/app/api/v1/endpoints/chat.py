# app/api/v1/endpoints/chat.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import chat
from app.models.models import User, Project
from app.schemas.chat import ChatMessage, ChatMessageCreate, ChatMessageList, ChatMessageResponse

router = APIRouter()

@router.post("/send", response_model=ChatMessageResponse)
def send_message(
    *,
    db: Session = Depends(deps.get_db),
    message_in: ChatMessageCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Send a chat message.
    """
    # Verificar que el usuario tiene acceso al proyecto
    project = db.query(Project).filter(Project.id == message_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.id not in [project.client_id, project.freelancer_id]:
        raise HTTPException(status_code=403, detail="Not authorized for this project")
    
    message = chat.create_message(db=db, message=message_in, sender_id=current_user.id)
    
    # Crear respuesta con información del remitente
    return ChatMessageResponse(
        id=message.id,
        message=message.message,
        receiver_id=message.receiver_id,
        project_id=message.project_id,
        sender_id=message.sender_id,
        status=message.status,
        created_at=message.created_at,
        sender_username=current_user.username,
        sender_full_name=current_user.full_name
    )

@router.get("/project/{project_id}", response_model=List[ChatMessageResponse])
def get_project_messages(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get messages for a specific project.
    """
    # Verificar acceso al proyecto
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.id not in [project.client_id, project.freelancer_id]:
        raise HTTPException(status_code=403, detail="Not authorized for this project")
    
    messages = chat.get_project_messages(db=db, project_id=project_id, skip=skip, limit=limit)
    
    # Marcar mensajes como leídos
    chat.mark_messages_as_read(db=db, project_id=project_id, user_id=current_user.id)
    
    # Convertir a respuestas con información del remitente
    result_messages = []
    for message in messages:
        sender = db.query(User).filter(User.id == message.sender_id).first()
        
        response_message = ChatMessageResponse(
            id=message.id,
            message=message.message,
            receiver_id=message.receiver_id,
            project_id=message.project_id,
            sender_id=message.sender_id,
            status=message.status,
            created_at=message.created_at,
            sender_username=sender.username if sender else None,
            sender_full_name=sender.full_name if sender else None
        )
        
        result_messages.append(response_message)
    
    return result_messages

@router.get("/conversations")
def get_conversations(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get user's conversations.
    """
    conversations = chat.get_user_conversations(db=db, user_id=current_user.id)
    
    # Enriquecer con información del proyecto
    for conv in conversations:
        project = db.query(Project).filter(Project.id == conv['project_id']).first()
        if project:
            conv['project_title'] = project.title
            conv['project_status'] = project.status
            # Determinar con quién está chateando
            other_user_id = project.client_id if current_user.id == project.freelancer_id else project.freelancer_id
            other_user = db.query(User).filter(User.id == other_user_id).first()
            if other_user:
                conv['other_user_name'] = other_user.full_name or other_user.username
                conv['other_user_id'] = other_user.id
    
    return conversations

@router.get("/unread-count")
def get_unread_count(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get unread messages count.
    """
    count = chat.get_unread_count(db=db, user_id=current_user.id)
    return {"unread_count": count}