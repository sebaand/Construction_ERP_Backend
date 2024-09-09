# app/services/file_service.py

import logging
from app.config import settings
from app.utils.file_handler import spaces_client
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.spaces_client = spaces_client

    async def get_privacy_notice_url(self):
        try:
            url = self.spaces_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.DO_SPACE_NAME,
                    'Key': 'sitesteer-file-storage/privacy_notice.pdf'  # Update this path if necessary
                },
                ExpiresIn=3600  # URL expires in 1 hour
            )
            logger.info(f"Pre-signed URL generated for privacy notice: {url}")
            return url
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            raise Exception("Failed to generate pre-signed URL for privacy notice")