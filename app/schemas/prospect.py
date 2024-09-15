from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Prospect(BaseModel):
    owner_org: str
    companyId: str
    address: str
    projectName: str
    projectId: str