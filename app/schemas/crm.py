from pydantic import BaseModel, Field

class Customer(BaseModel):
    companyId: str = Field(default="")
    name: str
    address: str
    contact: str
    email: str
    phone: str
