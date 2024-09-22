from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.prospect import Prospect
from app.schemas.prospect import CustomerNamesList
from app.schemas.prospect import MergedProspect
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
    prospect_service: Prospect_Service = Depends(get_prospect_service),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    prospects = await prospect_service.get_prospect_data(owner)
    customers = await crm_service.customer_list(owner)

    # Create a lookup dictionary for company names
    company_lookup = {customer.companyId: customer.name for customer in customers.customers}

    merged_items = [
        MergedProspect(
            companyId=prospect.companyId,
            companyName=company_lookup.get(prospect.companyId, "Unknown"),
            projectId=prospect.projectId,
            projectName=prospect.projectName,
            address=prospect.address,
            # Add other fields as needed
        )
        for prospect in prospects.items
    ]

    return MergedProspectData(
        owner_org=owner,
        items=merged_items
    )


@router.get("/customer-list/", response_model=CustomerNamesList)
async def customer_list(
    owner: str = Query(...),
    prospect_service: CRM_Service = Depends(get_crm_service)
):
    return await prospect_service.customer_list(owner)


@router.post("/prospect-details/", response_model=Prospect_Data)
async def update_prospect_data(
    owner: str = Query(...),
    prospect_data: Prospect_Data = Body(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    return await prospect_service.update_prospect_data(owner, prospect_data)