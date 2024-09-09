# app/api/v1/endpoints/dashboard.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.schemas.dashboard import DashboardItem
from app.services.dashboard_service import DashboardService
from app.api.deps import get_dashboard_service

router = APIRouter()

@router.get("/dashboard-data", response_model=List[DashboardItem])
async def get_dashboard_data(
    owner_org: str = Query(..., description="Organization ID to filter slates"),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    return await dashboard_service.get_dashboard_data(owner_org)

@router.get("/dashboard-kpis")
async def get_dashboard_kpis(
    owner_org: str = Query(..., description="Organization ID to filter data"),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    return await dashboard_service.get_dashboard_kpis(owner_org)