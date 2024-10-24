import logging
from fastapi import FastAPI
from app.api.v1.router import api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SiteSteer API")

# Set pymongo logger to WARNING level
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("motor").setLevel(logging.WARNING)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.sitesteer.ai", "https://localhost:3000"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")