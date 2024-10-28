from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any, Dict
from datetime import datetime
from app.schemas.slate import FormField

class LineItem(BaseModel):
    lineItem: str
    quantity: float
    units: str
    pricePerUnit: float

class InvoiceSlateModel(BaseModel):
    name: str
    work_description: Optional[str] = Field(default="")
    creator: Optional[str] = Field(default="")
    last_updated: datetime
    invoiceId: str
    quoteId: str
    projectId: str
    companyId: str  
    status: str
    terms: str
    issue_date: datetime
    cis_reversal: bool
    invoiceTotal: float
    lineItems: List[LineItem]

    class Config:
        schema_extra = {
            "example": {
                "name": "Facade Cleaning",
                "creator": "john.doe@sitesteerai.com",
                "last_updated": "2024-10-31T12:00:00",
                "invoiceId": "777e4567-e89b-12d3-a456-6000000000",
                "quoteId": "123e4567-e89b-12d3-a456-426614174000",
                "projectId": "570b908e-7347-4192-b95d-7e7f80adb397",
                "companyId": "46fa2e62-da31-4b56-af82-463c1661b02c",
                "status": "Paid",
                "terms": "30 Days",
                "issue_date": "2024-10-31T00:00:00",
                "quote_number": "1",
                "invoice_number": "1234",
                "order_number": "123456",
                "invoiceTotal": "5055.89",
                "lineItems": [
                    {
                        "lineItem": "Labour",
                        "quantity": 10,
                        "units": "/ hour",
                        "pricePerUnit": 100
                    },
                    {
                        "lineItem": "Material",
                        "quantity": 1,
                        "units": "/ project",
                        "pricePerUnit": 6000
                    }
                ]
            }
        }
    
class InvoiceDownloadModel(BaseModel):
    name: str
    creator: Optional[str] = Field(default="")
    work_description: str
    last_updated: datetime
    invoiceId: str
    quoteId: str
    projectId: str
    companyId: str  
    status: str
    terms: str
    issue_date: datetime
    quote_number: Optional[str] = Field(default="")
    order_number: Optional[str] = Field(default="")
    cis_reversal: bool
    invoiceTotal: float
    lineItems: List[LineItem]
    projectName: str
    companyName: str
    company_address: str
    site_address: str
    invoice_address: str
    telephone: str
    vat_number: str
    company_number: str
    bank: str
    bank_address: str
    sort_code: str
    account_number: str