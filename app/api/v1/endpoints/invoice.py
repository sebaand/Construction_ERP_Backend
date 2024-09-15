from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from io import BytesIO
from app.schemas.invoice import Invoice
from app.services.invoice_service import InvoiceService
from app.utils.pdf_config import generate_invoice_pdf
from app.api.deps import get_invoice_service

router = APIRouter()

@router.get("/invoice/{slate_id}", response_model=Invoice)
async def get_invoice_data(
    slate_id: str,
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    return await invoice_service.get_invoice_data(slate_id)

@router.get("/invoice/{slate_id}/pdf")
async def get_invoice_pdf(
    slate_id: str,
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    try:
        invoice_data = await invoice_service.get_invoice_data(slate_id)
        
        # Generate PDF
        buffer = BytesIO()
        generate_invoice_pdf(invoice_data.model_dump(), buffer)
        
        # Return PDF as a downloadable file
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=invoice_{slate_id}.pdf"}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))