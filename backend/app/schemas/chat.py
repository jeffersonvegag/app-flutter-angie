# app/schemas/chat.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatMessageBase(BaseModel):
    message: str
    receiver_id: int

class ChatMessageCreate(ChatMessageBase):
    project_id: int

class ChatMessage(ChatMessageBase):
    id: int
    project_id: int
    sender_id: int
    status: str
    created_at: datetime
    
    # Información del remitente
    sender_username: Optional[str] = None
    sender_full_name: Optional[str] = None

    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):
    """Schema específico para las respuestas de mensajes con información del remitente"""
    id: int
    message: str
    receiver_id: int
    project_id: int
    sender_id: int
    status: str
    created_at: datetime
    sender_username: Optional[str] = None
    sender_full_name: Optional[str] = None

class ChatMessageList(BaseModel):
    messages: list[ChatMessage]
    total: int