from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Union, Any, Dict
from datetime import date, datetime
from typing_extensions import Annotated
from bson import ObjectId
import motor.motor_asyncio
from pymongo import ReturnDocument
import os

app = FastAPI()

# MongoDB Database and Collections Declaration
MONGODB_URL = "mongodb+srv://andreasebastio014:{os.getenv('MONGO_DB_PASSWORD')}@cluster0.jqaqs3v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.Forms
form_samples = db.get_collection("Samples")

origins = [
    "http://localhost:3000",
    "localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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
        allowed_types = ["text", "number", "email", "date", "signature", "select", "checkbox", "radio", "dropdown","description", "section_break"]
        if v not in allowed_types:
            raise ValueError(f"field_type must be one of {allowed_types}")
        return v

# # FormModel now contains a list of FormFields and a dictionary for the form data
class CreateFormModel(BaseModel):
    title: str
    description: str
    organization: str
    template: bool
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields

# # FormModel now contains a list of FormFields and a dictionary for the form data
class SubmitFormModel(BaseModel):
    id: str
    title: str
    description: str
    organization: str
    template: bool
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields

class FormsCollection(BaseModel):
    forms: List[SubmitFormModel]

@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your todo list."}

@app.get(
    "/FormData/",
    response_description="List all Form Data",
    response_model=FormsCollection,
    response_model_by_alias=False,
)
async def list_forms(organization: str, email: str, status: str):
    """
    List all of the data in the database that match the given organization and email.
    The response is unpaginated and limited to 1000 results.
    """

    # Convert the status string to a boolean value
    status_bool = status.lower() == 'true'

     # query sets the conditions which it searches for in the forms collection
    query = {"organization": organization, "data.email": email, "status": status_bool}
    forms = await form_samples.find(query).to_list(1000)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(forms):
        form_id = str(form["_id"])
        form["id"] =  form_id # Add the index to the form data

    return FormsCollection(forms=forms)

# POST endpoint to accept and store cleans forms created by an Document Manager
@app.post("/create-form/")
async def submit_form(form: CreateFormModel = Body(...)):
    print('Received Form Data:', form)  # Add this line
    try:
        form_dict = form.model_dump(by_alias=True)  # Convert to dict, respecting field aliases if any
        insert_result = await form_samples.insert_one(form_dict)
        return {"message": "Form data submitted successfully", "id": str(insert_result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PUT endpoint to update the form data
@app.put("/submit-form/{form_id}")
async def update_form(form_id: str, form: SubmitFormModel = Body(...)):
    # print('Received Form Data:', form)
    print('form_id', form_id)
    try:
        # Convert the form data to a dictionary
        form_dict = form.model_dump(by_alias=True)
        
        # Update the form data in the database
        update_result = await form_samples.update_one({"_id": ObjectId(form_id)}, {"$set": form_dict})
        
        if update_result.modified_count == 1:
            return {"message": "Form data updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Form not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
