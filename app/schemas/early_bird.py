from pydantic import BaseModel
from typing import Optional

class EarlyBird(BaseModel):
    name: Optional[str]
    email: str 
    organization: Optional[str]
    privacyNoticeAccepted: bool
    receiveMarketingCommunication: bool