from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.prospect import Prospect
from app.schemas.prospect import MergedProspect
from app.schemas.collections import Prospect_Data, MergedProspectData
from app.services.crm_service import CRM_Service
from uuid import uuid4

class Prospect_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.prospect_details = self.db.get_collection("Prospects")


    async def get_prospect_data(self, owner: str) -> Prospect_Data:
        Prospects = await self.prospect_details.find_one({"owner_org": owner})
        if Prospects:
            return Prospect_Data(
                owner_org=owner,
                items=[Prospect(**item) for item in Prospects.get("items", [])]
            )
        else:
            return Prospect_Data(
                owner_org=owner,
                items=[]
            )
        

    async def get_merged_prospect_data(self, owner: str) -> MergedProspectData:
        prospects = await self.get_prospect_data(owner)
        customers = await CRM_Service.customer_list(owner)  # Assuming you have access to crm_service

        company_lookup = {customer.companyId: customer.name for customer in customers.customers}

        merged_items = [
            MergedProspect(
                companyId=prospect.companyId,
                companyName=company_lookup.get(prospect.companyId, "Unknown"),
                projectId=prospect.projectId,
                projectName=prospect.projectName,
                address=prospect.address,
                # Add other fields as needed
            )
            for prospect in prospects.items
        ]

        return MergedProspectData(
            owner_org=owner,
            items=merged_items
        )

    async def update_prospect_data(self, owner: str, Prospects: Prospect_Data) -> Prospect_Data:
        try:
            # Ensure the owner_org matches the one from the URL
            Prospects.owner_org = owner

            updated_items = []
            for item in Prospects.items:
                if not item.projectId:
                    # Generate a new companyId for new customers (empty string)
                    item.projectId = str(uuid4())
                # If companyId is not empty, it's an existing customer, so we keep the id
                updated_items.append(item)

            validated_data = Prospect_Data(
                owner_org=owner,
                items=updated_items
            )

            update_data = validated_data.model_dump()

            existing_entry = await self.prospect_details.find_one({"owner_org": owner})

            if existing_entry:
                result = await self.prospect_details.replace_one(
                    {"owner_org": owner},
                    update_data
                )
                if result.modified_count == 0:
                    raise HTTPException(status_code=400, detail="Failed to update customer details")
            else:
                result = await self.prospect_details.insert_one(update_data)
                if not result.inserted_id:
                    raise HTTPException(status_code=400, detail="Failed to create customer details")

            return validated_data
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))