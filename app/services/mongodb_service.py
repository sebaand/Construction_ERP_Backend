from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from uuid import uuid4

class MongoDB_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.platform_users = self.db.get_collection("Users")

    async def list_users(self):
        users = await self.platform_users.find().to_list(None)
        for user in users:
            user["database_id"] = str(user["_id"])
        return users
    
    async def register_user(self, user_fields: dict) -> dict:
        """
        Add or update a user in the platform with organization details inherited from admin.
        """
        
        print('user_fields', user_fields)
        try:
            # Check if user already exists
            existing_user = await self.platform_users.find_one(
                {"email": user_fields["email"]}
            )
            
            if existing_user:
                # Prepare update fields
                update_fields = {
                    "auth0_id": user_fields["auth0_id"]
                }
                
                # Update the user
                await self.platform_users.update_one(
                    {"email": user_fields["email"]},
                    {"$set": update_fields}
                )
                return {"message": "User updated successfully"}

            else:
                org = str(uuid4())
                # Create new user with initial organization_id
                new_user = {
                    "name": "",
                    "email": user_fields["email"],
                    "organization": org,
                    "organization_id": [{
                        org : "Premium User"
                    }],
                    "auth0_id": user_fields["auth0_id"]
                }
                
                await self.platform_users.insert_one(new_user)
                return {"message": "User added successfully"}

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing user: {str(e)}"
            )



    # async def update_users(self, user_ids: List[str], updated_fields: Dict):
    #     try:
    #         for user_id in user_ids:
    #             user = await self.platform_users.find_one({"_id": ObjectId(user_id)})
    #             if user:
    #                 self._update_user_fields(user, updated_fields)
    #                 await self.platform_users.replace_one({"_id": ObjectId(user_id)}, user)
    #         return {"message": "User profile(s) updated successfully"}
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=str(e))

    # def _update_user_fields(self, user: Dict, updated_fields: Dict):
    #     user["name"] = updated_fields.get("name", user.get("name"))
    #     user["organization"] = updated_fields.get("organization", user.get("organization"))
        
    #     existing_org_ids = user.get("organization_id", [])
    #     updated_org_ids = updated_fields.get("organization_id", [])
        
    #     updated_org_id_keys = [list(org_id.keys())[0] for org_id in updated_org_ids]
    #     user["organization_id"] = [org_id for org_id in existing_org_ids if list(org_id.keys())[0] in updated_org_id_keys]
        
    #     for org_id in updated_org_ids:
    #         key = list(org_id.keys())[0]
    #         if key in [list(x.keys())[0] for x in user["organization_id"]]:
    #             for item in user["organization_id"]:
    #                 if key in item:
    #                     item[key] = org_id[key]
    #                     break
    #         else:
    #             user["organization_id"].append(org_id)

    # async def delete_users(self, user_ids: List[str]):
    #     try:
    #         for user_id in user_ids:
    #             await self.platform_users.delete_one({"_id": ObjectId(user_id)})
    #         return {"message": f"Deleted users with ids {user_ids}"}
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=str(e))


    # async def _update_existing_user(self, user, admin, user_fields):
    #     organization = user.get("organization", admin["organization"])
    #     organization_id = user.get("organization_id", [])
        
    #     admin_key = list(admin["organization_id"][0].keys())[0]
    #     for item in organization_id:
    #         if admin_key in item:
    #             item[admin_key] = user_fields["organization_id"]
    #             break
    #     else:
    #         organization_id.append({admin_key: user_fields["organization_id"]})

    #     new_user = {
    #         "name": user_fields["name"],
    #         "email": user_fields["email"],
    #         "organization": organization,
    #         "organization_id": organization_id,
    #         "auth0_id": user.get("auth0_id")
    #     }
        
    #     await self.platform_users.update_one({"email": user_fields["email"]}, {"$set": new_user})
    #     return {"message": "User updated successfully"}

    # async def _create_new_user(self, admin, user_fields):
    #     admin_key = list(admin["organization_id"][0].keys())[0]
    #     organization_id = [{admin_key: user_fields["organization_id"]}]
        
    #     new_user = {
    #         "name": user_fields["name"],
    #         "email": user_fields["email"],
    #         "organization": admin["organization"],
    #         "organization_id": organization_id,
    #         "database_id": None,
    #         "auth0_id": None
    #     }
        
    #     await self.platform_users.insert_one(new_user)
    #     return {"message": "User added successfully"}

    # async def _update_team_user(self, user, premium_key, updated_fields):
    #     user["name"] = updated_fields["name"]
        
    #     for org_id in user["organization_id"]:
    #         if premium_key in org_id:
    #             org_id[premium_key] = updated_fields["organization_id"][0]
    #             break
    #     else:
    #         user["organization_id"].append({premium_key: updated_fields["organization_id"][0]})
        
    #     await self.platform_users.update_one({"email": updated_fields["email"]}, {"$set": user})
    #     return {"message": "User profile updated successfully"}


    # async def _create_team_user(self, admin, premium_key, updated_fields):
    #     new_user = {
    #         "email": updated_fields["email"],
    #         "name": updated_fields["name"],
    #         "organization": admin["organization"],
    #         "organization_id": [{premium_key: updated_fields["organization_id"][0]}],
    #         "database_id": None,
    #         "auth0_id": None
    #     }
        
    #     await self.platform_users.insert_one(new_user)
    #     return {"message": "User profile added successfully"}