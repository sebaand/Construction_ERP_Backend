from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Prospect(BaseModel):
    companyId: str
    projectId: str
    projectName: str
    address: str
    