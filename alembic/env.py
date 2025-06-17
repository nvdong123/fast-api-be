from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
# from app.db.base import Base
from app.core.config import settings

# Import Base và tất cả models để alembic có thể thấy
from app.models.base import Base

from app.models.tenant.tenant import Tenant
from app.models.user.user import User
from app.models.user.customer import Customer
from app.models.hotel.hotel import Hotel
from app.models.hotel.room import Room, RoomType
from app.models.hotel.room_image import RoomImage
from app.models.booking.booking import Booking
from app.models.booking.booking_room import BookingRoom
from app.models.booking.payment import Payment

from app.models.enums.tenant import TenantStatus, SubscriptionPlan
from app.models.enums.hotel import HotelStatus
from app.models.enums.booking import BookingStatus

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# from app.schemas import *  # Import all schemas
# from app.models import *   # Import all models

# Pass tất cả models vào metadata
# all_models = [Tenant, User, Customer, Hotel, Room, RoomType, RoomImage, Booking, BookingRoom, Payment]
target_metadata = Base.metadata
# target_metadata = None


def get_url():
    return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Thêm config này
        compare_type=True,
        include_schemas=True
    )

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Thêm config này để tự động xử lý thứ tự tạo bảng
            render_as_batch=True,            
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()