# app/services/file_service.py

from fastapi import Depends
from typing import Dict
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from app.schemas.notification import UserRegistration, UserData

class Email_Service:
    async def send_registration_notification(self, user_data: UserData):
        message = MIMEMultipart()
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = f"{settings.ADMIN_EMAIL}, {settings.SECOND_ADMIN_EMAIL}"
        message["Subject"] = "Site Steer - New User Registration!"

        body = f"""
        New user has registered:
        
        Email: {user_data.email}
        Name: {user_data.name}
        Organization: {user_data.organization}
        Marketing Accepted: {user_data.marketing_accepted}
        Registration Time: {user_data.created_at}
        """

        message.attach(MIMEText(body, "plain"))

        # Use async context manager for better resource handling
        async with aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=False,
            start_tls=True  # This will handle the TLS startup automatically
        ) as smtp:
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            await smtp.send_message(message)
