"""seed checker_before_contest config

Revision ID: b4bda61d486f
Revises: b265af5c2d6c
Create Date: 2025-08-05 21:57:09.686577

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4bda61d486f'
down_revision = 'b265af5c2d6c'
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
            "key": "CHECKER_BEFORE_CONTEST",
            "value": "false"
        }
    ])


def downgrade():
    pass
