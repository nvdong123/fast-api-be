"""
app/schemas/zalo.py
Pydantic models for Zalo integration
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class ZaloEventType(str, Enum):
    """Các loại event từ Zalo Webhook"""
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    USER_SEND_TEXT = "user_send_text"
    USER_SEND_IMAGE = "user_send_image"
    USER_SEND_STICKER = "user_send_sticker"
    USER_SEND_GIF = "user_send_gif"
    USER_SEND_AUDIO = "user_send_audio"
    USER_SEND_FILE = "user_send_file"

class TokenBase(BaseModel):
    """Schema cơ bản cho Zalo Token"""
    access_token: str = Field(..., description="Access token từ Zalo")
    expires_at: datetime = Field(..., description="Thời điểm token hết hạn")

class TokenCreate(TokenBase):
    """Schema cho việc tạo mới token"""
    refresh_token: Optional[str] = Field(None, description="Refresh token từ Zalo")

class TokenUpdate(TokenBase):
    """Schema cho việc cập nhật token"""
    refresh_token: Optional[str] = None

class TokenInDB(TokenBase):
    """Schema cho token trong database"""
    id: str = Field(..., description="ID của token record")
    refresh_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ZaloUser(BaseModel):
    """Schema cho thông tin user Zalo"""
    id: str = Field(..., description="Zalo User ID")
    display_name: Optional[str] = Field(None, description="Tên hiển thị")
    avatar: Optional[str] = Field(None, description="URL avatar")
    shared_info: Optional[Dict[str, Any]] = Field(None, description="Thông tin được chia sẻ")
    tags: Optional[List[str]] = Field(default_factory=list, description="Các tags của user")
    
    @validator('id')
    def validate_user_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('User ID không hợp lệ')
        return v

class ZaloMessage(BaseModel):
    """Schema cho tin nhắn Zalo"""
    msg_id: Optional[str] = Field(None, description="ID của tin nhắn")
    text: Optional[str] = Field(None, description="Nội dung text")
    attachment: Optional[Dict[str, Any]] = Field(None, description="File đính kèm")
    tracking_id: Optional[str] = Field(None, description="ID theo dõi tin nhắn")

    @validator('text')
    def validate_text(cls, v):
        if v and len(v) > 2000:  # Zalo giới hạn độ dài tin nhắn
            raise ValueError('Tin nhắn quá dài')
        return v

class ZaloWebhookEvent(BaseModel):
    """Schema cho Zalo webhook event"""
    app_id: str = Field(..., description="App ID")
    event_name: ZaloEventType = Field(..., description="Tên event")
    sender: Optional[ZaloUser] = Field(None, description="Người gửi")
    recipient: Optional[ZaloUser] = Field(None, description="Người nhận")
    message: Optional[ZaloMessage] = Field(None, description="Nội dung tin nhắn")
    timestamp: datetime = Field(..., description="Thời gian nhận event")

class MessageRequest(BaseModel):
    """Schema cho request gửi tin nhắn"""
    user_id: str = Field(..., description="ID người nhận")
    message: str = Field(..., description="Nội dung tin nhắn")
    
    @validator('message')
    def validate_message(cls, v):
        if not v:
            raise ValueError('Tin nhắn không được để trống')
        if len(v) > 2000:
            raise ValueError('Tin nhắn quá dài')
        return v

class ImageMessageRequest(BaseModel):
    """Schema cho request gửi tin nhắn hình ảnh"""
    user_id: str = Field(..., description="ID người nhận")
    image_url: str = Field(..., description="URL hình ảnh")
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL hình ảnh không hợp lệ')
        return v

class TagRequest(BaseModel):
    """Schema cho request gắn/gỡ tag"""
    user_id: str = Field(..., description="ID người dùng")
    tag_name: str = Field(..., description="Tên tag")
    
    @validator('tag_name')
    def validate_tag_name(cls, v):
        if not v or len(v) > 50:
            raise ValueError('Tên tag không hợp lệ')
        return v

class MessageResponse(BaseModel):
    """Schema cho response khi gửi tin nhắn"""
    message_id: Optional[str] = Field(None, description="ID tin nhắn")
    success: bool = Field(..., description="Trạng thái gửi tin nhắn")
    error: Optional[str] = Field(None, description="Thông tin lỗi nếu có")

class UserProfileResponse(BaseModel):
    """Schema cho response khi lấy thông tin user"""
    id: str
    display_name: Optional[str]
    avatar: Optional[str]
    shared_info: Optional[Dict[str, Any]]
    tags: List[str] = Field(default_factory=list)
    followed: bool = Field(..., description="Trạng thái follow OA")
    error: Optional[str] = None

class ErrorResponse(BaseModel):
    """Schema cho response lỗi"""
    error_code: int = Field(..., description="Mã lỗi")
    error_message: str = Field(..., description="Thông báo lỗi")
    error_data: Optional[Dict[str, Any]] = Field(None, description="Dữ liệu lỗi bổ sung")