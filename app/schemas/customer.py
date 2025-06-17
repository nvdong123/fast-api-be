from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from .base import BaseModelConfig

class CustomerBase(BaseModelConfig):
    zalo_id: Optional[str] = Field(None, max_length=255)
    name: str = Field(..., max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModelConfig):
    zalo_id: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)

class CustomerBookingInfo(BaseModelConfig):
    id: UUID
    booking_number: str
    check_in: datetime
    check_out: datetime
    status: str
    total_amount: float

class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class CustomerWithBookings(CustomerResponse):
    bookings: List[CustomerBookingInfo] = []

# Cập nhật alias cho Customer để giữ tương thích
Customer = CustomerResponse