# app/utils/email.py
import logging
from pathlib import Path
from typing import Any, Dict
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Template
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    USE_CREDENTIALS=True,
    MAIL_SSL_TLS=True,
    MAIL_STARTTLS=True
)

async def send_email(
    email_to: str,
    subject_template: str = "",
    html_template: str = "",
    environment: Dict[str, Any] = {}
) -> None:
    try:
        message = MessageSchema(
            subject=Template(subject_template).render(**environment),
            recipients=[email_to],
            body=Template(html_template).render(**environment),
            subtype="html"
        )
        
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        raise

async def send_reset_password_email(
    email_to: str,
    token: str,
    username: str
) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery"
    
    html_template = """
        <p>Hi {username},</p>
        <p>We received a request to reset your password.</p>
        <p>Click the link below to reset your password:</p>
        <p>
            <a href="{reset_url}">
                Reset Password
            </a>
        </p>
        <p>If you didn't request this, please ignore this email.</p>
        <p>Thanks,<br>{project_name} Team</p>
    """
    
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    await send_email(
        email_to=email_to,
        subject_template=subject,
        html_template=html_template,
        environment={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "reset_url": reset_url,
            "valid_hours": settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
        }
    )

async def send_new_account_email(
    email_to: str,
    username: str,
    password: str
) -> None:
    """
    Send welcome email to new user with their credentials
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for {username}"
    
    html_template = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">{project_name} - Welcome!</h2>
            <p>Hi {username},</p>
            <p>Your account has been created successfully. Here are your login credentials:</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Email:</strong> {email}</p>
                <p style="margin: 5px 0;"><strong>Password:</strong> {password}</p>
            </div>
            
            <p>You can login at: <a href="{login_url}" style="color: #3498db;">{login_url}</a></p>
            
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                    <strong>Important:</strong> Please change your password after your first login for security reasons.
                </p>
            </div>
            
            <p>If you need any assistance, please don't hesitate to contact our support team.</p>
            
            <p>Best regards,<br>{project_name} Team</p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                This is an automated message, please do not reply to this email.
            </p>
        </div>
    """
    
    login_url = f"{settings.FRONTEND_URL}/login"
    
    try:
        await send_email(
            email_to=email_to,
            subject_template=subject,
            html_template=html_template,
            environment={
                "project_name": project_name,
                "username": username,
                "email": email_to,
                "password": password,
                "login_url": login_url
            }
        )
    except Exception as e:
        logging.error(f"Failed to send welcome email to {email_to}: {str(e)}")
        # You might want to handle this error based on your requirements
        # For now, we'll re-raise it
        raise

async def send_test_email(email_to: str) -> None:
    """
    Send test email to verify email configuration
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    
    html_template = """
        <p>Hi,</p>
        <p>This is a test email from {project_name}.</p>
        <p>If you received this email, it means your email configuration is working properly.</p>
        <p>Thanks,<br>{project_name} Team</p>
    """
    
    await send_email(
        email_to=email_to,
        subject_template=subject,
        html_template=html_template,
        environment={
            "project_name": project_name,
        }
    )