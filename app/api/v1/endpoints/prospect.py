from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.prospect import Prospect
from app.schemas.crm import CustomerNamesList
from app.schemas.prospect import MergedProspect, ProspectsNamesList
from app.schemas.collections import Prospect_Data, MergedProspectData
from app.services.prospect_service import Prospect_Service
from app.services.crm_service import CRM_Service
from app.api.deps import get_prospect_service, get_crm_service

router = APIRouter()

@router.get("/prospect-details/", response_model=Prospect_Data)
async def get_prospect_data(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    return await prospect_service.get_prospect_data(owner)

@router.get("/merged-prospect-data/", response_model=MergedProspectData)
async def get_merged_prospect_data(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    """Endpoint that handles the HTTP request"""
    return await prospect_service.get_merged_prospect_data(owner)

@router.get("/merged-prospect-data/", response_model=MergedProspectData)
async def get_merged_prospect_data(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    """Endpoint that handles the HTTP request"""
    return await prospect_service.get_merged_prospect_data(owner)

@router.get("/active-merged-prospect-data/", response_model=MergedProspectData)
async def get_active_merged_prospect_data(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    """Endpoint that handles the HTTP request"""
    return await prospect_service.get_active_merged_prospect_data(owner)

@router.get("/customer-list/", response_model=CustomerNamesList)
async def customer_list(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    return await prospect_service.customer_list(owner)


@router.get("/prospect-list/", response_model=ProspectsNamesList)
async def prospect_list(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    return await prospect_service.prospect_list(owner)


@router.post("/prospect-details/", response_model=MergedProspectData)
async def update_prospect_data(
    owner: str = Query(...),
    prospect_data: Prospect_Data = Body(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    return await prospect_service.update_prospect_data(owner, prospect_data)


@router.post("/archive/")
async def archive_prospect(
    owner: str = Query(...),
    projectId: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    try:
        return await prospect_service.archive_prospect(owner, projectId)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/delete/")
async def delete_prospect(
    owner: str = Query(...),
    projectId: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    try:
        deleted_items = await prospect_service.delete_prospect(owner, projectId)
        return {
            "message": "Prospect and related items deleted successfully",
            "deleted_items": deleted_items
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
