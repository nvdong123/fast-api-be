from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID

class BookingBase(BaseModel):
    hotel_id: UUID
    customer_id: UUID
    check_in: datetime
    check_out: datetime
    special_requests: Optional[str] = Field(None, max_length=500)
    
    model_config = {"from_attributes": True}

    @validator('check_out')
    def check_dates(cls, check_out, values):
        if 'check_in' in values and check_out <= values['check_in']:
            raise ValueError('Check-out must be after check-in')
        return check_out
