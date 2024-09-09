# app/utils/file_handler.py

import boto3
from botocore.exceptions import ClientError
from app.config import settings
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

spaces_client = boto3.client('s3',
    region_name=settings.DO_SPACE_REGION,
    endpoint_url=settings.DO_ENDPOINT_URL,
    aws_access_key_id=settings.DO_ACCESS_KEY,
    aws_secret_access_key=settings.DO_SECRET_KEY
)

def get_file(key):
    try:
        file_obj = spaces_client.get_object(Bucket=settings.DO_SPACE_NAME, Key=key)
        return file_obj['Body'].read()
    except ClientError as e:
        logger.error(f"Error fetching file {key}: {str(e)}")
        return None

def upload_file(file_content, file_name):
    try:
        spaces_client.put_object(
            Bucket=settings.DO_SPACE_NAME,
            Key=file_name,
            Body=file_content,
            ACL='private'
        )
        return True
    except ClientError as e:
        logger.error(f"Error uploading file {file_name}: {str(e)}")
        return False

def test_spaces_connection():
    print(f"Using Access Key: {settings.DO_ACCESS_KEY}")
    print(f"Using Endpoint URL: {settings.DO_ENDPOINT_URL}")
    try:
        # List all buckets
        response = spaces_client.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        logger.info(f"Successfully connected. Available buckets: {buckets}")

        # List objects in the specific bucket
        response = spaces_client.list_objects_v2(Bucket=settings.DO_SPACE_NAME)
        if 'Contents' in response:
            objects = [obj['Key'] for obj in response['Contents']]
            logger.info(f"Objects in {settings.DO_SPACE_NAME}: {objects}")
        else:
            logger.info(f"No objects found in {settings.DO_SPACE_NAME}")

        return True
    except ClientError as e:
        logger.error(f"Error connecting to Spaces: {str(e)}")
        return False

# You can call this function to test the connection
if __name__ == "__main__":
    test_spaces_connection()