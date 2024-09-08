from fastapi import APIRouter
from app.api.v1.endpoints import user, project, slate, team

api_router = APIRouter()
# api_router.include_router(user.router, prefix="/users", tags=["users"])
# api_router.include_router(project.router, prefix="/projects", tags=["projects"])
# api_router.include_router(slate.router, prefix="/slates", tags=["slates"])
api_router.include_router(team.router, prefix="/team", tags=["team"])