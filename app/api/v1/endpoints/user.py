# app/api/v1/endpoints/user.py

from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request
from typing import Optional
from app.schemas.user import PlatformUsers, UserData
from app.schemas.early_bird import EarlyBird
from app.schemas.collections import UsersCollection
from app.services.user_service import User_Service
from app.api.deps import get_user_service

router = APIRouter()

@router.get("/user-profile/{auth0_id}", response_model=Optional[PlatformUsers])
async def get_user_profile(
    auth0_id: str,
    user_service: User_Service = Depends(get_user_service)
):
    return await user_service.get_user_profile(auth0_id)

@router.get("/user-data/", response_model=UserData)
async def get_user_data(
    email: str = Query(...),
    user_service: User_Service = Depends(get_user_service)
):
    return await user_service.get_user_data(email)

@router.put("/early-signon")
async def early_signon(
    user_profile: EarlyBird = Body(...),
    user_service: User_Service = Depends(get_user_service)
):
    return await user_service.early_signon(user_profile)

@router.put("/user-profile")
async def update_user_profile(
    user_profile: PlatformUsers = Body(...),
    user_service: User_Service = Depends(get_user_service)
):
    return await user_service.update_user_profile(user_profile)

@router.post("/register")
async def register_user(
    user_data: dict = Body(...),
    user_service: User_Service = Depends(get_user_service)
):
    return await user_service.register_user(user_data)

@router.post("/login/")
async def login_user(
    user_service: User_Service = Depends(get_user_service)
):
    return await user_service.login_user()

@router.get("/users/", response_model=UsersCollection)
async def list_users(
    user_service: User_Service = Depends(get_user_service)
):
    return await user_service.list_users()

# Add more routes as needed