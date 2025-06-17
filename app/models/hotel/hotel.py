# app/models/hotel/hotels.py
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Integer, Enum, Text, func
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from typing import List
from app.db.base_class import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin
from app.models.enums.hotel import HotelStatus
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

from app.models.enums import RoomStatus
from app.models.hotel.room import Room
from app.db.session import SessionLocal

class Hotel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "hotels"

    # Foreign Keys
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Basic Information
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20))
    
    # Contact Information
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255), nullable=True)
    
    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Hotel Details
    description = Column(Text)
    star_rating = Column(Integer)
    check_in_time = Column(String(50), default="14:00")
    check_out_time = Column(String(50), default="12:00")
    
    # Settings and Features
    amenities = Column(JSON)  # List of amenity strings
    facilities = Column(JSON)  # List of facility strings
    rules = Column(JSON)      # List of hotel rules
    policies = Column(Text)   # Hotel policies
    status = Column(Enum(HotelStatus), default=HotelStatus.DRAFT, nullable=False)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Media
    thumbnail = Column(String(500))  # Main image URL
    gallery = Column(JSON)           # List of image URLs

    # Relationships
    tenant = relationship("Tenant", back_populates="hotels")
    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="hotel")

    @validates('email')
    def validate_email(self, key, email):
        if email:
            assert '@' in email, 'Invalid email address'
        return email

    @property
    def total_bookings(self) -> int:
        """Get total number of bookings"""
        if hasattr(self, '_total_bookings'):
            return self._total_bookings
            
        return len([b for b in self.bookings if not b.deleted_at]) if self.bookings else 0

    @property
    def total_rooms(self) -> int:
        """Get total number of rooms"""
        if hasattr(self, '_total_rooms'):
            return self._total_rooms
            
        return len([r for r in self.rooms if not r.deleted_at]) if self.rooms else 0

    @property
    def available_rooms(self) -> int:
        """Get number of currently available rooms"""
        if hasattr(self, '_available_rooms'):
            return self._available_rooms
            
        return len([
            r for r in self.rooms 
            if not r.deleted_at and r.status == RoomStatus.AVAILABLE
        ]) if self.rooms else 0

    def can_be_published(self) -> object:
        """Check if hotel has all required data to be published"""
        if not all([self.name, self.address, self.city, self.country]):
            return False, "Basic information is incomplete"
        if not self.rooms:
            return False, "No rooms configured"
        if not self.amenities:
            return False, "No amenities specified"
        return True, "Ready to publish"

    def __repr__(self):
        return f"<Hotel {self.name} ({self.city}, {self.country})>"