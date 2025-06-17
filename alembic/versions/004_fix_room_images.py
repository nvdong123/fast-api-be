"""update_tables

Revision ID: 004_fix_room_images
Revises: 003_update_room_relationship
Create Date: 2025-01-14 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '004_fix_room_images'
down_revision: str = '003_update_room_relationship'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Drop old table and recreate from scratch
    op.drop_table('room_images')

    # Create room_type_images table
    op.create_table(
        'room_type_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('image_url', sa.String(1024), nullable=False),
        sa.Column('thumbnail_url', sa.String(1024)),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('display_order', sa.Integer),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['room_type_id'], ['room_types.id'], ondelete='CASCADE')
    )

    # Create room_images table
    op.create_table(
        'room_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('image_url', sa.String(1024), nullable=False),
        sa.Column('thumbnail_url', sa.String(1024)),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('display_order', sa.Integer),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE')
    )

def downgrade():
    # Drop both new tables
    op.drop_table('room_images')
    op.drop_table('room_type_images')

    # Recreate original room_images table
    op.create_table(
        'room_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('image_url', sa.String(1024), nullable=False),
        sa.Column('thumbnail_url', sa.String(1024)),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('display_order', sa.Integer),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['room_type_id'], ['room_types.id'], ondelete='CASCADE')
    )