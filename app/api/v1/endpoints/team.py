from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import List
from bson import ObjectId
from app.schemas.user import PlatformUsers
from app.schemas.collections import UsersCollection
from app.services.mongodb_service import MongoDB_Service
from app.services.team_service import Team_Service
from app.api.deps import get_mongodb_service, get_team_service

router = APIRouter()

@router.get("/", response_model=UsersCollection)
async def list_team_users(
    owner: str = Query(...),
    mongodb_service: MongoDB_Service = Depends(get_mongodb_service)
):
    return await mongodb_service.list_team_users(owner)

@router.put("/add-user/")
async def add_user(
    email: str = Query(...),
    user_fields: dict = Body(...),
    team_service: Team_Service = Depends(get_team_service)
):
    return await team_service.add_user(email, user_fields)


@router.put("/update-team-users/")
async def update_existing_user(
    user_fields: dict = Body(...),
    team_service: Team_Service = Depends(get_team_service)
):
    return await team_service.update_existing_user(user_fields)