from pydantic import BaseModel

class Company(BaseModel):
    owner_org: str
    name: str
    address: str  
    vat: str
    email: str
    telephone: str

class Payment(BaseModel):
    owner_org: str
    bank: str
    bank_address: str
    sort_code: str
    account_number: str
    terms: str

class PricingItem(BaseModel):
    category: str
    vatPercentage: float
    cost: float
    units: str
    currency: str
