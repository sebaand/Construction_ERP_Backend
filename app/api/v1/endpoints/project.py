# In your route files (e.g., project.py)
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.project import Projects
from app.schemas.collections import ProjectsCollection
from app.services.project_service import Project_Service
from app.api.deps import get_project_service

router = APIRouter()

@router.post("/", response_model=ProjectsCollection)
async def list_projects(
    owner: str,
    project_service: Project_Service = Depends(get_project_service)
):
    return await project_service.list_projects(owner)

@router.post("/create-project/")
async def create_project(
    project: Projects = Body(...),
    project_service: Project_Service = Depends(get_project_service)
):
    return await project_service.create_project(project)

@router.post("/delete-project/")
async def delete_project(
    project_id: str, 
    projectName: str, 
    projectOwner: str,
    project_service: Project_Service = Depends(get_project_service)
):
    return await project_service.delete_project(project_id, projectName, projectOwner)

@router.post("/archive-project/{project_id}")
async def archive_project(
    project_id: str, 
    project_service: Project_Service = Depends(get_project_service)
):
    return await project_service.archive_project(project_id)

@router.post("/edit-project")
async def edit_project(
    project_info: Projects = Body(...),
    project_service: Project_Service = Depends(get_project_service)
):
    return await project_service.edit_project(project_info)

# ... other routes