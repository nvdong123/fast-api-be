"""update_tables

Revision ID: 005_add_json_room
Revises: 004_fix_room_images
Create Date: 2025-01-14 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '005_add_json_room'
down_revision: str = '004_fix_room_images'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Add JSON columns with default empty list
    op.add_column('rooms', sa.Column('images', postgresql.JSONB, server_default='[]'))
    op.add_column('rooms', sa.Column('amenities', postgresql.JSONB, server_default='[]'))

def downgrade():
    op.drop_column('rooms', 'images')
    op.drop_column('rooms', 'amenities')