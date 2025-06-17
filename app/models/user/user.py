from sqlalchemy import Boolean, Column, String, ForeignKey, Enum, DateTime
from app.models.enums.user import UserRole
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.db.base_class import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin

# class UserRole(str, enum.Enum):
#     SUPER_ADMIN = "super_admin"
#     TENANT_ADMIN = "tenant_admin"
#     HOTEL_ADMIN = "hotel_admin"
#     STAFF = "staff"
#     USER = "user"

class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean(), default=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    
    # Optional fields
    phone = Column(String(50))
    avatar = Column(String(500))
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset fields
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<User {self.email}>"