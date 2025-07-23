# app/core/init_admin.py
"""
Inicialización automática del usuario administrador
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash
import os

def create_admin_user():
    """
    Crear usuario administrador automáticamente si no existe.
    Se ejecuta al iniciar la aplicación.
    """
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existe el usuario admin
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            # Si existe, asegurar que tenga los permisos correctos
            if not existing_admin.is_admin:
                existing_admin.is_admin = True
                existing_admin.is_client = False
                existing_admin.is_freelancer = False
                db.commit()
                print("✅ Permisos de admin actualizados")
            return existing_admin
        
        # Obtener credenciales desde variables de entorno o usar defaults
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "tesis1234")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
        
        # Crear nuevo usuario admin
        admin_user = User(
            email=admin_email,
            username=admin_username,
            hashed_password=get_password_hash(admin_password),
            full_name="admin test",
            is_active=True,
            is_client=False,
            is_freelancer=False,
            is_admin=True,  # 🔥 ESTO ES LO IMPORTANTE
            credits_balance=0.0,
            rating=0.0
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Usuario administrador creado: {admin_username}")
        return admin_user
        
    except Exception as e:
        print(f"❌ Error inicializando admin: {e}")
        db.rollback()
        return None
    finally:
        db.close()
