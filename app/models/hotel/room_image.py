# app/models/hotel/room_image.py
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin
from sqlalchemy.dialects.postgresql import UUID

class RoomImage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "room_images" 

    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    image_url = Column(String(1024), nullable=False)
    thumbnail_url = Column(String(1024))
    is_primary = Column(Boolean, default=False)
    display_order = Column(Integer)
    
    # room = relationship("Room", back_populates="images")

class RoomTypeImage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "room_type_images"

    room_type_id = Column(UUID(as_uuid=True), ForeignKey("room_types.id"), nullable=False)
    image_url = Column(String(1024), nullable=False)
    thumbnail_url = Column(String(1024))
    is_primary = Column(Boolean, default=False)
    display_order = Column(Integer)

    room_type = relationship("RoomType", back_populates="images")