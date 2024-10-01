from pydantic import BaseModel
from typing import List, Optional, Union, Any, Dict
from datetime import datetime

class TableColumn(BaseModel):
    name: str
    label: str
    dataType: str
    required: Optional[bool] = False

class FormField(BaseModel):
    name: str
    field_type: str
    label: str
    required: Optional[bool] = False
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    columns: Optional[List[TableColumn]] = None

class CreateTemplateModel(BaseModel):
    title: str
    description: str
    owner_org: str
    last_updated: datetime
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]

class SlateTemplateModel(BaseModel):
    database_id: str
    title: str
    description: str
    owner_org: str
    last_updated: datetime
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]

class AssignSlateModel(BaseModel):
    database_id: Optional[str]
    title: str
    projectId: str
    description: str
    due_date: datetime
    assigned_date: datetime
    assignee: str
    owner_org: str
    last_updated: datetime
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]

class SubmitSlateModel(BaseModel):
    assigned_date: datetime
    assignee: str
    data: Dict[str, Any]
    database_id: str
    description: str
    due_date: datetime
    fields: List[FormField]
    last_updated: datetime
    owner_org: str
    title: str
    project: str
    status: bool

class DraftSlateModel(BaseModel):
    assigned_date: datetime
    assignee: str
    data: Dict[str, Any]
    database_id: str
    description: str
    due_date: datetime
    fields: List[FormField]
    last_updated: datetime
    owner_org: str
    title: str
    projectId: str
    status: str

class QuoteSlateModel(BaseModel):
    assigned_date: datetime
    assignee: str
    data: Dict[str, Any]
    database_id: str
    description: str
    due_date: datetime
    fields: List[FormField]
    last_updated: datetime
    owner_org: str
    title: str
    quoteId: str
    status: str