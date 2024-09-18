from pydantic import BaseModel
from typing import List

class Customer(BaseModel):
    companyId: str
    name: str
    address: str
    contact: str
    email: str
    phone: str

class CustomerInfo(BaseModel):
    companyId: str
    name: str

class CustomerNamesList(BaseModel):
    owner_org: str
    customers: List[CustomerInfo]
