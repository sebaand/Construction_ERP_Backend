# app/services/team_service.py
# from motor.motor_asyncio import AsyncIOMotorClient
# from bson import ObjectId
# from fastapi import HTTPException
# from typing import List, Dict, Optional
# from app.schemas.user import PlatformUsers

# class Team_Service:
#     def __init__(self, client: AsyncIOMotorClient):
#         self.db = client.Forms
#         self.platform_users = self.db.get_collection("Users")

#     # Route for adding users to project team
#     async def add_user(self, user_fields: dict, email: str):
#         # Retrieve the admin user based on the provided email
#         admin = await self.platform_users.find_one({"email": email})
#         user = await self.platform_users.find_one({"email": user_fields["email"]})
#         print(user_fields)

#         if not admin:
#             raise HTTPException(status_code=404, detail="Admin user not found")

#         try:
#             if user:
#                 print(1)
#                 # Update the user's profile fields
#                 organization = user.get("organization", admin["organization"])
#                 database_id = user.get("database_id")
#                 auth0_id = user.get("auth0_id")

#                 # Check if the user already has an organization_id array
#                 if user.get("organization_id"):
#                     # Append the new value pair to the existing organization_id array
#                     organization_id = user["organization_id"]
#                     # Update the subscription tier for the existing key
#                     for item in organization_id:
#                         key = list(item.keys())[0]
#                         if key == list(admin["organization_id"][0].keys())[0]:
#                             item[key] = user_fields["organization_id"]
#                             break
#                 else:
#                     # Create a new organization_id array with the value pair using the admin's key
#                     admin_key = list(admin["organization_id"][0].keys())[0]
#                     organization_id = [{admin_key: user_fields["organization_id"]}]

#                 new_user = {
#                     "name": user_fields["name"],
#                     "email": user_fields["email"],
#                     "organization": organization,
#                     "organization_id": organization_id,
#                     "database_id": database_id,
#                     "auth0_id": auth0_id
#                 }
#                 # Update the user in the database
#                 await self.platform_users.update_one({"email": user_fields["email"]}, {"$set": new_user})
#                 return {"message": "User updated successfully"}
#             else:
#                 # Get the key from the admin's organization_id
#                 admin_key = list(admin["organization_id"][0].keys())[0]
#                 print(admin_key)
                
#                 # Convert organization_id to a list of dictionaries
#                 organization_id = [{admin_key: user_fields["organization_id"]}]
#                 organization_id = [
#                     {key: str(value[0]) if isinstance(value, list) else str(value)}
#                     for org_id in organization_id
#                     for key, value in org_id.items()
#                 ]
                
#                 new_user = {
#                     "name": user_fields["name"],
#                     "email": user_fields["email"],
#                     "organization": admin["organization"],
#                     "organization_id": organization_id,
#                     "database_id": None,
#                     "auth0_id": None
#                 }
#                 # Insert the new user into the database
#                 await self.platform_users.insert_one(new_user)
#                 return {"message": "User added successfully"}
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=str(e))

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