from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Projects(BaseModel):
    database_id: str
    owner: str
    address: str
    currency: str
    status: str
    projectName: str
    projectId: str
    projectType: str  
    projectLead: str
    estimated_date: datetime
    completion_date: Optional[datetime]