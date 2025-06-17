from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base, TimestampMixin, UUIDMixin

class Customer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "customers"

    zalo_id = Column(String(255), unique=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))

    # Relationships
    bookings = relationship("Booking", back_populates="customer", cascade="all, delete-orphan")