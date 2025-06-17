# app/core/config.py

from pydantic_settings import BaseSettings
from typing import List
from pydantic import EmailStr
from pathlib import Path

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    # JWT Settings
    SECRET_KEY: str = "Booking123!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7    

    # CORS Settings
    BACKEND_CORS_ORIGINS: list = ["http://ai.ailab.vn:3006"]  # Frontend URL

    # Database Settings
    DATABASE_URL: str = "postgresql://hotel_admin:Booking123!@ai.ailab.vn:5432/hotel_saas"
    
    # Email Settings (for password reset)
    EMAILS_ENABLED: bool = False

    SMTP_TLS: bool = False
    SMTP_PORT: int = 465
    SMTP_HOST: str = "mail.ailab.vn"
    SMTP_USER: str = "dev@ailab.vn"
    SMTP_PASSWORD: str = "Ai@123456"
    EMAILS_FROM_NAME: str = "Hotel Booking"
    EMAILS_FROM_EMAIL: str = "Booking@ailab.vn"

    EMAIL_TEMPLATES_DIR: Path = Path(__file__).parent.parent / "email-templates"
    
    # Upload settings
    PARRENT_DIR: Path = Path(__file__).parent.parent 
    UPLOAD_DIR: Path = Path(__file__).parent.parent / "uploads"
    MEDIA_ROOT: Path = Path(__file__).parent.parent / "media"
    MEDIA_URL: str = "/media"
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB

    UPLOADS_URL_PREFIX: str = "/uploads"  # URL prefix cho static file serving
    USE_S3: bool = False
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""

    # OA settings 
    ZALO_APP_ID: str = "422691514268734554"
    ZALO_APP_SECRET: str = "FsLUO0K54RUsE7uxCYul"
    ZALO_CALLBACK_URL: str = f"https://zalo-api.ailab.vn/api/v1/zalo/webhook"
    ZALO_WEBHOOK_URL: str = f"https://zalo-api.ailab.vn/api/v1/zalo/webhook"

    ZALO_MINI_APP_ID: str = "422691514268734554"
    ZALO_BOOKING_TEMPLATE_ID: str = "00126fd75392bacce383"
    MINI_APP_URL: str = "https://openapi.mini.zalo.me/notification/template"
    HOTEL_NAME: str = "The Cliff"

    # Password Reset
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24
    
    POSTGRES_SERVER: str = 'ai.ailab.vn'
    POSTGRES_USER: str = 'hotel_admin'
    POSTGRES_PASSWORD: str = 'Booking123!'
    POSTGRES_DB: str = 'hotel_saas'
    POSTGRES_PORT: str = 5432


    class Config:
        env_file = ".env"
        case_sensitive = True
   
    @property
    def media_base_dir(self) -> Path:
        """Get base media directory"""
        return self.MEDIA_ROOT

    @property
    def media_url(self) -> str:
        """Get media URL prefix"""
        return self.MEDIA_URL

    def get_media_path(self, *paths) -> Path:
        """Get media path for specific directory/file"""
        return self.MEDIA_ROOT.joinpath(*paths)

    def get_media_url(self, path: str) -> str:
        """Get media URL for specific file"""
        return f"{self.MEDIA_URL}/{path}"

settings = Settings()

# Create necessary directories
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)