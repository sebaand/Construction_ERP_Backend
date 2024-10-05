from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.quote import MergedQuote
from app.schemas.collections import Quote_Data, MergedQuoteData, Quote_Complete_Data
from app.services.quote_service import Quote_Service
from app.services.prospect_service import Prospect_Service
from app.services.crm_service import CRM_Service
from app.api.deps import get_prospect_service, get_quote_service, get_crm_service 

router = APIRouter()

@router.get("/quote-details/", response_model=Quote_Data)
async def get_quote_data(
    owner: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    return await quote_service.get_quote_data(owner)


@router.get("/merged-quote-data/", response_model=MergedQuoteData)
async def get_merged_quote_data(
    owner: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service),
    prospect_service: Prospect_Service = Depends(get_prospect_service),
    crm_service: CRM_Service = Depends(get_crm_service)
):
    quotes = await quote_service.get_quote_data(owner)
    prospects = await prospect_service.prospect_list(owner)
    customers = await crm_service.customer_list(owner)

    # Create a lookup dictionary for company names and prospect name
    company_lookup = {customer.companyId: customer.name for customer in customers.customers}
    project_lookup = {prospect.projectId: prospect.projectName for prospect in prospects.prospects}
    address_lookup = {prospect.projectId: prospect.address for prospect in prospects.prospects}

    merged_items = [
        MergedQuote(
            quoteId=quote.quoteId,
            companyId=quote.companyId,
            companyName=company_lookup.get(quote.companyId, "Unknown"),
            projectId=quote.projectId,
            projectName=project_lookup.get(quote.projectId, "Unknown"),
            address=address_lookup.get(quote.projectId, "Unknown"),
            name=quote.name,
            status=quote.status
            # Add other fields as needed
        )
        for quote in quotes.items
    ]

    return MergedQuoteData(
        owner_org=owner,
        items=merged_items
    )

# @router.post("/quote-details/", response_model=Quote_Data)
# async def update_quote_data(
#     owner: str = Query(...),
#     quote_data: Quote_Data = Body(...),
#     quote_service: Quote_Service = Depends(get_quote_service)
# ):
#     return await quote_service.update_quote_data(owner, quote_data)
@router.post("/quote-details/", response_model=Quote_Complete_Data)
async def update_quote_data(
    owner: str = Query(...),
    quote_data: Quote_Complete_Data = Body(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    return await quote_service.update_quote_data(owner, quote_data)


@router.post("/archive/")
async def archive_quote(
    owner: str = Query(...),
    quoteId: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    try:
        return await quote_service.archive_quote(owner, quoteId)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")