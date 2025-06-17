from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, constr, Field
from app.models.enums.user import UserRole
from uuid import UUID

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = True
    role: Optional[UserRole] = None
    tenant_id: UUID

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: constr(min_length=8)
    full_name: constr(min_length=1)
    role: UserRole
    tenant_id: UUID

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[constr(min_length=8)] = None

# Additional properties stored in DB
class UserInDBBase(UserBase):
    id: UUID
    created_at: datetime
    tenant_name: Optional[str] = None
    last_login: Optional[datetime] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True

# Additional properties to return via API
class UserResponse(UserInDBBase):
    pass

# Properties stored in DB
class UserInDB(UserInDBBase):
    password: str

# Password change
class ChangePassword(BaseModel):
    old_password: constr(min_length=8)
    new_password: constr(min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "oldpass123",
                "new_password": "newpass123"
            }
        }

# Password reset request
class ForgotPassword(BaseModel):
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

# Password reset with token
class ResetPassword(BaseModel):
    token: str
    new_password: constr(min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset-token-123",
                "new_password": "newpass123"
            }
        }

# User filters for query
class UserFilters(BaseModel):
    search: Optional[str] = None
    role: Optional[UserRole] = None
    tenant_id: UUID
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "search": "john",
                "role": "STAFF",
                "tenant_id": "tenant-123",
                "is_active": True
            }
        }

# Pagination response
class UserPagination(BaseModel):
    items: List[UserResponse]
    total: int
    page: int = Field(ge=0)
    size: int = Field(gt=0)
    pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "user-123",
                        "email": "john@example.com",
                        "full_name": "John Doe",
                        "role": "STAFF",
                        "is_active": True,
                        "tenant_id": "tenant-123",
                        "tenant_name": "Hotel Group A",
                        "phone": "+1234567890",
                        "avatar": "https://example.com/avatars/john.jpg",
                        "last_login": "2024-01-13T10:00:00",
                        "created_at": "2024-01-01T00:00:00"
                    }
                ],
                "total": 100,
                "page": 0,
                "size": 10,
                "pages": 10
            }
        }

# Token response for authentication
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "user-123",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "role": "STAFF"
                }
            }
        }

# Token payload for JWT
class TokenPayload(BaseModel):
    sub: str  # user id
    exp: datetime
    role: UserRole
    tenant_id: UUID