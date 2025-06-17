# app/schemas/tenant.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, constr
from app.models.enums.tenant import TenantStatus, SubscriptionPlan
from uuid import UUID

class TenantBase(BaseModel):
    name: constr(min_length=1, max_length=255)
    subdomain: Optional[constr(min_length=3, max_length=255)] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    timezone: Optional[str] = "UTC"
    locale: Optional[str] = "en"
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None

class TenantCreate(TenantBase):
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    max_users: Optional[int] = 10
    max_hotels: Optional[int] = 5

class TenantUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=255)] = None
    subdomain: Optional[constr(min_length=3, max_length=255)] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None
    max_users: Optional[int] = None
    max_hotels: Optional[int] = None
    subscription_plan: Optional[SubscriptionPlan] = None

class TenantStatusUpdate(BaseModel):
    status: TenantStatus

class TenantResponse(TenantBase):
    id: UUID
    status: TenantStatus
    is_active: bool
    max_users: int
    max_hotels: int
    subscription_plan: SubscriptionPlan
    subscription_start: Optional[datetime]
    subscription_end: Optional[datetime]
    is_subscription_active: bool
    days_until_subscription_end: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str  # Convert UUID to string in JSON response
        }