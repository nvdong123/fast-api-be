"""update_tables

Revision ID: 003_update_room_relationship
Revises: 002_update_tables
Create Date: 2025-01-14 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '003_update_room_relationship'
down_revision: str = '002_update_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Drop old foreign key if exists
    op.drop_constraint('room_images_room_type_id_fkey', 'room_images', type_='foreignkey')
    
    # Drop old column
    op.drop_column('room_images', 'room_type_id')
    
    # Add new column and foreign key
    op.add_column('room_images', sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.create_foreign_key('room_images_room_id_fkey', 'room_images', 'rooms', ['room_id'], ['id'])

def downgrade():
    # Drop new foreign key
    op.drop_constraint('room_images_room_id_fkey', 'room_images', type_='foreignkey')
    
    # Drop new column
    op.drop_column('room_images', 'room_id')
    
    # Add back old column and foreign key
    op.add_column('room_images', sa.Column('room_type_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.create_foreign_key('room_images_room_type_id_fkey', 'room_images', 'room_types', ['room_type_id'], ['id'])