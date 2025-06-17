# app/schemas/hotel.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl, constr, confloat, validator
from app.models.enums.hotel import HotelStatus
from uuid import UUID

class HotelBase(BaseModel):
    name: constr(min_length=2, max_length=255)
    address: constr(min_length=5, max_length=500)
    city: constr(min_length=2, max_length=100)
    country: constr(min_length=2, max_length=100)
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    latitude: Optional[confloat(ge=-90, le=90)] = None
    longitude: Optional[confloat(ge=-180, le=180)] = None
    description: Optional[str] = None
    star_rating: Optional[int] = None
    check_in_time: Optional[str] = "14:00"
    check_out_time: Optional[str] = "12:00"
    amenities: Optional[List[str]] = []
    facilities: Optional[List[str]] = []
    rules: Optional[List[str]] = []
    policies: Optional[str] = None
    thumbnail: Optional[str] = None
    gallery: Optional[List[str]] = []

    @validator('star_rating')
    def validate_star_rating(cls, v):
        if v is not None and not 1 <= v <= 5:
            raise ValueError('Star rating must be between 1 and 5')
        return v

class HotelCreate(HotelBase):
    tenant_id: UUID

class HotelUpdate(BaseModel):
    name: Optional[constr(min_length=2, max_length=255)] = None
    address: Optional[constr(min_length=5, max_length=500)] = None
    city: Optional[constr(min_length=2, max_length=100)] = None
    country: Optional[constr(min_length=2, max_length=100)] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    latitude: Optional[confloat(ge=-90, le=90)] = None
    longitude: Optional[confloat(ge=-180, le=180)] = None
    description: Optional[str] = None
    star_rating: Optional[int] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    amenities: Optional[List[str]] = None
    facilities: Optional[List[str]] = None
    rules: Optional[List[str]] = None
    policies: Optional[str] = None
    thumbnail: Optional[str] = None
    gallery: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

class HotelInDB(HotelBase):
    id: UUID
    tenant_id: UUID
    status: HotelStatus
    is_active: bool
    is_featured: bool
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    total_rooms: int
    available_rooms: int

    class Config:
        from_attributes = True

class HotelResponse(HotelInDB):
    tenant_name: str
    room_types: List[Dict[str, Any]]  # Summary of room types available
    total_bookings: int               # Total number of bookings

class HotelListResponse(BaseModel):
    items: List[HotelResponse]
    total: int
    page: int
    size: int
    pages: int

class HotelStatusUpdate(BaseModel):
    status: HotelStatus

class HotelImageUpload(BaseModel):
    image_type: str  # "thumbnail" or "gallery"
    file_name: str
    file_size: int
    content_type: str

class HotelStatsResponse(BaseModel):
    total_hotels: int
    published_hotels: int
    total_rooms: int
    occupied_rooms: int
    available_rooms: int
    maintenance_rooms: int
    total_bookings: int
    active_bookings: int