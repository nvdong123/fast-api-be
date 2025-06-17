# app/api/v1/endpoints/rooms.py
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, date
from app.api import deps
from app.models.hotel.room import Room, RoomType
from app.models.hotel.room_image import RoomImage
from app.models.enums import RoomStatus
from app.schemas.room import (
    RoomCreate, RoomUpdate, RoomResponse, RoomWithDetails,
    RoomFilter, RoomFilterResponse, RoomTypeCreate,
    RoomTypeUpdate, RoomTypeResponse, RoomTypeSummary,
    RoomSummary, RoomTypeInfo, RoomImageResponse
)
from app.core.config import settings
from uuid import UUID
import uuid

import shutil
import os
from uuid import uuid4
from PIL import Image
from fastapi import UploadFile, HTTPException
from app.models.hotel.room_image import RoomImage
from app.schemas.room_image import ImageUploadResponse
from fastapi.responses import FileResponse


router = APIRouter()

@router.get("/", response_model=RoomFilterResponse)
async def get_rooms(
    hotel_id: Optional[UUID] = None,
    room_type_id: Optional[UUID] = None,
    status: Optional[RoomStatus] = None,
    floor: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_occupancy: Optional[int] = None,
    max_occupancy: Optional[int] = None,
    available_from: Optional[datetime] = None,
    available_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """Get list of rooms with filtering"""
    # Base query
    query = db.query(Room).options(
        joinedload(Room.room_type),
        joinedload(Room.hotel)
    ).filter(Room.deleted_at.is_(None))

    # Apply filters
    if hotel_id:
        query = query.filter(Room.hotel_id == hotel_id)
    if room_type_id:
        query = query.filter(Room.room_type_id == room_type_id)
    if status:
        query = query.filter(Room.status == status)
    if floor:
        query = query.filter(Room.floor == floor)
    if is_active is not None:
        query = query.filter(Room.is_active == is_active)
    if search:
        query = query.filter(Room.room_number.ilike(f"%{search}%"))
    if min_price:
        query = query.join(RoomType).filter(RoomType.base_price >= min_price)
    if max_price:
        query = query.join(RoomType).filter(RoomType.base_price <= max_price)
    if min_occupancy:
        query = query.join(RoomType).filter(RoomType.base_occupancy >= min_occupancy)
    if max_occupancy:
        query = query.join(RoomType).filter(RoomType.max_occupancy <= max_occupancy)

    # Count total
    total = query.count()

    # Get paginated results
    rooms = query.offset(skip).limit(limit).all()

    # Add extra details
    room_details = []
    for room in rooms:
        detail = RoomWithDetails(
            **room.__dict__,
            hotel_name=room.hotel.name if room.hotel else None,
            room_type_name=room.room_type.name if room.room_type else None,
            is_available=room.status == RoomStatus.AVAILABLE
        )
        room_details.append(detail)

    return RoomFilterResponse(
        total=total,
        rooms=room_details,
        has_more=total > skip + limit,
        page=(skip // limit) + 1,
        total_pages=(total + limit - 1) // limit
    )

@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    room: RoomUpdate,
    db: Session = Depends(deps.get_db)
):
    """Update room details"""
    db_room = db.query(Room).filter(
        Room.id == room_id,
        Room.deleted_at.is_(None)
    ).first()
    
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    print("db_room", db_room)
    # Debug information
    print("Input room data:", room)
    
    # Convert Pydantic model to dict, excluding unset fields
    update_data = room.model_dump(exclude_unset=True)
    print("Update data after model_dump:", update_data)
    
    # Handle images field
    if 'images' in update_data:
        images = update_data.pop('images')
        print("Images data:", images)
        # Ensure images is a list
        if images is None:
            db_room.images = []
        else:
            db_room.images = list(images)

    # Handle amenities field
    if 'amenities' in update_data:
        amenities = update_data.pop('amenities')
        print("Amenities data:", amenities)
        # Ensure amenities is a list
        if amenities is None:
            db_room.amenities = []
        else:
            db_room.amenities = list(amenities)

    # Update remaining fields
    for field, value in update_data.items():
        setattr(db_room, field, value)

    try:
        db.commit()
        db.refresh(db_room)
        return db_room
    except Exception as e:
        print("Error updating room:", str(e))
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/", response_model=RoomResponse)
async def create_room(
    room: RoomCreate,
    db: Session = Depends(deps.get_db)
):
    """Create new room"""
    # Validate room_type exists
    room_type = db.query(RoomType).filter(
        RoomType.id == room.room_type_id,
        RoomType.deleted_at.is_(None)
    ).first()
    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    # Convert Pydantic model to dict
    room_data = room.model_dump()
    
    # Extract special fields
    images = room_data.pop('images', []) or []
    amenities = room_data.pop('amenities', []) or []

    # Create room instance
    db_room = Room(**room_data)
    db_room.images = images
    db_room.amenities = amenities

    try:
        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        return db_room
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{room_id}")
async def delete_room(
    room_id: UUID,
    db: Session = Depends(deps.get_db)
):
    """Soft delete room"""
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    db_room.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Room deleted successfully"}

@router.get("/hotel/{hotel_id}/summary", response_model=RoomSummary)
async def get_hotel_room_summary(
    hotel_id: UUID,
    db: Session = Depends(deps.get_db)
):
    """Get room summary statistics for a hotel"""
    # Get total counts by status
    status_counts = db.query(
        Room.status,
        func.count(Room.id).label('count')
    ).filter(
        Room.hotel_id == hotel_id,
        Room.deleted_at.is_(None)
    ).group_by(Room.status).all()

    # Convert to dict
    by_status = {s[0]: s[1] for s in status_counts}

    # Get counts by floor
    floor_counts = db.query(
        Room.floor,
        func.count(Room.id).label('count')
    ).filter(
        Room.hotel_id == hotel_id,
        Room.deleted_at.is_(None)
    ).group_by(Room.floor).all()

    by_floor = {f[0] or 'unspecified': f[1] for f in floor_counts}

    # Get room type summaries
    room_types = db.query(RoomType).join(Room).filter(
        Room.hotel_id == hotel_id,
        Room.deleted_at.is_(None)
    ).all()

    by_type = []
    for rt in room_types:
        total = sum(1 for r in rt.rooms if not r.deleted_at and r.hotel_id == hotel_id)
        available = sum(1 for r in rt.rooms 
                       if not r.deleted_at 
                       and r.hotel_id == hotel_id 
                       and r.status == RoomStatus.AVAILABLE)
        by_type.append(RoomTypeSummary(
            id=rt.id,
            name=rt.name,
            base_price=rt.base_price,
            total_rooms=total,
            available_rooms=available,
            thumbnail_url=next((img.thumbnail_url for img in rt.images if img.is_primary), None)
        ))

    # Calculate totals
    total_rooms = sum(c for c in by_status.values())
    occupied_rooms = by_status.get(RoomStatus.OCCUPIED, 0)
    
    return RoomSummary(
        total_rooms=total_rooms,
        available_rooms=by_status.get(RoomStatus.AVAILABLE, 0),
        occupied_rooms=occupied_rooms,
        maintenance_rooms=by_status.get(RoomStatus.MAINTENANCE, 0),
        by_type=by_type,
        by_floor=by_floor,
        by_status=by_status,
        occupancy_rate=round((occupied_rooms / total_rooms * 100) if total_rooms else 0, 2)
    )

@router.get("/types", response_model=List[RoomTypeResponse])
async def get_room_types(
    hotel_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(deps.get_db)
):
    """Get list of room types"""
    query = db.query(RoomType).options(
        joinedload(RoomType.images),
        joinedload(RoomType.rooms)
    ).filter(RoomType.deleted_at.is_(None))

    if hotel_id:
        query = query.join(Room).filter(Room.hotel_id == hotel_id)
    if search:
        query = query.filter(RoomType.name.ilike(f"%{search}%"))

    room_types = query.all()
    return room_types

@router.get("/types/{room_type_id}", response_model=RoomTypeResponse)
async def get_room_type(
    room_type_id: UUID,
    db: Session = Depends(deps.get_db)
):
    """Get room type details by ID"""
    room_type = db.query(RoomType).options(
        joinedload(RoomType.images),
        joinedload(RoomType.rooms)
    ).filter(
        RoomType.id == room_type_id,
        RoomType.deleted_at.is_(None)
    ).first()

    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")
    
    return room_type

@router.post("/types", response_model=RoomTypeResponse)
async def create_room_type(
    room_type: RoomTypeCreate,
    db: Session = Depends(deps.get_db)
):
    """Create new room type"""
    # Validate base price
    if room_type.base_price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Base price must be greater than zero"
        )

    # Validate occupancy
    if room_type.max_occupancy < room_type.base_occupancy:
        raise HTTPException(
            status_code=400,
            detail="Max occupancy must be greater than or equal to base occupancy"
        )

    db_room_type = RoomType(**room_type.dict())
    db.add(db_room_type)
    db.commit()
    db.refresh(db_room_type)
    return db_room_type

@router.put("/types/{room_type_id}", response_model=RoomTypeResponse)
async def update_room_type(
    room_type_id: UUID,
    room_type: RoomTypeUpdate,
    db: Session = Depends(deps.get_db)
):
    """Update room type details"""
    db_room_type = db.query(RoomType).filter(
        RoomType.id == room_type_id,
        RoomType.deleted_at.is_(None)
    ).first()
    
    if not db_room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    # Validate base price if provided
    if room_type.base_price is not None and room_type.base_price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Base price must be greater than zero"
        )

    # Validate occupancy if both values provided
    if room_type.max_occupancy is not None and room_type.base_occupancy is not None:
        if room_type.max_occupancy < room_type.base_occupancy:
            raise HTTPException(
                status_code=400,
                detail="Max occupancy must be greater than or equal to base occupancy"
            )

    # Update fields
    for field, value in room_type.dict(exclude_unset=True).items():
        setattr(db_room_type, field, value)

    db.commit()
    db.refresh(db_room_type)
    return db_room_type

@router.delete("/types/{room_type_id}")
async def delete_room_type(
    room_type_id: UUID,
    db: Session = Depends(deps.get_db)
):
    """Soft delete room type"""
    db_room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
    if not db_room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    # Check if there are active rooms using this type
    active_rooms = db.query(Room).filter(
        Room.room_type_id == room_type_id,
        Room.deleted_at.is_(None),
        Room.status != RoomStatus.MAINTENANCE
    ).count()

    if active_rooms > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete room type with {active_rooms} active rooms"
        )

    db_room_type.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Room type deleted successfully"}

@router.post("/types/{room_type_id}/images", response_model=RoomImageResponse)
async def upload_room_type_image(
    room_type_id: UUID,
    file: UploadFile = File(...),
    is_primary: bool = False,
    display_order: Optional[int] = None,
    db: Session = Depends(deps.get_db)
):
    """Upload image for room type"""
    room_type = db.query(RoomType).filter(
        RoomType.id == room_type_id,
        RoomType.deleted_at.is_(None)
    ).first()
    
    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Allowed types: jpg, jpeg, png, gif, webp"
            )
            
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Save file
        file_location = f"{settings.MEDIA_ROOT}/room-types/{unique_filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Create thumbnail
        thumbnail_filename = f"thumb_{unique_filename}"
        thumbnail_location = f"{settings.MEDIA_ROOT}/room-types/{thumbnail_filename}"
        
        # Get max display order if not provided
        if display_order is None:
            max_order = db.query(func.max(RoomImage.display_order)).filter(
                RoomImage.room_type_id == room_type_id
            ).scalar() or 0
            display_order = max_order + 1

        # If is_primary, unset other primary images
        if is_primary:
            db.query(RoomImage).filter(
                RoomImage.room_type_id == room_type_id,
                RoomImage.is_primary == True
            ).update({"is_primary": False})

        # Create image record
        image = RoomImage(
            room_type_id=room_type_id,
            image_url=f"{settings.MEDIA_URL}/room-types/{unique_filename}",
            thumbnail_url=f"{settings.MEDIA_URL}/room-types/{thumbnail_filename}",
            is_primary=is_primary,
            display_order=display_order,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(image)
        db.commit()
        db.refresh(image)
        
        return RoomImageResponse(
            id=image.id,
            room_type_id=image.room_type_id,
            image_url=image.image_url,
            thumbnail_url=image.thumbnail_url,
            is_primary=image.is_primary,
            display_order=image.display_order,
            created_at=image.created_at,
            updated_at=image.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not upload image: {str(e)}"
        )

@router.delete("/types/{room_type_id}/images/{image_id}")
async def delete_room_image(
    room_type_id: UUID,
    image_id: UUID,
    db: Session = Depends(deps.get_db)
):
    """Delete room type image"""
    image = db.query(RoomImage).filter(
        RoomImage.id == image_id,
        RoomImage.room_type_id == room_type_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete file
    try:
        os.remove(f"{settings.MEDIA_ROOT}/room-types/{image.image_url.split('/')[-1]}")
        if image.thumbnail_url:
            os.remove(f"{settings.MEDIA_ROOT}/room-types/{image.thumbnail_url.split('/')[-1]}")
    except:
        pass  # Ignore file deletion errors

    db.delete(image)
    db.commit()
    return {"message": "Image deleted successfully"}

@router.post("/upload-image", response_model=ImageUploadResponse) 
async def upload_room_image(
    file: UploadFile,
    db: Session = Depends(deps.get_db)
):
    """Upload image for room"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )

        filename = f"{uuid4()}.{file_extension}"
        file_location = f"{settings.MEDIA_ROOT}/rooms/{filename}"
        
        # Create rooms directory if not exists
        os.makedirs(os.path.dirname(file_location), exist_ok=True)

        # Save original file
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Create thumbnail
        image = Image.open(file_location)
        image.thumbnail((300, 300))  # Max thumbnail size
        thumb_filename = f"thumb_{filename}"
        thumb_location = f"{settings.MEDIA_ROOT}/rooms/{thumb_filename}"
        image.save(thumb_location)

        return ImageUploadResponse(
            url=f"/media/rooms/{filename}",
            thumbnail_url=f"/media/rooms/{thumb_filename}"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images/{image_path:path}")
async def get_room_image(image_path: str):
    """Get room image by path"""
    file_location = f"{settings.PARRENT_DIR}/{image_path}"
    print(file_location)
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="Image not found")
        
    return FileResponse(file_location)