# app/models/hotel/room.py
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin
from app.models.enums import RoomStatus
from sqlalchemy.dialects.postgresql import UUID

class Room(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):  # Thêm SoftDeleteMixin vào đây
    __tablename__ = "rooms"

    hotel_id = Column(UUID(as_uuid=True), ForeignKey("hotels.id"), nullable=False)
    room_type_id = Column(UUID(as_uuid=True), ForeignKey("room_types.id"))
    room_number = Column(String(50), nullable=False)
    floor = Column(String(10))
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE)
    is_active = Column(Boolean, default=True)
    images = Column(JSON, default=list)  # Add this
    amenities = Column(JSON, default=list)  # Add this

    # Relationships
    hotel = relationship("Hotel", back_populates="rooms")
    room_type = relationship("RoomType", back_populates="rooms")
    bookings = relationship("BookingRoom", back_populates="room")
    # images = relationship("RoomImage", back_populates="room", cascade="all, delete-orphan")



    def __repr__(self):
        return f"<Room {self.room_number} (Hotel: {self.hotel_id})>"

class RoomType(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):  # Cũng thêm SoftDeleteMixin cho RoomType
    __tablename__ = "room_types"

    name = Column(String(100), nullable=False)
    description = Column(String(500))
    hotel_id = Column(UUID(as_uuid=True), ForeignKey("hotels.id"), nullable=False)
    base_occupancy = Column(Integer, default=2)
    max_occupancy = Column(Integer, default=4)
    base_price = Column(Float, nullable=False)
    extra_person_price = Column(Float, default=0)
    amenities = Column(JSON)

    # Relationships
    rooms = relationship("Room", back_populates="room_type")
    images = relationship("RoomTypeImage", back_populates="room_type", cascade="all, delete-orphan")
