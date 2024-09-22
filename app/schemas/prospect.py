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

class CustomerInfo(BaseModel):
    companyId: str
    name: str

class CustomerNamesList(BaseModel):
    owner_org: str
    customers: List[CustomerInfo]