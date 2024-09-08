from pydantic import BaseModel
from datetime import datetime

class OrganizationMetrics(BaseModel):
    owner_org: str
    date: datetime
    project_health: int
    average_overdue: int
    total_slates: int
    overdue_slates: int