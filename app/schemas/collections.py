from pydantic import BaseModel
from typing import List, Optional
from .slate import SlateTemplateModel, AssignSlateModel, SubmitSlateModel
from .project import Projects
from .user import PlatformUsers
from .company import Company, PricingItem
from .crm import Customer
from .prospect import Prospect

class TemplateCollection(BaseModel):
    forms: List[SlateTemplateModel]

class ProjectsCollection(BaseModel):
    user_projects: List[Projects]

class AssignedSlatesCollection(BaseModel):
    slates: List[AssignSlateModel]

class CompanyDetails(BaseModel):
    details: List[Company]

class UsersCollection(BaseModel):
    users: List[PlatformUsers]
    premium_key: Optional[str] = None

class SlatesCollection(BaseModel):
    slates: List[SubmitSlateModel]

class PricingData(BaseModel):
    owner_org: str
    items: List[PricingItem]

class CRM_Data(BaseModel):
    owner_org: str
    items: List[Customer]

class Prospect_Data(BaseModel):
    owner_org: str
    items: List[Prospect]