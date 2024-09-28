from pydantic import BaseModel

class Quote(BaseModel):
    quoteId: str
    companyId: str  
    projectId: str  
    name: str
    status: str

class MergedQuote(BaseModel):
    quoteId: str
    companyId: str
    companyName: str
    projectId: str  
    address: str
    projectName: str 
    name: str
    status: str
