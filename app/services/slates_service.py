# app/services/slates_service.py

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from typing import Optional
from app.schemas.slate import CreateTemplateModel, AssignSlateModel, SlateTemplateModel, SubmitSlateModel
from app.schemas.collections import TemplateCollection, AssignedSlatesCollection

class Slates_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.assigned_slates = self.db.get_collection("Assigned_Slates")
        self.templates = self.db.get_collection("Templates")

    async def list_forms(self, owner_org: str, status: bool) -> TemplateCollection:
        query = {"owner_org": owner_org, "status": status}
        forms = await self.templates.find(query).to_list(10000)
        for form in forms:
            form["database_id"] = str(form["_id"])
        return TemplateCollection(forms=forms)

    # async def get_template(self, owner_org: str, templateId: ObjectId) -> SlateTemplateModel:
    #     query = {"owner_org": owner_org, "_id": templateId}
    #     form = await self.templates.find_one(query)
    #     if not form:
    #         return None
    #     form["database_id"] = str(form["_id"])
    #     return SlateTemplateModel(**form)

    async def template_exists(self, owner_org: str, templateId: str) -> bool:
        try:
            object_id = ObjectId(templateId)
            query = {"owner_org": owner_org, "_id": object_id}
            form = await self.templates.find_one(query, projection={"_id": 1})
            return form is not None
        except Exception as e:
            # Log the error here if needed
            return False

    async def get_template(self, owner_org: str, templateId: str) -> Optional[SlateTemplateModel]:
        try:
            object_id = ObjectId(templateId)
            query = {"owner_org": owner_org, "_id": object_id}
            form = await self.templates.find_one(query)
            if not form:
                return None
            form["database_id"] = str(form["_id"])
            del form["_id"]  # Remove the ObjectId as it's not JSON serializable
            return SlateTemplateModel(**form)
        except Exception as e:
            # Log the error here if needed
            return None

    async def list_user_slates(self, assignee: str, status: bool) -> AssignedSlatesCollection:
        query = {"assignee": assignee, "status": status}
        slates = await self.assigned_slates.find(query).to_list(10000)
        for slate in slates:
            slate["database_id"] = str(slate["_id"])
        return AssignedSlatesCollection(slates=slates)

    async def create_slate(self, slate: CreateTemplateModel) -> Dict[str, str]:
        slate_dict = slate.model_dump(by_alias=True)
        insert_result = await self.templates.insert_one(slate_dict)
        return {"message": "Form data submitted successfully", "id": str(insert_result.inserted_id)}

    async def assign_slate(self, slate: AssignSlateModel) -> Dict[str, str]:
        slate_dict = slate.model_dump(by_alias=True)
        insert_result = await self.assigned_slates.insert_one(slate_dict)
        return {"message": "Slate successfully assigned", "id": str(insert_result.inserted_id)}

    async def update_slate(self, form_id: str, json_data: Dict) -> Dict[str, any]:
        update_result = await self.assigned_slates.update_one(
            {"_id": ObjectId(form_id)},
            {"$set": json_data}
        )
        if update_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Form not found or not modified")
        return {"message": "Form updated successfully", "data": json_data}

    async def update_slate_template(self, template_id: str, slate: CreateTemplateModel) -> Dict[str, str]:
        slate_dict = slate.model_dump(by_alias=True)
        update_result = await self.templates.update_one({"_id": ObjectId(template_id)}, {"$set": slate_dict})
        if update_result.modified_count == 1:
            return {"message": "Slate template updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Slate template not found")

    async def delete_slate_template(self, slate_id: str) -> Dict[str, str]:
        delete_result = await self.templates.delete_one({"_id": ObjectId(slate_id)})
        if delete_result.deleted_count == 1:
            return {"message": "Slate template deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Slate template not found")

    async def list_org_slates(self, owner_org: str) -> AssignedSlatesCollection:
        query = {"owner_org": owner_org}
        slates = await self.assigned_slates.find(query).to_list(None)
        for slate in slates:
            slate["database_id"] = str(slate["_id"])
        return AssignedSlatesCollection(slates=slates)

    # Add more methods as needed for other slate operations