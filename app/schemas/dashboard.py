from pydantic import BaseModel
from datetime import datetime

class DashboardItem(BaseModel):
    id: str
    project_name: str
    project_type: str
    slate_name: str
    status: str
    assignee_name: str
    assignee_email: str
    assigned_date: datetime
    due_date: datetime
    description: str
    owner_org: str
    last_updated: datetime

class OrganizationMetrics(BaseModel):
    owner_org: str
    date: datetime
    project_health: int
    average_overdue: int
    total_slates: int
    overdue_slates: int