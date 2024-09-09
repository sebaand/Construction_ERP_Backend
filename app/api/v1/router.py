from fastapi import APIRouter
from app.api.v1.endpoints import slates, user, project, team, dashboard, general

api_router = APIRouter()
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(project.router, prefix="/projects", tags=["projects"])
api_router.include_router(slates.router, prefix="/slates", tags=["slates"])
api_router.include_router(team.router, prefix="/team", tags=["team"])
api_router.include_router(general.router, tags=["general"])