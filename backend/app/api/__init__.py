from fastapi import APIRouter
from app.api.endpoints import auth, users, status, copro, admin, public

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(status.router, prefix="/status", tags=["status"])
api_router.include_router(copro.router, prefix="/copro", tags=["copro"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(public.router, prefix="/public", tags=["public"])

