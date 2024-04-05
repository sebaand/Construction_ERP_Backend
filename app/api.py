from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Union, Any, Dict
from datetime import date, datetime
from typing_extensions import Annotated
from bson import ObjectId
import motor.motor_asyncio
from pymongo import ReturnDocument


app = FastAPI()

MONGODB_URL = "mongodb+srv://andreasebastio014:testpass@cluster0.jqaqs3v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.Forms
form_samples = db.get_collection("Samples")

origins = [
    "http://localhost:3000",
    "localhost:3000"
]

# FormField now only holds metadata about each form field
class FormField(BaseModel):
    name: str  # Unique identifier for the field, used as the key in the form data
    field_type: str  # Could be 'text', 'number', 'date', 'signature', etc.
    label: str  # Display label for the field
    required: Optional[bool] = False
    placeholder: Optional[str] = None  # Placeholder text for text fields
    options: Optional[List[str]] = None  # List of options for select/radio fields
    min_length: Optional[int] = None  # Minimum length for text fields
    max_length: Optional[int] = None  # Maximum length for text fields
    min_value: Optional[Union[int, float]] = None  # Min value for number fields
    max_value: Optional[Union[int, float]] = None  # Max value for number fields
    # ...additional field attributes based on type

    @validator('field_type')
    def validate_field_type(cls, v):
        allowed_types = ["text", "number", "email", "date", "signature", "select", "checkbox", "radio"]
        if v not in allowed_types:
            raise ValueError(f"field_type must be one of {allowed_types}")
        return v

# FormModel now contains a list of FormFields and a dictionary for the form data
class FormModel(BaseModel):
    title: str
    description: str = ""
    fields: List[FormField]
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields


class FormsCollection(BaseModel):
    """
    A container holding a list of `StudentModel` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """

    forms: List[FormModel]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your todo list."}

@app.get(
    "/FormData/",
    response_description="List all Form Data",
    response_model=FormsCollection,
    response_model_by_alias=False,
)
async def list_forms():
    """
    List all of the student data in the database.

    The response is unpaginated and limited to 1000 results.
    """
    temp = FormsCollection(forms=await form_samples.find().to_list(1000))
    print(temp)
    return FormsCollection(forms=await form_samples.find().to_list(1000))


# POST endpoint to accept and store form data
@app.post("/submit-form/")
async def submit_form(form: FormModel = Body(...)):
    try:
        form_dict = form.model_dump(by_alias=True)  # Convert to dict, respecting field aliases if any
        insert_result = await form_samples.insert_one(form_dict)
        return {"message": "Form data submitted successfully", "id": str(insert_result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # Obsolete Code # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# # # If the Form is pre-defined an approach like this works:
# class FormField(BaseModel):
#     type: str  # The type of the field (text, number, date, checkbox, signature, etc.)
#     label: str  # Human-readable label for the field
#     value: Optional[Union[str, int, List[str], datetime]] = None  # The value of the field
#     required: bool = False  # Whether the field is required

# class FormModel(BaseModel):
#     id: str  # Unique identifier for the form
#     name: Optional[str] = None
#     date: Optional[datetime] = None
#     email: Optional[EmailStr] = None
#     address: Optional[str] = None
#     job_status: Optional[str] = None  # Could also be an Enum if you have predefined statuses
#     trades: Optional[List[str]] = Field(default=None, example=["electrical", "plumbing"])
#     column1: Optional[str] = None  # Custom text field
#     column2: Optional[str] = None  # Custom text field
#     column3: Optional[str] = None  # Custom text field (or number if these are always numeric)
#     column4: Optional[str] = None  # Custom text field
#     column5: Optional[str] = None  # Custom text field (or number if these are always numeric)
#     signature: Optional[str] = None  # Base64 encoded image or some string representation
#     # ... other form fields as required

#     class Config:
#         schema_extra = {
#             "example": {
#                 "id": "1",
#                 "name": "",
#                 "date": "2024-03-11T00:00:00",
#                 "email": "test@email.com",
#                 "address": "Test Avenue 100, UK, M201DX",
#                 "job_status": "completed",
#                 "trades": ["electrical", "plumbing"],
#                 "column1": "Mechanical motor and electrical switch failure. Substituting broken pieces.",
#                 "column2": "RAMS must be sent to owner",
#                 "column3": "3",
#                 "signature": "Bobby Lee"
#             }
#         }

# @app.get("/FormData", tags=["formdata"])
# async def get_formdata() -> dict:
#     return { "data": formdata }