from typing import Any
from datetime import datetime
import uuid
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy import Column, DateTime, String, Boolean

class CustomBase:
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

Base = declarative_base(cls=CustomBase)

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    # is_deleted = Column(Boolean, default=False)

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()
        # self.is_deleted = True

class UUIDMixin:
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))