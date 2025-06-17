from typing import List, Optional
# from pydantic import BaseModel, Field, validator  # Import validator từ pydantic
from pydantic import BaseModel, Field, field_validator  # Cho Pydantic v2

from uuid import UUID
from datetime import datetime
from app.models.enums import BookingStatus
from .base import TimestampModel, UUIDModel, BaseModelConfig

class CustomerBasicInfo(BaseModelConfig):
    id: UUID
    name: str
    email: Optional[str] = None

class HotelBasicInfo(BaseModelConfig):
    id: UUID
    name: str

class BookingRoomInfo(BaseModelConfig):
    id: UUID
    created_at: datetime
    updated_at: datetime
    room_id: UUID
    room_price: float
    extra_person_count: int = 0
    room_number: Optional[str] = None
    room_type_name: Optional[str] = None

class PaymentInfo(BaseModelConfig):
    id: UUID
    amount: float
    payment_method: str
    status: str
    payment_date: Optional[datetime] = None

class BookingBase(BaseModelConfig):
    hotel_id: UUID
    customer_id: UUID
    check_in: datetime
    check_out: datetime
    special_requests: Optional[str] = Field(None, max_length=500)

    @field_validator('check_out')
    def check_dates(cls, check_out, values):
        if 'check_in' in values and check_out <= values['check_in']:
            raise ValueError('Check-out must be after check-in')
        return check_out

class BookingCreate(BookingBase):
    rooms: List[UUID]

class BookingUpdate(BaseModelConfig):
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: Optional[BookingStatus] = None
    special_requests: Optional[str] = Field(None, max_length=500)

class BookingResponse(BookingBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    booking_number: str
    status: BookingStatus
    total_amount: float
    rooms: List[BookingRoomInfo]
    payments: List[PaymentInfo]
    customer: Optional[CustomerBasicInfo] = None
    hotel: Optional[HotelBasicInfo] = None