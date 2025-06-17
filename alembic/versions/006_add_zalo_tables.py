# alembic/versions/006_add_zalo_tables.py

"""add_zalo_tables

Revision ID: 006_add_zalo_tables
Revises: 005_add_json_room
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_zalo_tables'
down_revision = '005_add_json_room'
branch_labels = None
depends_on = None

def upgrade():
    # Tạo bảng zalo_tokens
    op.create_table(
        'zalo_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Tạo bảng zalo_users
    op.create_table(
        'zalo_users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('zalo_id', sa.String(), nullable=False, unique=True),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('shared_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_following', sa.Boolean(), default=False),
        sa.Column('followed_at', sa.DateTime(), nullable=True),
        sa.Column('unfollowed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Tạo bảng zalo_messages
    op.create_table(
        'zalo_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('zalo_message_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('attachment_type', sa.String(), nullable=True),
        sa.Column('attachment_url', sa.String(), nullable=True),
        sa.Column('direction', sa.String(), nullable=False),  # incoming/outgoing
        sa.Column('status', sa.String(), nullable=False),  # sent/delivered/failed
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['zalo_users.id'], ondelete='CASCADE')
    )

    # Tạo bảng zalo_user_tags
    op.create_table(
        'zalo_user_tags',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('tag_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['zalo_users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'tag_name', name='uq_user_tag')
    )

    # Create indexes
    op.create_index('idx_zalo_users_zalo_id', 'zalo_users', ['zalo_id'])
    op.create_index('idx_zalo_messages_user_id', 'zalo_messages', ['user_id'])
    op.create_index('idx_zalo_user_tags_user_id', 'zalo_user_tags', ['user_id'])
    op.create_index('idx_zalo_user_tags_tag_name', 'zalo_user_tags', ['tag_name'])

def downgrade():
    op.drop_table('zalo_user_tags')
    op.drop_table('zalo_messages')
    op.drop_table('zalo_users')
    op.drop_table('zalo_tokens')