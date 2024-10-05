from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.crm import Customer, CustomerInfo, CustomerNamesList, CustomerList
from app.schemas.collections import CRM_Data
from uuid import uuid4

class CRM_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.crm_details = self.db.get_collection("CRM")

    async def get_crm_data(self, owner: str) -> CRM_Data:
        crm_data = await self.crm_details.find_one({"owner_org": owner})
        if crm_data:
            return CRM_Data(
                owner_org=owner,
                items=[Customer(**item) for item in crm_data.get("items", [])]
            )
        else:
            return CRM_Data(
                owner_org=owner,
                items=[]
            )
        

    async def customer_list(self, owner: str) -> CustomerNamesList:
        crm_data = await self.crm_details.find_one({"owner_org": owner})
        if crm_data:
            customers = [
                CustomerInfo(companyId=item.get("companyId", ""), name=item.get("name", ""), company_address=item.get("company_address", ""), vat_nm=item.get("vat_nm", ""), company_nm=item.get("company_nm", ""), telephone=item.get("telephone", ""))
                for item in crm_data.get("items", [])
            ]
            return CustomerNamesList(
                owner_org=owner,
                customers=customers
            )
        else:
            return CustomerNamesList(
                owner_org=owner,
                customers=[]
            )
    

    async def update_crm_data(self, owner: str, crm_data: CRM_Data) -> CRM_Data:
        try:
            # Ensure the owner_org matches the one from the URL
            crm_data.owner_org = owner

            updated_items = []
            for item in crm_data.items:
                if not item.companyId:
                    # Generate a new companyId for new customers (empty string)
                    item.companyId = str(uuid4())
                # If companyId is not empty, it's an existing customer, so we keep the id
                updated_items.append(item)

            validated_data = CRM_Data(
                owner_org=owner,
                items=updated_items
            )

            update_data = validated_data.model_dump()

            existing_entry = await self.crm_details.find_one({"owner_org": owner})

            if existing_entry:
                result = await self.crm_details.replace_one(
                    {"owner_org": owner},
                    update_data
                )
                if result.modified_count == 0:
                    raise HTTPException(status_code=400, detail="Failed to update customer details")
            else:
                result = await self.crm_details.insert_one(update_data)
                if not result.inserted_id:
                    raise HTTPException(status_code=400, detail="Failed to create customer details")

            return validated_data
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))