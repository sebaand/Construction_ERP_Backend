from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from app.schemas.project import Projects
from app.schemas.slate import CreateTemplateModel, AssignSlateModel, SlateTemplateModel, SubmitSlateModel
from app.schemas.collections import ProjectsCollection, TemplateCollection, AssignedSlatesCollection
from app.schemas.invoice import Invoice
from bson import ObjectId

class InvoiceService:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.assigned_slates = self.db.get_collection("Assigned_Slates")
        self.projects = self.db.get_collection("Projects")
        self.templates = self.db.get_collection("Templates")

    async def get_invoice_data(self, slate_id: str) -> Invoice:
        # Convert string ID to ObjectId
        object_id = ObjectId(slate_id)
        
        # Find the slate in the Assigned_Slates collection
        slate_data = await self.assigned_slates.find_one({"_id": object_id})
        
        if not slate_data:
            raise HTTPException(status_code=404, detail="Slate not found")
        
        # Check if the slate is named "invoice"
        if slate_data.get("name", "").lower() != "invoice":
            raise HTTPException(status_code=400, detail="Requested slate is not an invoice")
        
        # Convert slate data to Invoice schema
        try:
            invoice_data = Invoice(
                invoice_number=str(slate_data["_id"]),
                issue_date=slate_data.get("created_at"),
                due_date=slate_data.get("due_date"),
                customer_name=slate_data.get("customer_name"),
                customer_address=slate_data.get("customer_address"),
                company_name=slate_data.get("company_name"),
                company_address=slate_data.get("company_address"),
                items=slate_data.get("items", []),
                total=slate_data.get("total"),
                job_name=slate_data.get("job_name"),
                project_number=slate_data.get("project_number"),
                created_by=slate_data.get("created_by"),
                order_number=slate_data.get("order_number"),
                company_phone=slate_data.get("company_phone"),
                company_email=slate_data.get("company_email"),
                vat_number=slate_data.get("vat_number"),
                company_number=slate_data.get("company_number"),
                bank_address=slate_data.get("bank_address"),
                sort_code=slate_data.get("sort_code"),
                account_number=slate_data.get("account_number")
            )
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"Error processing invoice data: {str(e)}")
        
        return invoice_data

    async def generate_invoice_pdf(self, slate_id: str):
        invoice_data = await self.get_invoice_data(slate_id)
        # Here you would call your PDF generation function
        # For now, we'll just return the invoice data
        return invoice_data.model_dump()

    # Add other invoice-related methods here as needed