from pydantic import BaseModel
from typing import List

class Customer(BaseModel):
    companyId: str
    customer_name: str
    customer_address: str
    contact: str
    email: str
    telephone: str
    vat_number: str
    company_number: str

class CustomerInfo(BaseModel):
    companyId: str
    customer_name: str
    customer_address: str
    vat_number: str
    company_number: str
    telephone: str

class CustomerNamesList(BaseModel):
    owner_org: str
    customers: List[CustomerInfo]

class CustomerList(BaseModel):
    owner_org: str
    customers: List[Customer]
