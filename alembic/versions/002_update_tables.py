"""update_tables

Revision ID: 002_update_tables
Revises: 001_init_database
Create Date: 2025-01-14 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '002_update_tables'
down_revision: str = '001_init_database'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Thêm các enum values mới cho hotel_status
    op.execute("ALTER TYPE hotelstatus ADD VALUE IF NOT EXISTS 'pending'")
    op.execute("ALTER TYPE hotelstatus ADD VALUE IF NOT EXISTS 'suspended'")
    op.execute("ALTER TYPE hotelstatus ADD VALUE IF NOT EXISTS 'maintenance'")

    # Bổ sung hotel_id cho room_types
    op.add_column('room_types', sa.Column('hotel_id', UUID(as_uuid=True), sa.ForeignKey('hotels.id'), nullable=False))

    # Bổ sung các cột mới cho bookings
    op.add_column('bookings', sa.Column('adult_count', sa.Integer, nullable=False, server_default='1'))
    op.add_column('bookings', sa.Column('children_count', sa.Integer, nullable=False, server_default='0'))
    op.add_column('bookings', sa.Column('guest_name', sa.String(255), nullable=True))
    op.add_column('bookings', sa.Column('guest_email', sa.String(255), nullable=True))
    op.add_column('bookings', sa.Column('guest_phone', sa.String(50), nullable=True))
    op.add_column('bookings', sa.Column('note', sa.Text, nullable=True))
    op.add_column('bookings', sa.Column('payment_status', sa.String(50), nullable=False, server_default='pending'))
    op.add_column('bookings', sa.Column('channel', sa.String(50), nullable=True))
    op.add_column('bookings', sa.Column('discount_amount', sa.Float, nullable=False, server_default='0'))
    op.add_column('bookings', sa.Column('tax_amount', sa.Float, nullable=False, server_default='0'))

    # Bổ sung cột cho booking_rooms
    op.add_column('booking_rooms', sa.Column('extra_services', postgresql.JSONB, nullable=True))
    op.add_column('booking_rooms', sa.Column('total_amount', sa.Float, nullable=False, server_default='0'))
    op.add_column('booking_rooms', sa.Column('notes', sa.Text, nullable=True))

    # Bổ sung cột cho payments 
    op.add_column('payments', sa.Column('payment_provider', sa.String(50), nullable=True))
    op.add_column('payments', sa.Column('payment_fee', sa.Float, nullable=False, server_default='0'))
    op.add_column('payments', sa.Column('refund_amount', sa.Float, nullable=True))
    op.add_column('payments', sa.Column('refund_reason', sa.Text, nullable=True))
    op.add_column('payments', sa.Column('metadata', postgresql.JSONB, nullable=True))

    # Tạo bảng promotions
    op.create_table(
        'promotions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('hotel_id', UUID(as_uuid=True), sa.ForeignKey('hotels.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('start_date', sa.DateTime, nullable=False),
        sa.Column('end_date', sa.DateTime, nullable=False),
        sa.Column('min_nights', sa.Integer, nullable=True),
        sa.Column('max_discount', sa.Float, nullable=True),
        sa.Column('room_types', postgresql.JSONB, nullable=True),
        sa.Column('usage_limit', sa.Integer, nullable=True),
        sa.Column('used_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # Tạo bảng room_prices
    op.create_table(
        'room_prices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('room_type_id', UUID(as_uuid=True), sa.ForeignKey('room_types.id'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # Tạo bảng services
    op.create_table(
        'services',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('hotel_id', UUID(as_uuid=True), sa.ForeignKey('hotels.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )

    # Add indexes
    op.create_index('ix_promotions_code', 'promotions', ['code'])
    op.create_index('ix_room_prices_date', 'room_prices', ['date'])
    op.create_index('ix_bookings_check_in', 'bookings', ['check_in'])
    op.create_index('ix_bookings_check_out', 'bookings', ['check_out'])
    op.create_index('ix_bookings_booking_number', 'bookings', ['booking_number'])

def downgrade():
    # Remove indexes
    op.drop_index('ix_promotions_code')
    op.drop_index('ix_room_prices_date')
    op.drop_index('ix_bookings_check_in')
    op.drop_index('ix_bookings_check_out')
    op.drop_index('ix_bookings_booking_number')

    # Drop tables
    op.drop_table('services')
    op.drop_table('room_prices')
    op.drop_table('promotions')

    # Remove added columns
    op.drop_column('payments', 'metadata')
    op.drop_column('payments', 'refund_reason')
    op.drop_column('payments', 'refund_amount')
    op.drop_column('payments', 'payment_fee')
    op.drop_column('payments', 'payment_provider')

    op.drop_column('booking_rooms', 'notes')
    op.drop_column('booking_rooms', 'total_amount')
    op.drop_column('booking_rooms', 'extra_services')

    op.drop_column('bookings', 'tax_amount')
    op.drop_column('bookings', 'discount_amount')
    op.drop_column('bookings', 'channel')
    op.drop_column('bookings', 'payment_status')
    op.drop_column('bookings', 'note')
    op.drop_column('bookings', 'guest_phone')
    op.drop_column('bookings', 'guest_email')
    op.drop_column('bookings', 'guest_name')
    op.drop_column('bookings', 'children_count')
    op.drop_column('bookings', 'adult_count')

    op.drop_column('room_types', 'hotel_id')

    # Remove added enum values 
    # Note: PostgreSQL does not support removing enum values
    # You would need to create a new enum type without these values