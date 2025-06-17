from typing import Optional
from pydantic import BaseModel, Field
from .base import TimestampModel, UUIDModel
from datetime import datetime
from uuid import UUID
from app.models.enums import PaymentStatus

class PaymentBase(BaseModel):
    amount: float = Field(gt=0)
    payment_method: str
    transaction_id: Optional[str] = None
    status: PaymentStatus
    payment_date: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class PaymentCreate(PaymentBase):
    booking_id: UUID

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    payment_date: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class PaymentResponse(PaymentBase, UUIDModel, TimestampModel):
    booking_id: UUID