# Enums for message types and status
from enum import Enum

class MessageType(str, Enum):
    """Enum for message types"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    STICKER = "sticker"
    GIF = "gif"
    AUDIO = "audio"
    VIDEO = "video"
    LINK = "link"


class MessageDirection(str, Enum):
    """Enum for message direction"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class MessageStatus(str, Enum):
    """Enum for message status"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class AttachmentType(str, Enum):
    """Enum for attachment types"""
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    STICKER = "sticker"
    GIF = "gif"
    LINK = "link"