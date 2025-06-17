# app/models/enums/hotel.py
from enum import Enum

class HotelStatus(str, Enum):
    DRAFT = 'DRAFT'
    PENDING = 'PENDING'  
    PUBLISHED = 'PUBLISHED'
    SUSPENDED = 'SUSPENDED'
    MAINTENANCE = 'MAINTENANCE'
    ARCHIVED = 'ARCHIVED'

class RoomStatus(str, Enum):
    AVAILABLE = "AVAILABLE"     # Phòng trống
    OCCUPIED = "OCCUPIED"       # Đã có người ở
    MAINTENANCE = "MAINTENANCE" # Đang bảo trì
    BLOCKED = "BLOCKED"         # Đã khóa
    CLEANING = "CLEANING"       # Đang dọn dẹp

class RoomType(str, Enum):
    SINGLE = "SINGLE"       # Phòng đơn
    DOUBLE = "DOUBLE"       # Phòng đôi
    TWIN = "TWIN"          # Phòng 2 giường đơn
    TRIPLE = "TRIPLE"      # Phòng 3 người
    QUAD = "QUAD"          # Phòng 4 người
    SUITE = "SUITE"        # Phòng suite
    DELUXE = "DELUXE"      # Phòng deluxe
    EXECUTIVE = "EXECUTIVE" # Phòng executive
    FAMILY = "FAMILY"      # Phòng gia đình
    VILLA = "VILLA"        # Biệt thự

class BedType(str, Enum):
    SINGLE = "SINGLE"      # Giường đơn
    TWIN = "TWIN"         # 2 giường đơn
    DOUBLE = "DOUBLE"     # Giường đôi
    QUEEN = "QUEEN"       # Giường queen
    KING = "KING"        # Giường king
    EXTRA = "EXTRA"      # Giường phụ