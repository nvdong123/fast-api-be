import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    HOTEL_ADMIN = "HOTEL_ADMIN"
    STAFF = "STAFF"
    USER = "USER"