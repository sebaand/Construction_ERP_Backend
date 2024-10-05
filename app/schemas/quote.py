from pydantic import BaseModel
from typing import List, Optional, Union, Any, Dict
from datetime import datetime
from app.schemas.slate import FormField

class Quote(BaseModel):
    quoteId: str
    companyId: str  
    projectId: str  
    name: str
    status: str

class QuoteSlateModel(BaseModel):
    name: str
    assigned_date: datetime
    assignee: str
    data: Dict[str, Any]
    database_id: str
    description: str
    due_date: datetime
    fields: List[FormField]
    last_updated: datetime
    title: str
    quoteId: str
    projectId: str
    companyId: str  
    status: str

# class MergedQuote(BaseModel):
#     quoteId: str
#     companyId: str
#     companyName: str
#     projectId: str  
#     address: str
#     projectName: str 
#     name: str
#     status: str
class MergedQuote(BaseModel):
    assigned_date: datetime
    assignee: str
    data: Dict[str, Any]
    database_id: str
    description: str
    due_date: datetime
    fields: List[FormField]
    last_updated: datetime
    title: str
    name: str
    quoteId: str
    projectId: str
    companyId: str  
    status: str
    companyName: str
    address: str
    projectName: str 
    
