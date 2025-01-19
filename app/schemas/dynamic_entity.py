from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
from enum import Enum

class FieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

class DynamicField(BaseModel):
    field_name: str
    field_type: FieldType
    required: bool = False
    default_value: Optional[Any] = None
    description: Optional[str] = None

class EntitySchema(BaseModel):
    schema_name: str  # e.g., "Project", "Quote"
    fields: Dict[str, DynamicField]
    description: Optional[str] = None

class EntityInstance(BaseModel):
    schema_id: str
    company_id: str
    data: Dict[str, Any]
    relationships: Dict[str, str]  # Store actual relationship IDs

class FieldMapping(BaseModel):
    source_schema: str
    source_field: str
    target_schema: str
    target_field: str
    transformation: Optional[str] = None  # Optional transformation logic

class WorkflowStep(BaseModel):
    step_name: str
    schema_name: str
    required: bool = True
    next_steps: List[str] = []
    field_mappings: List[FieldMapping] = []  # Field mappings for this step

class WorkflowDefinition(BaseModel):
    workflow_name: str
    company_id: str
    steps: Dict[str, WorkflowStep]
    initial_step: str 