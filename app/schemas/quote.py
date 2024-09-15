from pydantic import BaseModel

class Quote(BaseModel):
    owner_org: str
    projectId: str  
    name: str
    status: str
