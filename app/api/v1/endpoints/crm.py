from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.crm import CustomerNamesList
from app.schemas.collections import CRM_Data
from app.services.crm_service import CRM_Service
from app.api.deps import get_crm_service

router = APIRouter()

# # # # # # # All Get Routes # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # #

@router.get("/customer-details/", response_model=CRM_Data)
async def get_crm_data(
    owner: str = Query(...),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    return await crm_service.get_crm_data(owner)


@router.get("/customer-list/", response_model=CustomerNamesList)
async def customer_list(
    owner: str = Query(...),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    return await crm_service.customer_list(owner)

# # # # # # # All POST Routes # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # #

@router.post("/customer-details/", response_model=CRM_Data)
async def update_crm_data(
    owner: str = Query(...),
    crm_data: CRM_Data = Body(...),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    return await crm_service.update_crm_data(owner, crm_data)


@router.post("/delete/")
async def delete_customer(
    owner: str = Query(...),
    companyId: str = Query(...),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    try:
        deleted_items = await crm_service.delete_customer(owner, companyId)
        return {
            "message": "Customer and related items deleted successfully",
            "deleted_items": deleted_items
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")