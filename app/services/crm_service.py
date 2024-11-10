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
        self.prospect_details = self.db.get_collection("Prospects")
        self.quote_details = self.db.get_collection("Quotes")
        self.invoice_details = self.db.get_collection("Invoices")

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
                CustomerInfo(companyId=item.get("companyId", ""), customer_name=item.get("customer_name", ""), customer_address=item.get("customer_address", ""), vat_number=item.get("vat_number", ""), company_number=item.get("company_number", ""), telephone=item.get("telephone", ""))
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
 

    # Service to delete customer and all related dependencies
    async def delete_customer(self, owner: str, companyId: str) -> dict:
        """
        Delete a customer and all related records across collections.
        Returns a dictionary with counts of deleted items from each collection.
        """
        try:
            # Dictionary to track deletion results
            deletion_results = {
                "crm": 0,
                "prospects": 0,
                "quotes": 0,
                "invoices": 0
            }

            # Delete from CRM
            result_crm = await self.crm_details.update_one(
                {"owner_org": owner},
                {
                    "$pull": {
                        "items": {
                            "companyId": companyId
                        }
                    }
                }
            )
            
            if result_crm.modified_count == 0:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            deletion_results["crm"] = result_crm.modified_count

            # Delete related records from other collections
            collections = [
                (self.prospect_details, "prospects"),
                (self.quote_details, "quotes"),
                (self.invoice_details, "invoices")
            ]

            for collection, key in collections:
                result = await collection.update_one(
                    {"owner_org": owner},
                    {
                        "$pull": {
                            "items": {
                                "companyId": companyId
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
                detail=f"Error deleting customer and related items: {str(e)}"
            )