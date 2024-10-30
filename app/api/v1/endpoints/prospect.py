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
    return await prospect_service.merge_prospect_data(owner)


@router.get("/merged-prospect-data/", response_model=MergedProspectData)
async def get_merged_prospect_data(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    prospects = await prospect_service.get_prospect_data(owner)
    customers = await crm_service.customer_list(owner)

    # Create a lookup dictionary for info from CRM
    company_lookup = {customer.companyId: customer.customer_name for customer in customers.customers}
    company_address_lookup = {customer.companyId: customer.customer_address for customer in customers.customers}
    company_vat_lookup = {customer.companyId: customer.vat_number for customer in customers.customers}
    company_nm_lookup = {customer.companyId: customer.company_number for customer in customers.customers}
    telephone_lookup = {customer.companyId: customer.telephone for customer in customers.customers}

    merged_items = [
        MergedProspect(
            companyId=prospect.companyId,
            projectId=prospect.projectId,
            projectName=prospect.projectName,
            site_address=prospect.site_address,
            status=prospect.status,
            companyName=company_lookup.get(prospect.companyId, "Unknown"),
            company_address=company_address_lookup.get(prospect.companyId, "Unknown"),
            company_number=company_nm_lookup.get(prospect.companyId, "Unknown"),
            vat_number=company_vat_lookup.get(prospect.companyId, "Unknown"),
            telephone=telephone_lookup.get(prospect.companyId, "Unknown"),
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
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    return await prospect_service.customer_list(owner)


@router.get("/prospect-list/", response_model=ProspectsNamesList)
async def prospect_list(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    return await prospect_service.prospect_list(owner)


@router.post("/prospect-details/", response_model=Prospect_Data)
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