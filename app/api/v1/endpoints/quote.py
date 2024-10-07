from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.collections import Quote_Data, Quote_Complete_Data
from app.schemas.quote import QuoteSlateModel
from app.services.quote_service import Quote_Service
from app.services.prospect_service import Prospect_Service
from app.services.crm_service import CRM_Service
from app.api.deps import get_prospect_service, get_quote_service, get_crm_service 

router = APIRouter()

@router.get("/quote-details/", response_model=Quote_Complete_Data)
async def get_quote_data(
    owner: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    return await quote_service.get_quote_data(owner)


@router.post("/quotes/")
async def create_or_update_quote(quote: QuoteSlateModel):
    if quote.status == "Finalized":
        # Perform additional validation for finalized quotes
        if not all([quote.assignee, quote.due_date, quote.order_number]):
            raise HTTPException(status_code=400, detail="All fields must be filled for finalized quotes")
    # Process the quote (save to database, etc.)
    ...


@router.get("/merged-quote-data/", response_model=Quote_Complete_Data)
async def get_merged_quote_data(
    owner: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    return await quote_service.get_merged_quote_data(owner)


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