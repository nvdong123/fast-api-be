# app/schemas/room_image.py
from typing import Optional
from pydantic import BaseModel, Field
from .base import TimestampModel, UUIDModel
from uuid import UUID

class RoomImageBase(BaseModel):
    room_type_id: UUID
    image_url: str = Field(max_length=1024)
    thumbnail_url: Optional[str] = Field(None, max_length=1024)
    is_primary: bool = False
    display_order: Optional[int] = None
    
    model_config = {"from_attributes": True}

class RoomImageCreate(RoomImageBase):
    pass

class RoomImageUpdate(BaseModel):
    thumbnail_url: Optional[str] = Field(None, max_length=1024)
    is_primary: Optional[bool] = None
    display_order: Optional[int] = None
    
    model_config = {"from_attributes": True}

class RoomImageResponse(RoomImageBase, UUIDModel, TimestampModel):
    pass

class ImageUploadResponse(BaseModel):
    url: str
    thumbnail_url: Optional[str] = None