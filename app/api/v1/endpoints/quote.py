from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.responses import StreamingResponse
from app.schemas.collections import Quote_Complete_Data
from app.schemas.quote import QuoteSlateModel, QuoteDownloadModel
from app.services.quote_service import Quote_Service
from app.services.prospect_service import Prospect_Service
from app.utils.generate_pdf import generate_quote_pdf
from app.api.deps import get_quote_service, get_prospect_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# # # # # # # All GET Routes # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # #
# Collect all quotes for an owner ID
@router.get("/quote-details/", response_model=Quote_Complete_Data)
async def get_quote_data(
    owner: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    return await quote_service.get_quote_data(owner)

# Collect data for a single quote
@router.get("/single-quote-details/", response_model=QuoteSlateModel)
async def get_single_quote_data(
    owner: str = Query(...),
    quoteId: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    try:
        return await quote_service.get_single_quote_data(owner, quoteId)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# @router.get("/download/")
# async def download_quote(
#     quoteId: str = Query(...),
#     owner: str = Query(...),
#     quote_service: Quote_Service = Depends(get_quote_service),
#     prospect_service: Prospect_Service = Depends(get_prospect_service)
# ):
#     try:
#         # Get merged quote data
#         quote_data = await get_merged_quote_data(owner, quoteId, prospect_service, quote_service)
        
#         # Generate PDF
#         pdf_buffer = generate_quote_pdf(quote_data)
        
#         # Return StreamingResponse
#         return StreamingResponse(
#             pdf_buffer,
#             media_type="application/pdf",
#             headers={"Content-Disposition": f"attachment; filename=quote_{quoteId}.pdf"}
#         )
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# # Helper function to get merged quote data
# async def get_merged_quote_data(owner, quoteId, prospect_service, quote_service):
#     quote = await quote_service.get_single_quote_data(owner, quoteId)
#     prospects = await prospect_service.get_merged_prospect_data(owner)

#     # Create lookup dictionaries
#     lookups = {
#         'name': {p.companyId: p.name for p in prospects.prospects},
#         'company_address': {p.companyId: p.company_address for p in prospects.prospects},
#         'site_address': {p.companyId: p.site_address for p in prospects.prospects},
#         'vat_number': {p.companyId: p.vat_number for p in prospects.prospects},
#         'company_number': {p.companyId: p.company_number for p in prospects.prospects},
#         'telephone': {p.companyId: p.telephone for p in prospects.prospects},
#     }

#     return QuoteDownloadModel(
#         **quote.dict(),
#         companyName=lookups['name'].get(quote.companyId, "Unknown"),
#         company_address=lookups['company_address'].get(quote.companyId, "Unknown"),
#         site_address=lookups['site_address'].get(quote.companyId, "Unknown"),
#         vat_number=lookups['vat_number'].get(quote.companyId, "Unknown"),
#         company_number=lookups['company_number'].get(quote.companyId, "Unknown"),
#         telephone=lookups['telephone'].get(quote.companyId, "Unknown"),
#     )
@router.get("/download/")
async def download_quote(
    quoteId: str = Query(...),
    owner: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    try:
        logger.info(f"Attempting to download quote with ID: {quoteId} for owner: {owner}")
        
        # Get merged quote data
        quote_data = await get_merged_quote_data(owner, quoteId, prospect_service, quote_service)
        logger.debug(f"Retrieved quote data: {quote_data}")
        
        # Generate PDF
        pdf_buffer = generate_quote_pdf(quote_data)
        
        # Return StreamingResponse
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=quote_{quoteId}.pdf"}
        )
    except Exception as e:
        logger.exception(f"Error occurred while downloading quote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Helper function for internal use
async def get_merged_quote_data(owner: str, quoteId: str, prospect_service: Prospect_Service, quote_service: Quote_Service):
    """Internal helper function"""
    try:
        quote = await quote_service.get_single_quote_data(owner, quoteId)
        merged_data = await prospect_service.merge_prospect_data(owner)
        
        # Use the merged data to create the quote download model
        return QuoteDownloadModel(
            **quote.model_dump(),
            projectName=next((p.projectName for p in merged_data.items if p.companyId == quote.companyId), "Unknown"),
            companyName=next((p.companyName for p in merged_data.items if p.companyId == quote.companyId), "Unknown"),
            company_address=next((p.company_address for p in merged_data.items if p.companyId == quote.companyId), "Unknown"),
            site_address=next((p.site_address for p in merged_data.items if p.companyId == quote.companyId), "Unknown"),
            vat_number=next((p.vat_number for p in merged_data.items if p.companyId == quote.companyId), "Unknown"),
            company_number=next((p.company_number for p in merged_data.items if p.companyId == quote.companyId), "Unknown"),
            telephone=next((p.telephone for p in merged_data.items if p.companyId == quote.companyId), "Unknown"),
        )
    except Exception as e:
        logger.exception(f"Error in get_merged_quote_data: {str(e)}")
        raise

# # # # # # # All POST Routes # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # #
# Route for posting adding or updating a single quote associated with an owner_org
@router.post("/quotes/")
async def create_or_update_quote(quote: QuoteSlateModel):
    if quote.status == "Finalized":
        # Perform additional validation for finalized quotes
        if not all([quote.assignee, quote.due_date, quote.order_number]):
            raise HTTPException(status_code=400, detail="All fields must be filled for finalized quotes")
    # Process the quote (save to database, etc.)
    ...

# Route for posting adding or updating all quotes associated with an owner_org
@router.post("/quote-details/", response_model=Quote_Complete_Data)
async def update_quote_data(
    owner: str = Query(...),
    quote_data: Quote_Complete_Data = Body(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    return await quote_service.update_quote_data(owner, quote_data)

# Route for archiving a specific quoteId
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
    