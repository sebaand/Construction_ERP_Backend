from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.quote import Quote, QuoteSlateModel
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