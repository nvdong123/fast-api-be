"""
app/models/zalo/__init__.py
Models for Zalo integration
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class ZaloToken(Base):
    """Model for storing Zalo access tokens"""
    __tablename__ = "zalo_tokens"

    id = Column(String, primary_key=True, index=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ZaloUser(Base):
    """Model for storing Zalo user information"""
    __tablename__ = "zalo_users"

    id = Column(String, primary_key=True, index=True)
    zalo_id = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    shared_info = Column(JSON, nullable=True)
    is_following = Column(Boolean, default=False)
    followed_at = Column(DateTime, nullable=True)
    unfollowed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    messages = relationship("ZaloMessage", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("ZaloUserTag", back_populates="user", cascade="all, delete-orphan")


class ZaloMessage(Base):
    """Model for storing Zalo messages"""
    __tablename__ = "zalo_messages"

    id = Column(String, primary_key=True, index=True)
    zalo_message_id = Column(String, nullable=True)
    user_id = Column(String, ForeignKey("zalo_users.id", ondelete="CASCADE"), nullable=False)
    message_type = Column(String, nullable=False)  # text, image, file, etc.
    content = Column(String, nullable=True)
    attachment_type = Column(String, nullable=True)  # image, file, etc.
    attachment_url = Column(String, nullable=True)
    direction = Column(String, nullable=False)  # incoming/outgoing
    status = Column(String, nullable=False)  # sent, delivered, failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("ZaloUser", back_populates="messages")


class ZaloUserTag(Base):
    """Model for storing user tags"""
    __tablename__ = "zalo_user_tags"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("zalo_users.id", ondelete="CASCADE"), nullable=False)
    tag_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("ZaloUser", back_populates="tags")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'tag_name', name='uq_user_tag'),
    )

