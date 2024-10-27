from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.invoice import InvoiceSlateModel, InvoiceDownloadModel
from app.schemas.collections import Invoice_Complete_Data
from app.services.company_service import Company_Service
from app.services.prospect_service import Prospect_Service
from app.services.crm_service import CRM_Service
from uuid import uuid4
from datetime import datetime

class Invoice_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.invoice_details = self.db.get_collection("Invoices")
        self.company_service = Company_Service(client)  # Initialize Company_Service
        self.prospect_service = Prospect_Service(client)  # Initialize Prospect_Service
        self.crm_service = CRM_Service(client)  # Initialize CRM_Service


    # service function for returning a list of all invoices associated to an owner_org
    async def get_invoice_data(self, owner: str) -> Invoice_Complete_Data:
        Invoices = await self.invoice_details.find_one({"owner_org": owner})
        if Invoices:
            return Invoice_Complete_Data(
                owner_org=owner,
                items=[InvoiceSlateModel(**item) for item in Invoices.get("items", [])]
            )
        else:
            return Invoice_Complete_Data(
                owner_org=owner,
                items=[]
            )

    # service function for returning a single invoice associated to an owner_org
    async def get_single_invoice_data(self, owner: str, invoiceId: str) -> InvoiceSlateModel:
        # Query for the document containing the owner's invoices
        owner_invoices = await self.invoice_details.find_one({"owner_org": owner})
        
        if owner_invoices:
            # Search for the specific invoice in the items list
            for invoice in owner_invoices.get("items", []):
                if invoice.get("invoiceId") == invoiceId:
                    return InvoiceSlateModel(**invoice)
            
            # If the loop completes without finding the invoice, it doesn't exist
            raise HTTPException(status_code=404, detail=f"Quote with ID {invoiceId} not found")
        else:
            # If no document found for the owner, return an empty invoice or raise an exception
            raise HTTPException(status_code=404, detail=f"No invoices found for owner {owner}")
        
        
    # function for both updating the invoice data of an existing invoice or adding a new one
    async def update_invoice_data(self, owner: str, invoices: Invoice_Complete_Data) -> Invoice_Complete_Data:
        try:
            invoices.owner_org = owner
            updated_items = []
            for item in invoices.items:
                if not item.invoiceId:
                    item.invoiceId = str(uuid4())
                item.last_updated = datetime.utcnow()
                updated_items.append(item)

            validated_data = Invoice_Complete_Data(
                owner_org=owner,
                items=updated_items
            )

            update_data = validated_data.model_dump()

            result = await self.invoice_details.replace_one(
                {"owner_org": owner},
                update_data,
                upsert=True
            )

            if result.modified_count == 0 and result.upserted_id is None:
                raise HTTPException(status_code=400, detail="Failed to update invoice details")

            return validated_data
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        

    # Function for setting the invoice status to archived
    async def archive_invoice(self, owner: str, invoiceId: str) -> None:
        result = await self.invoice_details.update_one(
            {"owner_org": owner, "items.invoiceId": invoiceId},
            {"$set": {"items.$.status": "Archived"}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Quote not found or already archived")

        # Fetch and return the updated document
        updated_doc = await self.invoice_details.find_one({"owner_org": owner})
        if not updated_doc:
            raise HTTPException(status_code=404, detail="Updated document not found")
        
        return InvoiceSlateModel(**updated_doc)