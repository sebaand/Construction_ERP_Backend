from pydantic import BaseModel
from typing import Optional, List, Dict

class PlatformUsers(BaseModel):
    database_id: Optional[str]
    name: Optional[str]
    organization: Optional[str]
    organization_id: List[Dict[str, str]] = None
    email: str
    auth0_id: Optional[str]

class UserData(BaseModel):
    is_premium_user: bool
    premium_key: Optional[str] = None