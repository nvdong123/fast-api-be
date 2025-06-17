# from app.models.tenant import Tenant
# from app.models.hotel import Hotel, Room, RoomType, RoomImage
# from app.models.booking import Booking, BookingRoom, Payment
# from app.models.user import User, Customer, UserRole
# from app.models.enums.tenant import TenantStatus, SubscriptionPlan, SubscriptionStatus
# from app.models.enums.user import UserRole

from app.db.base_class import Base
from app.models.user.customer import Customer  # noqa
from app.models.user.user import User  # noqa
from app.models.tenant.tenant import Tenant  # noqa
from app.models.hotel.hotel import Hotel  # noqa
from app.models.booking import Booking, BookingRoom, Payment # noqa
from app.models.zalo import ZaloMessage, ZaloToken, ZaloUser, ZaloUserTag

__all__ = ["Base", "Tenant", "User", "Hotel", "Booking", "BookingRoom", "Payment", "ZaloMessage", "ZaloToken", "ZaloUser", "ZaloUserTag"]