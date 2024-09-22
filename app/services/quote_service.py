from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.quote import Quote, MergedQuote
from app.schemas.collections import Quote_Data, MergedQuoteData
from app.services.prospect_service import Prospect_Service
from uuid import uuid4

class Quote_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.quote_details = self.db.get_collection("Quotes")


    async def get_quote_data(self, owner: str) -> Quote_Data:
        Quotes = await self.quote_details.find_one({"owner_org": owner})
        if Quotes:
            return Quote_Data(
                owner_org=owner,
                items=[Quote(**item) for item in Quotes.get("items", [])]
            )
        else:
            return Quote_Data(
                owner_org=owner,
                items=[]
            )
        

    async def get_merged_quote_data(self, owner: str) -> MergedQuoteData:
        quotes = await self.get_quote_data(owner)
        prospects = await Prospect_Service.customer_list(owner)

        company_lookup = {prospect.companyId: prospect.name for prospect in prospects.prospects}
        project_lookup = {prospect.projectId: prospect.projectName for prospect in prospects.prospects}

        merged_items = [
            MergedQuote(
                companyId=quote.companyId,
                companyName=company_lookup.get(quote.companyId, "Unknown"),
                projectId=quote.projectId,
                projectName=project_lookup.get(quote.projectId, "Unknown"),
                address=quote.address,
                name=quote.name,
                status=quote.name
                # Add other fields as needed
            )
            for quote in quotes.items
        ]

        return MergedQuoteData(
            owner_org=owner,
            items=merged_items
        )

    async def update_quote_data(self, owner: str, Quotes: Quote_Data) -> Quote_Data:
        try:
            # Ensure the owner_org matches the one from the URL
            Quotes.owner_org = owner

            updated_items = []
            for item in Quotes.items:
                if not item.quoteId:
                    # Generate a new quoteId for new quotes (empty string)
                    item.quoteId = str(uuid4())
                # If quoteId is not empty, it's an existing quote, so we keep the id
                updated_items.append(item)

            validated_data = Quote_Data(
                owner_org=owner,
                items=updated_items
            )

            update_data = validated_data.model_dump()

            existing_entry = await self.quote_details.find_one({"owner_org": owner})

            if existing_entry:
                result = await self.quote_details.replace_one(
                    {"owner_org": owner},
                    update_data
                )
                if result.modified_count == 0:
                    raise HTTPException(status_code=400, detail="Failed to update quote details")
            else:
                result = await self.quote_details.insert_one(update_data)
                if not result.inserted_id:
                    raise HTTPException(status_code=400, detail="Failed to create quote details")

            return validated_data
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))