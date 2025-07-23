from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, projects, chat, transactions, applications, credit_requests

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(credit_requests.router, prefix="/credit-requests", tags=["credit-requests"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])