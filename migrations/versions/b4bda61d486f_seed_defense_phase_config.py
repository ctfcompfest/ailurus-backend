"""seed defense phase feature config

Revision ID: b4bda61d486f
Revises: 198a881141f4
Create Date: 2025-08-05 21:57:09.686577

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4bda61d486f'
down_revision = '198a881141f4'
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
            "key": "ATTACK_TIME",
            "value": "2037-10-10T10:10:10Z"
        }
    ])


def downgrade():
    pass
