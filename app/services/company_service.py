from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.company import Company, Payment, PricingItem
from app.schemas.collections import PricingData

class CompanyService:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.company_details = self.db.get_collection("Company_Details")
        self.payment_details = self.db.get_collection("Payment_Details")
        self.pricing_details = self.db.get_collection("Pricing")

    async def get_company_details(self, owner: str) -> Company:
        company_data = await self.company_details.find_one({"owner_org": owner})
        if company_data:
            return Company(**company_data)
        else:
            return Company(owner_org=owner, name="", address="", vat="", email="", telephone="")

    async def update_company_details(self, owner: str, company_data: Company) -> Company:
        company_dict = company_data.model_dump()
        company_dict["owner_org"] = owner  # Ensure the owner is set correctly
        print('owner', owner)
        print('company_data', company_data)
        try:
            # Check if an entry exists
            existing_entry = await self.company_details.find_one({"owner_org": owner})
            
            if existing_entry:
                # Update existing entry
                result = await self.company_details.replace_one(
                    {"owner_org": owner},
                    company_dict
                )
                if result.modified_count == 0:
                    raise HTTPException(status_code=400, detail="Failed to update company details")
            else:
                # Insert new entry
                result = await self.company_details.insert_one(company_dict)
                if not result.inserted_id:
                    raise HTTPException(status_code=400, detail="Failed to create company details")
            
            return company_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")


    async def get_payment_details(self, owner: str) -> Payment:
            payment_data = await self.payment_details.find_one({"owner_org": owner})
            if payment_data:
                return Payment(
                    owner_org=owner,
                    bank=payment_data.get("bank", ""),
                    bank_address=payment_data.get("bank_address", ""),
                    sort_code=payment_data.get("sort_code", ""),
                    account_number=payment_data.get("account_number", ""),
                    terms=payment_data.get("terms", "")
                )
            else:
                return Payment(
                    owner_org=owner,
                    bank="",
                    bank_address="",
                    sort_code="",
                    account_number="",
                    terms=""
                )

    async def update_payment_details(self, owner: str, payment_data: Payment) -> Payment:
        try:
            # Check if an entry exists
            existing_entry = await self.payment_details.find_one({"owner_org": owner})
            
            update_data = payment_data.model_dump()
            update_data["owner_org"] = owner  # Ensure the owner is set correctly
            
            if existing_entry:
                # Update existing entry
                result = await self.payment_details.replace_one(
                    {"owner_org": owner},
                    update_data
                )
                if result.modified_count == 0:
                    raise HTTPException(status_code=400, detail="Failed to update payment details")
            else:
                # Insert new entry
                result = await self.payment_details.insert_one(update_data)
                if not result.inserted_id:
                    raise HTTPException(status_code=400, detail="Failed to create payment details")
            
            return payment_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")

    async def get_pricing_data(self, owner: str) -> PricingData:
        pricing_data = await self.pricing_details.find_one({"owner_org": owner})
        if pricing_data:
            return PricingData(
                owner_org=owner,
                items=[PricingItem(**item) for item in pricing_data.get("items", [])]
            )
        else:
            return PricingData(
                owner_org=owner,
                items=[]
            )
        

    async def update_pricing_data(self, owner: str, pricing_data: PricingData) -> PricingData:
        try:
            # Ensure the owner_org matches the one from the URL
            pricing_data.owner_org = owner

            # Validate the incoming data
            validated_data = PricingData(
                owner_org=owner,
                items=[item if isinstance(item, PricingItem) else PricingItem(**item) for item in pricing_data.items]
            )

            update_data = validated_data.model_dump()
            
            existing_entry = await self.pricing_details.find_one({"owner_org": owner})
            
            if existing_entry:
                result = await self.pricing_details.replace_one(
                    {"owner_org": owner},
                    update_data
                )
                if result.modified_count == 0:
                    raise HTTPException(status_code=400, detail="Failed to update pricing details")
            else:
                result = await self.pricing_details.insert_one(update_data)
                if not result.inserted_id:
                    raise HTTPException(status_code=400, detail="Failed to create pricing details")
            
            return validated_data
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))