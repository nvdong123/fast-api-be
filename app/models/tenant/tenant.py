from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, Text
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base_class import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin
from app.models.enums.tenant import TenantStatus, SubscriptionPlan

class Tenant(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tenants"

    # Basic Information
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(255), unique=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(512), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    # Status and Configuration
    status = Column(Enum(TenantStatus), default=TenantStatus.PENDING)
    is_active = Column(Boolean, default=True)
    max_users = Column(Integer, default=10)
    max_hotels = Column(Integer, default=5)

    # Subscription Details
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    subscription_start = Column(DateTime)
    subscription_end = Column(DateTime)
    billing_email = Column(String(255), nullable=True)
    billing_address = Column(Text, nullable=True)
    
    # Additional Settings
    settings = Column(Text, nullable=True)  # JSON stored as text
    timezone = Column(String(50), default="UTC")
    locale = Column(String(10), default="en")

    # # Relationships
    hotels = relationship("Hotel", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    @validates('subdomain')
    def validate_subdomain(self, key, subdomain):
        """Validate subdomain format and uniqueness"""
        if not subdomain:
            return subdomain
            
        # Convert to lowercase and remove spaces
        subdomain = subdomain.lower().strip()
        
        # Basic validation
        if not subdomain.isalnum() and not set(subdomain).issubset(set(subdomain + '-')):
            raise ValueError("Subdomain can only contain letters, numbers, and hyphens")
            
        return subdomain

    @hybrid_property
    def is_subscription_active(self) -> bool:
        """Check if tenant's subscription is currently active"""
        if self.subscription_end is None:
            return False
        return datetime.utcnow() <= self.subscription_end

    @hybrid_property
    def days_until_subscription_end(self) -> int:
        """Calculate days remaining in subscription"""
        if not self.subscription_end:
            return 0
        delta = self.subscription_end - datetime.utcnow()
        return max(0, delta.days)

    def can_add_hotel(self) -> bool:
        """Check if tenant can add more hotels"""
        return len(self.hotels) < self.max_hotels if self.max_hotels else True

    def can_add_user(self) -> bool:
        """Check if tenant can add more users"""
        return len(self.users) < self.max_users if self.max_users else True

    def suspend(self) -> None:
        """Suspend the tenant"""
        self.status = TenantStatus.SUSPENDED
        self.is_active = False

    def activate(self) -> None:
        """Activate the tenant"""
        self.status = TenantStatus.ACTIVE
        self.is_active = True

    def extend_subscription(self, days: int) -> None:
        """Extend subscription by specified number of days"""
        if not self.subscription_end:
            self.subscription_end = datetime.utcnow()
        self.subscription_end = self.subscription_end + timedelta(days=days)

    def get_active_hotels(self) -> List["Hotel"]:
        """Get list of active hotels for this tenant"""
        return [hotel for hotel in self.hotels if hotel.is_active]

    def get_active_users(self) -> List["User"]:
        """Get list of active users for this tenant"""
        return [user for user in self.users if user.is_active]

    def __repr__(self):
        return f"<Tenant {self.name} ({self.subdomain})>"