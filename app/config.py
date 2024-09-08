from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "SiteSteer API"
    MONGO_DB_PASSWORD: str
    
    # Your Auth0 M2M application's client ID, client secret and domain
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    AUTH0_DOMAIN: str

    @property
    def MONGODB_URL(self) -> str:
        return f"mongodb+srv://andreasebastio014:{self.MONGO_DB_PASSWORD}@cluster0.jqaqs3v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    # Configure Digital Ocean Spaces credentials
    DO_SPACE_REGION: str
    DO_SPACE_NAME: str
    DO_ACCESS_KEY: str
    DO_SECRET_KEY: str
    DO_ENDPOINT_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()