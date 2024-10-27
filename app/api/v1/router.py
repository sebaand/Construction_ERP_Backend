from fastapi import APIRouter
from app.api.v1.endpoints import slates, user, project, team, dashboard, general, company, crm, prospect, quote, invoice

api_router = APIRouter()
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(project.router, prefix="/projects", tags=["projects"])
api_router.include_router(slates.router, prefix="/slates", tags=["slates"])
api_router.include_router(team.router, prefix="/team", tags=["team"])
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(crm.router, prefix="/crm", tags=["crm"])
api_router.include_router(prospect.router, prefix="/prospect", tags=["prospect"])
api_router.include_router(quote.router, prefix="/quote", tags=["quote"])
api_router.include_router(invoice.router, prefix="/invoice", tags=["invoice"])
api_router.include_router(general.router, tags=["general"])