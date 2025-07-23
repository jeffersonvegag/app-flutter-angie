# app/models/models.py
from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, Table, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base

# Definición de enumeraciones
class ProjectStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"

class TransactionType(str, enum.Enum):
    CREDIT_PURCHASE = "credit_purchase"
    PROJECT_PAYMENT = "project_payment"
    WITHDRAWAL_REQUEST = "withdrawal_request"
    CREDIT_REQUEST = "credit_request"  # Nueva

class CreditRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

# Tablas de asociación
user_skills = Table(
    'user_skills',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('skill_id', Integer, ForeignKey('skills.id'))
)

project_skills = Table(
    'project_skills',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('skill_id', Integer, ForeignKey('skills.id'))
)

# Modelos principales
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_freelancer = Column(Boolean, default=False)
    is_client = Column(Boolean, default=False)
    
    # Para freelancers
    experience_years = Column(Float, nullable=True)
    hourly_rate = Column(Float, nullable=True)
    rating = Column(Float, default=0.0)
    area_expertise = Column(String, nullable=True)
    
    # Sistema de créditos
    credits_balance = Column(Float, default=0.0)
    
    # Campos de administrador
    is_admin = Column(Boolean, default=False)
    
    # Relaciones
    skills = relationship("Skill", secondary=user_skills, back_populates="users")
    # Relaciones para proyectos
    projects_created = relationship("Project", back_populates="client", foreign_keys="Project.client_id")
    projects_assigned = relationship("Project", back_populates="freelancer", foreign_keys="Project.freelancer_id")
    # Relaciones para chat
    sent_messages = relationship("ChatMessage", back_populates="sender", foreign_keys="ChatMessage.sender_id")
    received_messages = relationship("ChatMessage", back_populates="receiver", foreign_keys="ChatMessage.receiver_id")
    # Relaciones para transacciones
    transactions = relationship("Transaction", back_populates="user")
    # Relaciones para aplicaciones a proyectos
    applications = relationship("ProjectApplication", back_populates="freelancer")

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Relaciones
    users = relationship("User", secondary=user_skills, back_populates="skills")
    projects = relationship("Project", secondary=project_skills, back_populates="skills_required")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    client_id = Column(Integer, ForeignKey("users.id"))
    freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default=ProjectStatus.OPEN.value)
    
    budget = Column(Float)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    area = Column(String, index=True)
    
    # Para pagos
    credits_held = Column(Float, default=0.0)  # Créditos retenidos para este proyecto
    is_paid = Column(Boolean, default=False)
    
    # Relaciones
    client = relationship("User", back_populates="projects_created", foreign_keys=[client_id])
    freelancer = relationship("User", back_populates="projects_assigned", foreign_keys=[freelancer_id])
    skills_required = relationship("Skill", secondary=project_skills, back_populates="projects")
    # Relación para mensajes del proyecto
    messages = relationship("ChatMessage", back_populates="project")
    # Relación para aplicaciones al proyecto
    applications = relationship("ProjectApplication", back_populates="project")

# Nuevos modelos
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    status = Column(String, default=MessageStatus.SENT.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    project = relationship("Project", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    transaction_type = Column(String)
    amount = Column(Float)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="transactions")

class ProjectApplication(Base):
    __tablename__ = "project_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    freelancer_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String, nullable=True)  # Mensaje opcional del freelancer
    status = Column(String, default=ApplicationStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    project = relationship("Project", back_populates="applications")
    freelancer = relationship("User", back_populates="applications")

class CreditRequest(Base):
    __tablename__ = "credit_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)  # Cantidad solicitada
    description = Column(String, nullable=True)  # Descripción opcional
    status = Column(String, default=CreditRequestStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin que revisó
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)
    
    # Relaciones
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])