from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class InvoiceItem(BaseModel):
    description: str
    hours: float
    price: float
    total: float

class Invoice(BaseModel):
    invoice_number: str
    issue_date: date
    due_date: date
    customer_name: str
    customer_address: str
    company_name: str
    company_address: str
    items: List[InvoiceItem]
    total: float
    payment_terms: str = Field(default="30 days")
    job_name: str
    project_number: str
    created_by: str
    order_number: str
    company_phone: str
    company_email: str
    vat_number: str
    company_number: str
    bank_address: str
    sort_code: str
    account_number: str