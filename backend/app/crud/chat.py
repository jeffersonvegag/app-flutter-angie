# app/crud/chat.py
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import ChatMessage, User
from app.schemas.chat import ChatMessageCreate

def create_message(db: Session, message: ChatMessageCreate, sender_id: int) -> ChatMessage:
    """Crear un nuevo mensaje de chat"""
    db_message = ChatMessage(
        project_id=message.project_id,
        sender_id=sender_id,
        receiver_id=message.receiver_id,
        message=message.message
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_project_messages(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[ChatMessage]:
    """Obtener mensajes de un proyecto específico"""
    return db.query(ChatMessage).filter(
        ChatMessage.project_id == project_id
    ).order_by(ChatMessage.created_at).offset(skip).limit(limit).all()

def mark_messages_as_read(db: Session, project_id: int, user_id: int):
    """Marcar mensajes como leídos"""
    db.query(ChatMessage).filter(
        ChatMessage.project_id == project_id,
        ChatMessage.receiver_id == user_id,
        ChatMessage.status != "read"
    ).update({"status": "read"})
    db.commit()

def get_unread_count(db: Session, user_id: int) -> int:
    """Obtener número de mensajes no leídos"""
    return db.query(ChatMessage).filter(
        ChatMessage.receiver_id == user_id,
        ChatMessage.status != "read"
    ).count()

def get_user_conversations(db: Session, user_id: int) -> List[dict]:
    """Obtener conversaciones del usuario"""
    # Subquery para obtener el último mensaje de cada proyecto
    subquery = db.query(
        ChatMessage.project_id,
        ChatMessage.message,
        ChatMessage.created_at,
        ChatMessage.sender_id
    ).filter(
        (ChatMessage.sender_id == user_id) | (ChatMessage.receiver_id == user_id)
    ).order_by(ChatMessage.project_id, ChatMessage.created_at.desc()).all()
    
    # Agrupar por proyecto y tomar el último mensaje
    conversations = {}
    for msg in subquery:
        if msg.project_id not in conversations:
            conversations[msg.project_id] = {
                'project_id': msg.project_id,
                'last_message': msg.message,
                'last_message_time': msg.created_at,
                'last_sender_id': msg.sender_id
            }
    
    return list(conversations.values())