from fastapi import FastAPI, HTTPException, Body, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Union, Any, Dict
from datetime import date, datetime
from typing_extensions import Annotated
from bson import ObjectId
import motor.motor_asyncio
import os

# imports for pdf generation
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

app = FastAPI()

# MongoDB Database and Collections Declaration
MONGODB_URL = f"mongodb+srv://andreasebastio014:{os.getenv('MONGO_DB_PASSWORD')}@cluster0.jqaqs3v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.Forms
form_samples = db.get_collection("Samples")
users = db.get_collection("Users")
assigned_slates = db.get_collection("Assigned_Slates")
early_birds = db.get_collection("Early_Birds")
templates = db.get_collection("Templates")
projects = db.get_collection("Projects")

# Origins for local deployment during development stage. 
origins = [
    "http://localhost:3000",
    "localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=['https://polyglotplus.com', 'https://www.polyglotplus.com'],
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Class for defining the model of the key data on the users
class Projects(BaseModel):
    owner: str
    address: str
    currency: str
    projectName: str
    projectType: str  
    projectLead: str


# Class for defining the model of the key data on the users
class PlatformUsers(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    organization: Optional[str]
    email: str  
    auth0_id: str
    subscription_tier: str


# Class for defining the model of the key data on an early_bird adoption
class EarlyBird(BaseModel):
    name: Optional[str]
    email: str 
    organization: Optional[str]
    privacyNoticeAccepted: bool
    receiveMarketingCommunication: bool


# Class for defining the datamodel for the table columns
class TableColumn(BaseModel):
    name: str  # Unique identifier for the column
    label: str  # Display label for the column
    dataType: str  # Data type of the column (e.g., 'text', 'number', 'date', etc.)
    required: Optional[bool] = False

    @validator('dataType')
    def validate_data_type(cls, v):
        allowed_types = ["text", "number", "decimal", "date", "signature", "colour"]
        if v not in allowed_types:
            raise ValueError(f"dataType must be one of {allowed_types}")
        return v


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
    columns: Optional[List[TableColumn]] = None  # List of columns for table fields

    @validator('field_type')
    def validate_field_type(cls, v):
        allowed_types = ["text", "number", "decimal", "email", "date", "signature","table","table-column","select", "checkbox", "radio", "dropdown","description", "section_break"]
        if v not in allowed_types:
            raise ValueError(f"field_type must be one of {allowed_types}")
        return v


# # FormModel now contains a list of Slate Fields and a dictionary for the form data
class CreateSlateModel(BaseModel):
    title: str
    description: str
    owner: str
    last_updated: datetime
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields


# # FormModel now contains a list of Slate Fields and a dictionary for the form data
class AssignSlateModel(BaseModel):
    title: str
    project: str
    description: str
    due_date: datetime
    owner: str
    last_updated: datetime
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields


# # SubmitSlateModel defines the model structure for the slates once they're assigned to a user
class SubmitSlateModel(BaseModel):
    id: str
    title: str
    description: str
    project: str
    owner: str
    last_updated: datetime
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields


class TemplateCollection(BaseModel):
    forms: List[CreateSlateModel]


class ProjectsCollection(BaseModel):
    user_projects: List[Projects]


class AssignedSlatesCollection(BaseModel):
    slates: List[AssignSlateModel]


class SlatesCollection(BaseModel):
    slates: List[SubmitSlateModel]



@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome!."}



# Route for geting for getting the logged in user's profile
@app.get("/user-profile/{auth0_id}", response_model=Optional[PlatformUsers])
async def get_user_profile(auth0_id: str):
    try:
        user = await users.find_one({"auth0_id": auth0_id})
        print("User:", user)
        if user:
            return PlatformUsers(**user)
        else:
            print(f"User with auth0_id '{auth0_id}' not found")
            return None
    except Exception as e:
        print(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


# Route for geting for getting the template form's
@app.get(
    "/FormData/",
    response_description="List all Form Data",
    response_model=TemplateCollection,
    response_model_by_alias=False,
)
async def list_forms(owner: str, status: str):
    """
    List all of the data in the database that match the given organization and email.
    The response is unpaginated and limited to 1000 results.
    """

    # Convert the status string to a boolean value
    status_bool = status.lower() == 'true'
    
     # query sets the conditions which it searches for in the forms collection
    query = {"owner": owner, "status": status_bool}
    forms = await templates.find(query).to_list(10000)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(forms):
        form_id = str(form["_id"])
        form["id"] =  form_id # Add the index to the form data

    return TemplateCollection(forms=forms)



# Route for geting for getting the user's projects
@app.get(
    "/Projects/",
    response_description="List all projects",
    response_model=ProjectsCollection,
    response_model_by_alias=False,
)
async def list_projects(owner: str):
    
     # query sets the conditions which it searches for in the forms collection
    query = {"owner": owner}
    user_projects = await projects.find(query).to_list(10000)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(user_projects):
        form_id = str(form["_id"])
        form["id"] =  form_id # Add the index to the form data

    return ProjectsCollection(user_projects=user_projects)



# Route for geting for getting the slates assigned on a project
@app.get(
    "/user-slates/",
    response_description="List all project slates",
    response_model=SlatesCollection,
    response_model_by_alias=False,
)
async def list_slates(owner: str, status: bool):
    
    # query sets the conditions which it searches for in the forms collection
    query = {"owner": owner, "status": status}
    slates = await assigned_slates.find(query).to_list(10000)
    # print(query)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(slates):
        form_id = str(form["_id"])
        form["id"] =  form_id # Add the index to the form data
    print("slates:")
    print(slates)
    return SlatesCollection(slates=slates)



# Route for geting for getting the slates assigned on a project
@app.get(
    "/project-slates/",
    response_description="List all project slates",
    response_model=AssignedSlatesCollection,
    response_model_by_alias=False,
)
async def list_slates(project: str, owner: str):
# async def list_slates(owner: str):
    
    # query sets the conditions which it searches for in the forms collection
    query = {"project": project, "owner": owner}
    # query = {"owner": owner}
    slates = await assigned_slates.find(query).to_list(10000)
    # print(query)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(slates):
        form_id = str(form["_id"])
        form["id"] =  form_id # Add the index to the form data

    return AssignedSlatesCollection(slates=slates)


# Route for generating pdfs from the available form data. 
@app.get("/download-pdf/{form_id}")
async def download_pdf(form_id: str):
    form_data = await get_form_data(form_id)  # Implement this function to fetch form data from DB
    if not form_data:
        raise HTTPException(status_code=404, detail="Form not found")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.drawString(100, height - 100, f"Form Title: {form_data['title']}")
    c.drawString(100, height - 120, f"Assignee: {form_data['assignee']}")
    c.drawString(100, height - 140, f"Due Date: {form_data['due_date']}")
    # Add more fields as needed

    c.save()
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment;filename={form_data['title']}.pdf"})

# POST endpoint to accept and store cleans forms created by an Document Manager
@app.post("/create-slate/")
# async def submit_form(form: CreateFormModel = Body(...)): # FastAPI will automatically parse the JSON request body &- create an instance of the CreateFormModel class
async def submit_form(form: CreateSlateModel = Body(...)): # FastAPI will automatically parse the JSON request body &- create an instance of the CreateFormModel class
    print('Received Form Data:', form)  # Add this line
    try:
        form_dict = form.model_dump(by_alias=True)  # Convert to dict, respecting field aliases if any
        insert_result = await templates.insert_one(form_dict)
        return {"message": "Form data submitted successfully", "id": str(insert_result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# POST endpoint to accept and store cleans forms created by an Document Manager
@app.post("/create-project/")
async def create_project(project: Projects = Body(...)):
    print('Received Form Data:', project)  # Add this line
    try:
        project_dict = project.model_dump(by_alias=True)  # Convert to dict, respecting field aliases if any
        insert_result = await projects.insert_one(project_dict)
        return {"message": "project created successfully", "id": str(insert_result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# POST endpoint to first assign slates to users
@app.post("/assign-slate/")
async def assign_slate(slate: AssignSlateModel = Body(...)):
    try:
        slate_dict = slate.model_dump(by_alias=True)  # Convert to dict, respecting field aliases if any
        insert_result = await assigned_slates.insert_one(slate_dict)
        return {"message": "slate successfully assigned", "id": str(insert_result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# PUT endpoint to update the form data
@app.put("/submit-form/{form_id}")
async def update_form(form_id: str, slate: SubmitSlateModel = Body(...)):
    # print('Received Form Data:', form)
    print('form_id', form_id)
    try:
        # Convert the form data to a dictionary
        slate_dict = slate.model_dump(by_alias=True)
        
        # Update the form data in the database
        update_result = await assigned_slates.update_one({"_id": ObjectId(form_id)}, {"$set": slate_dict})
        
        if update_result.modified_count == 1:
            return {"message": "Form data updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Form not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# # Route for adding an early bird request to the database  
@app.put("/early-signon/")
async def update_user_profile(user_profile: EarlyBird = Body(...)):
    try:
        # Add the user to the early_bird database
        result = await early_birds.insert_one(user_profile.model_dump(by_alias=True))
        return {"message": "Early bird request added to database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding early bird request to database: {str(e)}")



# Route for updating the user profile  
@app.put("/user-profile/")
async def update_user_profile(user_profile: PlatformUsers = Body(...)):
    user = await users.find_one({"auth0_id": user_profile.auth0_id})
    print("user: ", user)
    print("user_profile: ", user_profile.first_name)
    try:
        # Find the user in the database by auth0_id
        user = await users.find_one({"auth0_id": user_profile.auth0_id})
        if user:
            # Update the user's profile fields
            user["first_name"] = user_profile.first_name
            user["last_name"] = user_profile.last_name
            user["organization"] = user_profile.organization
            user["email"] = user_profile.email

            # Update the user in the database
            await users.replace_one({"auth0_id": user_profile.auth0_id}, user)
            return {"message": "User profile updated successfully"}
        else:
            # Create a new user profile
            new_user = {
                "first_name": user_profile.first_name,
                "last_name": user_profile.last_name,
                "organization": user_profile.organization,
                "email": user_profile.email,
                "auth0_id": user_profile.auth0_id
            }
            await users.insert_one(new_user)
            return {"message": "User profile created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Route for updating the user profile  
@app.post("/register/")
async def register_user(request: Request):
    user_profile = await request.json()
    try:
        # Update the user's profile fields
        # Create a new user profile
        new_user = {
            # "email": user_profile.email,
            # "auth0_id": user_profile.auth0_id,
            # "subscription_tier": user_profile.subscription_tier
            "email": user_profile["email"],
            "auth0_id": user_profile["auth0_id"],
            # "subscription_tier": user_profile["subscription_tier"],
            "subscription_tier": "basic""
        }
        await users.insert_one(new_user)
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Route for updating the user profile  
@app.post("/login/")
async def login_user():
    try:
        print("logged in!")
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/project-slates/")
# async def debug_query(project: Optional[str] = Query(None), owner: Optional[str] = Query(None)):
# # async def debug_query(project: Optional[str] = Query(None), owner: Optional[str] = Query(None)):
#     query = {"project": project, "owner": owner}
#     print('Query:', query)
#     return query



# @app.post("/assign-slate/")
# async def assign_slate(request: Request, slate: AssignSlateModel = Body(...)):
#     try:
#         # Print the received data
#         print('Received data:', await request.json())
#         print('Received model data:', slate.model_dump())
#         slate_dict = slate.model_dump(by_alias=True)
#         insert_result = await assigned_slates.insert_one(slate_dict)
#         return {"message": "slate successfully assigned", "id": str(insert_result.inserted_id)}
#     except Exception as e:
#         print('Error:', str(e))
#         raise HTTPException(status_code=500, detail=str(e))