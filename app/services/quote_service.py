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
from typing import Optional, List
from enum import Enum

class Quote_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.quote_details = self.db.get_collection("Quotes")
        self.invoice_details = self.db.get_collection("Invoices")
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
        
    class QuoteStatus(Enum):
        ARCHIVED = "Archived"
        CREATED = "Created"
        ISSUED = "ISSUED"
        APPROVED = "Approved"
        # Add other statuses as needed

    async def get_active_quote_data(
        self, 
        owner: str,
        exclude_statuses: Optional[List[str]] = None
    ) -> Quote_Complete_Data:
        """
        Get quotes for an owner, excluding specified statuses.
        
        Args:
            owner: The owner organization ID
            exclude_statuses: List of status values to exclude. Defaults to ["Archived"]
        """
        # Get all quotes
        quotes = await self.get_quote_data(owner)
        
        # Default to excluding archived if no statuses specified
        if exclude_statuses is None:
            exclude_statuses = ["Archived"]

        # Filter out quotes with excluded statuses
        filtered_quotes = [
            quote for quote in quotes.items 
            if quote.status not in exclude_statuses
        ]

        return Quote_Complete_Data(
            owner_org=owner,
            items=filtered_quotes
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
    

    # Service to delete prospect and all related dependencies
    async def delete_quote(self, owner: str, quoteId: str) -> dict:
        """
        Delete a customer and all related records across collections.
        Returns a dictionary with counts of deleted items from each collection.
        """
        try:
            # Dictionary to track deletion results
            deletion_results = {
                "quotes": 0,
                "invoices": 0
            }

            # Delete from CRM
            result_quotes = await self.quote_details.update_one(
                {"owner_org": owner},
                {
                    "$pull": {
                        "items": {
                            "quoteId": quoteId
                        }
                    }
                }
            )
            
            if result_quotes.modified_count == 0:
                raise HTTPException(status_code=404, detail="Quote not found")
            
            deletion_results["quotes"] = result_quotes.modified_count

            # Delete related records from other collections
            collections = [
                (self.quote_details, "quotes"),
                (self.invoice_details, "invoices")
            ]

            for collection, key in collections:
                result = await collection.update_one(
                    {"owner_org": owner},
                    {
                        "$pull": {
                            "items": {
                                "quoteId": quoteId
                            }
                        }
                    }
                )
                deletion_results[key] = result.modified_count
            print('deletion_results', deletion_results)
            return deletion_results

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting quotes and related items: {str(e)}"
            )