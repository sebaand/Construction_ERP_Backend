from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.crm import CustomerNamesList
from app.schemas.collections import CRM_Data
from app.services.crm_service import CRM_Service
from app.api.deps import get_crm_service

router = APIRouter()

@router.get("/customer-details/", response_model=CRM_Data)
async def get_crm_data(
    owner: str = Query(...),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    return await crm_service.get_crm_data(owner)

@router.post("/customer-details/", response_model=CRM_Data)
async def update_crm_data(
    owner: str = Query(...),
    crm_data: CRM_Data = Body(...),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    return await crm_service.update_crm_data(owner, crm_data)

@router.get("/customer-list/", response_model=CustomerNamesList)
async def customer_list(
    owner: str = Query(...),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    return await crm_service.customer_list(owner)