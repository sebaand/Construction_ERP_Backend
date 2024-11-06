from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from typing import List, Dict, Optional
import logging
import json


class Team_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.platform_users = self.db.get_collection("Users")

    async def add_user(self, admin_email: str, user_fields: dict) -> dict:
        """
        Add or update a user in the platform with organization details inherited from admin.
        """
        
        print('user_fields', user_fields)
        # Validate required fields
        required_fields = ["email", "name", "premiumKey", "subscription_tier"]
        if not all(field in user_fields for field in required_fields):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields. Need email, name, premiumKey and subscription_tier"
            )

        # Retrieve the admin user
        admin = await self.platform_users.find_one({"email": admin_email})
        if not admin:
            raise HTTPException(status_code=404, detail="Admin user not found")

        try:
            # Check if user already exists
            existing_user = await self.platform_users.find_one(
                {"email": user_fields["email"]}
            )
            
            if existing_user:
                
                # Get existing organization_id or initialize empty list
                organization_id = existing_user.get("organization_id", [])
                
                # Look for existing entry with premiumKey
                premium_key = user_fields["premiumKey"]
                key_exists = False
                
                # Update existing organization_id entry if key exists
                for org in organization_id:
                    if premium_key in org:
                        org[premium_key] = user_fields["subscription_tier"]
                        key_exists = True
                        break
                
                # If key doesn't exist, append new entry
                if not key_exists:
                    organization_id.append({
                        premium_key: user_fields["subscription_tier"]
                    })
                
                # Prepare update fields
                update_fields = {
                    "name": user_fields["name"],
                    "email": user_fields["email"],
                    "organization": existing_user.get("organization", admin["organization"]),
                    "organization_id": organization_id,
                    "auth0_id": existing_user.get("auth0_id")
                }
                
                # Update the user
                await self.platform_users.update_one(
                    {"email": user_fields["email"]},
                    {"$set": update_fields}
                )
                return {"message": "User updated successfully"}

            else:
                
                # Create new user with initial organization_id
                new_user = {
                    "name": user_fields["name"],
                    "email": user_fields["email"],
                    "organization": admin["organization"],
                    "organization_id": [{
                        user_fields["premiumKey"]: user_fields["subscription_tier"]
                    }],
                    "auth0_id": None
                }
                
                await self.platform_users.insert_one(new_user)
                return {"message": "User added successfully"}

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing user: {str(e)}"
            )
        
    async def update_existing_user(self, user_fields):
        print('user_fields', user_fields)
        # Validate required fields
        required_fields = ["name", "email", "subscription_tier"]
        if not all(field in user_fields for field in required_fields):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields. Need email, name, premiumKey and subscription_tier"
            )

        try:
            # Check if user already exists
            existing_user = await self.platform_users.find_one(
                {"email": user_fields["email"]}
            )

            # Get existing organization_id or initialize empty list
            organization_id = existing_user.get("organization_id", [])
            
            # Look for existing entry with premiumKey
            premium_key = user_fields["premiumKey"]
            key_exists = False
            
            # Update existing organization_id entry if key exists
            for org in organization_id:
                if premium_key in org:
                    org[premium_key] = user_fields["subscription_tier"]
                    key_exists = True
                    break
            
            # If key doesn't exist, append new entry
            if not key_exists:
                organization_id.append({
                    premium_key: user_fields["subscription_tier"]
                })
            
            # Prepare update fields
            update_fields = {
                "name": user_fields["name"],
                "organization_id": organization_id,
            }
            
            # Update the user
            await self.platform_users.update_one(
                {"email": user_fields["email"]},
                {"$set": update_fields}
            )
            return {"message": "User updated successfully"}


        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing user: {str(e)}"
            )
        

    async def remove_team_users(self, users: List[str], premiumKey: str):
        try:
            updated_users = []
            for email in users:
                # Find the user by email
                user = await self.platform_users.find_one({"email": email})
                
                if user:
                    # Filter out the object that has premiumKey as its key
                    updated_org_ids = [
                        org for org in user.get("organization_id", [])
                        if premiumKey not in org  # This checks if premiumKey is not a key in the dictionary
                    ]
                    
                    # Update the user document with filtered organization_ids
                    result = await self.platform_users.update_one(
                        {"_id": user["_id"]},
                        {"$set": {"organization_id": updated_org_ids}}
                    )
                    
                    if result.modified_count > 0:
                        updated_users.append(email)
            
            if not updated_users:
                return {"message": "No users were found or updated"}
            
            return {
                "message": "Users removed from the team successfully",
                "updated_users": updated_users
            }
            
        except Exception as e:
            logging.error(f"Error removing team users: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error removing users from team: {str(e)}"
            )
