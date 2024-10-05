from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Prospect(BaseModel):
    companyId: str
    projectId: str
    projectName: str
    site_address: str
    status: Optional[str]

class MergedProspect(BaseModel):
    companyId: str
    projectId: str
    projectName: str
    site_address: str
    status: Optional[str]
    companyName: str
    company_address: str
    telephone: str
    vat_nm: str
    company_nm: str

class ProspectInfo(BaseModel):
    projectId: str
    projectName: str
    site_address: str

class ProspectsNamesList(BaseModel):
    owner_org: str
    prospects: List[ProspectInfo]