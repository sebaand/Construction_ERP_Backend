from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserData(BaseModel):
    email: str
    name: Optional[str] = "Not provided"
    organization: Optional[str] = "Not provided"
    marketing_accepted: Optional[bool] = False
    created_at: datetime

class UserRegistration(BaseModel):
    user: UserData