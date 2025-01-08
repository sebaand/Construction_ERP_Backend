from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.team_service import Team_Service
from app.services.mongodb_service import MongoDB_Service
from app.services.slates_service import Slates_Service
from app.services.project_service import Project_Service
from app.services.user_service import User_Service
from app.services.dashboard_service import Dashboard_Service
from app.services.invoice_service import Invoice_Service
from app.services.company_service import Company_Service
from app.services.crm_service import CRM_Service
from app.services.prospect_service import Prospect_Service
from app.services.quote_service import Quote_Service
from app.services.file_service import File_Service
from app.services.email_service import Email_Service
from app.config import settings


async def get_mongodb_client():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    try:
        yield client
    finally:
        client.close()

def get_company_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Company_Service(client)

def get_team_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Team_Service(client)

def get_mongodb_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return MongoDB_Service(client)

def get_slates_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Slates_Service(client)

def get_project_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Project_Service(client)

def get_user_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return User_Service(client)

def get_dashboard_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Dashboard_Service(client)

def get_invoice_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Invoice_Service(client)

def get_company_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Company_Service(client)

def get_crm_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return CRM_Service(client)

def get_prospect_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Prospect_Service(client)

def get_quote_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Quote_Service(client)

def get_file_service():
    return File_Service()


def get_email_service():
    return Email_Service()