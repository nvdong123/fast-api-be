from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin

class BookingRoom(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "booking_rooms"

    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=False)
    room_price = Column(Float, nullable=False)
    extra_person_count = Column(Integer, default=0)

    # Relationships
    booking = relationship("Booking", back_populates="rooms")
    room = relationship("Room", back_populates="bookings")
