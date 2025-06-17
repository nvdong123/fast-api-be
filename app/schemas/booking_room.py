from typing import Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from .base import TimestampModel, UUIDModel
from uuid import UUID
from typing import ForwardRef

RoomResponse = ForwardRef('RoomResponse')

class BookingRoomBase(BaseModel):
    room_id: UUID
    room_price: float = Field(gt=0)
    extra_person_count: int = Field(default=0, ge=0)
    
    model_config = {"from_attributes": True}

class BookingRoomResponse(BookingRoomBase, UUIDModel, TimestampModel):
    booking_id: UUID
    room: Optional[RoomResponse] = None