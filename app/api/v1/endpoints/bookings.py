from fastapi import APIRouter, Depends
from typing import List
from app.schemas.booking import BookingCreate, BookingResponse
from uuid import UUID
from app.api.deps import get_db
from sqlalchemy.orm import Session


router = APIRouter()


@router.post("/bookings")
async def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):
    # Tạo booking
    db_booking = crud_booking.create(db, obj_in=booking)
    
    # Chuẩn bị data
    booking_data = {
        "booking_id": db_booking.id,
        "room_name": db_booking.room.name,
        "check_in": db_booking.check_in.strftime("%d/%m/%Y"),
        "check_out": db_booking.check_out.strftime("%d/%m/%Y"),
        "guests": db_booking.guests,
        "total_price": db_booking.total_price
    }
    
    # Gửi notification
    await zalo_api.send_booking_notification(
        user_id=booking.user_id,
        booking_data=booking_data
    )
    
    return db_booking

@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: UUID):
    pass

@router.get("/bookings/", response_model=List[BookingResponse])
async def get_bookings():
    pass
