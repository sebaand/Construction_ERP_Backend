from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.responses import StreamingResponse
from app.schemas.collections import Invoice_Complete_Data
from app.schemas.invoice import InvoiceSlateModel, InvoiceDownloadModel
from app.services.company_service import Company_Service
from app.services.invoice_service import Invoice_Service
from app.services.prospect_service import Prospect_Service
from app.utils.generate_pdf import generate_invoice_pdf
from app.api.deps import get_company_service, get_invoice_service, get_prospect_service
import logging

router = APIRouter()

router = APIRouter()
logger = logging.getLogger(__name__)

# # # # # # # All GET Routes # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # #

# Collect all invoices for an owner ID
@router.get("/invoice-details/", response_model=Invoice_Complete_Data)
async def get_invoice_data(
    owner: str = Query(...),
    invoice_service: Invoice_Service = Depends(get_invoice_service)
):
    return await invoice_service.get_invoice_data(owner)

# Collect data for a single invoice
@router.get("/single-invoice-details/", response_model=InvoiceSlateModel)
async def get_single_invoice_data(
    owner: str = Query(...),
    invoiceId: str = Query(...),
    invoice_service: Invoice_Service = Depends(get_invoice_service)
):
    try:
        return await invoice_service.get_single_invoice_data(owner, invoiceId)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# route for sending the download request for the selected invoice
@router.get("/download/")
async def download_invoice(
    invoiceId: str = Query(...),
    owner: str = Query(...),
    invoice_service: Invoice_Service = Depends(get_invoice_service),
    prospect_service: Prospect_Service = Depends(get_prospect_service)
):
    try:
        logger.info(f"Attempting to download invoice with ID: {invoiceId} for owner: {owner}")
        
        # Get merged invoice data
        invoice_data = await get_merged_invoice_data(owner, invoiceId, prospect_service, invoice_service)
        logger.debug(f"Retrieved invoice data: {invoice_data}")
        
        # Generate PDF
        pdf_buffer = generate_invoice_pdf(invoice_data)
        
        # Return StreamingResponse
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=invoice_{invoiceId}.pdf"}
        )
    except Exception as e:
        logger.exception(f"Error occurred while downloading invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Helper function for internal use
async def get_merged_invoice_data(owner: str, invoiceId: str, prospect_service: Prospect_Service, invoice_service: Invoice_Service, company_service: Company_Service,):
    """Internal helper function"""
    try:
        invoice = await invoice_service.get_single_invoice_data(owner, invoiceId)
        merged_data = await prospect_service.merge_prospect_data(owner)
        payment_data = await company_service.get_payment_details(owner)
        
        # Use the merged data to create the invoice download model
        return InvoiceDownloadModel(
            **invoice.model_dump(),
            bank=payment_data.bank,
            bank_address=payment_data.bank_address,
            sort_code=payment_data.sort_code,
            account_number=payment_data.account_number,
            projectName=next((p.projectName for p in merged_data.items if p.companyId == invoice.companyId), "Unknown"),
            companyName=next((p.companyName for p in merged_data.items if p.companyId == invoice.companyId), "Unknown"),
            company_address=next((p.company_address for p in merged_data.items if p.companyId == invoice.companyId), "Unknown"),
            site_address=next((p.site_address for p in merged_data.items if p.companyId == invoice.companyId), "Unknown"),
            vat_number=next((p.vat_number for p in merged_data.items if p.companyId == invoice.companyId), "Unknown"),
            company_number=next((p.company_number for p in merged_data.items if p.companyId == invoice.companyId), "Unknown"),
            telephone=next((p.telephone for p in merged_data.items if p.companyId == invoice.companyId), "Unknown"),
            
        )
    except Exception as e:
        logger.exception(f"Error in get_merged_invoice_data: {str(e)}")
        raise

# # # # # # # All POST Routes # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # #

# Route for posting adding or updating all invoices associated with an owner_org
@router.post("/invoice-details/", response_model=Invoice_Complete_Data)
async def update_invoice_data(
    owner: str = Query(...),
    invoice_data: Invoice_Complete_Data = Body(...),
    invoice_service: Invoice_Service = Depends(get_invoice_service)
):
    return await invoice_service.update_invoice_data(owner, invoice_data)

# Route for archiving a specific invoiceId
@router.post("/archive/")
async def archive_invoice(
    owner: str = Query(...),
    invoiceId: str = Query(...),
    invoice_service: Invoice_Service = Depends(get_invoice_service)
):
    try:
        return await invoice_service.archive_invoice(owner, invoiceId)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")