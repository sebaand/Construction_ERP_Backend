from fastapi import FastAPI, HTTPException, Body, Request, Query, Response, File
from starlette.datastructures import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Union, Any, Dict
from datetime import datetime, timedelta
from typing_extensions import Annotated
from bson import ObjectId
import motor.motor_asyncio
import boto3
from botocore.exceptions import NoCredentialsError
from botocore.exceptions import ClientError
import os
import uuid
from io import BytesIO 
import traceback
import logging

# imports for the scheduling of the background calculations
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# imports for Auth0 roles:
import json
import requests
from jose import jwt


# imports for pdf generation
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Flowable
from reportlab.lib.colors import black, HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from app.utils.pdf_config import PDF_STYLE
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect
import base64

# Register a cursive font (you'll need to download and place the font file in your project)
pdfmetrics.registerFont(TTFont('Cursive', 'DancingScript-VariableFont_wght.ttf'))

class CustomCheckbox(Flowable):
    def __init__(self, checked=False):
        Flowable.__init__(self)
        self.checked = checked
        self.size = 4*mm

    def draw(self):
        self.canv.saveState()
        self.canv.setLineWidth(0.5)
        self.canv.rect(0, 0, self.size, self.size)
        if self.checked:
            self.canv.line(1, 1, self.size-1, self.size-1)
            self.canv.line(1, self.size-1, self.size-1, 1)
        self.canv.restoreState()

class HorizontalLine(Flowable):
    def __init__(self, width):
        Flowable.__init__(self)
        self.width = width

    def draw(self):
        self.canv.setStrokeColor(black)
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 0, self.width, 0)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



# Specify the directory to save images
UPLOAD_DIRECTORY = "uploaded_images"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

app = FastAPI()

# Your Auth0 M2M application's client ID, client secret and domain
AUTH0_CLIENT_ID = os.getenv('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = os.getenv('AUTH0_CLIENT_SECRET')
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')

# MongoDB Database and Collections Declaration
MONGODB_URL = f"mongodb+srv://andreasebastio014:{os.getenv('MONGO_DB_PASSWORD')}@cluster0.jqaqs3v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.Forms
form_samples = db.get_collection("Samples")
platform_users = db.get_collection("Users")
assigned_slates = db.get_collection("Assigned_Slates")
early_birds = db.get_collection("Early_Birds")
templates = db.get_collection("Templates")
company_details = db.get_collection("Company_Details")
projects = db.get_collection("Projects")
org_metrics = db.get_collection("OrganizationMetrics")


# Configure Digital Ocean Spaces credentials
DO_SPACE_REGION = os.getenv('DO_SPACE_REGION')
DO_SPACE_NAME = os.getenv('DO_SPACE_NAME')
DO_ACCESS_KEY = os.getenv('DO_ACCESS_KEY')
DO_SECRET_KEY = os.getenv('DO_SECRET_KEY')
DO_ENDPOINT_URL = os.getenv('DO_ENDPOINT_URL')

spaces_client = boto3.client('s3',
    region_name=DO_SPACE_REGION,
    endpoint_url=DO_ENDPOINT_URL,
    aws_access_key_id=DO_ACCESS_KEY,
    aws_secret_access_key=DO_SECRET_KEY
)

# Origins for local deployment during development stage. 
origins = [
    "https://localhost:3000",
    "localhost:3000", 
    "https://www.sitesteer.ai", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Definition for the organization level KPIs that get calculated
class OrganizationMetrics(BaseModel):
    owner_org: str
    date: datetime
    project_health: int
    average_overdue: int
    total_slates: int
    overdue_slates: int  


# Definition for the organization level KPIs that get calculated
class Company(BaseModel):
    owner_org: str
    name: str
    address: str  
    vat: str
    email: str
    telephone: str
    


# Class for defining the model of the key data on the users
class Projects(BaseModel):
    database_id: str
    owner: str
    address: str
    currency: str
    status: str
    projectName: str
    projectId: str
    projectType: str  
    projectLead: str
    estimated_date: datetime
    completion_date: Optional[datetime]


class PlatformUsers(BaseModel):
    database_id: Optional[str]
    name: Optional[str]
    organization: Optional[str]
    organization_id: List[Dict[str, str]] = None
    email: str
    auth0_id: Optional[str]


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


# # FormModel now contains a list of Slate Fields and a dictionary for the form data
class CreateSlateModel(BaseModel):
    title: str
    description: str
    owner_org: str
    last_updated: datetime
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields


# # FormModel now contains a list of Slate Fields and a dictionary for the form data
class SlateTemplateModel(BaseModel):
    database_id: str
    title: str
    description: str
    owner_org: str
    last_updated: datetime
    status: bool
    fields: List[FormField]
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields


# # FormModel now contains a list of Slate Fields and a dictionary for the form data
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
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields


# # SubmitSlateModel defines the model structure for the slates once they're assigned to a user
class SubmitSlateModel(BaseModel):
    assigned_date: datetime
    assignee: str
    data: Dict[str, Any]  # Holds the dynamic values for each field named by 'name' in FormFields
    database_id: str
    description: str
    due_date: datetime
    fields: List[FormField]
    last_updated: datetime
    owner_org: str
    title: str
    project: str
    status: bool

# Definition for the data that get's lumped from the Assigned_Slates, Users and Projects collections and sent as a bulk to the dashboard.
class DashboardItem(BaseModel):
    id: str
    project_name: str
    project_type: str
    slate_name: str
    status: str
    assignee_name: str
    assignee_email: str
    assigned_date: datetime
    due_date: datetime
    description: str
    owner_org: str
    last_updated: datetime      


class TemplateCollection(BaseModel):
    forms: List[SlateTemplateModel]


class ProjectsCollection(BaseModel):
    user_projects: List[Projects]


class AssignedSlatesCollection(BaseModel):
    slates: List[AssignSlateModel]

class CompanyDetails(BaseModel):
    details: List[Company]

class UsersCollection(BaseModel):
    users: List[PlatformUsers]
    premium_key: Optional[str] = None


class SlatesCollection(BaseModel):
    slates: List[SubmitSlateModel]


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome!."}


# # # # # # # # # # # # # # # # # # Retrieve User Data Routes # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


# Route for geting for getting the logged in user's profile
@app.get("/user-profile/{auth0_id}", response_model=Optional[PlatformUsers])
async def get_user_profile(auth0_id: str):
    try:
        user = await platform_users.find_one({"auth0_id": auth0_id})
        print("User:", user)
        if user:
            return PlatformUsers(**user)
        else:
            print(f"User with auth0_id '{auth0_id}' not found")
            return None
    except Exception as e:
        print(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

class UserData(BaseModel):
    is_premium_user: bool
    premium_key: Optional[str] = None


@app.get("/user-data/", response_model=UserData)
async def get_user_data(email: str = Query(...)):
    # Find the user document in the platform_users collection based on the email
    user = await platform_users.find_one({"email": email})
    print('email: ',email)
    print('user: ',user)
    if user:
        # Retrieve the organization_id list of the user
        user_org_ids = user["organization_id"]

        # Find the organization_id key for which the value is "Premium User"
        premium_org_id = None
        for org_id_dict in user_org_ids:
            for key, value in org_id_dict.items():
                if value == "Premium User":
                    premium_org_id = key
                    break
            if premium_org_id:
                break
        print(premium_org_id)
        if premium_org_id:
            # If the user has a "Premium User" value, return True and the corresponding key
            return UserData(is_premium_user=True, premium_key=premium_org_id)
        else:
            # If the user doesn't have a "Premium User" value, return False and None for the key
            return UserData(is_premium_user=False)
    else:
        # If the user is not found, return False and None for the key
        return UserData(is_premium_user=False)
    

# # # # # # # # # # # # # # # # # # Slate Related Routes # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


# Route for geting for getting the template form's
@app.get(
    "/FormData/",
    response_description="List all slates",
    response_model=TemplateCollection,
    response_model_by_alias=False,
)
async def list_forms(owner_org: str, status: str):
    """
    List all of the data in the database that match the given organization and email.
    The response is unpaginated and limited to 1000 results.
    """

    # Convert the status string to a boolean value
    status_bool = status.lower() == 'true'
    
     # query sets the conditions which it searches for in the forms collection
    query = {"owner_org": owner_org, "status": status_bool}
    forms = await templates.find(query).to_list(10000)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(forms):
        form_id = str(form["_id"])
        form["database_id"] =  form_id # Add the index to the form data

    print(forms)
    return TemplateCollection(forms=forms)



# Route for geting for getting the slates assigned on a project
@app.get(
    "/user-slates/",
    response_description="List all project slates",
    response_model=AssignedSlatesCollection,
    response_model_by_alias=False,
)
async def list_slates(assignee: str, status: bool):
    
    # query sets the conditions which it searches for in the forms collection
    query = {"assignee": assignee, "status": status}
    slates = await assigned_slates.find(query).to_list(10000)
    # print(query)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(slates):
        form_id = str(form["_id"])
        form["database_id"] =  form_id # Add the index to the form data
    print("slates:")
    print(slates)
    return AssignedSlatesCollection(slates=slates)



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



# POST endpoint to first assign slates to users
@app.post("/assign-slate/")
async def assign_slate(slate: AssignSlateModel = Body(...)):
    try:
        slate_dict = slate.model_dump(by_alias=True)  # Convert to dict, respecting field aliases if any
        insert_result = await assigned_slates.insert_one(slate_dict)
        return {"message": "slate successfully assigned", "id": str(insert_result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.put("/submit-slate/{form_id}")
async def update_form(request: Request, form_id: str):
    try:
        form = await request.form()
        print("Raw form data:", form)

        if 'json' not in form:
            return JSONResponse(status_code=400, content={"error": "Missing 'json' key in form data"})

        raw_json = form['json']
        print("Raw JSON string:", raw_json)

        try:
            json_data = json.loads(raw_json)
        except json.JSONDecodeError as json_error:
            return JSONResponse(status_code=400, content={"error": f"Invalid JSON data: {str(json_error)}"})

        print("Parsed JSON data:", json_data)

        # Process files
        files = form.getlist("files")
        print('files:', files)
        filename_mapping = {}
        for file in files:
            print(1)
            if isinstance(file, UploadFile):
                print(2)
                try:
                    contents = await file.read()
                    if contents:
                        unique_filename = f"{uuid.uuid4()}_{file.filename}"
                        filename_mapping[file.filename] = unique_filename
                        # Upload file to Digital Ocean Spaces

                        print('contents:', contents)
                        try:
                            spaces_client.put_object(
                                Bucket=DO_SPACE_NAME,
                                Key=unique_filename,
                                Body=contents,
                                ACL='private'
                            )
                            print(f"Successfully uploaded file: {unique_filename}")
                        except Exception as upload_error:
                            print(f"Error uploading file {file.filename}: {str(upload_error)}")
                            return JSONResponse(status_code=500, content={"error": f"File upload failed: {str(upload_error)}"})
                    else:
                        print(f"Warning: File {file.filename} is empty")
                except Exception as read_error:
                    print(f"Error reading file {file.filename}: {str(read_error)}")
                    return JSONResponse(status_code=500, content={"error": f"File read failed: {str(read_error)}"})
                finally:
                    await file.close()

        # Update JSON data with file keys
        if 'data' in json_data and isinstance(json_data['data'], dict):
            for field_name, field_value in json_data['data'].items():
                if isinstance(field_value, list):
                    for item in field_value:
                        if isinstance(item, dict):
                            for key, value in item.items():
                                if value in filename_mapping:
                                    item[key] = filename_mapping[value]

        # Update MongoDB
        update_result = await assigned_slates.update_one(
            {"_id": ObjectId(form_id)},
            {"$set": json_data}
        )

        if update_result.modified_count == 0:
            return JSONResponse(status_code=404, content={"message": "Form not found or not modified"})

        return JSONResponse(content={"message": "Form updated successfully", "data": json_data})

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})



@app.get("/test-put-object/")
async def test_put_object():
    try:
        test_key = 'test_object.txt'
        test_data = 'This is a test object'

        response = spaces_client.put_object(
            Bucket=DO_SPACE_NAME,
            Key=test_key,
            Body=test_data,
            ACL='private'
        )
        print("Put object response:", response)
        return JSONResponse(content={"message": "Test object created successfully", "response": str(response)})
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"ClientError: {error_code} - {error_message}")
        return JSONResponse(status_code=500, content={
            "error": f"Operation failed: {error_code}",
            "message": error_message
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print("Detailed error:", error_trace)
        return JSONResponse(status_code=500, content={"error": f"Operation failed: {str(e)}", "trace": error_trace})



# Endpoint to retrieve file content
@app.get("/get-file/{file_key}")
async def get_file(file_key: str):
    try:
        # Retrieve the file from Digital Ocean Spaces
        file_obj = spaces_client.get_object(Bucket=DO_SPACE_NAME, Key=file_key)
        file_content = file_obj['Body'].read()
        
        # Determine the content type (you might want to store this information when uploading)
        content_type = file_obj['ContentType']
        
        # Return the file content
        return Response(content=file_content, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")



# PUT endpoint to update the form data
@app.put("/update-slate/{templateId}")
async def update_form(templateId: str, slate: CreateSlateModel = Body(...)):
    print("Received Slate Data:", slate)
    # print('Received Form Data:', form)
    try:
        # Convert the form data to a dictionary
        print("Received Slate Data:", slate)
        slate_dict = slate.model_dump(by_alias=True)
        
        # Update the form data in the database
        update_result = await templates.update_one({"_id": ObjectId(templateId)}, {"$set": slate_dict})
        
        if update_result.modified_count == 1:
            return {"message": "Slate template updated successfully"}
        else:
            print("Received Slate Data:", slate)
            raise HTTPException(status_code=404, detail="Slate template not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# PUT endpoint to delete a specific slatetemplate
@app.delete("/delete-slate/{slate_id}")
async def delete_slate(slate_id: str):
    try:        
        # Update the form data in the database
        delete_result = await templates.delete_one({"_id": ObjectId(slate_id)})
        if delete_result.deleted_count == 1:
            return {"message": "Slate templates updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Slate template not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# # # # # # # # # # # # # # # # # # Org Related Routes # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

@app.get(
    "/org-slates/",
    response_description="List all slates of an organization",
    response_model=AssignedSlatesCollection,
    response_model_by_alias=False,
)
async def list_slates(owner_org: str):
# async def list_slates(owner: str):
    
    # query sets the conditions which it searches for in the forms collection
    query = {"owner_org": owner_org}
    slates = await assigned_slates.find(query).to_list(None)
    # print(query)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(slates):
        form_id = str(form["_id"])
        form["database_id"] =  form_id # Add the index to the form data

    return AssignedSlatesCollection(slates=slates)


# # # # # # # # # # # # # # # # # # Project Related Routes # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# POST endpoint to accept and store cleans forms created by an Document Manager
@app.post("/create-project/")
async def create_project(project: Projects = Body(...)):
    try:
        project_dict = project.model_dump(by_alias=True)  # Convert to dict, respecting field aliases if any
        project_dict["projectId"] = str(uuid.uuid4())
        insert_result = await projects.insert_one(project_dict)
        return {"message": "project created successfully", "id": str(insert_result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



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
        form["database_id"] =  form_id # Add the index to the form data
        
    return ProjectsCollection(user_projects=user_projects)



# PUT endpoint to delete a specific project
@app.delete("/delete-project/")
async def delete_project(project_id: str, projectName: str, projectOwner: str):
    query = {"owner": projectOwner, "project": projectName}
    try:        
        # Update the form data in the database
        delete_result = await projects.delete_one({"_id": ObjectId(project_id)})
        if delete_result.deleted_count == 1:
            slates2delete = await assigned_slates.find(query).to_list(None)
            for i in range(len(slates2delete)):
                await assigned_slates.delete_one({"_id": slates2delete[i]["_id"]})
            return {"message": "Project and related slates deleted"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# # Route for setting the status of a project to archived 
@app.put("/archive-project/{project_id}")
async def update_user_profile(project_id: str):
    project = await projects.find_one({"_id": ObjectId(project_id)})
    try:
        # Add the user to the early_bird database
        project["status"] = 'Archived'
        await projects.replace_one({"_id": ObjectId(project_id)}, project)
        return {"message": "Early bird request added to database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding early bird request to database: {str(e)}")
    


# Route for updating the user profile  
@app.put("/edit-project")
async def update_user_profile(project_info: Projects = Body(...)):
    try:
        # Find the project in the database by mongoDB Id
        project = await projects.find_one({"_id": ObjectId(project_info.database_id)})
        # Update the user's profile fields
        project["database_id"] = project_info.database_id
        project["status"] = project_info.status
        project["owner"] = project_info.owner
        project["address"] = project_info.address
        project["currency"] = project_info.currency
        project["projectName"] = project_info.projectName
        project["projectType"] = project_info.projectType
        project["projectLead"] = project_info.projectLead
        project["estimated_date"] = project_info.estimated_date
        project["completion_date"] = project_info.completion_date
        # Update the user in the database
        await projects.replace_one({"_id": ObjectId(project_info.database_id)}, project)
        return {"message": "Project updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# # # # # # # # # # # # # # # # # # Project Details Routes # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# Route for getting for getting the slates assigned on a project
@app.get(
    "/project-slates/",
    response_description="List all project slates",
    response_model=AssignedSlatesCollection,
    response_model_by_alias=False,
)
async def list_slates(projectId: str, owner_org: str):
# async def list_slates(owner: str):
    
    # query sets the conditions which it searches for in the forms collection
    query = {"projectId": projectId, "owner_org": owner_org}
    # query = {"owner": owner}
    slates = await assigned_slates.find(query).to_list(None)
    # print(query)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(slates):
        form_id = str(form["_id"])
        form["database_id"] =  form_id # Add the index to the form data

    return AssignedSlatesCollection(slates=slates)



# PUT endpoint to delete a specific project
@app.delete("/delete-assigned-slate/{slate_id}")
async def delete_assigned_slate(slate_id: str):
    try:        
        # Update the form data in the database
        delete_result = await assigned_slates.delete_one({"_id": ObjectId(slate_id)})
        if delete_result.deleted_count == 1:
            return {"message": "Assigned slate deleted"}
        else:
            raise HTTPException(status_code=404, detail="Slate not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# PUT endpoint to update information of an assigned slate
@app.put("/edit-assigned-slate/{slate_id}")
async def edit_assigned_slate(slate_id: str, update: AssignSlateModel = Body(...)):
    assigned_slate = await assigned_slates.find_one({"_id": ObjectId(slate_id)})
    try:        
        # Update the form data in the database
        assigned_slate["due_date"] = update.due_date
        assigned_slate["assignee"] = update.assignee
        assigned_slate["status"] = update.status
        assigned_slate["database_id"] = slate_id
        print(assigned_slate)
        await assigned_slates.replace_one({"_id": ObjectId(slate_id)}, assigned_slate)
        return {"message": "Assigned slate updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# function that formats RYG cell to fill the cell with the corresponding colour
def color_name_to_hex(color_name):
    color_map = {
        'red': '#FF0000',
        'green': '#008000',
        'yellow': '#FFFF00'
    }
    return color_map.get(color_name.lower(), '#FFFFFF')  # Default to white if color not found

# function that formats the data of the slate in order to print it out on an A4 pdf
def generate_slate_pdf(slate):
    buffer = BytesIO()
    page_width, page_height = A4
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            leftMargin=12.7*mm, rightMargin=12.7*mm,
                            topMargin=12.7*mm, bottomMargin=12.7*mm)
    
    available_width = doc.width
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        alignment=1,  # Center alignment
        spaceAfter=7.62*mm
    )
    description_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['BodyText'],
        fontSize=16,
        alignment=1,  # Center alignment
        spaceAfter=7.62*mm
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=5.08*mm,
        spaceAfter=2.54*mm
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        spaceBefore=2.54*mm,
        spaceAfter=2.54*mm
    )
    cursive_style = ParagraphStyle(
        'Cursive',
        parent=styles['BodyText'],
        fontName='Cursive',
        fontSize=12
    )
    
    # Add header information
    elements.append(Paragraph(f"<b>Assignee:</b> {slate['assignee']}", body_style))
    elements.append(Paragraph(f"<b>Project:</b> {slate['projectId']}", body_style))
    
    # Handle last_updated date
    try:
        last_updated = datetime.strptime(slate['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ")
        formatted_date = last_updated.strftime('%d/%m/%Y')
    except ValueError:
        formatted_date = slate['last_updated']  # Use as-is if it's not in the expected format
    elements.append(Paragraph(f"<b>Completion Date:</b> {formatted_date}", body_style))
    
     # Add horizontal line
    elements.append(Spacer(1, 5.08*mm))
    elements.append(HorizontalLine(available_width))
    elements.append(Spacer(1, 5.08*mm))

    # Add title
    elements.append(Paragraph(slate['title'], title_style))

    # Add description if available
    if slate.get('description'):
        elements.append(Paragraph(slate['description'], description_style))
        elements.append(Spacer(1, 5.08*mm))
    
    # Process fields and data
    for field in slate['fields']:
        elements.append(Paragraph(field['label'], heading_style))
        
        if field['field_type'] == 'table':
            table_data = [[col['label'] for col in field['columns']]]
            raw_data = slate['data'].get(field['name'], [[]])
            print('raw_data', raw_data)
            print(len(raw_data[0]))
            
            # if len(raw_data) > 0 and len(raw_data[0]) > 1:
            #     data_row = raw_data[0][1:]  # Skip the first entry as a null entry is created in cases wehre a length of greate than 1.
            # elif len(raw_data[0]) == 1:
            #     data_row = raw_data[0]
            if len(raw_data) > 0:
                if len(raw_data[0]) > 1:
                    data_row = raw_data[0][1:]  # Skip the first entry
                else:
                    data_row = raw_data[0]

                # Calculate cell width
                num_columns = len(field['columns'])
                cell_width = (available_width / num_columns) - 2*mm  # Subtracting 2mm for padding

                print('data_row', data_row)
                processed_row = []
                for value, col in zip(data_row, field['columns']):
                    print('col', col)
                    print('value', value)
                    print('picture id', data_row[value])
                    if col['dataType'] == 'picture':
                        try:
                        #     file_obj = spaces_client.get_object(Bucket=DO_SPACE_NAME, Key=data_row[value])
                        #     file_content = file_obj['Body'].read()
                        #     img = Image(BytesIO(file_content), width=15*mm, height=15*mm)  # Reduced size
                        #     processed_row.append(img)
                        # except ClientError as e:
                        #     logger.error(f"Error fetching image {value}: {str(e)}")
                        #     processed_row.append('Image not found')
                            file_obj = spaces_client.get_object(Bucket=DO_SPACE_NAME, Key=data_row[value])
                            file_content = file_obj['Body'].read()
                            img_reader = ImageReader(BytesIO(file_content))
                            img_width, img_height = img_reader.getSize()
                            aspect = img_height / float(img_width)
                            
                            # Scale image to fit cell width
                            new_width = cell_width
                            new_height = cell_width * aspect
                            
                            img = Image(BytesIO(file_content), width=new_width, height=new_height)
                            processed_row.append(img)
                        except ClientError as e:
                            logger.error(f"Error fetching image {value}: {str(e)}")
                            processed_row.append('Image not found')
                    elif col['dataType'] == 'colour':
                        processed_row.append(value)
                    elif col['dataType'] == 'signature':
                        if isinstance(value, str) and value.startswith('data:image'):
                            image_data = base64.b64decode(value.split(',')[1])
                            img = Image(BytesIO(image_data), width=15*mm, height=7.5*mm)  # Reduced size
                            processed_row.append(img)
                        else:
                            processed_row.append(Paragraph(str(value), cursive_style))
                    else:
                        processed_row.append(Paragraph(str(value), ParagraphStyle('Wrapped', wordWrap='CJK', fontSize=8)))
                
                table_data.append(processed_row)
            
            # Calculate column widths
            num_columns = len(field['columns'])
            col_widths = [available_width / num_columns] * num_columns
            
            # Create table with auto word wrap
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#CCCCCC')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#000000')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),  # Reduced font size
                ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#FFFFFF')),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#000000')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),  # Reduced font size
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5*mm, HexColor('#000000')),
                ('WORDWRAP', (0, 0), (-1, -1)),
            ])

            # Add color-specific styles
            for i, col in enumerate(field['columns']):
                if col['dataType'] == 'colour' and len(table_data) > 1:
                    color_value = str(table_data[1][i]).lower()
                    hex_color = color_name_to_hex(color_value)
                    table_style.add('BACKGROUND', (i, 1), (i, 1), HexColor(hex_color))

            t.setStyle(table_style)
            elements.append(t)
        elif field['field_type'] == 'signature':
            value = slate['data'].get(field['name'], '')
            if value.startswith('data:image'):  # It's a base64 encoded image
                image_data = base64.b64decode(value.split(',')[1])
                img = Image(BytesIO(image_data), width=100*mm, height=50*mm)
                elements.append(img)
            else:  # It's a typed signature
                elements.append(Paragraph(value, cursive_style))
        elif field['field_type'] == 'checkbox':
            options = field.get('options', [])
            value = slate['data'].get(field['name'], [])
            checkbox_text = " ".join([f"[{'X' if opt in value else ' '}] {opt}" for opt in options])
            elements.append(Paragraph(checkbox_text, body_style))
    try:
        doc.build(elements)
    except Exception as e:
        # logger.error(f"Error building PDF: {str(e)}")
        raise

    buffer.seek(0)
    return buffer



@app.get("/generate-slate-pdf/{slate_id}")
async def generate_slate_pdf_endpoint(slate_id: str):
    try:
        slate = await assigned_slates.find_one({"_id": ObjectId(slate_id)})
        if not slate:
            raise HTTPException(status_code=404, detail="Slate not found")

        pdf_buffer = generate_slate_pdf(slate)
        return Response(content=pdf_buffer.getvalue(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=slate_{slate_id}.pdf"})
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


# # # # # # # # # # # # # # # # # # Registration & Signon Routes # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


def get_auth0_token():
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("AUTH0_CLIENT_ID"),
        "client_secret": os.getenv("AUTH0_CLIENT_SECRET"),
        "audience": f"https://{AUTH0_DOMAIN}/api/v2/"
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception("Failed to obtain Auth0 access token")
    


# # Route for adding an early bird request to the database  
@app.put("/early-signon")
async def update_user_profile(user_profile: EarlyBird = Body(...)):
    try:
        # Add the user to the early_bird database
        result = await early_birds.insert_one(user_profile.model_dump(by_alias=True))
        return {"message": "Early bird request added to database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding early bird request to database: {str(e)}")



# Route for updating the user profile  
@app.put("/user-profile")
async def update_user_profile(user_profile: PlatformUsers = Body(...)):
    # user = await users.find_one({"auth0_id": user_profile.auth0_id})
    # print("user: ", user)
    # print("user_profile: ", user_profile.first_name)
    try:
        # Find the user in the database by auth0_id
        user = await platform_users.find_one({"auth0_id": user_profile.auth0_id})
        if user:
            # Update the user's profile fields
            user["name"] = user_profile.name
            user["organization"] = user_profile.organization
            user["email"] = user_profile.email

            # Update the user in the database
            await platform_users.replace_one({"auth0_id": user_profile.auth0_id}, user)
            return {"message": "User profile updated successfully"}
        else:
            # Create a new user profile
            new_user = {
                "name": user_profile.name,
                "organization": user_profile.organization,
                "email": user_profile.email,
                "auth0_id": user_profile.auth0_id
            }
            await platform_users.insert_one(new_user)
            return {"message": "User profile created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Route for updating the user profile  
@app.post("/register")
async def register_user(request: Request):
    user_profile = await request.json()

    new_user = {
            "email": user_profile["email"],
            "auth0_id": user_profile["auth0_id"],
            'database_id': None,
            "name": None,
            "organization": None,
            "organization_id": [],
        }
    await platform_users.insert_one(new_user)

    # Process the user data and store it in your MongoDB database
    # Assign the user a default "basic tier" role in your database
    
    # Generate an access token for the Auth0 Management API
    payload = ({
    "roles": [
        "rol_qtPngFIhl1aJihaC"
    ]
    })

    # Make a request to the Auth0 Management API to assign the role
    url = f"https://{AUTH0_DOMAIN}/api/v2/users/{user_profile['auth0_id']}/roles"
    token = get_auth0_token()  # Obtain the access token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("Response Status Code:", response.status_code)
    print("Response Text:", response.text)
    
    if response.status_code == 204:
        print("Role assigned successfully")
    else:
        print(f"Error assigning role: {response.text}")
    
    return {"message": "User registered successfully"}

    

# Route for updating the user profile  
@app.post("/login/")
async def login_user():
    try:
        print("logged in!")
        return {"message": "User logged in successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/privacy-notice-url")
async def get_privacy_notice_url():
    # Generate a pre-signed URL for the privacy notice PDF
    url = spaces_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': DO_SPACE_NAME, 'Key': 'privacy_notice.pdf'},
        ExpiresIn=3600  # URL expires in 1 hour
    )
    print(url)
    return {"url": url}




# # # # # # # # # # # # # # # # # # Admin Panel Routes # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


# Route for getting all the users signed up to your platform. 
@app.get(
    "/users/",
    response_description="List all users",
    response_model=UsersCollection,
    response_model_by_alias=False,
)
async def list_users():
    # query sets the conditions which it searches for in the forms collection
    users = await platform_users.find().to_list(None)
    # print(query)

    # Iterate over each form and store its _id in the dictionary
    for i,form in enumerate(users):
        form_id = str(form["_id"])
        form["database_id"] =  form_id # Add the index to the form data

    return UsersCollection(users=users)



class UpdateUsersRequest(BaseModel):
    user_ids: List[str]
    updated_fields: dict

@app.put("/update-users")
async def update_users(request: UpdateUsersRequest):
    user_ids = request.user_ids
    updated_fields = request.updated_fields
    print(user_ids)
    print(updated_fields)
    try:
        for i in range(len(user_ids)): # Check the length of user_ids as the entry fields that can be modified are different for a single select and multiselect

            # Validate if only one organization_id has the "Premium User" tier
            premium_user_count = sum(
                1 for org_id in updated_fields["organization_id"]
                if list(org_id.values())[0] == "Premium User"
            )
            if premium_user_count > 1:
                raise HTTPException(
                    status_code=400,
                    detail="Only one organization_id can have the 'Premium User' tier."
                )
            
            if len(user_ids) == 1:
                # Update the users with the specified database_ids and updated fields
                user = await platform_users.find_one({"_id": ObjectId(user_ids[i])})
                # Update the user's profile fields
                user["name"] = updated_fields["name"]
                user["organization"] = updated_fields["organization"]
                
                # Compare the existing organization_id with the updated organization_id
                existing_org_ids = user["organization_id"] if user["organization_id"] else []
                updated_org_ids = updated_fields["organization_id"]
                
                # Remove obsolete key-value pairs from the existing organization_id
                updated_org_id_keys = [list(org_id.keys())[0] for org_id in updated_org_ids]
                user["organization_id"] = [org_id for org_id in existing_org_ids if list(org_id.keys())[0] in updated_org_id_keys]
                
                # Update or add new key-value pairs from the updated organization_id
                for org_id in updated_org_ids:
                    key = list(org_id.keys())[0]
                    if key in [list(x.keys())[0] for x in user["organization_id"]]:
                        # If the key exists, update the subscription tier
                        for item in user["organization_id"]:
                            if key in item:
                                item[key] = org_id[key]
                                break
                    else:
                        # If the key doesn't exist, add a new key-value pair
                        user["organization_id"].append(org_id)
                
                print(user)
                await platform_users.replace_one({"_id": ObjectId(user_ids[i])}, user)
            else:
                user = await platform_users.find_one({"_id": ObjectId(user_ids[i])})
                user["organization"] = updated_fields["organization"]
                
                # Compare the existing organization_id with the updated organization_id
                existing_org_ids = user["organization_id"] if user["organization_id"] else []
                updated_org_ids = updated_fields["organization_id"]
                
                # Remove obsolete key-value pairs from the existing organization_id
                updated_org_id_keys = [list(org_id.keys())[0] for org_id in updated_org_ids]
                user["organization_id"] = [org_id for org_id in existing_org_ids if list(org_id.keys())[0] in updated_org_id_keys]
                
                # Update or add new key-value pairs from the updated organization_id
                for org_id in updated_org_ids:
                    key = list(org_id.keys())[0]
                    if key in [list(x.keys())[0] for x in user["organization_id"]]:
                        # If the key exists, update the subscription tier
                        for item in user["organization_id"]:
                            if key in item:
                                item[key] = org_id[key]
                                break
                    else:
                        # If the key doesn't exist, add a new key-value pair
                        user["organization_id"].append(org_id)
                
                await platform_users.replace_one({"_id": ObjectId(user_ids[i])}, user)
        return {"message": "User profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Delete endpoint to delete a users
@app.delete("/delete-users/")
async def delete_users(user_ids: List[str]):
    print(user_ids)
    try:
        for i in range(len(user_ids)):
            print("Received user id:", user_ids[i])
            # Delete the users with the specified database_ids
            await platform_users.delete_one({"_id": ObjectId(user_ids[i])})
        return {"message": f"Deleted users with id {user_ids[i]}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# # # # # # # # # # # # # # # # # # Manage Team Routes # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


# # Route for geting for getting the team members associated with an organization.
@app.get(
    "/team/",
    response_description="List all users in the same organization",
    response_model=UsersCollection,
    response_model_by_alias=False,
)
async def list_team_users(owner: str):
    # Find the owner's document in the platform_users collection
    org_admin = await platform_users.find_one({"email": owner})
    print(owner)
    
    if org_admin:
        # Retrieve the organization_id list of the owner
        owner_org_ids = org_admin["organization_id"]
        
        # Find the organization_id key for which the value is "Premium User"
        premium_org_id = None
        for org_id_dict in owner_org_ids:
            for key, value in org_id_dict.items():
                if value == "Premium User":
                    premium_org_id = key
                    break
            if premium_org_id:
                break
        
        if premium_org_id:
            # Query the platform_users collection to find all users with the premium_org_id in their organization_id list
            query = {"organization_id": {"$elemMatch": {premium_org_id: {"$exists": True}}}}
            users = await platform_users.find(query).to_list(None)
            
            # Iterate over each user and modify the data to match the model
            for user in users:
                user["database_id"] = str(user["_id"])
                user["organization_id"] = [
                    {key: str(value[0]) if isinstance(value, list) else str(value)}
                    for org_id in user["organization_id"]
                    for key, value in org_id.items()
                ]
                user["auth0_id"] = str(user["auth0_id"]) if user["auth0_id"] else ""
            
            print(users)
            return UsersCollection(users=users, premium_key=premium_org_id)  # Include premium_key in the response
        else:
            # If no organization_id with value "Premium User" is found, return an empty list of users
            return UsersCollection(users=[], premium_key=None)  # Set premium_key to None
    else:
        # If the owner is not found, return an empty list of users
        return UsersCollection(users=[], premium_key=None)  # Set premium_key to None    



# Route for adding users to project team
@app.put("/add-user/{email}")
async def add_user(user_fields: dict, email: str):
    # Retrieve the admin user based on the provided email
    admin = await platform_users.find_one({"email": email})
    user = await platform_users.find_one({"email": user_fields["email"]})
    print(user_fields)

    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")

    try:
        if user:
            print(1)
            # Update the user's profile fields
            organization = user.get("organization", admin["organization"])
            database_id = user.get("database_id")
            auth0_id = user.get("auth0_id")

            # Check if the user already has an organization_id array
            if user.get("organization_id"):
                # Append the new value pair to the existing organization_id array
                organization_id = user["organization_id"]
                # Update the subscription tier for the existing key
                for item in organization_id:
                    key = list(item.keys())[0]
                    if key == list(admin["organization_id"][0].keys())[0]:
                        item[key] = user_fields["organization_id"]
                        break
            else:
                # Create a new organization_id array with the value pair using the admin's key
                admin_key = list(admin["organization_id"][0].keys())[0]
                organization_id = [{admin_key: user_fields["organization_id"]}]

            new_user = {
                "name": user_fields["name"],
                "email": user_fields["email"],
                "organization": organization,
                "organization_id": organization_id,
                "database_id": database_id,
                "auth0_id": auth0_id
            }
            # Update the user in the database
            await platform_users.update_one({"email": user_fields["email"]}, {"$set": new_user})
            return {"message": "User updated successfully"}
        else:
            # Get the key from the admin's organization_id
            admin_key = list(admin["organization_id"][0].keys())[0]
            print(admin_key)
            
            # Convert organization_id to a list of dictionaries
            organization_id = [{admin_key: user_fields["organization_id"]}]
            organization_id = [
                {key: str(value[0]) if isinstance(value, list) else str(value)}
                for org_id in organization_id
                for key, value in org_id.items()
            ]
            
            new_user = {
                "name": user_fields["name"],
                "email": user_fields["email"],
                "organization": admin["organization"],
                "organization_id": organization_id,
                "database_id": None,
                "auth0_id": None
            }
            # Insert the new user into the database
            await platform_users.insert_one(new_user)
            return {"message": "User added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Route for updating team members info
@app.put("/update-team-users/{email}")
async def update_users(updated_fields: dict, email: str):
    # Retrieve the admin user based on the provided email
    admin = await platform_users.find_one({"email": email})
    
    # Find the key associated with the "Premium User" tier in the admin's organization_id
    premium_key = None
    for org_id in admin["organization_id"]:
        for key, value in org_id.items():
            if value == "Premium User":
                premium_key = key
                break
        if premium_key:
            break
    
    print('premium_key: ', premium_key)
    print('admin: ', admin)
    print('updated_fields: ', updated_fields)
    
    try:
        # Check if the user with the specified email exists
        user = await platform_users.find_one({"email": updated_fields["email"]})
        
        # If user exists, update the user's profile fields
        if user:
            print(1)
            user["name"] = updated_fields["name"]
            
            # Update the subscription tier for the user based on the premium key
            for org_id in user["organization_id"]:
                print('org_id:', org_id)
                if premium_key in org_id:
                    org_id[premium_key] = updated_fields["organization_id"][0]
                    break
            else:
                # If the premium key doesn't exist, add a new key-value pair
                user["organization_id"].append({premium_key: updated_fields["organization_id"][0]})
            
            await platform_users.update_one({"email": updated_fields["email"]}, {"$set": user})
            return {"message": "User profile updated successfully"}
        
        # If user doesn't exist, create a new user
        else:
            new_user = {
                "email": updated_fields["email"],
                "name": updated_fields["name"],
                "organization": admin["organization"],
                "organization_id": {premium_key: updated_fields["organization_id"][0]},
                "database_id": None,
                "auth0_id": None
            }
            
            # Convert organization_id to a list of dictionaries
            new_user["organization_id"] = [
                {key: str(value[0]) if isinstance(value, list) else str(value)}
                for org_id in [new_user["organization_id"]]
                for key, value in org_id.items()
            ]
            
            await platform_users.insert_one(new_user)
            return {"message": "User profile added successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/delete-users/{premiumKey}")
async def remove_team_users(databaseIds: List[str], premiumKey: str):
    print(databaseIds)
    try:
        for databaseId in databaseIds:
            user = await platform_users.find_one({"_id": ObjectId(databaseId)})
            if user:
                # Remove the dictionary entry within organization_id that contains the premiumKey
                user["organization_id"] = [
                    org_id for org_id in user["organization_id"]
                    if premiumKey not in org_id
                ]
                
                # Update the user in the database
                await platform_users.update_one(
                    {"_id": ObjectId(databaseId)},
                    {"$set": {"organization_id": user["organization_id"]}}
                )
                
                print(f"Removed user with id {databaseId} from the team")
            else:
                print(f"User with id {databaseId} not found")
        
        return {"message": "Users removed from the team successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# # # # # # # # # # # # # # # # # # Company Detail Routes # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# Route for creeating or updating the company details on name and address
@app.post("/company-details")
async def dummy_company_details(info: Company = Body(...)):
    print(f"Received data: {info}")
    return {
        "message": "Data received successfully",
        "received_data": info.model_dump()
    }
# async def update_company_details(info: Company = Body(...)):
#     try:
#         # Find the user in the database by auth0_id
#         company = await company_details.find_one({"owner_org": info.owner_org})
#         if company:
#             # Update the user's profile fields
#             company["name"] = info.name
#             company["address"] = info.address
#             company["vat"] = info.vat
#             company["email"] = info.email
#             company["telephone"] = info.telephone

#             # Update the user in the database
#             await company_details.replace_one({"owner_org": info.owner_org}, company)
#             return {"message": "Company profile updated successfully"}
#         else:
#             # Create a new user profile
#             new_company = {
#                 "name": new_company.name,
#                 "address": new_company.address,
#                 "vat": new_company.vat,
#                 "email": new_company.email,
#                 "telephone": new_company.vat,
#             }
#             await platform_users.insert_one(new_company)
#             return {"message": "Company profile created successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    


# Route for fetching the company details
@app.get(
    "/company/",
    response_description="List the company details",
    response_model=Company,
    response_model_by_alias=False,
)
async def list_company_details(owner: str):
    company_info = await company_details.find_one({"owner_org": owner})
    print(f"Owner: {owner}")
    print(f"Company info: {company_info}")
    
    if company_info:
        return Company(**company_info)
    else:
        # If the company with owner_org is not found, return an object with blank values
        return Company(
            owner_org="",
            name="",
            address="",
            vat="",
            email="",
            telephone=""
        )



# # # # # # # # # # # # # # # # # # Dashboard Routes # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


@app.get("/dashboard-data", response_model=List[DashboardItem])
async def get_dashboard_data(owner_org: str = Query(..., description="Organization ID to filter slates")):
    pipeline = [
        {"$match": {"owner_org": owner_org}},
        {"$lookup": {
            "from": "Projects",
            "localField": "projectId",
            "foreignField": "projectId",
            "as": "project_info"
        }},
        {"$unwind": {
            "path": "$project_info",
            "preserveNullAndEmptyArrays": True
        }},
        {"$lookup": {
            "from": "Users",
            "localField": "assignee",
            "foreignField": "email",
            "as": "user_info"
        }},
        {"$unwind": {
            "path": "$user_info",
            "preserveNullAndEmptyArrays": True
        }},
        {"$project": {
            "id": {"$toString": "$_id"},
            "project_name": "$project_info.projectName",
            "project_type": "$project_info.projectType",
            "slate_name": "$title",
            "status": {"$cond": ["$status", "Completed", "Active"]},
            "assignee_name": "$user_info.name",
            "assignee_email": "$assignee",
            "assigned_date": "$assigned_date",
            "due_date": "$due_date",
            "description": "$description",
            "owner_org": "$owner_org",
            "last_updated": "$last_updated"
        }}
    ]
    
    try:
        result = await db.Assigned_Slates.aggregate(pipeline).to_list(None)
        print(result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/dashboard-kpis")
async def get_dashboard_kpis(owner_org: str = Query(..., description="Organization ID to filter data")):
    try:
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        three_months_ago = current_date - timedelta(days=90)
        
        # Get latest metrics
        latest_metrics = db.OrganizationMetrics.find_one(
            {"owner_org": owner_org},
            sort=[("date", -1)]
        )
        
        # Get metrics from a month ago for comparison
        month_ago_metrics = db.OrganizationMetrics.find_one({
            "owner_org": owner_org,
            "date": {"$gte": current_date - timedelta(days=31), "$lt": current_date - timedelta(days=29)}
        })
        
        # Calculate percentage change in average overdue
        if month_ago_metrics and month_ago_metrics["average_overdue"] > 0:
            percentage_change = ((latest_metrics["average_overdue"] - month_ago_metrics["average_overdue"]) / 
                                 month_ago_metrics["average_overdue"]) * 100
        else:
            percentage_change = 0
        
        # Get project health data for the past 3 months
        project_health_data = list(db.OrganizationMetrics.find(
            {
                "owner_org": owner_org,
                "date": {"$gte": three_months_ago}
            },
            {"date": 1, "project_health": 1, "_id": 0}
        ).sort("date", 1))
        
        return {
            "average_overdue": {
                "current": latest_metrics["average_overdue"],
                "percentage_change": round(percentage_change, 2)
            },
            "project_health": [
                {
                    "date": item["date"].strftime("%Y-%m-%d"),
                    "health": item["project_health"]
                } for item in project_health_data
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()


# @app.put("/update-users/")
# async def update_users(request: UpdateUsersRequest):
#     user_ids = request.user_ids
#     updated_fields = request.updated_fields
#     for i in range(len(user_ids)):
#         print("Received user id:", user_ids[i])
#     print("updated_fields:", updated_fields["first_name"])
#     return {"message": "ok"}



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


# # Route for generating pdfs from the available form data. 
# @app.get("/download-pdf/{form_id}")
# async def download_pdf(form_id: str):
#     form_data = await get_form_data(form_id)  # Implement this function to fetch form data from DB
#     if not form_data:
#         raise HTTPException(status_code=404, detail="Form not found")

#     buffer = BytesIO()
#     c = canvas.Canvas(buffer, pagesize=A4)
#     width, height = A4

#     c.drawString(100, height - 100, f"Form Title: {form_data['title']}")
#     c.drawString(100, height - 120, f"Assignee: {form_data['assignee']}")
#     c.drawString(100, height - 140, f"Due Date: {form_data['due_date']}")
#     # Add more fields as needed

#     c.save()
#     buffer.seek(0)

#     return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment;filename={form_data['title']}.pdf"})


# @app.put("/update-slate/{templateId}")
# async def test_update_form(templateId: str, slate: dict = Body(...)):
#     print("Received Slate id:", templateId)
#     print("Received Slate Data:", slate)
#     return {"message": "ok"}