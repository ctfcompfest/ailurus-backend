"""Seed application default configuration

Revision ID: f9e5ec72e965
Revises: 9f9f857df3fb
Create Date: 2024-07-26 02:03:34.625852

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9e5ec72e965'
down_revision = '9f9f857df3fb'
branch_labels = None
depends_on = None


def upgrade():
    config_table = sa.table(
        "config",
        sa.column("id", sa.Integer()),
        sa.column("key", sa.String()),
        sa.column("value", sa.String())
    )
    op.bulk_insert(config_table, [
        {
            "key": "WORKER_SECRET",
            "value": "secret"
        },
    ])


def downgrade():
    pass
