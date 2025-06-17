# app/models/booking/booking.py
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Enum, Integer, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin
from app.models.enums import BookingStatus
from sqlalchemy.dialects.postgresql import UUID

class Booking(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):  # Thêm SoftDeleteMixin
    __tablename__ = "bookings"

    # Foreign keys với UUID type
    hotel_id = Column(UUID(as_uuid=True), ForeignKey("hotels.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    # Thông tin booking
    booking_number = Column(String(50), unique=True, nullable=False, index=True)
    check_in = Column(DateTime, nullable=False, index=True)
    check_out = Column(DateTime, nullable=False, index=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    
    # Thông tin khách
    adult_count = Column(Integer, nullable=False, default=1)
    children_count = Column(Integer, nullable=False, default=0)
    guest_name = Column(String(255))
    guest_email = Column(String(255))
    guest_phone = Column(String(50))
    
    # Ghi chú và yêu cầu
    special_requests = Column(String(500))
    note = Column(Text)
    
    # Thông tin thanh toán
    total_amount = Column(Float, nullable=False)
    payment_status = Column(String(50), nullable=False, default='pending')
    discount_amount = Column(Float, nullable=False, default=0)
    tax_amount = Column(Float, nullable=False, default=0)
    
    # Thông tin khác
    channel = Column(String(50))  # Nguồn booking (website, OTA, etc.)

    # Relationships
    hotel = relationship("Hotel", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")
    rooms = relationship("BookingRoom", back_populates="booking", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Booking {self.booking_number}>"

    @property
    def is_active(self):
        """Check if booking is active (confirmed or checked in)"""
        return self.status in [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]

    @property
    def total_paid(self):
        """Calculate total amount paid"""
        return sum(payment.amount for payment in self.payments 
                  if payment.status == 'completed' and not payment.deleted_at)

    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.total_amount - self.total_paid

    @property
    def nights(self):
        """Calculate number of nights"""
        if self.check_in and self.check_out:
            return (self.check_out.date() - self.check_in.date()).days
        return 0

    @property
    def room_count(self):
        """Get number of rooms booked"""
        return len([room for room in self.rooms if not room.deleted_at])

    def can_be_cancelled(self):
        """Check if booking can be cancelled"""
        return self.status not in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]

    def can_be_modified(self):
        """Check if booking can be modified"""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]