from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.enums.user import UserRole
from datetime import datetime
from uuid import UUID

class TokenPayload(BaseModel):
    sub: str
    exp: float
    type: str
    role: Optional[str] = None
    tenant_id: UUID

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    expires_in: int
    user: 'UserResponse'

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "strongpassword",
                "remember_me": True
            }
        }

class ForgotPassword(BaseModel):
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

class ResetPassword(BaseModel):
    token: str
    new_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset-token",
                "new_password": "newstrongpassword"
            }
        }

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "oldpassword",
                "new_password": "newpassword"
            }
        }

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    tenant_id: UUID
    avatar: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "STAFF",
                "is_active": True,
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "avatar": "https://example.com/avatar.jpg",
                "last_login": "2024-01-13T12:00:00",
                "created_at": "2024-01-01T00:00:00"
            }
        }