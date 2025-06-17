# app/api/v1/endpoints/hotels.py
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload  # Thêm joinedload vào đây
from sqlalchemy import func, case
from datetime import datetime
from app.api import deps
from app.models.hotel.hotel import Hotel
from app.models.tenant.tenant import Tenant
from app.models.booking.booking import Booking
from app.models.enums.hotel import HotelStatus
from app.models.enums.tenant import TenantStatus
from app.models.enums import RoomStatus  # Thêm import RoomStatus
from app.schemas.hotel import (
    HotelCreate, HotelUpdate, HotelResponse, HotelListResponse,
    HotelStatusUpdate, HotelStatsResponse
)
from app.core.config import settings
import uuid
import shutil
import os

router = APIRouter()

@router.get("/", response_model=List[HotelResponse])
async def get_hotels(
    tenant_id: Optional[str] = None,
    status: Optional[HotelStatus] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Get list of hotels
    """
    query = db.query(Hotel).options(
        joinedload(Hotel.rooms),
        joinedload(Hotel.tenant),
        joinedload(Hotel.bookings)  # Thêm eager loading cho bookings
    ).filter(Hotel.deleted_at.is_(None))

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id is required"
        )
    
    query = query.filter(Hotel.tenant_id == tenant_id)

    # Apply filters
    if status:
        try:
            hotel_status = HotelStatus(status)
            query = query.filter(Hotel.status == hotel_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join([e.value for e in HotelStatus])}"
            )

    if is_active is not None:
        query = query.filter(Hotel.is_active == is_active)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            Hotel.name.ilike(search_filter) |
            Hotel.city.ilike(search_filter) |
            Hotel.country.ilike(search_filter)
        )

    hotels = query.offset(skip).limit(limit).all()

    # Calculate stats for each hotel
    for hotel in hotels:
        hotel.tenant_name = hotel.tenant.name
        
        # Get room type summary
        room_types = {}
        for room in hotel.rooms:
            if not room.deleted_at and room.room_type:
                room_type = room.room_type.name
                if room_type not in room_types:
                    room_types[room_type] = {
                        'type': room_type,
                        'count': 0,
                        'min_price': None,
                        'max_price': None
                    }
                room_types[room_type]['count'] += 1
                price = room.room_type.base_price
                if room_types[room_type]['min_price'] is None or price < room_types[room_type]['min_price']:
                    room_types[room_type]['min_price'] = price
                if room_types[room_type]['max_price'] is None or price > room_types[room_type]['max_price']:
                    room_types[room_type]['max_price'] = price
        
        hotel.room_types = list(room_types.values())
        
        # Set cached values for properties
        hotel._total_rooms = len([r for r in hotel.rooms if not r.deleted_at])
        hotel._available_rooms = len([r for r in hotel.rooms if not r.deleted_at and r.status == RoomStatus.AVAILABLE])
        hotel._total_bookings = len([b for b in hotel.bookings if not b.deleted_at])

    return hotels
    
@router.post("/", response_model=HotelResponse)
async def create_hotel(
    hotel: HotelCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Create new hotel
    """
    # Validate tenant_id
    tenant = db.query(Tenant).filter(Tenant.id == hotel.tenant_id).first()    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check if tenant can add more hotels
    if not tenant.can_add_hotel():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant has reached maximum hotel limit ({tenant.max_hotels})"
        )

    # Check tenant status
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create hotel for inactive tenant"
        )

    # Create hotel
    db_hotel = Hotel(**hotel.dict())
    db.add(db_hotel)
    
    try:
        db.commit()
        db.refresh(db_hotel)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Add response data
    db_hotel.tenant_name = tenant.name
    return db_hotel

@router.get("/fetch/{hotel_id}", response_model=HotelResponse)
async def get_hotel(
    hotel_id: str,
    db: Session = Depends(deps.get_db)
):
    """
    Get hotel by ID
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Add additional response data
    hotel.tenant_name = hotel.tenant.name
    
    room_types = {}
    for room in hotel.rooms:
        if room.room_type not in room_types:
            room_types[room.room_type] = {
                'count': 0,
                'min_price': None,
                'max_price': None
            }
        room_types[room.room_type]['count'] += 1
        if (room_types[room.room_type]['min_price'] is None or 
            room.price < room_types[room.room_type]['min_price']):
            room_types[room.room_type]['min_price'] = room.price
        if (room_types[room.room_type]['max_price'] is None or 
            room.price > room_types[room.room_type]['max_price']):
            room_types[room.room_type]['max_price'] = room.price
    
    hotel.room_types = [{'type': k, **v} for k, v in room_types.items()]
    hotel.total_bookings = len(hotel.bookings)
    
    return hotel

@router.put("/{hotel_id}", response_model=HotelResponse)
async def update_hotel(
    hotel_id: str,
    hotel_update: HotelUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Update hotel details
    """
    db_hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not db_hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Update fields
    update_data = hotel_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_hotel, field, value)

    db.commit()
    db.refresh(db_hotel)
    
    # Add additional response data
    db_hotel.tenant_name = db_hotel.tenant.name
    
    room_types = {}
    for room in db_hotel.rooms:
        if room.room_type not in room_types:
            room_types[room.room_type] = {
                'count': 0,
                'min_price': None,
                'max_price': None
            }
        room_types[room.room_type]['count'] += 1
        if (room_types[room.room_type]['min_price'] is None or 
            room.price < room_types[room.room_type]['min_price']):
            room_types[room.room_type]['min_price'] = room.price
        if (room_types[room.room_type]['max_price'] is None or 
            room.price > room_types[room.room_type]['max_price']):
            room_types[room.room_type]['max_price'] = room.price
    
    db_hotel.room_types = [{'type': k, **v} for k, v in room_types.items()]
    db_hotel.total_bookings = len(db_hotel.bookings)
    
    return db_hotel

# app/api/v1/endpoints/hotels.py (tiếp tục)
@router.patch("/{hotel_id}/status", response_model=HotelResponse)
async def update_hotel_status(
    hotel_id: str,
    status_update: HotelStatusUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Update hotel status
    """
    db_hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not db_hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Validate status change
    if status_update.status == HotelStatus.PUBLISHED:
        can_publish, message = db_hotel.can_be_published()
        if not can_publish:
            raise HTTPException(
                status_code=400,
                detail=f"Hotel cannot be published: {message}"
            )

    db_hotel.status = status_update.status
    db.commit()
    db.refresh(db_hotel)
    
    # Add additional response data
    db_hotel.tenant_name = db_hotel.tenant.name
    db_hotel.room_types = [{'type': room.room_type, 'count': 1} for room in db_hotel.rooms]
    db_hotel.total_bookings = len(db_hotel.bookings)
    
    return db_hotel

@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotel(
    hotel_id: str,
    db: Session = Depends(deps.get_db)
):
    """
    Delete hotel (soft delete)
    """
    db_hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not db_hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Check if hotel has active bookings
    active_bookings = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.status.in_(['confirmed', 'checked_in'])
    ).count()

    if active_bookings > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete hotel with active bookings"
        )

    db_hotel.deleted_at = datetime.utcnow()
    db_hotel.is_active = False
    db.commit()

@router.get("/tenant/{tenant_id}/stats", response_model=HotelStatsResponse)
async def get_tenant_hotel_stats(
    tenant_id: str,
    db: Session = Depends(deps.get_db)
):
    """
    Get hotel statistics for a tenant
    """
    from sqlalchemy import case
    from app.models.hotel.room import Room
    from app.models.enums import RoomStatus
    from app.models.booking.booking import Booking
    from app.models.enums.booking import BookingStatus

    # Get hotel stats
    stats = db.query(
        func.count(Hotel.id).label('total_hotels'),
        func.sum(case((Hotel.status == HotelStatus.PUBLISHED, 1), else_=0)).label('published_hotels'),
    ).filter(
        Hotel.tenant_id == tenant_id,
        Hotel.deleted_at.is_(None)
    ).first()

    # Get room stats from active hotels
    room_stats = db.query(
        func.count(Room.id).label('total_rooms'),
        func.sum(case((Room.status == RoomStatus.AVAILABLE, 1), else_=0)).label('available_rooms'),
        func.sum(case((Room.status == RoomStatus.OCCUPIED, 1), else_=0)).label('occupied_rooms'),
        func.sum(case((Room.status == RoomStatus.MAINTENANCE, 1), else_=0)).label('maintenance_rooms'),
    ).join(Hotel).filter(
        Hotel.tenant_id == tenant_id,
        Hotel.deleted_at.is_(None),
        Hotel.is_active == True,
        Room.deleted_at.is_(None)
    ).first()

    # Get booking stats
    booking_stats = db.query(
        func.count(Booking.id).label('total_bookings'),
        func.sum(case((
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]), 
            1), else_=0)
        ).label('active_bookings')
    ).join(Hotel).filter(
        Hotel.tenant_id == tenant_id,
        Hotel.deleted_at.is_(None),
        Booking.deleted_at.is_(None)
    ).first()

    return {
        'total_hotels': stats.total_hotels or 0,
        'published_hotels': stats.published_hotels or 0,
        'total_rooms': room_stats.total_rooms or 0,
        'available_rooms': room_stats.available_rooms or 0,
        'occupied_rooms': room_stats.occupied_rooms or 0,
        'maintenance_rooms': room_stats.maintenance_rooms or 0,
        'total_bookings': booking_stats.total_bookings or 0,
        'active_bookings': booking_stats.active_bookings or 0
    }

@router.post("/upload-image")
async def upload_hotel_image(
    file: UploadFile = File(...),
    hotel_id: str = Form(...)
):
    """
    Upload hotel image (thumbnail or gallery)
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )

        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{hotel_id}.{file_extension}"
        
        # Save file
        file_location = f"{settings.MEDIA_ROOT}/hotels/{unique_filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Return file URL
        return {
            "url": f"{settings.MEDIA_URL}/hotels/{unique_filename}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not upload image: {str(e)}"
        )

@router.get("/images/{image_path:path}", response_class=FileResponse)
async def get_hotel_image(image_path: str):
    """
    Get hotel image by path
    """
    try:        
        image_full_path = os.path.join(f"{settings.PARRENT_DIR}", image_path)
        print(image_full_path)
        if not os.path.exists(image_full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        return FileResponse(image_full_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

