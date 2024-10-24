from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.quote import QuoteSlateModel, QuoteDownloadModel
from app.schemas.collections import Quote_Data, Quote_Complete_Data
from app.services.prospect_service import Prospect_Service
from app.services.crm_service import CRM_Service
from uuid import uuid4
from datetime import datetime

class Quote_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.quote_details = self.db.get_collection("Quotes")
        self.prospect_service = Prospect_Service(client)  # Initialize Prospect_Service
        self.crm_service = CRM_Service(client)  # Initialize CRM_Service


    # service function for returning a list of all quotes associated to an owner_org
    async def get_quote_data(self, owner: str) -> Quote_Complete_Data:
        Quotes = await self.quote_details.find_one({"owner_org": owner})
        if Quotes:
            return Quote_Complete_Data(
                owner_org=owner,
                items=[QuoteSlateModel(**item) for item in Quotes.get("items", [])]
            )
        else:
            return Quote_Complete_Data(
                owner_org=owner,
                items=[]
            )

    # service function for returning a single quote associated to an owner_org
    async def get_single_quote_data(self, owner: str, quoteId: str) -> QuoteSlateModel:
        # Query for the document containing the owner's quotes
        owner_quotes = await self.quote_details.find_one({"owner_org": owner})
        
        if owner_quotes:
            # Search for the specific quote in the items list
            for quote in owner_quotes.get("items", []):
                if quote.get("quoteId") == quoteId:
                    return QuoteSlateModel(**quote)
            
            # If the loop completes without finding the quote, it doesn't exist
            raise HTTPException(status_code=404, detail=f"Quote with ID {quoteId} not found")
        else:
            # If no document found for the owner, return an empty quote or raise an exception
            raise HTTPException(status_code=404, detail=f"No quotes found for owner {owner}")
        

    # # Function for returning the merged quote+prospect data
    # async def get_merged_prospect_data(self, owner: str) -> QuoteDownloadModel:

    #     # Retrieved quote data to download
    #     quote = await self.get_single_quote_data(owner)

    #     # Retrieving merged prospects for cross matching to quote
    #     prospects = await Prospect_Service.get_merged_prospect_data(owner)

    #     # Create a lookup dictionary for info from Prospects
    #     company_lookup = {prospect.companyId: prospect.name for prospect in prospects.prospects}
    #     company_address_lookup = {prospect.companyId: prospect.company_address for prospect in prospects.prospects}
    #     site_address_lookup = {prospect.companyId: prospect.site_address for prospect in prospects.prospects}
    #     company_vat_lookup = {prospect.companyId: prospect.vat_number for prospect in prospects.prospects}
    #     company_number_lookup = {prospect.companyId: prospect.company_number for prospect in prospects.prospects}
    #     telephone_lookup = {prospect.companyId: prospect.telephone for prospect in prospects.prospects}

    #     return QuoteDownloadModel(
    #         name=quote.name,
    #         creator=quote.creator,
    #         last_updated=quote.last_updated,
    #         quoteId=quote.quoteId,
    #         projectId=quote.projectId,
    #         companyId=quote.companyId,
    #         status=quote.status,
    #         terms=quote.terms,
    #         issue_date=quote.issue_date,
    #         quote_number=quote.quote_number,
    #         order_number=quote.order_number,
    #         quoteTotal=quote.quoteTotal,
    #         lineItems=quote.lineItems,
    #         companyName=company_lookup.get(quote.companyId, "Unknown"),
    #         company_address=company_address_lookup.get(quote.companyId, "Unknown"),
    #         site_address=site_address_lookup.get(quote.companyId, "Unknown"),
    #         company_number=company_number_lookup.get(quote.companyId, "Unknown"),
    #         vat_number=company_vat_lookup.get(quote.companyId, "Unknown"),
    #         telephone=telephone_lookup.get(quote.companyId, "Unknown"),
    #         # Add other fields as needed
    #     )
        
        
    # function for both updating the quote data of an existing quote or adding a new one
    async def update_quote_data(self, owner: str, quotes: Quote_Complete_Data) -> Quote_Complete_Data:
        try:
            quotes.owner_org = owner
            updated_items = []
            for item in quotes.items:
                if not item.quoteId:
                    item.quoteId = str(uuid4())
                item.last_updated = datetime.utcnow()
                updated_items.append(item)

            validated_data = Quote_Complete_Data(
                owner_org=owner,
                items=updated_items
            )

            update_data = validated_data.model_dump()

            result = await self.quote_details.replace_one(
                {"owner_org": owner},
                update_data,
                upsert=True
            )

            if result.modified_count == 0 and result.upserted_id is None:
                raise HTTPException(status_code=400, detail="Failed to update quote details")

            return validated_data
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        

    # Function for setting the quote status to archived
    async def archive_quote(self, owner: str, quoteId: str) -> None:
        result = await self.quote_details.update_one(
            {"owner_org": owner, "items.quoteId": quoteId},
            {"$set": {"items.$.status": "Archived"}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Quote not found or already archived")

        # Fetch and return the updated document
        updated_doc = await self.quote_details.find_one({"owner_org": owner})
        if not updated_doc:
            raise HTTPException(status_code=404, detail="Updated document not found")
        
        return Quote_Data(**updated_doc)