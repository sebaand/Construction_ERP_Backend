# app/api/v1/endpoints/general.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from app.services.file_service import File_Service
from app.api.deps import get_file_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/privacy-notice-url")
async def get_privacy_notice_url(
    file_service: File_Service = Depends(get_file_service)
):
    try:
        url = await file_service.get_privacy_notice_url()
        logger.info(f"Generated pre-signed URL: {url}")
        return {"url": url}
    except Exception as e:
        logger.error(f"Error generating privacy notice URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating privacy notice URL")
