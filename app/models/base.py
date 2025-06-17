# models/base.py
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from app.db.base_class import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SoftDeleteMixin:
    deleted_at = Column(DateTime, nullable=True)

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()

# class UUIDMixin:
#     id = Column(String(36), primary_key=True, default=generate_uuid)

class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)