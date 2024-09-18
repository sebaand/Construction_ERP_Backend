from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.prospect import Prospect
from app.schemas.collections import Prospect_Data
from app.services.prospect_service import Prospect_Service
from app.api.deps import get_prospect_service

router = APIRouter()

@router.get("/prospect-details/", response_model=Prospect_Data)
async def get_prospect_data(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    return await prospect_service.get_prospect_data(owner)

@router.post("/prospect-details/", response_model=Prospect_Data)
async def update_prospect_data(
    owner: str = Query(...),
    prospect_data: Prospect_Data = Body(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    return await prospect_service.update_prospect_data(owner, prospect_data)