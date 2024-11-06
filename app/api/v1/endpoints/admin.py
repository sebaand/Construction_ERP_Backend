from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import List
from bson import ObjectId
from app.schemas.user import PlatformUsers
from app.schemas.collections import UsersCollection
from app.services.mongodb_service import MongoDB_Service
from app.api.deps import get_mongodb_service

router = APIRouter()

@router.get("/", response_model=UsersCollection)
async def list_team_users(
    owner: str = Query(...),
    mongodb_service: MongoDB_Service = Depends(get_mongodb_service)
):
    return await mongodb_service.list_team_users(owner)