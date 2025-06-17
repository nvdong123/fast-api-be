# app/schemas/room_image.py
from typing import Optional
from pydantic import BaseModel
from .base import TimestampModel, UUIDModel
from uuid import UUID

class RoomResponse(BaseModel, UUIDModel, TimestampModel):
    hotel_id: UUID
    room_type_id: UUID
    room_number: str
    floor: Optional[str] = None
    status: str
    is_active: bool = True