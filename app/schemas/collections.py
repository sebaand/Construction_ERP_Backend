from pydantic import BaseModel
from typing import List, Optional
from .slate import SlateTemplateModel, AssignSlateModel, SubmitSlateModel
from .project import Projects
from .user import PlatformUsers
from .company import Company, PricingItem
from .crm import Customer
from .prospect import Prospect, MergedProspect
from .quote import Quote, QuoteSlateModel, QuoteDownloadModel
from .invoice import InvoiceSlateModel, InvoiceDownloadModel

# Projects Collections
class ProjectsCollection(BaseModel):
    user_projects: List[Projects]

# Company Collections
class CompanyDetails(BaseModel):
    details: List[Company]

# Users Collections
class UsersCollection(BaseModel):
    users: List[PlatformUsers]
    premium_key: Optional[str] = None

# Slates Collections
class SlatesCollection(BaseModel):
    slates: List[SubmitSlateModel]

class AssignedSlatesCollection(BaseModel):
    slates: List[AssignSlateModel]

class TemplateCollection(BaseModel):
    forms: List[SlateTemplateModel]

# Pricing Collections
class PricingData(BaseModel):
    owner_org: str
    items: List[PricingItem]

# CRM Collections
class CRM_Data(BaseModel):
    owner_org: str
    items: List[Customer]

# Prospect Collections
class Prospect_Data(BaseModel):
    owner_org: str
    items: List[Prospect]

class MergedProspectData(BaseModel):
    owner_org: str
    items: List[MergedProspect]

# Quote Collections
class Quote_Data(BaseModel):
    owner_org: str
    items: List[Quote]

class Quote_Complete_Data(BaseModel):
    owner_org: str
    items: List[QuoteSlateModel]

class MergedQuoteData(BaseModel):
    owner_org: str
    items: List[QuoteDownloadModel]

# Invoice Collections
class Invoice_Complete_Data(BaseModel):
    owner_org: str
    items: List[InvoiceSlateModel]

class MergedInvoiceData(BaseModel):
    owner_org: str
    items: List[InvoiceDownloadModel]

