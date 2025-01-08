from fastapi import APIRouter, Depends, HTTPException, Security, Body
from fastapi.security import APIKeyHeader
from typing import Dict
from app.services.email_service import Email_Service
from app.schemas.notification import UserRegistration, UserData
from app.config import settings

router = APIRouter()
api_key_header = APIKeyHeader(name="Authorization")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key.replace("Bearer ", "") != settings.AUTH0_ACTION_API_KEY:
        print("error")
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@router.post("/new-user")
async def notify_new_user(
    # email_data: dict = Body(...),  # Change to dict to accept any JSON data
    email_data: UserRegistration = Body(...),  # Change to dict to accept any JSON data
    api_key: str = Security(verify_api_key),
    email_service: Email_Service = Depends()
):
    user_data = email_data.user
    print('user_data', email_data)
    try:
        await email_service.send_registration_notification(user_data)
        return {"status": "success", "message": "Notification sent"}
    except Exception as e:
        print("Error:", str(e))  # Add this line
        raise HTTPException(status_code=500, detail=str(e))