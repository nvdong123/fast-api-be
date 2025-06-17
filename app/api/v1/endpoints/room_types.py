from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
import uuid
import shutil
import os

from app.api import deps
from app.models.hotel.room import Room, RoomType
from app.models.hotel.room_image import RoomImage
from app.models.enums import RoomStatus
from app.schemas.room import (
    RoomTypeCreate,
    RoomTypeUpdate,
    RoomTypeResponse,
    RoomTypeSummary,
    RoomImageResponse
)
from app.core.config import settings
from uuid import UUID


router = APIRouter()

@router.get("/", response_model=List[RoomTypeResponse])
async def get_room_types(
    hotel_id: UUID = Query(None, description="Filter by hotel ID"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db)
):
    """
    Get list of room types with optional filtering
    """    
    query = db.query(RoomType).options(
        joinedload(RoomType.images),
        joinedload(RoomType.rooms)
    ).filter(RoomType.deleted_at.is_(None), RoomType.hotel_id == hotel_id)

    # if hotel_id:
    #     query = query.join(Room).filter(
    #         Room.hotel_id == hotel_id,
    #         Room.deleted_at.is_(None)
    #     ).group_by(RoomType.id)

    if search:
        query = query.filter(RoomType.name.ilike(f"%{search}%"))
    
    total = query.count()
    room_types = query.offset(skip).limit(limit).all()
    print(room_types)

    return room_types

@router.get("/{type_id}", response_model=RoomTypeResponse)
async def get_room_type(
    type_id: UUID,
    db: Session = Depends(deps.get_db)
):
    """
    Get room type details by ID
    """
    room_type = db.query(RoomType).options(
        joinedload(RoomType.images),
        joinedload(RoomType.rooms)
    ).filter(
        RoomType.id == type_id,
        RoomType.deleted_at.is_(None)
    ).first()

    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")
    
    return room_type

@router.post("/", response_model=RoomTypeResponse)
async def create_room_type(
    room_type: RoomTypeCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Create new room type
    """
    # Validate occupancy
    if room_type.max_occupancy < room_type.base_occupancy:
        raise HTTPException(
            status_code=400,
            detail="Max occupancy must be greater than or equal to base occupancy"
        )

    # Validate price
    if room_type.base_price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Base price must be greater than zero"
        )

    db_room_type = RoomType(**room_type.dict())
    db.add(db_room_type)
    db.commit()
    db.refresh(db_room_type)

    return db_room_type

@router.put("/{type_id}", response_model=RoomTypeResponse)
async def update_room_type(
    type_id: UUID,
    room_type: RoomTypeUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Update room type details
    """
    db_room_type = db.query(RoomType).filter(
        RoomType.id == type_id,
        RoomType.deleted_at.is_(None)
    ).first()

    if not db_room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    update_data = room_type.dict(exclude_unset=True)

    # Validate occupancy if updating
    if 'max_occupancy' in update_data and 'base_occupancy' in update_data:
        if update_data['max_occupancy'] < update_data['base_occupancy']:
            raise HTTPException(
                status_code=400,
                detail="Max occupancy must be greater than or equal to base occupancy"
            )

    # Update fields
    for field, value in update_data.items():
        setattr(db_room_type, field, value)

    db.commit()
    db.refresh(db_room_type)
    return db_room_type

@router.delete("/{type_id}")
async def delete_room_type(
    type_id: UUID,
    db: Session = Depends(deps.get_db)
):
    """
    Soft delete room type and mark associated rooms as maintenance
    """
    db_room_type = db.query(RoomType).filter(RoomType.id == type_id).first()
    if not db_room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    # Check for active bookings
    active_rooms = db.query(Room).filter(
        Room.room_type_id == type_id,
        Room.deleted_at.is_(None),
        Room.status == RoomStatus.OCCUPIED
    ).count()

    if active_rooms > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete room type with {active_rooms} occupied rooms"
        )

    # Mark associated rooms as maintenance
    db.query(Room).filter(
        Room.room_type_id == type_id,
        Room.deleted_at.is_(None)
    ).update({
        "status": RoomStatus.MAINTENANCE,
        "updated_at": datetime.utcnow()
    })

    # Soft delete room type
    db_room_type.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "Room type deleted successfully"}

# Endpoints for room type images
@router.post("/{type_id}/images", response_model=RoomImageResponse)
async def upload_room_type_image(
    type_id: UUID,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    db: Session = Depends(deps.get_db)
):
    """Upload image for room type"""
    room_type = db.query(RoomType).filter(
        RoomType.id == type_id,
        RoomType.deleted_at.is_(None)
    ).first()
    
    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    # Validate file
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['jpg', 'jpeg', 'png']:
        raise HTTPException(
            status_code=400,
            detail="Only jpg, jpeg and png files are allowed"
        )

    try:
        # Tạo thư mục uploads nếu chưa tồn tại
        upload_dir = settings.UPLOAD_DIR / f"room-types/{type_id}"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = upload_dir / unique_filename

        # Đường dẫn tương đối để lưu vào database
        relative_path = f"room-types/{type_id}/{unique_filename}"
        
        # Lưu file
        with file_path.open("wb+") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update primary status if needed
        if is_primary:
            db.query(RoomImage).filter(
                RoomImage.room_type_id == type_id,
                RoomImage.is_primary == True
            ).update({"is_primary": False})

        # Get next display order
        max_order = db.query(func.coalesce(func.max(RoomImage.display_order), 0))\
            .filter(RoomImage.room_type_id == type_id)\
            .scalar()

        # Create image record
        image = RoomImage(
            room_type_id=type_id,
            image_url=f"/uploads/{relative_path}",
            thumbnail_url=None,  # TODO: Implement thumbnail generation
            is_primary=is_primary,
            display_order=max_order + 1
        )

        db.add(image)
        db.commit()
        db.refresh(image)

        return image

    except Exception as e:
        # Cleanup file if upload failed
        if 'file_path' in locals() and file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{type_id}/images/{image_id}")
async def delete_room_type_image(
    type_id: UUID,
    image_id: UUID,
    db: Session = Depends(deps.get_db)
):
    """Delete room type image"""
    image = db.query(RoomImage).filter(
        RoomImage.id == image_id,
        RoomImage.room_type_id == type_id
    ).first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        # Remove physical file
        if image.image_url:
            file_path = settings.UPLOAD_DIR / image.image_url.replace('/uploads/', '')
            if file_path.exists():
                os.remove(file_path)
                
            # Remove thumbnail if exists    
            if image.thumbnail_url:
                thumb_path = settings.UPLOAD_DIR / image.thumbnail_url.replace('/uploads/', '')
                if thumb_path.exists():
                    os.remove(thumb_path)

        # Delete empty folders if no other images exist
        folder_path = settings.UPLOAD_DIR / f"room-types/{type_id}"
        if folder_path.exists() and not any(folder_path.iterdir()):
            folder_path.rmdir()

        db.delete(image)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting image: {str(e)}"
        )

    return {"message": "Image deleted successfully"}
@router.put("/{type_id}/images/{image_id}", response_model=RoomImageResponse)
async def update_room_type_image(
    type_id: UUID,
    image_id: UUID,
    is_primary: bool = Body(...),
    display_order: Optional[int] = Body(None),
    db: Session = Depends(deps.get_db)
):
    """Update room type image properties"""
    image = db.query(RoomImage).filter(
        RoomImage.id == image_id,
        RoomImage.room_type_id == type_id
    ).first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Update primary status
    if is_primary:
        db.query(RoomImage).filter(
            RoomImage.room_type_id == type_id,
            RoomImage.is_primary == True
        ).update({"is_primary": False})
        
    image.is_primary = is_primary
    if display_order is not None:
        image.display_order = display_order

    db.commit()
    db.refresh(image)

    return image