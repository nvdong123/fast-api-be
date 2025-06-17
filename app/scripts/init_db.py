"""create_initial_tables

Revision ID: 001_init_database
Revises: 
Create Date: 2025-01-12 21:14:34.341196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.models.enums.tenant import TenantStatus, SubscriptionPlan
from app.models.enums.hotel import HotelStatus, RoomStatus
from app.models.enums.booking import BookingStatus

# revision identifiers, used by Alembic.
revision: str = '001_init_database'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    # 1. Create enums
    # tenant_status = postgresql.ENUM(TenantStatus, name='tenant_status')
    # tenant_status.create(op.get_bind())
    
    # subscription_plan = postgresql.ENUM(SubscriptionPlan, name='subscription_plan')
    # subscription_plan.create(op.get_bind())
    
    # hotel_status = postgresql.ENUM('draft', 'published', 'archived', 
    #                             name='hotel_status', create_type=False)
    
    # hotel_status.create(op.get_bind())

    # room_status = postgresql.ENUM('available', 'occupied', 'maintenance', 'blocked', 
    #                             name='room_status', create_type=False)
    # room_status.create(op.get_bind())
    
    # booking_status = postgresql.ENUM(BookingStatus, name='booking_status')
    # booking_status.create(op.get_bind())
    
    # Drop existing enums if they exist
    op.execute('DROP TYPE IF EXISTS tenant_status CASCADE')
    op.execute('DROP TYPE IF EXISTS subscription_plan CASCADE')
    op.execute('DROP TYPE IF EXISTS hotel_status CASCADE')
    op.execute('DROP TYPE IF EXISTS booking_status CASCADE')
    op.execute('DROP TYPE IF EXISTS room_status CASCADE')    

    # Create enums
    tenant_status = postgresql.ENUM('active', 'inactive', 'pending', 'suspended', 
                                  name='tenant_status', create_type=False)
    subscription_plan = postgresql.ENUM('free', 'basic', 'premium', 'enterprise', 
                                      name='subscription_plan', create_type=False)
    hotel_status = postgresql.ENUM('draft', 'published', 'archived', 
                                 name='hotel_status', create_type=False)
    room_status = postgresql.ENUM('available', 'occupied', 'maintenance', 'blocked', 
                                name='room_status', create_type=False)
    booking_status = postgresql.ENUM('pending', 'confirmed', 'completed', 'cancelled', 
                                   name='booking_status', create_type=False)

    tenant_status.create(op.get_bind(), checkfirst=True)
    subscription_plan.create(op.get_bind(), checkfirst=True)
    hotel_status.create(op.get_bind(), checkfirst=True)
    booking_status.create(op.get_bind(), checkfirst=True)
    room_status.create(op.get_bind(), checkfirst=True)

    # 2. Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('subdomain', sa.String(255), unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('logo_url', sa.String(512), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('status', sa.Enum(TenantStatus), default=TenantStatus.PENDING),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('max_users', sa.Integer, default=10),
        sa.Column('max_hotels', sa.Integer, default=5),
        sa.Column('subscription_plan', sa.Enum(SubscriptionPlan), default=SubscriptionPlan.FREE),
        sa.Column('subscription_start', sa.DateTime, nullable=True),
        sa.Column('subscription_end', sa.DateTime, nullable=True),
        sa.Column('billing_email', sa.String(255), nullable=True),
        sa.Column('billing_address', sa.Text, nullable=True),
        sa.Column('settings', sa.Text, nullable=True),
        sa.Column('timezone', sa.String(50), default="UTC"),
        sa.Column('locale', sa.String(10), default="en"),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # 3. Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('zalo_id', sa.String(255), unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # 4. Create hotels table
    op.create_table(
        'hotels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('postal_code', sa.String(20)),
        sa.Column('phone', sa.String(50)),
        sa.Column('email', sa.String(255)),
        sa.Column('website', sa.String(255)),
        sa.Column('latitude', sa.Float),
        sa.Column('longitude', sa.Float),
        sa.Column('description', sa.Text),
        sa.Column('star_rating', sa.Integer),
        sa.Column('check_in_time', sa.String(50), default="14:00"),
        sa.Column('check_out_time', sa.String(50), default="12:00"),
        sa.Column('amenities', postgresql.JSONB),
        sa.Column('facilities', postgresql.JSONB),
        sa.Column('rules', postgresql.JSONB),
        sa.Column('policies', sa.Text),
        sa.Column('status', sa.Enum(HotelStatus), default=HotelStatus.DRAFT),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('thumbnail', sa.String(500)),
        sa.Column('gallery', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # 5. Create room_types table
    op.create_table(
        'room_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('base_occupancy', sa.Integer, default=2),
        sa.Column('max_occupancy', sa.Integer, default=4),
        sa.Column('base_price', sa.Float, nullable=False),
        sa.Column('extra_person_price', sa.Float, default=0),
        sa.Column('amenities', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # 6. Create rooms table
    op.create_table(
        'rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('hotel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hotels.id'), nullable=False),
        sa.Column('room_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('room_types.id')),
        sa.Column('room_number', sa.String(50), nullable=False),
        sa.Column('floor', sa.String(10)),
        sa.Column('status', sa.Enum(RoomStatus), default=RoomStatus.AVAILABLE),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # 7. Create bookings table
    op.create_table(
        'bookings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('hotel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hotels.id'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('booking_number', sa.String(50), unique=True, nullable=False),
        sa.Column('check_in', sa.DateTime, nullable=False),
        sa.Column('check_out', sa.DateTime, nullable=False),
        sa.Column('status', sa.Enum(BookingStatus), default=BookingStatus.PENDING),
        sa.Column('total_amount', sa.Float, nullable=False),
        sa.Column('special_requests', sa.String(500)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # 8. Create booking_rooms table
    op.create_table(
        'booking_rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bookings.id'), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rooms.id'), nullable=False),
        sa.Column('room_price', sa.Float, nullable=False),
        sa.Column('extra_person_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # 9. Create payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bookings.id'), nullable=False),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('transaction_id', sa.String(255)),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('payment_date', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # 10. Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('avatar', sa.String(500)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('last_login', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # 11. Create room_images table
    op.create_table(
            'room_images',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('room_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('room_types.id'), nullable=False),
            sa.Column('image_url', sa.String(1024), nullable=False),
            sa.Column('thumbnail_url', sa.String(1024)),
            sa.Column('is_primary', sa.Boolean, default=False),
            sa.Column('display_order', sa.Integer),
            sa.Column('created_at', sa.DateTime, nullable=False),
            sa.Column('updated_at', sa.DateTime, nullable=False),
            sa.Column('deleted_at', sa.DateTime, nullable=True)
        )

def downgrade():
    # Drop tables in reverse order
    op.drop_table('payments')
    op.drop_table('booking_rooms')
    op.drop_table('bookings')
    op.drop_table('rooms')
    op.drop_table('room_types')
    op.drop_table('hotels')
    op.drop_table('customers')
    op.drop_table('tenants')
    op.drop_table('users')
    op.drop_table('room_images')



    # Drop enums
    op.execute('DROP TYPE IF EXISTS bookingstatus')
    op.execute('DROP TYPE IF EXISTS hotelstatus')
    op.execute('DROP TYPE IF EXISTS subscriptionplan')
    op.execute('DROP TYPE IF EXISTS tenantstatus')
