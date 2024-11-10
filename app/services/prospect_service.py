from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.crm import CustomerInfo, CustomerNamesList
from app.schemas.prospect import Prospect, MergedProspect, ProspectsNamesList, ProspectInfo
from app.schemas.collections import Prospect_Data, MergedProspectData
from app.services.crm_service import CRM_Service
from uuid import uuid4

class Prospect_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.prospect_details = self.db.get_collection("Prospects")
        self.crm_details = self.db.get_collection("CRM")
        self.quote_details = self.db.get_collection("Quotes")
        self.invoice_details = self.db.get_collection("Invoices")
        self.crm_service = CRM_Service(client)


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
        

    async def merge_prospect_data(self, owner: str) -> MergedProspectData:
        prospects = await self.get_prospect_data(owner)
        customers = await self.crm_service.customer_list(owner)  # Assuming you have access to crm_service

        # Create lookup dictionaries
        lookups = {
            'customer_name': {c.companyId: c.customer_name for c in customers.customers},
            'customer_address': {c.companyId: c.customer_address for c in customers.customers},
            'vat_number': {c.companyId: c.vat_number for c in customers.customers},
            'company_number': {c.companyId: c.company_number for c in customers.customers},
            'telephone': {c.companyId: c.telephone for c in customers.customers}
        }

        merged_items = [
            MergedProspect(
                companyId=prospect.companyId,
                projectId=prospect.projectId,
                projectName=prospect.projectName,
                site_address=prospect.site_address,
                status=prospect.status,
                companyName=lookups['customer_name'].get(prospect.companyId, "Unknown"),
                company_address=lookups['customer_address'].get(prospect.companyId, "Unknown"),
                company_number=lookups['company_number'].get(prospect.companyId, "Unknown"),
                vat_number=lookups['vat_number'].get(prospect.companyId, "Unknown"),
                telephone=lookups['telephone'].get(prospect.companyId, "Unknown"),
            )
            for prospect in prospects.items
        ]

        return MergedProspectData(
            owner_org=owner,
            items=merged_items
        )

    # Function to update a prospect  
    async def update_prospect_data(self, owner: str, Prospects: Prospect_Data) -> MergedProspectData:
        try:
            # Ensure the owner_org matches the one from the URL
            Prospects.owner_org = owner

            # Process items and generate new IDs where needed
            updated_items = []
            for item in Prospects.items:
                if not item.projectId:
                    item.projectId = str(uuid4())
                updated_items.append(item)

            validated_data = Prospect_Data(
                owner_org=owner,
                items=updated_items
            )

            update_data = validated_data.model_dump()

            # Update or insert the data
            existing_entry = await self.prospect_details.find_one({"owner_org": owner})
            if existing_entry:
                result = await self.prospect_details.replace_one(
                    {"owner_org": owner},
                    update_data
                )
                if result.modified_count == 0:
                    raise HTTPException(status_code=400, detail="Failed to update prospect details")
            else:
                result = await self.prospect_details.insert_one(update_data)
                if not result.inserted_id:
                    raise HTTPException(status_code=400, detail="Failed to create prospect details")

            # After successful update, return merged data
            merged_data = await self.merge_prospect_data(owner)
            return merged_data

        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        

    # Function returning the list of customers that have a prospect
    async def customer_list(self, owner: str) -> CustomerNamesList:
        crm_data = await self.crm_details.find_one({"owner_org": owner})
        prospect_data = await self.prospect_details.find_one({"owner_org": owner})
        
        if crm_data and prospect_data:
            # Create a lookup dictionary for company names from CRM data
            company_lookup = {
                item.get("companyId", ""): item.get("name", "")
                for item in crm_data.get("items", [])
            }
            
            # Process prospect data and match with company names
            customers = []
            seen_company_ids = set()  # To avoid duplicates
            for item in prospect_data.get("items", []):
                company_id = item.get("companyId", "")
                if company_id and company_id not in seen_company_ids:
                    company_name = company_lookup.get(company_id, "Unknown")
                    customers.append(CustomerInfo(companyId=company_id, name=company_name))
                    seen_company_ids.add(company_id)
            
            return CustomerNamesList(
                owner_org=owner,
                customers=customers
            )
        else:
            return CustomerNamesList(
                owner_org=owner,
                customers=[]
            )
        
    # Function returning list of prospectid and name 
    async def prospect_list(self, owner: str) -> ProspectsNamesList:
        prospect_data = await self.prospect_details.find_one({"owner_org": owner})
        if prospect_data:
            prospects = [
                ProspectInfo(projectId=item.get("projectId", ""), projectName=item.get("projectName", ""), site_address=item.get("site_address", ""))
                for item in prospect_data.get("items", [])
            ]
            return ProspectsNamesList(
                owner_org=owner,
                prospects=prospects
            )
        else:
            return ProspectsNamesList(
                owner_org=owner,
                prospects=[]
            )

    # Function to archive a prospect   
    async def archive_prospect(self, owner: str, projectId: str) -> None:
        result = await self.prospect_details.update_one(
            {"owner_org": owner, "items.projectId": projectId},
            {"$set": {"items.$.status": "Archived"}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Prospect not found or already archived")

        # Fetch and return the updated document
        updated_doc = await self.prospect_details.find_one({"owner_org": owner})
        if not updated_doc:
            raise HTTPException(status_code=404, detail="Updated document not found")

        return Prospect_Data(**updated_doc)
    

    # Service to delete prospect and all related dependencies
    async def delete_prospect(self, owner: str, projectId: str) -> dict:
        """
        Delete a customer and all related records across collections.
        Returns a dictionary with counts of deleted items from each collection.
        """
        try:
            # Dictionary to track deletion results
            deletion_results = {
                "prospects": 0,
                "quotes": 0,
                "invoices": 0
            }

            # Delete from CRM
            result_prospects = await self.prospect_details.update_one(
                {"owner_org": owner},
                {
                    "$pull": {
                        "items": {
                            "projectId": projectId
                        }
                    }
                }
            )
            
            if result_prospects.modified_count == 0:
                raise HTTPException(status_code=404, detail="Prospect not found")
            
            deletion_results["prospects"] = result_prospects.modified_count

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
                                "projectId": projectId
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
                detail=f"Error deleting prospect and related items: {str(e)}"
            )