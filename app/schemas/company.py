from pydantic import BaseModel

class Company(BaseModel):
    owner_org: str
    name: str
    address: str  
    vat: str
    email: str
    telephone: str