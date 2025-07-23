from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from app.api.v1.api import api_router
from app.core.config import settings
from app.database import Base, engine
from app.ml.init_model import create_initial_model
from app.core.init_admin import create_admin_user

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear modelo inicial si no existe
create_initial_model()

# Crear usuario admin si no existe
create_admin_user()

app = FastAPI(
    title="Investig-arte API",
    description="API para la aplicación de intermediación de servicios de investigación freelance",
    version="0.1.0",
)

# Configuración de CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",  # Para React/Flutter web
    "*",  # Para desarrollo
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Bienvenido a la API de Investig-arte"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)