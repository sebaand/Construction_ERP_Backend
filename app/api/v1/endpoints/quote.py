from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.collections import Quote_Complete_Data
from app.schemas.quote import QuoteSlateModel, QuoteDownloadModel
from app.services.quote_service import Quote_Service
from app.services.prospect_service import Prospect_Service
from app.utils.generate_pdf import generate_quote_pdf
from app.api.deps import get_quote_service, get_prospect_service

router = APIRouter()

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
@router.get("/quote-details/", response_model=QuoteSlateModel)
async def get_single_quote_data(
    owner: str = Query(...),
    quoteId: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    return await quote_service.get_single_quote_data(owner)

# Merging quote details from multiple sources
@router.get("/merged-quote-data/", response_model=QuoteDownloadModel)
async def get_merged_quote_data(
    owner: str = Query(...),
    prospect_service: Prospect_Service = Depends(get_prospect_service),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    # Retrieved quote data to download
    quote = await quote_service.get_single_quote_data(owner)

    # Retrieving merged prospects for cross matching to qutoe
    prospects = await prospect_service.get_merged_prospect_data(owner)

    # Create a lookup dictionary for info from CRM
    company_lookup = {prospect.companyId: prospect.name for prospect in prospects.prospects}
    company_address_lookup = {prospect.companyId: prospect.company_address for prospect in prospects.prospects}
    site_address_lookup = {prospect.companyId: prospect.site_address for prospect in prospects.prospects}
    company_vat_lookup = {prospect.companyId: prospect.vat_number for prospect in prospects.prospects}
    company_number_lookup = {prospect.companyId: prospect.company_number for prospect in prospects.prospects}
    telephone_lookup = {prospect.companyId: prospect.telephone for prospect in prospects.prospects}

    QuoteDownloadModel(
        name=quote.name,
        creator=quote.creator,
        last_updated=quote.last_updated,
        quoteId=quote.quoteId,
        projectId=quote.projectId,
        companyId=quote.companyId,
        status=quote.status,
        terms=quote.terms,
        issue_date=quote.issue_date,
        quote_number=quote.quote_number,
        order_number=quote.order_number,
        quoteTotal=quote.quoteTotal,
        lineItems=quote.lineItems,
        companyName=company_lookup.get(quote.companyId, "Unknown"),
        company_address=company_address_lookup.get(quote.companyId, "Unknown"),
        site_address=site_address_lookup.get(quote.companyId, "Unknown"),
        company_number=company_number_lookup.get(quote.companyId, "Unknown"),
        vat_number=company_vat_lookup.get(quote.companyId, "Unknown"),
        telephone=telephone_lookup.get(quote.companyId, "Unknown"),
        # Add other fields as needed
    )


    return QuoteDownloadModel(
        items=merged_items
    )

# Route for posting downloading a quoteId
@router.get("/download/")
async def download_quote(
    quoteId: str = Query(...),
    owner: str = Query(...),
    quote_service: Quote_Service = Depends(get_quote_service)
):
    try:
        quote = await quote_service.get_quote_by_id(owner, quoteId)
        pdf_buffer = generate_quote_pdf(quote)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=quote_{quoteId}.pdf"}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

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
    