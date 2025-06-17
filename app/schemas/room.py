# app/schemas/room.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime
from app.models.enums import RoomStatus
from .base import BaseModelConfig, TimestampModel, UUIDModel

# Room Schemas
class RoomBase(BaseModelConfig):
    hotel_id: UUID
    room_type_id: UUID
    room_number: str = Field(..., max_length=50)
    floor: Optional[str] = Field(None, max_length=10)
    status: RoomStatus = RoomStatus.AVAILABLE
    is_active: bool = True
    amenities: Optional[List[str]] = Field(default_factory=list)  # Set default empty list
    images: Optional[List[str]] = Field(default_factory=list)     # Set default empty list

    class Config:
        from_attributes = True


class RoomCreate(RoomBase):
    pass



class RoomTypeInfo(BaseModelConfig):
    id: UUID
    name: str
    base_occupancy: int
    max_occupancy: int
    base_price: float
    extra_person_price: float


class RoomImageResponse(BaseModelConfig):
    id: UUID
    image_url: str
    thumbnail_url: Optional[str] = None
    is_primary: bool = False
    display_order: Optional[int] = None

class RoomUpdate(BaseModelConfig):
    room_type_id: Optional[UUID] = None
    room_number: Optional[str] = Field(None, max_length=50)
    floor: Optional[str] = Field(None, max_length=10)
    status: Optional[RoomStatus] = None
    is_active: Optional[bool] = None
    amenities: Optional[List[str]] = None  # Set default empty list
    images: Optional[List[str]] = None

    class Config:
        from_attributes = True

# Room type schemas
class RoomTypeBase(BaseModelConfig):
    name: str = Field(..., max_length=100)
    hotel_id: UUID
    description: Optional[str] = Field(None, max_length=500)
    base_occupancy: int = Field(default=2, ge=1)
    max_occupancy: int = Field(default=4, ge=1)
    base_price: float = Field(..., gt=0)
    extra_person_price: float = Field(default=0, ge=0)
    amenities: Optional[List[str]] = Field(default_factory=list)  # Changed from Any to str


    @validator('max_occupancy')
    def validate_occupancy(cls, v, values):
        if 'base_occupancy' in values and v < values['base_occupancy']:
            raise ValueError('Max occupancy must be greater than or equal to base occupancy')
        return v

class RoomType(RoomTypeBase):
    id: UUID
    hotel_id: UUID
    created_at: datetime
    updated_at: datetime
    images: List[str] = Field(default_factory=list)
    total_rooms: Optional[int] = None
    available_rooms: Optional[int] = None

    class Config:
        from_attributes = True

class RoomResponse(RoomBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    room_type: Optional[RoomType] = None
    current_booking: Optional["BookingBasicInfo"] = None
    last_booking: Optional["BookingBasicInfo"] = None
    amenities: List[str] = Field(default_factory=list)  # Ensure always returns list
    images: List[str] = Field(default_factory=list)     # Ensure always returns list

    class Config:
        from_attributes = True

class RoomWithDetails(RoomResponse):
    hotel_name: Optional[str] = None
    room_type_name: Optional[str] = None
    current_booking_id: Optional[UUID] = None
    is_available: Optional[bool] = None

class RoomFilter(BaseModelConfig):
    hotel_id: Optional[UUID] = None
    room_type_id: Optional[UUID] = None
    room_number: Optional[str] = None
    floor: Optional[str] = None
    status: Optional[RoomStatus] = None
    is_active: Optional[bool] = None
    
    # Lọc theo giá phòng
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    
    # Lọc theo sức chứa
    min_occupancy: Optional[int] = Field(None, ge=1)
    max_occupancy: Optional[int] = Field(None, ge=1)
    
    # Lọc theo ngày
    available_from: Optional[datetime] = None
    available_to: Optional[datetime] = None

    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v

    @validator('max_occupancy')
    def validate_occupancy_range(cls, v, values):
        if v is not None and 'min_occupancy' in values and values['min_occupancy'] is not None:
            if v < values['min_occupancy']:
                raise ValueError('max_occupancy must be greater than min_occupancy')
        return v

    @validator('available_to')
    def validate_date_range(cls, v, values):
        if v is not None and 'available_from' in values and values['available_from'] is not None:
            if v <= values['available_from']:
                raise ValueError('available_to must be after available_from')
        return v

class RoomFilterResponse(BaseModelConfig):
    total: int
    rooms: List[RoomWithDetails]
    has_more: bool
    page: int
    total_pages: int    


class RoomTypeUpdate(BaseModelConfig):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    base_occupancy: Optional[int] = Field(None, ge=1)
    max_occupancy: Optional[int] = Field(None, ge=1)
    base_price: Optional[float] = Field(None, gt=0)
    extra_person_price: Optional[float] = Field(None, ge=0)
    amenities: Optional[List[str]] = None

    
# class RoomTypeResponse(RoomTypeBase):
#     id: UUID
#     created_at: datetime
#     updated_at: datetime


# Cập nhật lại RoomTypeResponse để bao gồm images
class RoomTypeResponse(RoomTypeBase, UUIDModel, TimestampModel):
    images: List[str] = Field(default_factory=list)  # Changed from RoomImageResponse to str
    total_rooms: Optional[int] = None
    available_rooms: Optional[int] = None

    class Config:
        from_attributes = True

class RoomTypeCreate(RoomTypeBase):
    pass



# Cập nhật RoomTypeSummary để bao gồm primary image
class RoomTypeSummary(BaseModelConfig):
    id: UUID
    name: str
    base_price: float
    total_rooms: int
    available_rooms: int
    primary_image: Optional[RoomImageResponse] = None
    thumbnail_url: Optional[str] = None

class RoomSummary(BaseModelConfig):
    total_rooms: int
    available_rooms: int
    occupied_rooms: int
    maintenance_rooms: int
    by_type: List[RoomTypeSummary]
    by_floor: Dict[str, int]  # Floor number -> count of rooms
    by_status: Dict[RoomStatus, int]  # Status -> count of rooms
    occupancy_rate: float  # Percentage of occupied rooms
    average_daily_rate: Optional[float] = None  # Average room rate

    @validator('occupancy_rate')
    def validate_occupancy_rate(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Occupancy rate must be between 0 and 100')
        return v    


class BookingBasicInfo(BaseModelConfig):
    id: UUID
    booking_number: str
    check_in: datetime
    check_out: datetime
    status: str        


class RoomImageBase(BaseModelConfig):
    room_type_id: UUID
    image_url: str = Field(..., max_length=1024)
    thumbnail_url: Optional[str] = Field(None, max_length=1024)
    is_primary: bool = Field(default=False)
    display_order: Optional[int] = Field(default=99)

class RoomImageCreate(RoomImageBase):
    pass

class RoomImageUpdate(BaseModelConfig):
    thumbnail_url: Optional[str] = Field(None, max_length=1024)
    is_primary: Optional[bool] = None
    display_order: Optional[int] = None
