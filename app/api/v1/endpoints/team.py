from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import List
from bson import ObjectId
from app.schemas.user import PlatformUsers
from app.schemas.collections import UsersCollection
from app.services.mongodb_service import MongoDBService
from app.api.deps import get_mongodb_service

router = APIRouter()

@router.get("/", response_model=UsersCollection)
async def list_team_users(
    owner: str = Query(...),
    mongodb_service: MongoDBService = Depends(get_mongodb_service)
):
    return await mongodb_service.list_team_users(owner)

@router.put("/{email}")
async def add_user(
    email: str,
    user_fields: dict = Body(...),
    mongodb_service: MongoDBService = Depends(get_mongodb_service)
):
    return await mongodb_service.add_user(email, user_fields)

@router.put("/update/{email}")
async def update_team_users(
    email: str,
    updated_fields: dict = Body(...),
    mongodb_service: MongoDBService = Depends(get_mongodb_service)
):
    return await mongodb_service.update_team_user(email, updated_fields)

@router.post("/delete/{premium_key}")
async def remove_team_users(
    premium_key: str,
    database_ids: List[str] = Body(...),
    mongodb_service: MongoDBService = Depends(get_mongodb_service)
):
    return await mongodb_service.remove_team_users(database_ids, premium_key)