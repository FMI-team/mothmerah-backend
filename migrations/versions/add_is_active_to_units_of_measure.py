"""add is_active to units_of_measure

Revision ID: add_is_active_units
Revises: f6a2837f2c73
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_active_units'
down_revision = 'f6a2837f2c73'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active column to units_of_measure table
    op.add_column('units_of_measure', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")))


def downgrade() -> None:
    # Remove is_active column from units_of_measure table
    op.drop_column('units_of_measure', 'is_active')

