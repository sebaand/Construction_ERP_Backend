# app/api/v1/endpoints/slates.py

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import List
from bson import ObjectId
from app.schemas.slate import CreateSlateModel, AssignSlateModel, SlateTemplateModel, SubmitSlateModel
from app.schemas.collections import TemplateCollection, AssignedSlatesCollection
from app.services.slates_service import SlatesService
from app.api.deps import get_slates_service

router = APIRouter()

@router.get("/FormData/", response_model=TemplateCollection)
async def list_forms(
    owner_org: str,
    status: bool,
    slates_service: SlatesService = Depends(get_slates_service)
):
    return await slates_service.list_forms(owner_org, status)

@router.get("/user-slates/", response_model=AssignedSlatesCollection)
async def list_user_slates(
    assignee: str,
    status: bool,
    slates_service: SlatesService = Depends(get_slates_service)
):
    return await slates_service.list_user_slates(assignee, status)

@router.post("/create-slate/")
async def create_slate(
    slate: CreateSlateModel = Body(...),
    slates_service: SlatesService = Depends(get_slates_service)
):
    return await slates_service.create_slate(slate)

@router.post("/assign-slate/")
async def assign_slate(
    slate: AssignSlateModel = Body(...),
    slates_service: SlatesService = Depends(get_slates_service)
):
    return await slates_service.assign_slate(slate)

@router.put("/submit-slate/{form_id}")
async def update_slate(
    form_id: str,
    slate_data: dict = Body(...),
    slates_service: SlatesService = Depends(get_slates_service)
):
    return await slates_service.update_slate(form_id, slate_data)

@router.put("/update-slate/{template_id}")
async def update_slate_template(
    template_id: str,
    slate: CreateSlateModel = Body(...),
    slates_service: SlatesService = Depends(get_slates_service)
):
    return await slates_service.update_slate_template(template_id, slate)

@router.delete("/delete-slate/{slate_id}")
async def delete_slate_template(
    slate_id: str,
    slates_service: SlatesService = Depends(get_slates_service)
):
    return await slates_service.delete_slate_template(slate_id)

@router.get("/org-slates/", response_model=AssignedSlatesCollection)
async def list_org_slates(
    owner_org: str,
    slates_service: SlatesService = Depends(get_slates_service)
):
    return await slates_service.list_org_slates(owner_org)

# Add more routes as needed