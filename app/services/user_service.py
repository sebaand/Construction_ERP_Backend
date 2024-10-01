# app/services/user_service.py

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict, Optional
from app.schemas.user import PlatformUsers, UserData
from app.schemas.early_bird import EarlyBird
from app.schemas.collections import UsersCollection

class UserService:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.platform_users = self.db.get_collection("Users")
        self.early_birds = self.db.get_collection("Early_Birds")

    async def get_user_profile(self, auth0_id: str) -> Optional[PlatformUsers]:
        user = await self.platform_users.find_one({"auth0_id": auth0_id})
        if user:
            return PlatformUsers(**user)
        return None


    async def get_user_data(self, email: str) -> UserData:
        user = await self.platform_users.find_one({"email": email})
        if user:
            user_org_ids = user["organization_id"]
            premium_org_id = None
            for org_id_dict in user_org_ids:
                for key, value in org_id_dict.items():
                    if value == "Premium User":
                        premium_org_id = key
                        break
                if premium_org_id:
                    break
            if premium_org_id:
                return UserData(is_premium_user=True, premium_key=premium_org_id)
        return UserData(is_premium_user=False)


    async def early_signon(self, user_profile: EarlyBird) -> Dict[str, str]:
        result = await self.early_birds.insert_one(user_profile.model_dump(by_alias=True))
        return {"message": "Early bird request added to database"}


    async def update_user_profile(self, user_profile: PlatformUsers) -> Dict[str, str]:
        user = await self.platform_users.find_one({"auth0_id": user_profile.auth0_id})
        if user:
            user["name"] = user_profile.name
            user["organization"] = user_profile.organization
            user["email"] = user_profile.email
            await self.platform_users.replace_one({"auth0_id": user_profile.auth0_id}, user)
            return {"message": "User profile updated successfully"}
        else:
            new_user = {
                "name": user_profile.name,
                "organization": user_profile.organization,
                "email": user_profile.email,
                "auth0_id": user_profile.auth0_id
            }
            await self.platform_users.insert_one(new_user)
            return {"message": "User profile created successfully"}

    async def register_user(self, user_profile: Dict) -> Dict[str, str]:
        new_user = {
            "email": user_profile["email"],
            "auth0_id": user_profile["auth0_id"],
            'database_id': None,
            "name": None,
            "organization": None,
            "organization_id": [],
        }
        await self.platform_users.insert_one(new_user)
        return {"message": "User registered successfully"}

    async def login_user(self) -> Dict[str, str]:
        return {"message": "User logged in successfully"}

    async def list_users(self) -> UsersCollection:
        users = await self.platform_users.find().to_list(None)
        for user in users:
            user["database_id"] = str(user["_id"])
        return UsersCollection(users=users)

    # Add more methods as needed for other user operations