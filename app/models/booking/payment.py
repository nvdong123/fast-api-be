from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin
from app.models.enums import PaymentStatus

class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    transaction_id = Column(String(255))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_date = Column(DateTime)

    # Relationships
    booking = relationship("Booking", back_populates="payments")
