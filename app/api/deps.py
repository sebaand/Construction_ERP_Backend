from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.mongodb_service import MongoDBService
from app.services.slates_service import SlatesService
from app.services.project_service import ProjectService
from app.services.user_service import UserService
from app.services.dashboard_service import DashboardService
from app.services.invoice_service import InvoiceService
from app.services.company_service import CompanyService
from app.services.crm_service import CRM_Service
from app.services.prospect_service import Prospect_Service
from app.config import settings
from app.services.file_service import FileService

async def get_mongodb_client():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    try:
        yield client
    finally:
        client.close()

def get_company_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return CompanyService(client)

def get_mongodb_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return MongoDBService(client)

def get_slates_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return SlatesService(client)

def get_project_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return ProjectService(client)

def get_user_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return UserService(client)

def get_dashboard_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return DashboardService(client)

def get_invoice_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return InvoiceService(client)

def get_company_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return CompanyService(client)

def get_crm_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return CRM_Service(client)

def get_prospect_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return Prospect_Service(client)

def get_file_service():
    return FileService()