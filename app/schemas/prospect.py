from pydantic import BaseModel
from datetime import datetime
from typing import List

class Prospect(BaseModel):
    companyId: str
    projectId: str
    projectName: str
    address: str

class MergedProspect(BaseModel):
    companyId: str
    companyName: str
    projectId: str
    projectName: str
    address: str

class ProspectInfo(BaseModel):
    projectId: str
    projectName: str
    address: str

class ProspectsNamesList(BaseModel):
    owner_org: str
    prospects: List[ProspectInfo]