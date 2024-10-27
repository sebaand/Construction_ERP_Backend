# app/services/project_service.py

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.project import Projects
from app.schemas.collections import ProjectsCollection
import uuid

class Project_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.projects = self.db.get_collection("Projects")
        self.assigned_slates = self.db.get_collection("Assigned_Slates")

    async def create_project(self, project: Projects) -> Dict[str, str]:
        project_dict = project.model_dump(by_alias=True)
        project_dict["projectId"] = str(uuid.uuid4())
        insert_result = await self.projects.insert_one(project_dict)
        return {"message": "project created successfully", "id": str(insert_result.inserted_id)}

    async def list_projects(self, owner: str) -> ProjectsCollection:
        query = {"owner": owner}
        user_projects = await self.projects.find(query).to_list(10000)
        for form in user_projects:
            form["database_id"] = str(form["_id"])
        return ProjectsCollection(user_projects=user_projects)

    async def delete_project(self, project_id: str, projectName: str, projectOwner: str) -> Dict[str, str]:
        query = {"owner": projectOwner, "project": projectName}
        delete_result = await self.projects.delete_one({"_id": ObjectId(project_id)})
        if delete_result.deleted_count == 1:
            slates2delete = await self.assigned_slates.find(query).to_list(None)
            for slate in slates2delete:
                await self.assigned_slates.delete_one({"_id": slate["_id"]})
            return {"message": "Project and related slates deleted"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")

    async def archive_project(self, project_id: str) -> Dict[str, str]:
        project = await self.projects.find_one({"_id": ObjectId(project_id)})
        if project:
            project["status"] = 'Archived'
            await self.projects.replace_one({"_id": ObjectId(project_id)}, project)
            return {"message": "Project archived successfully"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")

    async def edit_project(self, project_info: Projects) -> Dict[str, str]:
        project = await self.projects.find_one({"_id": ObjectId(project_info.database_id)})
        if project:
            project["database_id"] = project_info.database_id
            project["status"] = project_info.status
            project["owner"] = project_info.owner
            project["address"] = project_info.address
            project["currency"] = project_info.currency
            project["projectName"] = project_info.projectName
            project["projectType"] = project_info.projectType
            project["projectLead"] = project_info.projectLead
            project["estimated_date"] = project_info.estimated_date
            project["completion_date"] = project_info.completion_date
            
            await self.projects.replace_one({"_id": ObjectId(project_info.database_id)}, project)
            return {"message": "Project updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")

  