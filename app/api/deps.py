from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.mongodb_service import MongoDBService
from app.config import settings

async def get_mongodb_client():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    try:
        yield client
    finally:
        client.close()

def get_mongodb_service(client: AsyncIOMotorClient = Depends(get_mongodb_client)):
    return MongoDBService(client)